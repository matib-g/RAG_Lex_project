import os
from pathlib import Path
from llama_cpp import Llama
from typing import Dict, Any, Tuple, Generator
from src.utils.config import LLAMA_GGUF_PATH, LLAMA_N_CTX
from src.utils.logger import setup_logger

logger = setup_logger("llm_model")

class LlamaModel:
    def __init__(self, model_path: Path = LLAMA_GGUF_PATH, n_ctx: int = LLAMA_N_CTX):
        if not model_path.exists():
            raise FileNotFoundError(f"LLAMA model file not found at: {model_path}")
        
        logger.info(f"Loading LLM from {model_path}")
        # Adjust n_threads/n_gpu_layers as needed or make configurable
        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=n_ctx,
            n_threads=8,
            n_gpu_layers=1, # Defaulting to some GPU usage if available (Metal on Mac)
            n_batch=512
        )

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> Tuple[str, Dict[str, Any]]:
        logger.info("Generating answer from LLM...")
        resp = self.llm(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        text = resp.get("choices", [{}])[0].get("text", "").strip()
        return text, resp

    def generate_stream(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> Generator[str, None, None]:
        """Generate tokens one at a time for streaming."""
        logger.info("Streaming answer from LLM...")
        for chunk in self.llm(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True
        ):
            token = chunk.get("choices", [{}])[0].get("text", "")
            if token:
                yield token
