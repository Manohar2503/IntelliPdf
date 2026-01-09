from rouge_score import rouge_scorer

# Load summaries
with open("generated.txt", "r", encoding="utf-8") as f:
    generated = f.read()

with open("reference.txt", "r", encoding="utf-8") as f:
    reference = f.read()

# Initialize scorer
scorer = rouge_scorer.RougeScorer(
    ["rouge1", "rouge2", "rougeL"],
    use_stemmer=True
)

scores = scorer.score(reference, generated)

print("ROUGE-1:", scores["rouge1"].fmeasure)
print("ROUGE-2:", scores["rouge2"].fmeasure)
print("ROUGE-L:", scores["rougeL"].fmeasure)
