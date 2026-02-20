"""
Evaluation tools: ROUGE and BERTScore wrappers with graceful fallbacks.
"""
from typing import List, Tuple


def compute_rouge(preds, refs):
    from rouge_score import rouge_scorer

    scorer = rouge_scorer.RougeScorer(
        ["rouge1", "rouge2", "rougeL"],
        use_stemmer=True
    )

    agg = {"rouge1": [], "rouge2": [], "rougeL": []}

    for p, r in zip(preds, refs):
        scores = scorer.score(r, p)
        for k in agg:
            agg[k].append(scores[k].fmeasure)

    return {k: sum(v)/len(v) for k, v in agg.items()}



def compute_bertscore(preds: List[str], refs: List[str]) -> dict:
    """Compute BERTScore if available."""
    try:
        from bert_score import score

        P, R, F1 = score(preds, refs, lang="en", verbose=False)
        return {"precision": float(P.mean()), "recall": float(R.mean()), "f1": float(F1.mean())}
    except Exception:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}