import json
from typing import List, Tuple, Dict, Any
from src.utils.config import PROMPT_MAX_CHARS, LLAMA_N_CTX
from src.utils.logger import setup_logger
from src.utils.cache import generate_cache_key, get_cache, set_cache
from src.database.vector_store import VectorStore
from src.models.embedding import EmbeddingModel
from src.models.llm import LlamaModel

logger = setup_logger("rag_pipeline")

class RAGPipeline:
    def __init__(self, vector_store: VectorStore, embedding_model: EmbeddingModel, llm_model: LlamaModel):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.llm_model = llm_model

    def retrieve(self, query: str, top_k: int = 5, char_limit: int = PROMPT_MAX_CHARS) -> Tuple[str, List[Dict]]:
        """
        Embeds query, searches vector store, and formats context.
        """
        logger.info(f"Retrieving context for query: {query}")
        
        query_emb = self.embedding_model.encode([query])
        
        results = self.vector_store.query(query_embeddings=query_emb, n_results=top_k)
        
        docs = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results.get("distances", [[]])[0]

        hits = []
        for i, (doc, meta, dist) in enumerate(zip(docs, metadatas, distances)):
            citation = meta.get("filename", "unknown")
            if meta.get("year") and meta.get("pos"):
                citation = f"{meta.get('publisher', '')}_{meta.get('year', '')}_poz.{meta.get('pos', '')}"
            
            chunk_id = meta.get("chunk_id", None)
            full_citation = f"{citation}#{chunk_id}" if chunk_id is not None else citation
            
            hits.append({
                "rank": i+1,
                "score": float(dist) if dist is not None else None,
                "text": doc,
                "meta": meta,
                "citation": full_citation
            })

        # Compose context
        parts = []
        total_chars = 0
        for h in hits:
            block = f"[Źródło: {h['citation']}]\n{h['text'].strip()}\n"
            if total_chars + len(block) > char_limit:
                break
            parts.append(block)
            total_chars += len(block)
        
        context_text = "\n---\n".join(parts)
        return context_text, hits

    def build_prompt(self, question: str, context: str) -> str:
        """
        Constructs the prompt for the LLM.
        """
        prompt = f"""
        Jesteś ekspertem prawa polskiego. Odpowiedz na zadane pytanie **wyłącznie** na podstawie poniższych fragmentów ustaw (nie wymyślaj dodatkowych informacji).
        Jeśli fragmenty są sprzeczne lub niewystarczające, zaznacz to i wskaż jakie dodatkowe źródła byłyby potrzebne.
        Podaj odpowiedź po polsku. Na końcu krótkie odniesienie do użytych źródeł (np. "Źródła: DU_2020_poz.123#4).

        Poniżej fragmenty aktów:
        {context}

        Pytanie: {question}

        Odpowiedź:
        """.strip()
        
        # Simple truncation to fit context window approximately (considering system prompt + generation)
        # 1 token approx 4 chars, so LLAMA_N_CTX * 4 is rough char limit.
        if len(prompt) > LLAMA_N_CTX * 3:
            return prompt[:LLAMA_N_CTX * 3] + "..."
        return prompt


    def run(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Runs the full RAG pipeline: Retrieve -> Generate.
        Checks cache first to avoid redundant LLM calls.
        """
        # Check cache first
        cache_key = generate_cache_key(query, top_k)
        cached_result = get_cache(cache_key)
        if cached_result:
            logger.info("Returning cached response")
            cached_result["from_cache"] = True
            return cached_result
        
        context_text, hits = self.retrieve(query, top_k=top_k)
        
        if not context_text.strip():
            logger.warning("No relevant fragments found in database.")
            return {
                "answer": "Nie znaleziono odpowiednich fragmentów w bazie wiedzy, aby odpowiedzieć na to pytanie.",
                "hits": hits,
                "context": context_text,
                "from_cache": False
            }

        prompt = self.build_prompt(query, context_text)
        logger.debug(f"Prompt preview: {prompt[:200]}...")

        answer, raw_response = self.llm_model.generate(prompt)
        
        result = {
            "answer": answer,
            "hits": hits,
            "prompt": prompt,
            "raw_response": raw_response,
            "from_cache": False
        }
        
        # Store in cache (exclude raw_response to save space)
        cache_data = {
            "answer": answer,
            "hits": hits,
            "from_cache": True
        }
        set_cache(cache_key, cache_data)
        
        return result
