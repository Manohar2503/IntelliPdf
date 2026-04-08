#!/usr/bin/env python3
"""
Automated test harness: Compare FAST vs HYBRID summarization modes.
Tests ROUGE scores and quality metrics for both modes on real session data.

Usage:
  python test_summarizer_modes.py <sessionId> [--save-report]

Example:
  python test_summarizer_modes.py 4efbe859-6f43-430e-88cc-e5fe75377f4e --save-report
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from summarizer import DocumentSummarizer
from eval_tools import compute_rouge


def load_session_document(session_id: str) -> Optional[Dict]:
    """Load current_doc.json from session storage."""
    doc_path = Path(__file__).parent / "storage" / "sessions" / session_id / "output" / "current_doc.json"
    
    if not doc_path.exists():
        print(f"❌ Document not found: {doc_path}")
        return None
    
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "documents" in data:
                return data
            return {"documents": [data]} if isinstance(data, list) else None
    except Exception as e:
        print(f"❌ Error loading document: {e}")
        return None


def extract_sections(doc_data: Dict) -> List[Dict]:
    """Extract all sections from document."""
    sections = []
    for doc in doc_data.get("documents", []):
        sections.extend(doc.get("sections", []))
    return sections


def run_comparison(session_id: str, save_report: bool = False):
    """Compare FAST and HYBRID summarization modes."""
    
    print("\n" + "=" * 80)
    print("📊 SUMMARIZER MODE COMPARISON TEST")
    print("=" * 80)
    
    # Load document
    print(f"\n📄 Loading session: {session_id}...")
    doc_data = load_session_document(session_id)
    if not doc_data:
        return False
    
    sections = extract_sections(doc_data)
    if not sections:
        print("❌ No sections found in document")
        return False
    
    # Extract content for ROUGE reference (first meaningful section)
    reference_text = ""
    for sec in sections[:3]:  # Use first 3 sections as reference
        reference_text += sec.get("content", "") + " "
    reference_text = reference_text.strip()
    
    if not reference_text:
        print("❌ No content to summarize")
        return False
    
    print(f"✅ Loaded {len(sections)} sections")
    print(f"📝 Reference text length: {len(reference_text)} chars, {len(reference_text.split())} words")
    
    # Initialize summarizers
    print("\n🚀 Initializing summarizers...")
    try:
        fast_summarizer = DocumentSummarizer(use_hybrid_pipeline=False)
        print("✅ FAST mode initialized")
    except Exception as e:
        print(f"❌ FAST initialization failed: {e}")
        return False
    
    try:
        hybrid_summarizer = DocumentSummarizer(use_hybrid_pipeline=True)
        status = hybrid_summarizer.get_hybrid_pipeline_status()
        if not status["available"]:
            print(f"⚠️  HYBRID pipeline not available: {status}")
            hybrid_summarizer = None
        else:
            print(f"✅ HYBRID mode initialized: {status}")
    except Exception as e:
        print(f"⚠️  HYBRID initialization failed: {e}")
        hybrid_summarizer = None
    
    # Run FAST mode
    print("\n⏱️  Running FAST summarization...")
    try:
        import time
        start = time.time()
        fast_result = fast_summarizer.summarize_document(sections)
        fast_time = time.time() - start
        print(f"✅ FAST completed in {fast_time:.2f}s")
    except Exception as e:
        print(f"❌ FAST summarization failed: {e}")
        return False
    
    # Run HYBRID mode
    hybrid_result = None
    hybrid_time = None
    if hybrid_summarizer:
        print("\n⏱️  Running HYBRID summarization (this may take a minute)...")
        try:
            import time
            start = time.time()
            hybrid_result = hybrid_summarizer.summarize_document(sections)
            hybrid_time = time.time() - start
            print(f"✅ HYBRID completed in {hybrid_time:.2f}s")
        except Exception as e:
            print(f"❌ HYBRID summarization failed: {e}")
            hybrid_result = None
    
    # Prepare summaries for comparison
    fast_summary = fast_result.get("brief_summary", "")
    hybrid_summary = hybrid_result.get("brief_summary", "") if hybrid_result else None
    
    # Compute ROUGE scores
    print("\n📊 Computing ROUGE scores...")
    
    # FAST ROUGE
    try:
        fast_rouge = compute_rouge([fast_summary], [reference_text])
        print(f"✅ FAST ROUGE computed")
    except Exception as e:
        print(f"⚠️  FAST ROUGE failed: {e}")
        fast_rouge = {}
    
    # HYBRID ROUGE
    hybrid_rouge = None
    if hybrid_summary:
        try:
            hybrid_rouge = compute_rouge([hybrid_summary], [reference_text])
            print(f"✅ HYBRID ROUGE computed")
        except Exception as e:
            print(f"⚠️  HYBRID ROUGE failed: {e}")
            hybrid_rouge = None
    
    # Compute BERTScore (semantic similarity - better for abstractive summaries)
    print("\n📊 Computing BERTScore (semantic similarity)...")
    fast_bertscore = None
    hybrid_bertscore = None
    
    try:
        from eval_tools import compute_bertscore
        fast_bertscore = compute_bertscore([fast_summary], [reference_text])
        print(f"✅ FAST BERTScore computed")
    except Exception as e:
        print(f"⚠️  FAST BERTScore failed: {e}")
    
    if hybrid_summary:
        try:
            hybrid_bertscore = compute_bertscore([hybrid_summary], [reference_text])
            print(f"✅ HYBRID BERTScore computed")
        except Exception as e:
            print(f"⚠️  HYBRID BERTScore failed: {e}")
    
    # Display results
    print("\n" + "=" * 80)
    print("📈 RESULTS SUMMARY")
    print("=" * 80)
    
    print(f"\n⏱️  EXECUTION TIME:")
    print(f"  FAST:   {fast_time:.2f}s")
    if hybrid_time:
        print(f"  HYBRID: {hybrid_time:.2f}s")
        print(f"  Ratio:  {hybrid_time / fast_time:.1f}x slower (expected)")
    
    print(f"\n📏 OUTPUT LENGTH:")
    print(f"  FAST:   {len(fast_summary)} chars, {len(fast_summary.split())} words")
    if hybrid_summary:
        print(f"  HYBRID: {len(hybrid_summary)} chars, {len(hybrid_summary.split())} words")
    
    print(f"\n🎯 ROUGE SCORES (vs reference text):")
    print(f"  {'Metric':<12} {'FAST':<12} {'HYBRID':<12} {'Improvement':<12}")
    print(f"  {'-' * 48}")
    
    if fast_rouge:
        for metric in ["rouge1", "rouge2", "rougeL"]:
            fast_val = fast_rouge.get(metric, 0)
            hybrid_val = hybrid_rouge.get(metric, 0) if hybrid_rouge else None
            
            if hybrid_val is not None:
                improvement = ((hybrid_val - fast_val) / fast_val * 100) if fast_val > 0 else 0
                print(f"  {metric:<12} {fast_val:<12.4f} {hybrid_val:<12.4f} {improvement:>+.1f}%")
            else:
                print(f"  {metric:<12} {fast_val:<12.4f} {'N/A':<12} {'N/A':>12}")
    
    print(f"\n🧠 BERTScore (semantic similarity - scale 0-1):")
    print(f"  {'Metric':<12} {'FAST':<12} {'HYBRID':<12} {'Improvement':<12}")
    print(f"  {'-' * 48}")
    
    if fast_bertscore:
        for metric in ["precision", "recall", "f1"]:
            fast_val = fast_bertscore.get(metric, 0)
            hybrid_val = hybrid_bertscore.get(metric, 0) if hybrid_bertscore else None
            
            if hybrid_val is not None:
                improvement = ((hybrid_val - fast_val) / fast_val * 100) if fast_val > 0 else 0
                print(f"  {metric:<12} {fast_val:<12.4f} {hybrid_val:<12.4f} {improvement:>+.1f}%")
            else:
                print(f"  {metric:<12} {fast_val:<12.4f} {'N/A':<12} {'N/A':>12}")
    else:
        print(f"  ⚠️  BERTScore unavailable (batch_score package required)")
    
    # Detailed output samples
    print(f"\n📝 SUMMARY SAMPLES:")
    print(f"\n  FAST Mode:")
    print(f"  {fast_summary[:200]}...")
    
    if hybrid_summary:
        print(f"\n  HYBRID Mode:")
        print(f"  {hybrid_summary[:200]}...")
    
    # Metrics from hybrid
    if hybrid_result and "metrics" in hybrid_result and hybrid_result["metrics"]:
        print(f"\n📊 HYBRID Pipeline Metrics:")
        metrics = hybrid_result["metrics"]
        print(f"  ROUGE-1 (from pipeline): {metrics.get('rouge_1', 'N/A')}")
        print(f"  ROUGE-2 (from pipeline): {metrics.get('rouge_2', 'N/A')}")
        print(f"  Coherence Score:        {metrics.get('coherence_score', 'N/A')}")
    
    # Save report if requested
    if save_report:
        report_path = Path(__file__).parent / "test_summaries_report.json"
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": session_id,
            "document_stats": {
                "sections": len(sections),
                "reference_chars": len(reference_text),
                "reference_words": len(reference_text.split()),
            },
            "execution_time": {
                "fast_seconds": fast_time,
                "hybrid_seconds": hybrid_time,
            },
            "output_stats": {
                "fast_chars": len(fast_summary),
                "fast_words": len(fast_summary.split()),
                "hybrid_chars": len(hybrid_summary) if hybrid_summary else None,
                "hybrid_words": len(hybrid_summary.split()) if hybrid_summary else None,
            },
            "rouge_scores": {
                "fast": fast_rouge,
                "hybrid": hybrid_rouge,
            },
            "fast_summary": fast_summary[:500],
            "hybrid_summary": hybrid_summary[:500] if hybrid_summary else None,
        }
        
        # Add BERTScore if available
        if fast_bertscore or hybrid_bertscore:
            report["bertscore_scores"] = {
                "fast": fast_bertscore,
                "hybrid": hybrid_bertscore,
            }
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Report saved to: {report_path}")
    
    print("\n" + "=" * 80)
    print("✅ Test complete!")
    print("=" * 80 + "\n")
    
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("❌ Usage: python test_summarizer_modes.py <sessionId> [--save-report]")
        sys.exit(1)
    
    session_id = sys.argv[1]
    save_report = "--save-report" in sys.argv
    
    success = run_comparison(session_id, save_report=save_report)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
