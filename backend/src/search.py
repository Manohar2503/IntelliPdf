from urllib.parse import quote
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json
import numpy as np
from src.ranker import EmbeddingGenerator

app = FastAPI()

# Load stored embeddings
PAST_JSON_PATH = Path("output/output.json")
CURRENT_JSON_PATH = Path("output/current_doc.json")

def load_json(path: Path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("documents", [])
    return []

past_docs = load_json(PAST_JSON_PATH)
current_docs = load_json(CURRENT_JSON_PATH)

embedder = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")

class SearchRequest(BaseModel):
    selected_text: str
    top_k: int = 3
    min_score: float = 0.3  # optional threshold to filter low similarity

def cosine_similarity(vec1, vec2):
    """Cosine similarity between two vectors."""
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(vec1, vec2) / (norm1 * norm2)

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
    all_docs = past_docs + current_docs

    for doc in all_docs:
        source = "past" if doc in past_docs else "current"
        doc_matches = []

        for sec in doc["sections"]:
            sec_embedding = np.array(sec.get("embedding", []))
            if sec_embedding.size == 0:
                continue

            score = cosine_similarity(query_embedding, sec_embedding)
            if score < min_score:
                continue  # Skip low relevance sections

            snippets = [s["text"] for s in sec.get("snippets", [])][:3]  # Top 3 snippets
            snippet_text = snippets[0] if snippets else ""

            doc_matches.append({
                "section": sec["heading"],
                "page_number": sec["page_number"],
                "snippets": snippets,
                "top_snippet": snippet_text,
                "score": float(score)
            })

        if doc_matches:
            # Sort matches within document
            doc_matches_sorted = sorted(doc_matches, key=lambda x: x["score"], reverse=True)[:top_k]
            pdf_file_path = doc.get("file_path", "")
            public_pdf_url = "/uploads/" + quote(Path(pdf_file_path).name)
            
            results_by_doc.append({
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "pdf_url": public_pdf_url,
                "source": source,
                "matches": doc_matches_sorted
            })

    # Sort documents by the highest scoring section in each doc
    results_sorted = sorted(results_by_doc, key=lambda d: d["matches"][0]["score"], reverse=True)[:top_k]

    return results_sorted
