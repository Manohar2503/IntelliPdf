from typing import List, Dict
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from .text_repair import TextRepair


class FusionEngine:

    def __init__(
        self,
        embed_model: str = "all-MiniLM-L6-v2",
        redundancy_thresh: float = 0.92,
    ):
        self.embedder = SentenceTransformer(embed_model)
        self.redundancy_thresh = redundancy_thresh

    def _split_sentences(self, text: str) -> List[str]:
        return TextRepair.clean_sentences(TextRepair.split_sentences(text))

    def _normalized_signature(self, sentence: str) -> str:
        return re.sub(r"\W+", " ", sentence.lower()).strip()

    def _lexical_overlap(self, a: str, b: str) -> float:
        ta = set(re.findall(r"\w+", a.lower()))
        tb = set(re.findall(r"\w+", b.lower()))
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    def _dedupe_sentences(self, sentences: List[str]) -> List[str]:

        if not sentences:
            return []

        emb = self.embedder.encode(sentences, convert_to_numpy=True, show_progress_bar=False)

        sims = cosine_similarity(emb)

        keep = []
        seen_signatures = set()

        for i in range(len(sentences)):
            sig = self._normalized_signature(sentences[i])
            if not sig or sig in seen_signatures:
                continue

            duplicate = False

            for j in keep:
                semantic_dup = sims[i, j] > self.redundancy_thresh
                lexical_dup = self._lexical_overlap(sentences[i], sentences[j]) > 0.82
                if semantic_dup or lexical_dup:
                    duplicate = True
                    break

            if not duplicate:
                keep.append(i)
                seen_signatures.add(sig)

        return [sentences[i] for i in keep]

    def merge(self,candidate_summaries: List[Dict[str, str]],extractive_summary: str = None,
    ) -> str:
        all_sents = []
        all_meta = []
        position = 0
        for cand in candidate_summaries:
            if not cand:
                continue
            for model_name, txt in cand.items():
                if txt:
                    for sent in self._split_sentences(txt):
                        all_sents.append(sent)
                        all_meta.append({
                            "source": model_name,
                            "is_extractive": False,
                            "position": position,
                        })
                        position += 1
        if extractive_summary:
            for sent in self._split_sentences(extractive_summary):
                all_sents.append(sent)
                all_meta.append({
                    "source": "extractive",
                    "is_extractive": True,
                    "position": position,
                })
                position += 1
        unique_sents = self._dedupe_sentences(all_sents)
        if not unique_sents:
            return ""
        meta_map = {self._normalized_signature(s): m for s, m in zip(all_sents, all_meta)}
        emb = self.embedder.encode(unique_sents, convert_to_numpy=True, show_progress_bar=False)
        doc_vec = emb.mean(axis=0, keepdims=True)
        sims = cosine_similarity(emb, doc_vec).ravel()
        scored = []
        for i, sent in enumerate(unique_sents):
            length_bonus = min(len(sent.split()) / 20, 1.0)
            sim_score = sims[i]
            sig = self._normalized_signature(sent)
            meta = meta_map.get(sig, {"is_extractive": False, "position": i})
            extractive_bonus = 0.08 if meta["is_extractive"] else 0.0
            score = sim_score * 0.72 + length_bonus * 0.2 + extractive_bonus
            scored.append((score, meta["position"], sent))
        scored.sort(key=lambda x: x[0], reverse=True)
        selected = []
        word_budget = max(90, min(220, int(sum(len(s.split()) for s in unique_sents) * 0.55)))
        total_words = 0
        for _, pos, sent in scored:
            sent_words = len(sent.split())
            if total_words + sent_words > word_budget and len(selected) >= 4:
                continue
            selected.append((pos, sent))
            total_words += sent_words
            if total_words >= word_budget:
                break
        selected.sort(key=lambda x: x[0])
        ordered = [s for _, s in selected]
        merged = " ".join(ordered).strip()
        merged = self._final_cleanup(merged)
        return merged
    
    
    
    def coherence_score(self, text: str) -> float:

        sents = self._split_sentences(text)

        if len(sents) < 2:
            return 1.0

        emb = self.embedder.encode(sents, convert_to_numpy=True, show_progress_bar=False)

        sims = cosine_similarity(emb)

        adj = [sims[i, i + 1] for i in range(len(sents) - 1)]

        return float(np.mean(adj))

    def _final_cleanup(self, text: str) -> str:
        sentences = self._split_sentences(text)
        sentences = [s for s in sentences if len(s.split()) >= 6]
        paragraphs = TextRepair.paragraphize(sentences, per_paragraph=3)
        return "\n\n".join(paragraphs).strip()
