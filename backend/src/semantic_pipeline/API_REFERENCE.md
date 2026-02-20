# Semantic Pipeline API Reference

## Quick Start

```python
from semantic_pipeline.pipeline import HybridSummarizationPipeline

pipeline = HybridSummarizationPipeline()
result = pipeline.run(document_text)

print(result["final_summary"])
print(result["structured"])
```

## Module: Pipeline Orchestrator

**File**: `semantic_pipeline/pipeline.py`

### HybridSummarizationPipeline

Main orchestration class that chains all stages.

```python
class HybridSummarizationPipeline:
    def __init__(self, config: Dict[str, Any] = None)
    def run(self, raw_text: str, reference: str = None, use_pegasus: bool = False) -> Dict[str, Any]
```

**Parameters:**
- `raw_text`: Document text to summarize
- `reference`: Optional reference summary for evaluation
- `use_pegasus`: Use Pegasus in addition to DistilBART

**Returns:**
```python
{
    "paragraphs": List[str],                    # Cleaned paragraphs
    "ranked_sentences": List[Tuple[str, float]], # Top sentences with scores
    "chunks": List[str],                        # Semantic chunks
    "candidates": List[Dict[str, str]],         # Model summaries
    "final_summary": str,                       # Final merged summary
    "coherence": float,                         # Coherence score (0-1)
    "metrics": {
        "rouge": {...},                         # ROUGE-1 and ROUGE-2
        "semantic_similarity": float            # vs reference
    },
    "structured": {
        "recap": [                              # Bullet points
            {"heading": str, "bullets": [str]}
        ]
    }
}
```

---

## Module: Structural Cleaner

**File**: `semantic_pipeline/structural_cleaner.py`

Removes noise, headers, footers, OCR artifacts from raw text.

```python
class StructuralCleaner:
    def __init__(self, header_footer_regex: str = r"^\s*[0-9]{1,4}\s*$")
    def clean(self, raw_text: str) -> List[str]
```

**Methods:**
- `clean(raw_text)`: Returns list of cleaned paragraph blocks

**Features:**
- Header/footer removal
- Deduplication
- Spacing normalization
- Paragraph preservation

**Example:**
```python
cleaner = StructuralCleaner()
paragraphs = cleaner.clean(pdf_text)
# Returns: ['Paragraph 1...', 'Paragraph 2...', ...]
```

---

## Module: Embedding Graph

**File**: `semantic_pipeline/embedding_graph.py`

Constructs semantic similarity graph from paragraphs.

```python
class EmbeddingGraph:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2")
    def fit(self, paragraphs: List[str])
    def get_similarity_matrix(self) -> np.ndarray
    def top_k_similar(self, idx: int, k: int = 5) -> List[Tuple[int, float]]
    def important_nodes(self, top_n: int = 5) -> List[int]
```

**Attributes:**
- `embeddings`: numpy array of paragraph embeddings
- `similarity`: cosine similarity matrix
- `paragraphs`: input paragraphs

**Methods:**
- `fit()`: Compute embeddings and similarity
- `get_similarity_matrix()`: Return cosine similarity matrix
- `top_k_similar()`: K nearest neighbors for a paragraph
- `important_nodes()`: Highest degree (most connected) nodes

**Example:**
```python
graph = EmbeddingGraph()
graph.fit(paragraphs)

# Find similar paragraphs
similar = graph.top_k_similar(idx=0, k=5)  # [(idx, sim_score), ...]

# Find important paragraphs
important = graph.important_nodes(top_n=5)  # [idx, ...]
```

---

## Module: Extractive Ranker

**File**: `semantic_pipeline/extractive_ranker.py`

Ranks sentences by combined TF-IDF and semantic relevance.

```python
class ExtractiveRanker:
    def __init__(self, embed_model: str = "all-MiniLM-L6-v2")
    def rank(self, paragraphs: List[str], top_k: int = 10) -> List[Tuple[str, float]]
```

**Methods:**
- `rank()`: Return top-k sentences with scores

**Scoring:**
- 50% TF-IDF (term frequency)
- 50% Semantic relevance (cosine similarity to document centroid)

