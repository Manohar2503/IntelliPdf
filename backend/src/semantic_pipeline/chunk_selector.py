from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class ChunkSelector:

    def __init__(
        self,
        embed_model: str = "all-MiniLM-L6-v2",
        redundancy_thresh: float = 0.92,
    ):
        self.embedder = SentenceTransformer(embed_model)
        self.redundancy_thresh = redundancy_thresh

    def select(self,ranked_sentences: List[Tuple[str, float]],max_chunk_sentences: int = 10,
    ) -> List[List[str]]:
        sents = [s for s, _ in ranked_sentences]
        if not sents:
            return []
        emb = self.embedder.encode(sents, convert_to_numpy=True)
        sims = cosine_similarity(emb)
        selected = []
        used = set()
        for i, sent in enumerate(sents):
            if i in used:
                continue
            chunk = [sent]
            chunk_indices = [i]
            used.add(i)
            neighbors = list(range(i + 1, min(len(sents), i + 10)))
            for j in neighbors:
                if len(chunk) >= max_chunk_sentences:
                    break
                redundant = False
                for k_idx in chunk_indices:
                    if sims[j, k_idx] > self.redundancy_thresh:
                        redundant = True
                        break
                if not redundant:
                    chunk.append(sents[j])
                    chunk_indices.append(j)
                    used.add(j)
            selected.append(chunk)
        return selected
