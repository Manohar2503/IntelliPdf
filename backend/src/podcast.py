import os
import re
import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
from sarvamai import SarvamAI
from sarvamai.play import save

router = APIRouter()

# ======================
# SARVAMAI LLM HELPER
# ======================
def get_llm_response(prompt: str):
    api_key = os.getenv("SERVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SERVAM_API_KEY environment variable not set.")

    model_name = os.getenv("SERVAM_MODEL", "sarvam-ai-model-name") # Default model name for SarvamAI

    try:
        client = SarvamAI(api_subscription_key=api_key)
        response = client.chat.completions(
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        text_output = response.choices[0].message.content.strip()
        text_output = re.sub(r"^```(?:\w+)?\s*|\s*```$", "", text_output, flags=re.MULTILINE)
        return text_output
    except Exception as e:
        raise RuntimeError(f"SarvamAI API call failed: {e}")

# ======================
# TTS HELPER
# ======================
def text_to_speech(text: str, filename: str):
    sarvam_api_key = os.getenv("SARVAM_API_KEY")
    if not sarvam_api_key:
        raise RuntimeError("SARVAM_API_KEY environment variable not set for SarvamAI TTS.")

    client = SarvamAI(api_subscription_key=sarvam_api_key)

    audio = client.text_to_speech.convert(
        target_language_code="hi-IN", # Changed to match user's demo, consider making this configurable
        text=text
    )

    os.makedirs("static/audio", exist_ok=True)
    path = os.path.join("static/audio", filename)
    save(audio, path)

    return f"/static/audio/{filename}"

# ======================
# API ROUTE
# ======================
class PodcastRequest(BaseModel):
    insights: Dict

@router.post("/podcast")
def generate_podcast(req: PodcastRequest):
    # Step 1: Turn insights into a friendly podcast script
    insights_str = "\n".join(
        f"{key}: {', '.join(val)}"
        for key, val in req.insights.items() if isinstance(val, list)
    )

    prompt = (
        "You are a friendly podcast host. Turn the following insights into an engaging spoken podcast script "
        "that feels natural and conversational, lasting around 1-2 minutes. "
        "Do not include bullet points — make it sound like a human talking.\n\n"
        f"{insights_str}"
    )

    try:
        script = get_llm_response(prompt)
    except Exception as e:
        return {"error": str(e)}

    # Step 2: Convert script to audio
    try:
        audio_filename = f"podcast_{uuid.uuid4().hex}.mp3"
        audio_url = text_to_speech(script, audio_filename)
    except Exception as e:
        return {"error": f"TTS failed: {e}", "script": script}

    return {
        "script": script,
        "audio_url": audio_url
    }
