from typing import List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class EmbeddingGraph:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.paragraphs: List[str] = []
        self.embeddings: np.ndarray = None
        self.similarity: np.ndarray = None

    def fit(self, paragraphs: List[str]):
        self.paragraphs = paragraphs
        if not paragraphs:
            self.embeddings = np.array([])
            self.similarity = np.array([[]])
            return
        self.embeddings = self.model.encode(paragraphs, show_progress_bar=False, convert_to_numpy=True)
        self.similarity = cosine_similarity(self.embeddings)

    def get_similarity_matrix(self) -> np.ndarray:
        return self.similarity

    def top_k_similar(self, idx: int, k: int = 5) -> List[Tuple[int, float]]:
        if self.similarity is None or idx >= len(self.paragraphs):
            return []
        sims = self.similarity[idx]
        order = np.argsort(-sims)
        res = [(i, float(sims[i])) for i in order[1 : 1 + k]]
        return res

    def important_nodes(self, top_n: int = 5) -> List[int]:
        # importance by degree (sum similarity)
        if self.similarity is None:
            return []
        scores = self.similarity.sum(axis=1)
        return list(np.argsort(-scores)[:top_n])
