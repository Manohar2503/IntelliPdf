from typing import List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class ExtractiveRanker:
    """Ranks sentences by combined TF-IDF and semantic relevance.
    Produces top-k salient sentences from paragraph blocks.
    """

    def __init__(self, embed_model: str = "all-MiniLM-L6-v2"):
        self.tf_vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.embedder = SentenceTransformer(embed_model)

    def _sentences_from_paragraphs(self, paragraphs: List[str]) -> List[str]:
        # naive sentence split
        sents = []
        for p in paragraphs:
            parts = [s.strip() for s in p.split('.') if s.strip()]
            sents.extend([s + '.' for s in parts])
        return sents

    def rank(self, paragraphs: List[str], top_k: int = 10) -> List[Tuple[str, float]]:
        sents = self._sentences_from_paragraphs(paragraphs)
        if not sents:
            return []
        # TF-IDF scores
        tfidf = self.tf_vectorizer.fit_transform(sents)
        tf_scores = np.asarray(tfidf.sum(axis=1)).ravel()

        # Semantic relevance: similarity to document mean embedding
        emb = self.embedder.encode(sents, convert_to_numpy=True, show_progress_bar=False)
        doc_vec = emb.mean(axis=0, keepdims=True)
        sem_scores = cosine_similarity(emb, doc_vec).ravel()

        # Combine scores (normalized)
        if tf_scores.max() > 0:
            tf_norm = (tf_scores - tf_scores.min()) / (tf_scores.max() - tf_scores.min())
        else:
            tf_norm = tf_scores
        if sem_scores.max() > 0:
            sem_norm = (sem_scores - sem_scores.min()) / (sem_scores.max() - sem_scores.min())
        else:
            sem_norm = sem_scores

        combined = 0.3 * tf_norm + 0.7 * sem_norm
        order = list(np.argsort(-combined)[:top_k])
        return [(sents[i], float(combined[i])) for i in order]
