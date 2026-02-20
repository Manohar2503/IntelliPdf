from typing import List, Dict, Optional
from pydantic import BaseModel
from pathlib import Path
import os
import json
import numpy as np
import hashlib
import google.generativeai as genai
from dotenv import load_dotenv
from src.summarizer import DocumentSummarizer
from src.singletons import embedder

load_dotenv()

# ✅ Enable hybrid pipeline for research-grade summarization
doc_summarizer = DocumentSummarizer()
print(doc_summarizer.get_hybrid_pipeline_status())
print("🔥 HYBRID PIPELINE READY 🔥")


api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set")
genai.configure(api_key=api_key)


class ImageReference(BaseModel):
    filename: str
    page: int
    path: str
    caption: Optional[str] = None
    relevance_score: float = 0.0
    ocr_text: Optional[str] = None
    ai_labels: Optional[List[Dict[str, float]]] = None


class ChatbotResponse(BaseModel):
    response: str
    sources: List[Dict] = []
    is_summary: bool = False
    relevant_images: List[ImageReference] = []


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_current_docs(current_doc_path: Optional[Path] = None) -> List[Dict]:
    if current_doc_path is None:
        current_doc_path = _project_root() / "output" / "current_doc.json"

    if not current_doc_path.exists():
        return []

    with open(current_doc_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get("documents", [])
            if isinstance(data, list):
                return data
            return []
        except:
            return []


def _cosine_similarity(a, b) -> float:
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    if a.size == 0 or b.size == 0:
        return 0.0
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def find_relevant_sections(query: str, current_doc_path: Optional[Path] = None, top_k: int = 3):
    docs = _load_current_docs(current_doc_path=current_doc_path)
    if not docs:
        return []

    query_emb = np.array(embedder.embed_texts([query])[0], dtype=float)

    candidates = []
    for doc in docs:
        for sec in doc.get("sections", []):
            sec_emb = sec.get("embedding", [])
            if not sec_emb:
                continue
            score = _cosine_similarity(query_emb, sec_emb)

            snippet_list = sec.get("snippets", [])
            snippets = []
            for s in snippet_list:
                if isinstance(s, dict):
                    snippets.append(s.get("text", ""))
                else:
                    snippets.append(str(s))

            candidates.append({
                "doc_id": doc.get("doc_id"),
                "title": doc.get("title"),
                "section_heading": sec.get("heading"),
                "page_number": sec.get("page_number"),
                "top_snippet": snippets[0] if snippets else sec.get("content", ""),
                "score": float(score),
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_k]


def build_context_from_sections(sections: List[Dict], char_limit: int = 3000) -> str:
    parts = []
    for s in sections:
        parts.append(
            f"Source: {s.get('title')} | Section: {s.get('section_heading')} | Page: {s.get('page_number')}\n"
            f"{s.get('top_snippet')}"
        )
    text = "\n\n".join(parts)
    return text[:char_limit]


def generate_answer_with_gemini(query: str, context: str):
    system = (
        "Answer ONLY from the given context. "
        "If missing, say: 'The document does not contain that information.'"
    )
    prompt = f"{system}\n\nContext:\n{context}\n\nQuestion: {query}\nAnswer:"

    model = genai.GenerativeModel("gemini-2.5-flash")
    res = model.generate_content(prompt)
    return res.text if hasattr(res, "text") else str(res)


def get_chatbot_response(query: str, current_doc_path: Optional[Path] = None, top_k: int = 3) -> ChatbotResponse:
    if not query:
        return ChatbotResponse(response="Invalid query", sources=[])

    sections = find_relevant_sections(query, current_doc_path=current_doc_path, top_k=top_k)
    if not sections:
        return ChatbotResponse(response="No relevant content found.", sources=[])

    context = build_context_from_sections(sections)
    answer = generate_answer_with_gemini(query, context)

    return ChatbotResponse(response=answer.strip(), sources=sections, relevant_images=[])


def get_initial_summary(current_doc_path: Optional[Path] = None) -> ChatbotResponse:
    docs = _load_current_docs(current_doc_path=current_doc_path)
    if not docs:
        return ChatbotResponse(response="No documents loaded yet.", is_summary=True)

    all_sections = []
    for doc in docs:
        all_sections.extend(doc.get("sections", []))

    try:
        print(f"[DEBUG] Loaded {len(all_sections)} sections for summarization")
        print(f"[DEBUG] Hybrid pipeline enabled: {doc_summarizer.use_hybrid_pipeline}")
        print(f"[DEBUG] Hybrid pipeline initialized: {doc_summarizer.hybrid_pipeline is not None}")

        summary_data = doc_summarizer.summarize_document(all_sections)
        print(f"[DEBUG] Summary data generated: {list(summary_data.keys())}")

        # Save per-document summary files under session summaries/
        try:
            if current_doc_path is not None and current_doc_path.exists():
                # current_doc.json path: .../sessions/{sessionId}/output/current_doc.json
                session_dir = current_doc_path.parent.parent
                summaries_dir = session_dir / "summaries"
                summaries_dir.mkdir(parents=True, exist_ok=True)

                from datetime import datetime

                for doc in docs:
                    doc_id = doc.get("doc_id") or hashlib.md5(json.dumps(doc).encode("utf-8")).hexdigest()
                    out_path = summaries_dir / f"{doc_id}_summary.json"
                    payload = {
                        "doc_id": doc_id,
                        "title": doc.get("title"),
                        "generated_at": datetime.utcnow().isoformat() + "Z",
                        "mode": "hybrid" if doc_summarizer.use_hybrid_pipeline else "fast",
                        "summary": summary_data,
                    }
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(payload, f, indent=2, ensure_ascii=False)
                    print(f"[INFO] Saved summary to {out_path}")
        except Exception as e:
            print(f"[WARN] Failed to save summary files: {e}")

        msg = doc_summarizer.generate_initial_message(summary_data)
        print(f"[DEBUG] Initial message generated, length: {len(msg)}")
        return ChatbotResponse(response=msg, is_summary=True)
    except Exception as e:
        print(f"[ERROR] Summary generation failed: {e}")
        import traceback
        traceback.print_exc()
        return ChatbotResponse(
            response="Loaded document, but summary generation failed.",
            is_summary=True
        )
