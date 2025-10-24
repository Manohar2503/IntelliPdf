from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List
import numpy as np
from src.ranker import EmbeddingGenerator

class EnhancedSummarizer:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize with the embedding generator"""
        self.embedder = EmbeddingGenerator(model_name=embedding_model)
        self.vectorizer = TfidfVectorizer(max_features=100)
    
    def _get_embeddings(self, sentences: List[str]) -> np.ndarray:
        """Get embeddings for sentences using the sentence transformer model"""
        embeddings = self.embedder.embed_texts(sentences)
        return np.array(embeddings)
    
    def _get_tfidf_features(self, sentences: List[str]) -> np.ndarray:
        """Get TF-IDF features for sentences"""
        return self.vectorizer.fit_transform(sentences).toarray()
    
    def _combine_features(self, embeddings: np.ndarray, tfidf: np.ndarray) -> np.ndarray:
        """Combine embeddings with TF-IDF features"""
        # Normalize both feature sets
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1)[:, np.newaxis]
        tfidf_norm = tfidf / np.linalg.norm(tfidf, axis=1)[:, np.newaxis]
        
        # Concatenate features
        return np.hstack([embeddings_norm, tfidf_norm])
    
    def cluster_summarize(self, text_sections: List[str], num_clusters: int = 5, top_k: int = 3) -> List[str]:
        """
        Generate summary using k-means clustering on sentence embeddings
        
        Args:
            text_sections: List of text sections to summarize
            num_clusters: Number of clusters to create
            top_k: Number of sentences to select from each cluster
            
        Returns:
            List of representative sentences forming the summary
        """
        if not text_sections:
            return []
            
        # Get sentence embeddings
        embeddings = self._get_embeddings(text_sections)
        
        # Get TF-IDF features
        tfidf_features = self._get_tfidf_features(text_sections)
        
        # Combine features
        combined_features = self._combine_features(embeddings, tfidf_features)
        
        # Adjust number of clusters if we have fewer sentences
        actual_clusters = min(num_clusters, len(text_sections))
        
        # Apply k-means clustering
        kmeans = KMeans(n_clusters=actual_clusters, random_state=42)
        clusters = kmeans.fit_predict(combined_features)
        
        # Calculate distances to cluster centers
        distances = kmeans.transform(combined_features)
        
        # Select representative sentences from each cluster
        summary_sentences = []
        for i in range(actual_clusters):
            # Get indices of sentences in this cluster
            cluster_indices = np.where(clusters == i)[0]
            
            if len(cluster_indices) == 0:
                continue
                
            # Get distances to cluster center for these sentences
            cluster_distances = distances[cluster_indices, i]
            
            # Sort by distance to cluster center
            sorted_indices = cluster_indices[np.argsort(cluster_distances)]
            
            # Select top_k sentences closest to cluster center
            for idx in sorted_indices[:top_k]:
                summary_sentences.append(text_sections[idx])
        
        return summary_sentences

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using simple rules"""
    import re
    # Split on period followed by space and uppercase letter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]