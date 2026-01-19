import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent))

from src.database.vector_store import VectorStore
from src.utils.config import COLLECTION_NAME

try:
    print(f"Checking collection: {COLLECTION_NAME}...")
    vs = VectorStore()
    count = vs.collection.count()
    print(f"Total documents in collection: {count}")
    
    if count > 0:
        print("Peeking at first item:")
        peek = vs.collection.peek(limit=1)
        print(peek)
    else:
        print("Collection is empty!")
except Exception as e:
    print(f"Error checking DB: {e}")
