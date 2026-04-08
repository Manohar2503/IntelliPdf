"""
Integration example: Using the hybrid semantic summarization pipeline
with the existing DocumentSummarizer class.
"""

from src.summarizer import DocumentSummarizer


def example_basic_usage():
    """Example 1: Basic usage with default settings (fast extractive path)."""
    summarizer = DocumentSummarizer()
    
    sections = [
        {
            "heading": "Introduction",
            "content": "This is a sample document section. It contains important information about machine learning.",
            "page_number": 1,
        },
        {
            "heading": "Methods",
            "content": "We use transformer models for efficient document summarization. Our approach combines extractive and abstractive techniques.",
            "page_number": 2,
        },
    ]
    
    result = summarizer.summarize_document(sections)
    print("Brief Summary:")
    print(result["brief_summary"])
    print("\nDetailed Summary:")
    print(result["detailed_summary"])


def example_hybrid_pipeline():
    """Example 2: Enable the hybrid semantic pipeline for research-grade summarization."""
    # Initialize with hybrid pipeline enabled
    summarizer = DocumentSummarizer(use_hybrid_pipeline=True)
    
    # Check status
    status = summarizer.get_hybrid_pipeline_status()
    print(f"Hybrid Pipeline Status: {status}")
    
    sections = [
        {
            "heading": "Introduction",
            "content": """
            Machine learning has revolutionized how we process documents.
            Modern transformer models can understand semantic relationships between sentences.
            This enables more coherent and accurate summarization.
            """,
            "page_number": 1,
        },
        {
            "heading": "Technical Approach",
            "content": """
            Our hybrid pipeline implements multiple stages:
            1. Structural cleaning removes noise and OCR artifacts
            2. Semantic embedding graphs capture document structure
            3. Extractive ranking identifies salient sentences
            4. Abstractive summarization produces fluent text
            5. Fusion engine removes redundancy
            The final output is evaluated using ROUGE scoring.
            """,
            "page_number": 2,
        },
    ]
    
    result = summarizer.summarize_document(sections)
    print("Brief Summary (Hybrid Pipeline):")
    print(result["brief_summary"])
    print("\nDetailed Summary:")
    print(result["detailed_summary"])
    
    # Optional: check pipeline metrics
    if "coherence" in result:
        print(f"\nCoherence Score: {result['coherence']:.3f}")
    if "paragraphs_analyzed" in result:
        print(f"Paragraphs Analyzed: {result['paragraphs_analyzed']}")
        print(f"Chunks Created: {result['chunks_created']}")


def example_switching_modes():
    """Example 3: Start with fast mode, then switch to hybrid."""
    summarizer = DocumentSummarizer(use_hybrid_pipeline=False)
    
    sections = [
        {
            "heading": "Overview",
            "content": "This document discusses hybrid summarization approaches.",
            "page_number": 1,
        },
    ]
    
    # Use fast path
    result_fast = summarizer.summarize_document(sections)
    print("Fast Mode Result:")
    print(result_fast["brief_summary"])
    
    # Switch to hybrid if available
    if summarizer.enable_hybrid_pipeline():
        print("\n✅ Hybrid pipeline enabled!")
        result_hybrid = summarizer.summarize_document(sections)
        print("\nHybrid Mode Result:")
        print(result_hybrid["brief_summary"])
    else:
        print("❌ Hybrid pipeline not available (dependencies missing)")


if __name__ == "__main__":
    print("=" * 70)
    print("Example 1: Basic Fast Summarization")
    print("=" * 70)
    example_basic_usage()
    
    print("\n" + "=" * 70)
    print("Example 2: Hybrid Semantic Pipeline")
    print("=" * 70)
    try:
        example_hybrid_pipeline()
    except Exception as e:
        print(f"Note: Hybrid pipeline requires additional dependencies: {e}")
    
    print("\n" + "=" * 70)
    print("Example 3: Switching Between Modes")
    print("=" * 70)
    example_switching_modes()
