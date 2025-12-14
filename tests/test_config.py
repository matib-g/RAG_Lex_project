import os
from src.utils import config

def test_project_root():
    assert config.PROJECT_ROOT.exists()
    assert config.PROJECT_ROOT.name == "rag_lex_project"

def test_default_config_values():
    assert config.COLLECTION_NAME == "isap_acts"
    assert config.LLAMA_N_CTX == 4096

def test_env_override(monkeypatch):
    monkeypatch.setenv("COLLECTION_NAME", "test_collection")
    monkeypatch.setenv("LLAMA_N_CTX", "1024")
    
    # Reload config to pick up changes
    # Note: This is tricky with python modules as they are cached.
    # In a real scenario we might wrap config in a class or re-import.
    # For this simple test, we can check if helper functions work.
    
    from src.utils.config import get_env
    assert get_env("COLLECTION_NAME", "default") == "test_collection"
    assert get_env("LLAMA_N_CTX", 2048, int) == 1024
