"""
This file is intentionally kept LIGHT to avoid heavy slow clustering summary.

Old version used:
- EmbeddingGenerator (slow)
- KMeans clustering (slow)
- TF-IDF (extra CPU)

We removed it for performance reasons.
"""

from typing import List

class EnhancedSummarizer:
    def cluster_summarize(self, text_sections: List[str], num_clusters: int = 5, top_k: int = 3) -> List[str]:
        # ✅ Fast fallback: just return first few sentences
        return text_sections[: min(len(text_sections), top_k)]

def split_into_sentences(text: str) -> List[str]:
    import re
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]
