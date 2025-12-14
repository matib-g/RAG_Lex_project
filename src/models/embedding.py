from sentence_transformers import SentenceTransformer
from typing import List
from src.utils.config import EMBEDDING_MODEL_NAME
from src.utils.logger import setup_logger

logger = setup_logger("embedding_model")

class EmbeddingModel:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: List[str], show_progress_bar: bool = False) -> List[List[float]]:
        """
        Embeds a list of texts.
        """
        embeddings = self.model.encode(texts, show_progress_bar=show_progress_bar)
        
        # Ensure it returns list of lists (if it returns user numpy array)
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return embeddings