**Example:**
```python
ranker = ExtractiveRanker()
top_sentences = ranker.rank(paragraphs, top_k=30)

for sentence, score in top_sentences:
    print(f"{score:.3f}: {sentence}")
```

---

## Module: Chunk Selector

**File**: `semantic_pipeline/chunk_selector.py`

Groups ranked sentences into coherent chunks with redundancy removal.

```python
class ChunkSelector:
    def __init__(self, embed_model: str = "all-MiniLM-L6-v2", redundancy_thresh: float = 0.85)
    def select(self, ranked_sentences: List[Tuple[str, float]], max_chunk_sentences: int = 5) -> List[List[str]]
```

**Methods:**
- `select()`: Group sentences into chunks, remove redundancy

**Parameters:**
- `redundancy_thresh`: Similarity threshold for duplicate removal (0-1)
- `max_chunk_sentences`: Max sentences per chunk

**Example:**
```python
selector = ChunkSelector(redundancy_thresh=0.85)
chunks = selector.select(ranked_sentences, max_chunk_sentences=5)

# chunks: [['sent1', 'sent2', 'sent3'], ['sent4', 'sent5'], ...]
```

---

## Module: Abstractive Summarizer

**File**: `semantic_pipeline/abstractive_summarizer.py`

Parallel abstractive summarization using transformer models.

```python
class AbstractiveSummarizer:
    def __init__(self, distilbart_model: str = "sshleifer/distilbart-cnn-12-6", 
                 pegasus_model: str = "google/pegasus-xsum")
    def summarize_chunk(self, text: str, use_pegasus: bool = False, max_length: int = 150) -> Dict[str, str]
    def summarize_parallel(self, chunks: List[str], use_pegasus: bool = False, max_workers: int = 2) -> List[Dict[str, str]]
```

**Methods:**
- `summarize_chunk()`: Summarize single chunk
- `summarize_parallel()`: Summarize multiple chunks in parallel

**Returns:**
```python
{
    "distilbart": "Summary text...",
    "pegasus": "Alternative summary..."  # if use_pegasus=True
}
```

**Example:**
```python
summarizer = AbstractiveSummarizer()

# Single chunk
result = summarizer.summarize_chunk(chunk_text)
print(result["distilbart"])

# Multiple chunks in parallel
results = summarizer.summarize_parallel(chunk_list, max_workers=2)
```

---

## Module: Fusion Engine

**File**: `semantic_pipeline/fusion_engine.py`

Merges candidate summaries, removes redundancy, scores coherence.

```python
class FusionEngine:
    def __init__(self, embed_model: str = "all-MiniLM-L6-v2", redundancy_thresh: float = 0.85)
    def merge(self, candidate_summaries: List[Dict[str, str]]) -> str
    def coherence_score(self, text: str) -> float
```

**Methods:**
- `merge()`: Combine candidates into single summary
- `coherence_score()`: Score text coherence (0-1)

**Coherence Calculation:**
- Average cosine similarity of adjacent sentences
- Higher = more coherent flow

**Example:**
```python
fuser = FusionEngine(redundancy_thresh=0.85)

# Merge multiple summaries
final = fuser.merge(candidate_summaries)

# Score coherence
score = fuser.coherence_score(final)
print(f"Coherence: {score:.3f}")
```

---

## Module: Evaluator

**File**: `semantic_pipeline/evaluator.py`

Evaluation metrics (ROUGE, semantic similarity).

```python
class Evaluator:
    def __init__(self, embed_model: str = "all-MiniLM-L6-v2")
    def rouge_scores(self, hypothesis: str, reference: str) -> Dict[str, Dict[str, float]]
    def semantic_similarity(self, hypothesis: str, reference: str) -> float
```

**Methods:**
- `rouge_scores()`: ROUGE-1 and ROUGE-2 scores
- `semantic_similarity()`: Cosine similarity of embeddings

**ROUGE Output:**
```python
{
    "rouge-1": {"precision": 0.85, "recall": 0.80, "f1": 0.82},
    "rouge-2": {"precision": 0.75, "recall": 0.70, "f1": 0.72}
}
```

