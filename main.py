"""
RAG Lex Project - Command Line Interface
"""
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


# =============================================================================
# Command Handlers
# =============================================================================

def run_download(args):
    """Download acts from Sejm API."""
    downloader = SejmDownloader()
    downloader.download_acts(args.publisher, args.year, args.limit, args.offset)


def run_prepare(args):
    """Preprocess HTML files into JSON chunks."""
    preprocessor = DataPreprocessor()
    preprocessor.process_files(max_chars=args.max_chars)


def run_index(args):
    """Index prepared data into Vector Store."""
    emb_model = EmbeddingModel()
    vector_store = VectorStore()
    indexer = VectorIndexer(vector_store, emb_model)
    indexer.index_data(batch_size=args.batch_size)


def run_update(args):
    """Check for missing acts and update DB incrementally."""
    """Check for missing acts and update DB incrementally."""
    from src.data_ingestion.workflow import run_incremental_update
    
    run_incremental_update(
        publisher=args.publisher,
        year=args.year,
        limit=args.limit,
        max_chars=args.max_chars,
        batch_size=args.batch_size
    )


def run_rag(args):
    """Run RAG pipeline (interactive or single query)."""
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


def run_evaluate(args):
    """Run quality evaluation benchmark."""
    from src.evaluation.eval import evaluate_from_file
    
    questions_path = Path(args.questions)
    output_path = Path(args.output)
    
    if not questions_path.exists():
        logger.error(f"Questions file not found: {questions_path}")
        sys.exit(1)
    
    evaluate_from_file(questions_path, output_path)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="RAG Lex Project CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Download command
    parser_download = subparsers.add_parser("download", help="Download acts from Sejm API")
    parser_download.add_argument("--publisher", type=str, default="DU", help="Publisher (e.g. DU, MP)")
    parser_download.add_argument("--year", type=int, default=2020, help="Year")
    parser_download.add_argument("--limit", type=int, default=100, help="Limit")
    parser_download.add_argument("--offset", type=int, default=0, help="Offset")
    parser_download.set_defaults(func=run_download)

    # Prepare command
    parser_prepare = subparsers.add_parser("prepare", help="Preprocess HTML files to JSON chunks")
    parser_prepare.add_argument("--max_chars", type=int, default=1000, help="Max chars per chunk")
    parser_prepare.set_defaults(func=run_prepare)

    # Index command
    parser_index = subparsers.add_parser("index", help="Index prepared data into Vector Store")
    parser_index.add_argument("--batch_size", type=int, default=64, help="Batch size for embedding")
    parser_index.set_defaults(func=run_index)

    # Update command
    parser_update = subparsers.add_parser("update", help="Check for missing acts and update DB incrementally")
    parser_update.add_argument("--publisher", type=str, default="DU", help="Publisher")
    parser_update.add_argument("--year", type=int, default=2020, help="Year")
    parser_update.add_argument("--limit", type=int, default=10, help="Max number of new acts to download")
    parser_update.add_argument("--max_chars", type=int, default=1000, help="Chunk size")
    parser_update.add_argument("--batch_size", type=int, default=64, help="Batch size")
    parser_update.set_defaults(func=run_update)

    # RAG command
    parser_rag = subparsers.add_parser("rag", help="Run RAG pipeline")
    parser_rag.add_argument("--query", "-q", type=str, help="Query text (optional, runs interactive if missing)")
    parser_rag.set_defaults(func=run_rag)

    # Evaluate command
    parser_eval = subparsers.add_parser("evaluate", help="Run quality evaluation on test questions")
    parser_eval.add_argument("--questions", "-q", type=str, default="TEST_QUESTIONS.md", help="Path to questions file")
    parser_eval.add_argument("--output", "-o", type=str, default="evaluation_results.json", help="Output file path")
    parser_eval.set_defaults(func=run_evaluate)

    # Parse and execute
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
