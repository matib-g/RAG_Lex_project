import argparse
import sys
from pathlib import Path
from src.utils.logger import setup_logger
from src.data_ingestion.downloader import SejmDownloader
from src.data_ingestion.preprocessor import DataPreprocessor
from src.data_ingestion.indexer import VectorIndexer
from src.database.vector_store import VectorStore
from src.models.embedding import EmbeddingModel

logger = setup_logger("main")

def run_download(args):
    downloader = SejmDownloader()
    downloader.download_acts(args.publisher, args.year, args.limit, args.offset)

def run_prepare(args):
    preprocessor = DataPreprocessor()
    preprocessor.process_files(max_chars=args.max_chars)

def run_index(args):
    # Depending on architecture, we might want to initialize models lazily
    emb_model = EmbeddingModel()
    vector_store = VectorStore()
    indexer = VectorIndexer(vector_store, emb_model)
    indexer.index_data(batch_size=args.batch_size)

def run_rag(args):
    try:
        from src.models.llm import LlamaModel
        from src.rag.pipeline import RAGPipeline
    except ImportError as e:
        logger.error(f"Failed to import RAG components: {e}")
        sys.exit(1)
        
    logger.info("Initializing RAG components...")
    emb_model = EmbeddingModel()
    vector_store = VectorStore()
    llm_model = LlamaModel()
    
    pipeline = RAGPipeline(vector_store, emb_model, llm_model)
    
    if args.query:
        result = pipeline.run(args.query)
        print("\n\n=== FINAL ANSWER ===\n")
        print(result["answer"])
        print("\n=== SOURCES ===\n")
        for hit in result["hits"]:
            print(f"- {hit['citation']} (Rank: {hit['rank']}, Score: {hit['score']})")
    else:
        logger.info("Starting interactive mode. Type 'exit' to quit.")
        while True:
            q = input("\nEnter query: ")
            if q.lower() in ["exit", "quit"]:
                break
            result = pipeline.run(q)
            print("\n>>> ", result["answer"])

def main():
    parser = argparse.ArgumentParser(description="RAG Lex Project CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Download
    parser_download = subparsers.add_parser("download", help="Download acts from Sejm API")
    parser_download.add_argument("--publisher", type=str, default="DU", help="Publisher (e.g. DU, MP)")
    parser_download.add_argument("--year", type=int, default=2020, help="Year")
    parser_download.add_argument("--limit", type=int, default=100, help="Limit")
    parser_download.add_argument("--offset", type=int, default=0, help="Offset")
    parser_download.set_defaults(func=run_download)

    # Prepare
    parser_prepare = subparsers.add_parser("prepare", help="Preprocess HTML files to JSON chunks")
    parser_prepare.add_argument("--max_chars", type=int, default=1000, help="Max chars per chunk")
    parser_prepare.set_defaults(func=run_prepare)

    # Index
    parser_index = subparsers.add_parser("index", help="Index prepared data into Vector Store")
    parser_index.add_argument("--batch_size", type=int, default=64, help="Batch size for embedding")
    parser_index.set_defaults(func=run_index)

def run_update(args):
    logger.info("Starting Incremental Update...")
    
    # 1. Check for updates
    downloader = SejmDownloader()
    missing_items = downloader.check_for_updates(args.publisher, args.year)
    
    if not missing_items:
        logger.info("No updates found.")
        return

    # 2. Limit updates (Safety Brake)
    to_download = missing_items[:args.limit]
    logger.info(f"Downloading {len(to_download)} new acts (out of {len(missing_items)} missing).")
    
    # 3. Download specific items
    manifest = downloader.download_acts(args.publisher, args.year, specific_items=to_download)
    
    if not manifest:
        logger.warning("No files downloaded.")
        return
        
    downloaded_files = [item["filename"] for item in manifest]
    
    # 4. Process new files
    logger.info("Processing new files...")
    preprocessor = DataPreprocessor()
    # returns list of dicts (chunks)
    new_data = preprocessor.process_files(max_chars=args.max_chars, specific_files=downloaded_files)
    
    if not new_data:
        logger.warning("No data extracted from new files.")
        return

    # 5. Index new data
    logger.info("Indexing new data...")
    # Initialize models
    emb_model = EmbeddingModel()
    vector_store = VectorStore()
    indexer = VectorIndexer(vector_store, emb_model)
    
    indexer.index_data(dataset=new_data, batch_size=args.batch_size)
    logger.info("Incremental Update Completed Successfully.")

# ... (inside main function)

    # RAG
    parser_rag = subparsers.add_parser("rag", help="Run RAG pipeline")
    parser_rag.add_argument("--query", "-q", type=str, help="Query text (optional, runs interactive if missing)")
    parser_rag.set_defaults(func=run_rag)

    # Update
    parser_update = subparsers.add_parser("update", help="Check for missing acts and update DB incrementally")
    parser_update.add_argument("--publisher", type=str, default="DU", help="Publisher")
    parser_update.add_argument("--year", type=int, default=2020, help="Year")
    parser_update.add_argument("--limit", type=int, default=10, help="Max number of new acts to download")
    parser_update.add_argument("--max_chars", type=int, default=1000, help="Chunk size")
    parser_update.add_argument("--batch_size", type=int, default=64, help="Batch size")
    parser_update.set_defaults(func=run_update)

    # Evaluate
    parser_eval = subparsers.add_parser("evaluate", help="Run quality evaluation on test questions")
    parser_eval.add_argument("--questions", "-q", type=str, default="TEST_QUESTIONS.md", help="Path to questions file")
    parser_eval.add_argument("--output", "-o", type=str, default="evaluation_results.json", help="Output file path")
    parser_eval.set_defaults(func=run_evaluate)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


def run_evaluate(args):
    """Run evaluation benchmark."""
    from src.evaluation.eval import evaluate_from_file
    
    questions_path = Path(args.questions)
    output_path = Path(args.output)
    
    if not questions_path.exists():
        logger.error(f"Questions file not found: {questions_path}")
        sys.exit(1)
    
    evaluate_from_file(questions_path, output_path)


if __name__ == "__main__":
    main()
