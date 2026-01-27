"""
RAG Evaluation Runner.
Runs benchmark tests and generates quality reports.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from src.evaluation.metrics import RAGMetrics
from src.rag.pipeline import RAGPipeline
from src.database.vector_store import VectorStore
from src.models.embedding import EmbeddingModel
from src.models.llm import LlamaModel
from src.utils.logger import setup_logger

logger = setup_logger("evaluation")


def parse_test_questions(filepath: Path) -> List[Dict[str, str]]:
    """Parse TEST_QUESTIONS.md file into list of questions."""
    questions = []
    content = filepath.read_text(encoding="utf-8")
    
    # Simple parsing - find numbered questions
    lines = content.split("\n")
    current_q = None
    
    for line in lines:
        # Match patterns like "1." or "- " followed by question text
        match = re.match(r"^\d+\.\s*(.+)", line.strip())
        if match:
            current_q = match.group(1).strip()
            if current_q and "?" in current_q:
                questions.append({"question": current_q})
    
    return questions


def run_benchmark(
    questions: List[Dict[str, str]],
    pipeline: RAGPipeline,
    metrics: RAGMetrics
) -> List[Dict[str, Any]]:
    """Run evaluation on a list of questions."""
    results = []
    
    for i, q in enumerate(questions):
        question = q["question"]
        logger.info(f"Evaluating [{i+1}/{len(questions)}]: {question[:50]}...")
        
        try:
            # Run RAG pipeline
            result = pipeline.run(question, top_k=5)
            
            answer = result.get("answer", "")
            context = result.get("prompt", "")
            hits = result.get("hits", [])
            
            # Calculate metrics
            scores = metrics.calculate_all(question, answer, context, hits)
            
            results.append({
                "question": question,
                "answer": answer,
                "sources_count": len(hits),
                "from_cache": result.get("from_cache", False),
                "metrics": scores
            })
            
        except Exception as e:
            logger.error(f"Error evaluating question: {e}")
            results.append({
                "question": question,
                "error": str(e),
                "metrics": {"answer_relevance": 0, "faithfulness": 0, "context_precision": 0}
            })
    
    return results


def generate_report(results: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
    """Generate evaluation report with aggregated metrics."""
    if not results:
        return {"error": "No results to report"}
    
    # Aggregate metrics
    all_metrics = [r["metrics"] for r in results if "metrics" in r]
    
    avg_relevance = sum(m["answer_relevance"] for m in all_metrics) / len(all_metrics)
    avg_faithfulness = sum(m["faithfulness"] for m in all_metrics) / len(all_metrics)
    avg_precision = sum(m["context_precision"] for m in all_metrics) / len(all_metrics)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_questions": len(results),
        "successful": len([r for r in results if "error" not in r]),
        "aggregate_metrics": {
            "answer_relevance": round(avg_relevance, 3),
            "faithfulness": round(avg_faithfulness, 3),
            "context_precision": round(avg_precision, 3),
            "overall_score": round((avg_relevance + avg_faithfulness + avg_precision) / 3, 3)
        },
        "results": results
    }
    
    # Save to file
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Report saved to {output_path}")
    
    return report


def evaluate_from_file(questions_file: Path, output_file: Path = None) -> Dict[str, Any]:
    """Main evaluation entrypoint."""
    logger.info(f"Loading questions from {questions_file}")
    
    questions = parse_test_questions(questions_file)
    if not questions:
        raise ValueError(f"No questions found in {questions_file}")
    
    logger.info(f"Found {len(questions)} questions")
    
    # Initialize components
    logger.info("Initializing RAG components...")
    vector_store = VectorStore()
    embedding_model = EmbeddingModel()
    llm_model = LlamaModel()
    
    pipeline = RAGPipeline(vector_store, embedding_model, llm_model)
    metrics = RAGMetrics(embedding_model)
    
    # Run benchmark
    results = run_benchmark(questions, pipeline, metrics)
    
    # Generate report
    output_path = output_file or Path("evaluation_results.json")
    report = generate_report(results, output_path)
    
    # Print summary
    agg = report["aggregate_metrics"]
    logger.info("=" * 50)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Questions: {report['total_questions']}")
    logger.info(f"Answer Relevance: {agg['answer_relevance']:.3f}")
    logger.info(f"Faithfulness: {agg['faithfulness']:.3f}")
    logger.info(f"Context Precision: {agg['context_precision']:.3f}")
    logger.info(f"Overall Score: {agg['overall_score']:.3f}")
    logger.info("=" * 50)
    
    return report
