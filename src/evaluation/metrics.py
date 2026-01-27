"""
RAG Quality Metrics Module.
Calculates faithfulness, relevance, and precision metrics.
"""
import numpy as np
from typing import List, Dict, Any
from src.models.embedding import EmbeddingModel
from src.utils.logger import setup_logger

logger = setup_logger("metrics")


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
        Uses semantic similarity between question and answer embeddings.
        """
        if not answer.strip():
            return 0.0
        
        q_emb = self.embedding_model.encode([question])[0]
        a_emb = self.embedding_model.encode([answer])[0]
        return cosine_similarity(q_emb, a_emb)
    
    def faithfulness(self, answer: str, context: str) -> float:
        """
        Measures if the answer is grounded in the provided context.
        Uses semantic similarity between answer and context.
        """
        if not answer.strip() or not context.strip():
            return 0.0
        
        a_emb = self.embedding_model.encode([answer])[0]
        c_emb = self.embedding_model.encode([context])[0]
        return cosine_similarity(a_emb, c_emb)
    
    def context_precision(self, question: str, sources: List[Dict]) -> float:
        """
        Measures if retrieved sources are relevant to the question.
        Average similarity between question and each source.
        """
        if not sources:
            return 0.0
        
        q_emb = self.embedding_model.encode([question])[0]
        
        similarities = []
        for source in sources:
            text = source.get("text", "")
            if text.strip():
                s_emb = self.embedding_model.encode([text])[0]
                similarities.append(cosine_similarity(q_emb, s_emb))
        
        return float(np.mean(similarities)) if similarities else 0.0
    
    def calculate_all(self, question: str, answer: str, context: str, sources: List[Dict]) -> Dict[str, float]:
        """Calculate all metrics for a single Q&A pair."""
        return {
            "answer_relevance": self.answer_relevance(question, answer),
            "faithfulness": self.faithfulness(answer, context),
            "context_precision": self.context_precision(question, sources)
        }