**Semantic Similarity:**
- Range: 0 (completely different) to 1 (identical)
- Based on embedding cosine similarity

**Example:**
```python
evaluator = Evaluator()

# ROUGE scores
rouge = evaluator.rouge_scores(hypothesis, reference)
print(f"ROUGE-1 F1: {rouge['rouge-1']['f1']:.3f}")

# Semantic similarity
sim = evaluator.semantic_similarity(hypothesis, reference)
print(f"Similarity: {sim:.3f}")
```

---

## Module: Output Generator

**File**: `semantic_pipeline/output_generator.py`

Converts summary text to structured bullet-point format.

```python
class OutputGenerator:
    def __init__()
    def generate(self, final_summary: str, headings: List[str] = None) -> Dict
```

**Returns:**
```python
{
    "recap": [
        {
            "heading": "Topic 1",
            "bullets": ["Bullet 1", "Bullet 2", ...]
        },
        ...
    ]
}
```

**Example:**
```python
gen = OutputGenerator()
structured = gen.generate(final_summary, headings=["Intro", "Methods", "Results"])

for topic in structured["recap"]:
    print(f"## {topic['heading']}")
    for bullet in topic["bullets"]:
        print(f"• {bullet}")
```

---

## Advanced Usage

### Custom Configuration

```python
from semantic_pipeline.pipeline import HybridSummarizationPipeline
from semantic_pipeline.embedding_graph import EmbeddingGraph
from semantic_pipeline.abstractive_summarizer import AbstractiveSummarizer

# Use custom models
config = {
    "embedding_model": "sentence-transformers/all-mpnet-base-v2",  # Slower but more accurate
    "distilbart_model": "facebook/bart-large-cnn",                  # Larger, slower
}

# Manual pipeline composition
cleaner = StructuralCleaner()
graph = EmbeddingGraph(model_name="all-mpnet-base-v2")
summarizer = AbstractiveSummarizer(distilbart_model="facebook/bart-large-cnn")
```

### Component Isolation

Use individual components for custom workflows:

```python
from semantic_pipeline.structural_cleaner import StructuralCleaner
from semantic_pipeline.embedding_graph import EmbeddingGraph

# Just clean and embed, no summarization
cleaner = StructuralCleaner()
paragraphs = cleaner.clean(raw_text)

graph = EmbeddingGraph()
graph.fit(paragraphs)
similarity = graph.get_similarity_matrix()
```

### Custom Evaluation

```python
from semantic_pipeline.evaluator import Evaluator

evaluator = Evaluator()

# Evaluate your own outputs
my_summary = "..."
reference = "..."

rouge = evaluator.rouge_scores(my_summary, reference)
sim = evaluator.semantic_similarity(my_summary, reference)

print(f"ROUGE-1: {rouge['rouge-1']['f1']:.3f}")
print(f"Semantic Sim: {sim:.3f}")
```

---

## Performance Tips

### Memory Optimization
- Use `all-MiniLM-L6-v2` (lightweight embedding model)
- Reduce `max_chunk_sentences` if memory limited
- Process documents sequentially

### Speed Optimization
- Reduce `top_k` in ranking to 15-20 (vs 30)
- Use `max_workers=2` in parallel summarization
- Cache embeddings for repeated texts

### Quality Optimization
- Use `all-mpnet-base-v2` for better embeddings (slower)
- Use `facebook/bart-large-cnn` for better summarization
- Increase `top_k` ranking to 50+
- Lower `redundancy_thresh` to 0.75

---

## Troubleshooting

### Out of Memory
```python
# Reduce batch processing
summarizer = AbstractiveSummarizer()
results = summarizer.summarize_parallel(chunks, max_workers=1)  # Sequential
```

### Slow First Run
Models download on first use (~2GB total). Subsequent runs use cache.

### Poor Summary Quality
- Check input text is clean (no OCR noise)
- Increase redundancy threshold in ChunkSelector
- Use larger embedding model: `all-mpnet-base-v2`
- Manually review ranked_sentences output

---

**Last Updated**: February 2026
**Current Version**: 1.0
