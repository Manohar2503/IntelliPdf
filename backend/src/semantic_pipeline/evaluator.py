from typing import Dict, Tuple
import re
from collections import Counter
import numpy as np
from sentence_transformers import SentenceTransformer


def _ngrams(text: str, n: int):
    tokens = re.findall(r"\w+", text.lower())
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _rouge_n(hyp: str, ref: str, n: int = 1) -> Dict[str, float]:
    hyp_ngrams = _ngrams(hyp, n)
    ref_ngrams = _ngrams(ref, n)
    if not ref_ngrams or not hyp_ngrams:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    hyp_counts = Counter(hyp_ngrams)
    ref_counts = Counter(ref_ngrams)
    overlap = sum(min(hyp_counts[g], ref_counts[g]) for g in hyp_counts)
    precision = overlap / max(len(hyp_ngrams), 1)
    recall = overlap / max(len(ref_ngrams), 1)
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


class Evaluator:
    """Evaluation loop computing ROUGE-n and semantic similarity."""

    def __init__(self, embed_model: str = "all-MiniLM-L6-v2"):
        self.embedder = SentenceTransformer(embed_model)

    def rouge_scores(self, hypothesis: str, reference: str) -> Dict[str, Dict[str, float]]:
        return {"rouge-1": _rouge_n(hypothesis, reference, 1), "rouge-2": _rouge_n(hypothesis, reference, 2)}

    def semantic_similarity(self, hypothesis: str, reference: str) -> float:
        if not hypothesis or not reference:
            return 0.0
        emb = self.embedder.encode([hypothesis, reference], convert_to_numpy=True, show_progress_bar=False)
        v1, v2 = emb[0], emb[1]
        sim = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9))
        return sim
