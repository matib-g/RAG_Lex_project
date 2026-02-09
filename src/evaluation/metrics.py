"""
RAG Quality Metrics Module.
Calculates faithfulness, relevance, and precision metrics.
"""
import numpy as np
from typing import List, Dict, Any, Optional
from src.models.embedding import EmbeddingModel
from src.utils.logger import setup_logger

logger = setup_logger("metrics")

# Global cross-encoder instance (lazy loaded)
_cross_encoder = None


def get_cross_encoder():
    """Lazy load cross-encoder model for answer relevance scoring."""
    global _cross_encoder
    if _cross_encoder is None:
        try:
            from sentence_transformers import CrossEncoder
            logger.info("Loading Cross-Encoder model for relevance scoring...")
            _cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("Cross-Encoder loaded successfully.")
        except ImportError:
            logger.warning("sentence-transformers not available for CrossEncoder. Falling back to cosine similarity.")
            _cross_encoder = False  # Mark as unavailable
        except Exception as e:
            logger.warning(f"Failed to load Cross-Encoder: {e}. Falling back to cosine similarity.")
            _cross_encoder = False
    return _cross_encoder if _cross_encoder else None


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


class RAGMetrics:
    """Calculate quality metrics for RAG responses."""
    
    def __init__(self, embedding_model: EmbeddingModel = None):
        self.embedding_model = embedding_model or EmbeddingModel()
    
    def answer_relevance(self, question: str, answer: str) -> float:
        """
        Measures how relevant the answer is to the question.
        
        Uses Cross-Encoder (ms-marco-MiniLM) which is specifically trained
        to score query-document pairs. Falls back to cosine similarity
        if cross-encoder is unavailable.
        
        Returns: Score between 0 and 1 (higher = more relevant)
        """
        if not answer.strip():
            return 0.0
        
        cross_encoder = get_cross_encoder()
        
        if cross_encoder:
            # Cross-Encoder: directly scores (question, answer) pair
            # Returns logit score, apply sigmoid for 0-1 range
            score = cross_encoder.predict([[question, answer]])[0]
            # Sigmoid to normalize to 0-1
            return float(1 / (1 + np.exp(-score)))
        else:
            # Fallback: cosine similarity (less accurate for Q&A)
            q_emb = np.array(self.embedding_model.encode([question])[0])
            a_emb = np.array(self.embedding_model.encode([answer])[0])
            return cosine_similarity(q_emb, a_emb)
    
    def faithfulness(self, answer: str, context: str) -> float:
        """
        Measures if the answer is grounded in the provided context.
        Uses semantic similarity between answer and context.
        """
        if not answer.strip() or not context.strip():
            return 0.0
        
        a_emb = np.array(self.embedding_model.encode([answer])[0])
        c_emb = np.array(self.embedding_model.encode([context])[0])
        return cosine_similarity(a_emb, c_emb)
    
    def context_precision(self, question: str, sources: List[Dict]) -> float:
        """
        Measures if retrieved sources are relevant to the question.
        Average similarity between question and each source.
        Uses batch encoding for efficiency.
        """
        if not sources:
            return 0.0
        
        # Filter valid source texts
        source_texts = [s.get("text", "").strip() for s in sources]
        source_texts = [t for t in source_texts if t]
        
        if not source_texts:
            return 0.0
        
        # Batch encode: question + all sources in one call
        all_texts = [question] + source_texts
        all_embeddings = self.embedding_model.encode(all_texts)
        
        q_emb = np.array(all_embeddings[0])
        source_embs = [np.array(e) for e in all_embeddings[1:]]
        
        # Calculate similarities
        similarities = [cosine_similarity(q_emb, s_emb) for s_emb in source_embs]
        
        return float(np.mean(similarities)) if similarities else 0.0
    
    def calculate_all(self, question: str, answer: str, context: str, sources: List[Dict]) -> Dict[str, float]:
        """Calculate all metrics for a single Q&A pair."""
        return {
            "answer_relevance": self.answer_relevance(question, answer),
            "faithfulness": self.faithfulness(answer, context),
            "context_precision": self.context_precision(question, sources)
        }
