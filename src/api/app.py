from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router as api_router
from src.utils.logger import setup_logger

# Import RAG components
from src.models.embedding import EmbeddingModel
from src.models.llm import LlamaModel
from src.database.vector_store import VectorStore
from src.rag.pipeline import RAGPipeline

logger = setup_logger("api_main")

# CORS configuration - allow frontend origins
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: Initializing RAG pipeline components...")
    
    # Initialize components
    # These might be heavy (loading weights), so we do it once here.
    try:
        emb_model = EmbeddingModel()
        vector_store = VectorStore()
        llm_model = LlamaModel()
        
        pipeline = RAGPipeline(vector_store, emb_model, llm_model)
        
        # Store in app.state so routes can access it
        app.state.pipeline = pipeline
        
        logger.info("Startup: RAG pipeline initialized successfully.")
    except Exception as e:
        logger.error(f"Startup: Failed to initialize pipeline: {e}")
        # Allow app to start in "degraded" mode
        app.state.pipeline = None
        # raise e  <-- Commented out to prevent crash
        
    yield
    
    logger.info("Shutdown: cleaning up resources...")
    # Add cleanup logic if needed (e.g. close db connections)

app = FastAPI(
    title="RAG Lex Project API",
    description="API for Polish Law RAG System",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Welcome to RAG Lex API. Visit /docs for Swagger UI."}
