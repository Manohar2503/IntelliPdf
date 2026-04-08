import os
import json
import re
import requests
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List
import google.generativeai as genai


def get_llm_response(messages):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable not set.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    genai.configure(api_key=api_key)

    prompt = "\n".join([msg["content"] for msg in messages])

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        text_output = (response.text or "").strip()

        # Remove triple backticks if present
        text_output = re.sub(
            r"^```(?:json)?\s*|\s*```$", "", text_output, flags=re.MULTILINE
        )
        return text_output
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")


# ====================================
# INSIGHTS LOGIC
# ====================================
router = APIRouter()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080").rstrip("/")
RECOMMENDATION_API = f"{BACKEND_URL}/search"


class InsightsRequest(BaseModel):
    selected_text: str
    top_k: int = 3


def build_insights_prompt(selected_text: str, related_sections: List[dict]):
    related_formatted = "\n".join(
        [
            f"- {sec['title']} (Page {sec['page_number']}): {sec['snippet']}"
            for sec in related_sections
        ]
    )

    return [
        {
            "role": "system",
            "content": (
                "You are an AI that produces structured insights from a selected PDF passage "
                "and related document sections. Output must be valid JSON ONLY with keys:\n"
                "key_insights: list of concise factual insights\n"
                "did_you_know: list of interesting/surprising facts\n"
                "contradictions: list of conflicts, disagreements, or counterpoints\n"
                "inspirations: list of possible applications, ideas, or cross-connections\n"
                "No text outside the JSON. No explanations."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Selected text:\n{selected_text}\n\n"
                f"Related sections:\n{related_formatted}\n\n"
                "Now produce the structured insights JSON."
            ),
        },
    ]


def get_related_sections(selected_text: str, top_k: int, sessionId: str):
    """
    ✅ sessionId is REQUIRED so results are user-wise
    Backend returns: { "results": [ ... ] }
    """
    try:
        resp = requests.post(
            f"{RECOMMENDATION_API}?sessionId={sessionId}",
            json={
                "selected_text": selected_text,
                "top_k": top_k,
                "min_score": 0.3,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()  # {"results": [...]}
    except Exception as e:
        raise RuntimeError(f"Error calling recommendations API: {e}")

    related_sections = []
    for item in data.get("results", []):
        related_sections.append(
            {
                "title": item.get("title", ""),
                "page_number": item.get("page_number", -1),
                "snippet": (item.get("snippets", [""])[0] if item.get("snippets") else ""),
            }
        )

    return related_sections


@router.post("/insights")
def generate_insights(req: InsightsRequest, sessionId: str = Query(...)):
    """
    ✅ Example:
    POST /insights?sessionId=xxxx
    body: { "selected_text": "...", "top_k": 3 }
    """
    if not req.selected_text.strip():
        return {"error": "No text provided"}

    # ✅ get related sections only for that user session
    related_sections = get_related_sections(req.selected_text, req.top_k, sessionId)

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
