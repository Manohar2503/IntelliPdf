"""
Embedding generator module for sections/snippets
Persona-free version for Adobe Challenge Finale
"""

from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates embeddings for sections/snippets without persona filtering"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with a lightweight sentence transformer model"""
        logger.info(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Model loaded successfully")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text strings.

        Args:
            texts (List[str]): List of text content to embed

        Returns:
            List[List[float]]: List of embedding vectors (as lists)
        """
        if not texts:
            return []

        logger.info(f"Generating embeddings for {len(texts)} text blocks...")
        vectors = self.model.encode(texts, convert_to_numpy=False)  # Returns list of lists
        return [v.tolist() for v in vectors]

    def embed_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Given sections with 'content', generate and attach embeddings.

        Args:
            sections (List[Dict]): List of section dicts with 'content'

        Returns:
            List[Dict]: Same list with an added 'embedding' field for each section
        """
        if not sections:
            return []

        contents = [sec.get("content", "") for sec in sections]
        embeddings = self.embed_texts(contents)

        for sec, emb in zip(sections, embeddings):
            sec["embedding"] = emb

        return sections
