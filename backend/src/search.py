from urllib.parse import quote
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json
import numpy as np
from src.ranker import EmbeddingGenerator
from src.scoring import RelevanceScorer, cosine_similarity

app = FastAPI()

# Initialize scoring system
scorer = RelevanceScorer(min_similarity=0.3)

# Load stored embeddings
CURRENT_JSON_PATH = Path("output/current_doc.json")

def load_json(path: Path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Deduplicate JSON by file_path to avoid repeated docs
            seen_files = set()
            unique_docs = []
            for doc in data.get("documents", []):
                file_path = doc.get("file_path", "")
                if file_path not in seen_files:
                    unique_docs.append(doc)
                    seen_files.add(file_path)
            return unique_docs
    return []

current_docs = load_json(CURRENT_JSON_PATH)

embedder = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")

class SearchRequest(BaseModel):
    selected_text: str
    top_k: int = 3
    min_score: float = 0.3  # optional threshold to filter low similarity


@app.post("/search")
def search_recommendations(req: SearchRequest):
    query_text = req.selected_text.strip()
    top_k = req.top_k
    min_score = req.min_score

    if not query_text:
        return {"error": "No text provided"}

    # Embed query text
    query_embedding = np.array(embedder.embed_texts([query_text])[0])

    results_by_doc = []

    for doc in current_docs:
        source = "current"
        doc_matches = []

        for sec in doc.get("sections", []):
            sec_embedding = np.array(sec.get("embedding", []))
            if sec_embedding.size == 0:
                continue

            score = cosine_similarity(query_embedding, sec_embedding)
            if score < min_score:
                continue  # Skip low relevance sections

            snippets = [s["text"] for s in sec.get("snippets", [])][:3]
            snippet_text = snippets[0] if snippets else ""

            doc_matches.append({
                "section": sec.get("heading", ""),
                "page_number": sec.get("page_number", 0),
                "snippets": snippets,
                "top_snippet": snippet_text,
                "score": float(score)
            })

        if doc_matches:
            # Pick the single highest-scoring section
            best_match = max(doc_matches, key=lambda x: x["score"])
            pdf_file_path = doc.get("file_path", "")
            public_pdf_url = "/uploads/" + quote(Path(pdf_file_path).name)

            results_by_doc.append({
                "doc_id": doc.get("doc_id", ""),
                "title": doc.get("title", ""),
                "pdf_url": public_pdf_url,
                "source": source,
                "matches": [best_match]
            })

    # Deduplicate final results by pdf_url (avoids repeated PDFs)
    seen_files = set()
    unique_results_by_doc = []
    for rec in results_by_doc:
        file_key = rec["pdf_url"]
        if file_key not in seen_files:
            unique_results_by_doc.append(rec)
            seen_files.add(file_key)

    # Sort documents by the highest section score
    results_sorted = sorted(
        unique_results_by_doc,
        key=lambda d: d["matches"][0]["score"],
        reverse=True
    )[:top_k]

    return results_sorted
