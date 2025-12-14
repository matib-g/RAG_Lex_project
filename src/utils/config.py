import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Helper to get env with default or relative path handling
def get_path_env(key: str, default_relative: str) -> Path:
    val = os.getenv(key)
    if val:
        return Path(val) if Path(val).is_absolute() else PROJECT_ROOT / val
    return PROJECT_ROOT / default_relative

def get_env(key: str, default: any, cast_type: type = str):
    val = os.getenv(key)
    if val is None:
        return default
    return cast_type(val)

# Data Directories
DATA_DIR = PROJECT_ROOT / "data" # Keep as base
RAW_DATA_DIR = get_path_env("RAW_DATA_DIR", "data/raw_data")
PREPARED_DATA_FILE = get_path_env("PREPARED_DATA_FILE", "data/prepared_dataset.json")

# Vector DB
VECTOR_DB_DIR = get_path_env("VECTOR_DB_DIR", "vectordb")
CHROMA_DB_PATH = get_path_env("CHROMA_DB_PATH", "vectordb/chroma_db")
COLLECTION_NAME = get_env("COLLECTION_NAME", "isap_acts")

# Models
MODELS_DIR = get_path_env("MODELS_DIR", "models")
LLAMA_MODEL_FILENAME = get_env("LLAMA_MODEL_FILENAME", "PLLuM-8x7B-chat-gguf-q4_k_m.gguf")
LLAMA_GGUF_PATH = MODELS_DIR / LLAMA_MODEL_FILENAME

EMBEDDING_MODEL_NAME = get_env("EMBEDDING_MODEL_NAME", "sdadas/st-polish-paraphrase-from-distilroberta")

# API Sejm
SEJM_API_URL = get_env("SEJM_API_URL", "https://api.sejm.gov.pl/eli/acts")

# RAG Parameters
LLAMA_N_CTX = get_env("LLAMA_N_CTX", 4096, int)
TOP_K_RETRIEVAL = get_env("TOP_K_RETRIEVAL", 5, int)
MAX_GEN_TOKENS = get_env("MAX_GEN_TOKENS", 512, int)
PROMPT_MAX_CHARS = get_env("PROMPT_MAX_CHARS", 12000, int)
