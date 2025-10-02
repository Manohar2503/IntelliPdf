import os
import json
import re
import requests
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import google.generativeai as genai

# ====================================
# GEMINI-ONLY LLM WRAPPER (Direct SDK)
# ====================================
def get_llm_response(messages):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable not set.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Configure Gemini SDK using API key
    genai.configure(api_key=api_key)

    # Combine system + user messages into a single prompt
    prompt = "\n".join([msg["content"] for msg in messages])

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        text_output = (response.text or "").strip()
        # Remove triple backticks if present
        text_output = re.sub(r"^```(?:json)?\s*|\s*```$", "", text_output, flags=re.MULTILINE)
        return text_output
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")

# ====================================
# INSIGHTS LOGIC
# ====================================
router = APIRouter()
RECOMMENDATION_API = os.getenv("RECOMMENDATION_API", "http://localhost:8080/search")

class InsightsRequest(BaseModel):
    selected_text: str
    top_k: int = 3

def build_insights_prompt(selected_text: str, related_sections: List[dict]):
    related_formatted = "\n".join([
        f"- {sec['title']} (Page {sec['page_number']}): {sec['snippet']}"
        for sec in related_sections
    ])

    return [
        {
            "role": "system",
            "content": (
                "You are an AI that produces structured insights from a selected PDF passage "
                "and related past document sections. Output must be valid JSON ONLY with keys:\n"
                "key_insights: list of concise factual insights\n"
                "did_you_know: list of interesting/surprising facts\n"
                "contradictions: list of conflicts, disagreements, or counterpoints\n"
                "inspirations: list of possible applications, ideas, or cross-connections\n"
                "No text outside the JSON. No explanations."
            )
        },
        {
            "role": "user",
            "content": (
                f"Selected text:\n{selected_text}\n\n"
                f"Related sections:\n{related_formatted}\n\n"
                "Now produce the structured insights JSON."
            )
        }
    ]

def get_related_sections(selected_text: str, top_k: int):
    try:
        resp = requests.post(RECOMMENDATION_API, json={
            "selected_text": selected_text,
            "top_k": top_k
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"Error calling recommendations API: {e}")

    related_sections = []
    for doc in data:
        for match in doc.get("matches", []):
            related_sections.append({
                "title": doc.get("title", ""),
                "page_number": match.get("page_number", -1),
                "snippet": match.get("top_snippet", "")
            })
    return related_sections

@router.post("/insights")
def generate_insights(req: InsightsRequest):
    if not req.selected_text.strip():
        return {"error": "No text provided"}

    related_sections = get_related_sections(req.selected_text, req.top_k)

    if not related_sections:
        return {"error": "No related sections found", "related_sections": []}

    messages = build_insights_prompt(req.selected_text, related_sections)

    try:
        raw_output = get_llm_response(messages)
    except Exception as e:
        return {"error": f"LLM call failed: {e}"}

    try:
        insights_data = json.loads(raw_output)
    except json.JSONDecodeError:
        return {"error": "LLM output was not valid JSON", "raw_output": raw_output}

    return {"insights": insights_data, "related_sections": related_sections}
