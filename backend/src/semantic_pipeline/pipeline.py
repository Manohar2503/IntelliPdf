from typing import List, Dict, Any
from .structural_cleaner import StructuralCleaner
from .embedding_graph import EmbeddingGraph
from .extractive_ranker import ExtractiveRanker
from .chunk_selector import ChunkSelector
from .abstractive_summarizer import AbstractiveSummarizer
from .fusion_engine import FusionEngine
from .evaluator import Evaluator
from .output_generator import OutputGenerator


class HybridSummarizationPipeline:
    """
    Multi-Stage Hybrid Summarization Pipeline
    Optimized for higher ROUGE + semantic quality
    """

    def __init__(self, config: Dict[str, Any] = None):

        self.cleaner = StructuralCleaner()
        self.graph = EmbeddingGraph()
        self.ranker = ExtractiveRanker()
        self.selector = ChunkSelector()
        self.summarizer = AbstractiveSummarizer()
        self.fuser = FusionEngine()
        self.evaluator = Evaluator()
        self.output_gen = OutputGenerator()

        self.config = config or {}

    def run(
        self,
        raw_text: str,
        reference: str = None,
        use_pegasus: bool = False,
    ) -> Dict[str, Any]:

        # 1) Structural cleaning
        paragraphs = self.cleaner.clean(raw_text)

        # 2) Embedding graph
        self.graph.fit(paragraphs)

        # 3) Extractive ranking (INCREASED FOR ROUGE)
        ranked = self.ranker.rank(paragraphs, top_k=40)

        # 4) Chunk selection (more context)
        chunks = self.selector.select(
            ranked,
            max_chunk_sentences=8,
        )

        chunk_texts = [" ".join(c) for c in chunks]

        # Extractive guidance (IMPORTANT FOR ROUGE)
        extractive_summary = " ".join([s for s, _ in ranked[:10]])

        # 5) Abstractive summarization
        candidates = self.summarizer.summarize_parallel(
            chunk_texts,
            use_pegasus=use_pegasus,
            max_workers=2,
        )
        final = self.fuser.merge(
            candidates,
            extractive_summary=extractive_summary,
        )
        coherence = self.fuser.coherence_score(final)
        metrics = {}
        if reference:
            metrics["rouge"] = self.evaluator.rouge_scores(final, reference)
            metrics["semantic_similarity"] = self.evaluator.semantic_similarity(final, reference)
        structured = self.output_gen.generate(final)

        return {
            "paragraphs": paragraphs,
            "ranked_sentences": ranked,
            "chunks": chunk_texts,
            "candidates": candidates,
            "final_summary": final,
            "coherence": coherence,
            "metrics": metrics,
            "structured": structured,
        }
