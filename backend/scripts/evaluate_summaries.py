"""Small evaluator script that runs the summarizer on sample ground-truths and reports ROUGE/BERTScore."""
import json
from pathlib import Path

from src.summarizer import DocumentSummarizer
from src.eval_tools import compute_rouge, compute_bertscore


def run():
    data_path = Path(__file__).parent.parent / "tests" / "sample_ground_truth.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))

    preds = []
    refs = []

    s = DocumentSummarizer(use_extractive_guidance=True, use_ensemble=False)

    for doc in data:
        text = doc["text"]
        # naive: treat the whole doc as a single section
        sections = [{"heading": "", "content": text}]
        out = s.summarize_document(sections)
        pred = out.get("brief_summary") or out.get("detailed_summary") or ""
        # flatten bullets
        pred = pred.replace("\n", " ")
        preds.append(pred)
        refs.append(doc["summary"])

    rouge = compute_rouge(preds, refs)
    bert = compute_bertscore(preds, refs)

    print("ROUGE:", rouge)
    print("BERTScore:", bert)


if __name__ == "__main__":
    run()
