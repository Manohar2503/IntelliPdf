"""Small runner demonstrating the hybrid summarization pipeline."""
from .pipeline import HybridSummarizationPipeline


def demo():
    text = (
        "This is a short demo document. It explains the pipeline.\n\n"
        "Machine learning can be used to summarize documents. "
        "This text contains several sentences that will be cleaned, embedded, ranked, chunked, and summarized."
    )
    pipeline = HybridSummarizationPipeline()
    out = pipeline.run(text)
    print("Final summary:\n", out["final_summary"])
    print("Structured recap:\n", out["structured"])


if __name__ == "__main__":
    demo()
