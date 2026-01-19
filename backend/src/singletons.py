from src.ranker import EmbeddingGenerator

# Load ONCE only (super important)
embedder = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
