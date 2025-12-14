import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.utils.config import CHROMA_DB_PATH, COLLECTION_NAME
from src.utils.logger import setup_logger

logger = setup_logger("vector_store")

class VectorStore:
    def __init__(self, persist_path: Path = CHROMA_DB_PATH, collection_name: str = COLLECTION_NAME):
        logger.info(f"Opening ChromaDB persistent at: {persist_path}")
        self.client = chromadb.PersistentClient(path=str(persist_path))
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_documents(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Adds documents to the collection.
        """
        logger.info(f"Adding {len(documents)} documents to collection '{self.collection_name}'")
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )

    def query(self, query_embeddings: List[List[float]], n_results: int = 5) -> Dict[str, Any]:
        """
        Queries the collection.
        """
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        return results
