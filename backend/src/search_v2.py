"""
Enhanced search functionality with advanced scoring mechanisms
"""

from pathlib import Path
import json
import numpy as np
from typing import List, Dict, Any
from pydantic import BaseModel

from src.ranker import EmbeddingGenerator
from src.scoring import RelevanceScorer

# Initialize scoring system
scorer = RelevanceScorer(min_similarity=0.3)
embedder = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")

# Paths
PAST_JSON_PATH = Path("output/output.json")
CURRENT_JSON_PATH = Path("output/current_doc.json")

class SearchRequest(BaseModel):
    selected_text: str
    top_k: int = 5
    min_score: float = 0.3

def load_json(path: Path) -> List[Dict]:
    """Load JSON data from file"""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("documents", [])
    return []

def search_documents(req: SearchRequest) -> List[Dict[str, Any]]:
    """
    Enhanced search with advanced scoring mechanisms
    """
    query_text = req.selected_text.strip()
    if not query_text:
        return []

    # Load documents
    docs = load_json(CURRENT_JSON_PATH)
    if not docs:
        docs = load_json(PAST_JSON_PATH)

    # Embed query
    query_embedding = np.array(embedder.embed_texts([query_text])[0])

    results_by_doc = []
    total_sections_searched = 0
    relevant_sections = 0
    
    # Search through documents
    for doc in docs:
        doc_matches = []
        source = doc.get("title", "") or doc.get("file_path", "")

        for sec in doc.get("sections", []):
            total_sections_searched += 1
            sec_embedding = np.array(sec.get("embedding", []))
            if sec_embedding.size == 0:
                continue

            # Get comprehensive scoring
            scores = scorer.score_section(
                sec_embedding,
                query_embedding,
                additional_weights=[1.0]  # Can be customized based on metadata
            )

            if scores['weighted_score'] >= req.min_score:
                relevant_sections += 1
                doc_matches.append({
                    "section": sec.get("heading", ""),
                    "snippets": sec.get("snippets", [sec.get("text", "")]),
                    "page_number": sec.get("page_number"),
                    "base_score": float(scores['similarity']),
                    "advanced_score": float(scores['advanced_score']),
                    "final_score": float(scores['weighted_score'])
                })

        if doc_matches:
            # Sort matches by final score
            doc_matches_sorted = sorted(
                doc_matches,
                key=lambda x: x["final_score"],
                reverse=True
            )
            
            results_by_doc.append({
                "source": source,
                "matches": doc_matches_sorted
            })

    # Calculate overall metrics
    if relevant_sections > 0:
        metrics = scorer.evaluate_results(
            relevant_count=relevant_sections,
            retrieved_count=len(results_by_doc),
            true_positives=len([d for d in results_by_doc if any(m["final_score"] > 0.5 for m in d["matches"])])
        )
        print(f"Search Metrics: {metrics}")  # Log metrics for monitoring

    # Return top results sorted by best match score
    return sorted(
        results_by_doc,
        key=lambda d: max(m["final_score"] for m in d["matches"]),
        reverse=True
    )[:req.top_k]