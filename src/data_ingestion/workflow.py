from typing import Optional, List, Dict
from src.utils.logger import setup_logger
from src.data_ingestion.downloader import SejmDownloader
from src.data_ingestion.preprocessor import DataPreprocessor
from src.data_ingestion.indexer import VectorIndexer
from src.database.vector_store import VectorStore
from src.models.embedding import EmbeddingModel

logger = setup_logger("ingestion_workflow")

def run_incremental_update(
    publisher: str, 
    year: int, 
    limit: int = 10, 
    max_chars: int = 1000, 
    batch_size: int = 64
) -> bool:
    """
    Orchestrates the incremental update process:
    1. Check for missing acts
    2. Download new acts
    3. Preprocess
    4. Index
    
    Returns True if any data was processed, False otherwise.
    """
    logger.info(f"Starting incremental update workflow for {publisher}/{year}")
    
    # 1. Check for updates
    downloader = SejmDownloader()
    missing_items = downloader.check_for_updates(publisher, year)
    
    if not missing_items:
        logger.info("No updates found.")
        return False

    # 2. Limit updates
    to_download = missing_items[:limit]
    logger.info(f"Downloading {len(to_download)} new acts.")
    
    # Download specific items
    manifest = downloader.download_acts(publisher, year, specific_items=to_download)
    
    if not manifest:
        logger.warning("No files downloaded.")
        return False
        
    downloaded_files = [item["filename"] for item in manifest]
    
    # 3. Process new files
    logger.info("Processing new files...")
    preprocessor = DataPreprocessor()
    # Process only specific files
    new_data = preprocessor.process_files(max_chars=max_chars, specific_files=downloaded_files)
    
    if not new_data:
        logger.warning("No data extracted from new files.")
        return False

    # 4. Index new data
    logger.info("Indexing new data...")
    # Initialize indexing components
    emb_model = EmbeddingModel()
    vector_store = VectorStore()
    indexer = VectorIndexer(vector_store, emb_model)
    
    indexer.index_data(dataset=new_data, batch_size=batch_size)
    logger.info("Incremental update workflow completed successfully.")
    return True
