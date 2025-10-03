"""
Advanced scoring mechanisms for document relevance and accuracy evaluation
"""

import numpy as np
from typing import List, Dict, Union, Tuple

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

def calculate_f1(tp: int, fp: int, fn: int) -> float:
    """
    Calculate F1 score using precision and recall
    F1 = 2TP / (2TP + FP + FN)
    """
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    return f1

def calculate_accuracy(tp: int, tn: int, fp: int, fn: int) -> float:
    """
    Calculate accuracy score
    Accuracy = (TP + TN) / (TP + TN + FP + FN)
    """
    total = tp + tn + fp + fn
    return (tp + tn) / total if total > 0 else 0

def advanced_section_score(
    embeddings: np.ndarray,
    weights: List[float],
    context_factor: float,
    entity_importance: float
) -> float:
    """
    Advanced scoring function for section relevance:
    s = f(t1, t2, ..., tn) * p(ω1, ω2, ..., ωn) * Ek * c
    
    Args:
        embeddings: Vector embeddings of the text
        weights: Importance weights for different aspects
        context_factor: Contextual relevance factor
        entity_importance: Importance of entities in the section
    
    Returns:
        float: Combined relevance score
    """
    # Text similarity component
    text_similarity = np.mean([
        cosine_similarity(embeddings[i], embeddings[i+1]) 
        for i in range(len(embeddings)-1)
    ]) if len(embeddings) > 1 else 1.0

    # Weight factor (normalized)
    weight_factor = np.mean(weights)

    # Combined score
    score = text_similarity * weight_factor * entity_importance * context_factor
    return float(score)

def relationship_score(
    e1_embedding: np.ndarray,
    e2_embedding: np.ndarray,
    context_weights: List[float],
    entity_weights: List[float]
) -> float:
    """
    Calculate relationship score between two entities:
    r = f(e1, e2) * f(c(e1, e2)) * p(ωe1, ωe2) * p(c(ωe1, ωe2)) * (Ek1, Ek2)
    
    Args:
        e1_embedding: Embedding vector of first entity
        e2_embedding: Embedding vector of second entity
        context_weights: Weights for contextual relationships
        entity_weights: Weights for entity importance
    
    Returns:
        float: Relationship score
    """
    # Direct similarity between entities
    direct_sim = cosine_similarity(e1_embedding, e2_embedding)
    
    # Context weight factor
    context_weight = np.mean(context_weights)
    
    # Entity importance weight factor
    entity_weight = np.mean(entity_weights)
    
    # Combined score
    score = direct_sim * context_weight * entity_weight
    return float(score)

class RelevanceScorer:
    """
    Main class for scoring document sections and relationships
    """
    def __init__(
        self,
        min_similarity: float = 0.3,
        context_importance: float = 1.0
    ):
        self.min_similarity = min_similarity
        self.context_importance = context_importance
    
    def score_section(
        self,
        section_embedding: np.ndarray,
        query_embedding: np.ndarray,
        additional_weights: List[float] = None
    ) -> Dict[str, float]:
        """
        Score a section's relevance to a query using multiple metrics
        """
        # Basic similarity
        base_similarity = cosine_similarity(section_embedding, query_embedding)
        
        # Skip complex scoring if below threshold
        if base_similarity < self.min_similarity:
            return {
                'similarity': base_similarity,
                'advanced_score': 0.0,
                'weighted_score': 0.0
            }
            
        # Use default weights if none provided
        weights = additional_weights or [1.0]
        
        # Calculate advanced score
        adv_score = advanced_section_score(
            np.stack([section_embedding, query_embedding]),
            weights,
            self.context_importance,
            base_similarity
        )
        
        # Weighted combination
        weighted_score = 0.7 * base_similarity + 0.3 * adv_score
        
        return {
            'similarity': base_similarity,
            'advanced_score': adv_score,
            'weighted_score': weighted_score
        }
    
    def evaluate_results(
        self,
        relevant_count: int,
        retrieved_count: int,
        true_positives: int
    ) -> Dict[str, float]:
        """
        Calculate accuracy metrics for the results
        """
        false_positives = retrieved_count - true_positives
        false_negatives = relevant_count - true_positives
        true_negatives = 100 - (true_positives + false_positives + false_negatives)
        
        return {
            'accuracy': calculate_accuracy(true_positives, true_negatives, false_positives, false_negatives),
            'f1_score': calculate_f1(true_positives, false_positives, false_negatives),
            'precision': true_positives / retrieved_count if retrieved_count > 0 else 0,
            'recall': true_positives / relevant_count if relevant_count > 0 else 0
        }