import json
from pathlib import Path
from typing import Union
from src.utils.config import PREPARED_DATA_FILE
from src.utils.logger import setup_logger
from src.models.embedding import EmbeddingModel
from src.database.vector_store import VectorStore

logger = setup_logger("indexer")

class VectorIndexer:
    def __init__(self, vector_store: VectorStore, embedding_model: EmbeddingModel):
        self.vector_store = vector_store
        self.embedding_model = embedding_model

    def index_data(self, data_path: Union[str, Path] = PREPARED_DATA_FILE, batch_size: int = 64, dataset: list = None):
        """
        Indexes data into the vector store.
        If `dataset` list is provided, uses it directly.
        Otherwise loads from `data_path`.
        """
        if dataset is None:
            path = Path(data_path)
            if not path.exists():
                logger.error(f"Dataset file not found: {path}")
                return

            with open(path, "r", encoding="utf-8") as f:
                dataset = json.load(f)

        logger.info(f"Loaded {len(dataset)} items. Starting indexing...")

        if not dataset:
            logger.warning("Dataset is empty. Skipping indexing.")
            return

        texts = [item["text"] for item in dataset]
        ids = [f"{item['metadata']['filename']}_{item['metadata'].get('chunk_id', i)}" for i, item in enumerate(dataset)]
        metadatas = [item["metadata"] for item in dataset]
        
        # Batch processing
        total = len(texts)
        for i in range(0, total, batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            
            logger.info(f"Processing batch {i}/{total}...")
            # We assume embedding model handles batching or we pass the list
            batch_embeddings = self.embedding_model.encode(batch_texts)
            
            self.vector_store.add_documents(
                ids=batch_ids,
                documents=batch_texts,
                metadatas=batch_metadatas,
                embeddings=batch_embeddings
            )

        logger.info("Indexing completed successfully.")
