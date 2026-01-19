import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from src.database.vector_store import VectorStore
from src.utils.config import COLLECTION_NAME

print("Initializing VectorStore...")
vs = VectorStore()
print(f"Collection count before: {vs.collection.count()}")

print("Adding test document...")
vs.add_documents(
    ids=["test_1"],
    documents=["This is a test document."],
    metadatas=[{"source": "test"}],
    embeddings=[[0.1]*768] # Dummy embedding
)

print(f"Collection count after: {vs.collection.count()}")

print("Peeking...")
print(vs.collection.peek(limit=1))
