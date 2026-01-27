from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from src.api.schemas import QueryRequest, QueryResponse, Source, UpdateRequest, UpdateResponse
from src.utils.logger import setup_logger

# Import our modular logic
from src.data_ingestion.downloader import SejmDownloader
from src.data_ingestion.preprocessor import DataPreprocessor
from src.data_ingestion.indexer import VectorIndexer
from src.database.vector_store import VectorStore
from src.models.embedding import EmbeddingModel

logger = setup_logger("api_routes")
router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest, req_obj: Request):
    """
    Run the RAG pipeline for a given query.
    Note: 'req_obj' is used to access app state where pipeline is stored.
    """
    pipeline = getattr(req_obj.app.state, "pipeline", None)
    if not pipeline:
        raise HTTPException(status_code=503, detail="RAG Pipeline not initialized")

    try:
        # Pass query and top_k from request
        result = pipeline.run(request.query, top_k=request.top_k)
        
        sources = []
        for hit in result["hits"]:
            sources.append(Source(
                citation=hit.get("citation", "Unknown"),
                text=hit.get("text", ""),
                rank=hit.get("rank", 0),
                score=hit.get("score", 0.0)
            ))
            
        logger.info(f"Query processed successfully. Answer length: {len(result['answer'])}")
        return QueryResponse(
            question=request.query,
            answer=result["answer"],
            sources=sources
        )
    except Exception as e:
        logger.error(f"Error during query processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def background_update_task(req: UpdateRequest):
    """
    Background task logic for incremental update.
    """
    try:
        logger.info(f"Starting background update for {req.publisher}/{req.year}")
        downloader = SejmDownloader()
        missing_items = downloader.check_for_updates(req.publisher, req.year)
        
        if not missing_items:
            logger.info("No updates found.")
            return

        to_download = missing_items[:req.limit]
        logger.info(f"Downloading {len(to_download)} new acts.")
        
        manifest = downloader.download_acts(req.publisher, req.year, specific_items=to_download)
        if not manifest:
            return
            
        downloaded_files = [item["filename"] for item in manifest]
        
        preprocessor = DataPreprocessor()
        new_data = preprocessor.process_files(max_chars=req.max_chars, specific_files=downloaded_files)
        
        if not new_data:
            return

        # Initialize indexing components fresh (safe for threads usually if instances are separate)
        # Or reuse global ones? Safest to create new lightweight wrappers for indexing 
        # as it happens rarely.
        emb_model = EmbeddingModel()
        vector_store = VectorStore()
        indexer = VectorIndexer(vector_store, emb_model)
        
        indexer.index_data(dataset=new_data, batch_size=req.batch_size)
        logger.info("Background update completed.")
    except Exception as e:
        logger.error(f"Error in background update: {e}")

@router.post("/update", response_model=UpdateResponse)
def trigger_update(request: UpdateRequest, background_tasks: BackgroundTasks):
    """
    Trigger an incremental update in the background.
    """
    background_tasks.add_task(background_update_task, request)
    return UpdateResponse(
        status="accepted",
        message="Update task started in background."
    )


@router.post("/query/stream")
def query_stream(request: QueryRequest, req_obj: Request):
    """
    Stream RAG response token by token using Server-Sent Events.
    """
    from fastapi.responses import StreamingResponse
    import json
    
    pipeline = getattr(req_obj.app.state, "pipeline", None)
    if not pipeline:
        raise HTTPException(status_code=503, detail="RAG Pipeline not initialized")
    
    def generate():
        try:
            # Check cache first
            from src.utils.cache import generate_cache_key, get_cache, set_cache
            cache_key = generate_cache_key(request.query, request.top_k)
            cached = get_cache(cache_key)
            
            if cached:
                # Return cached answer as single event
                logger.info("Streaming from cache")
                yield f"data: {json.dumps({'token': cached['answer'], 'done': False})}\n\n"
                yield f"data: {json.dumps({'done': True, 'sources': cached.get('hits', [])})}\n\n"
                return
            
            # Retrieve context
            context_text, hits = pipeline.retrieve(request.query, top_k=request.top_k)
            
            if not context_text.strip():
                yield f"data: {json.dumps({'token': 'Nie znaleziono odpowiednich fragmentów.', 'done': True, 'sources': []})}\n\n"
                return
            
            # Build prompt
            prompt = pipeline.build_prompt(request.query, context_text)
            
            # Stream tokens
            full_answer = ""
            for token in pipeline.llm_model.generate_stream(prompt):
                full_answer += token
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
            
            # Send sources at the end
            sources = [{"citation": h["citation"], "text": h["text"], "score": h["score"]} for h in hits]
            yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"
            
            # Cache the full answer
            set_cache(cache_key, {"answer": full_answer, "hits": hits})
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
