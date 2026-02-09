from pydantic import BaseModel, Field
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000, description="The user's legal question to answer.")
    top_k: int = Field(5, ge=1, le=20, description="Number of source documents to retrieve (1-20).")

class Source(BaseModel):
    citation: str
    text: str
    rank: int
    score: float
    url: Optional[str] = None

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[Source]

class UpdateRequest(BaseModel):
    publisher: str = "DU"
    year: int = 2020
    limit: int = 10
    max_chars: int = 1000
    batch_size: int = 64

class UpdateResponse(BaseModel):
    status: str
    message: str
    downloaded_files: Optional[List[str]] = None
