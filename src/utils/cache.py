"""
Redis cache module for RAG responses.
"""
import os
import json
import hashlib
from typing import Optional, Any
import redis
from src.utils.logger import setup_logger

logger = setup_logger("cache")

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            _redis_client.ping()
            logger.info(f"Connected to Redis at {REDIS_URL}")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Caching disabled.")
            _redis_client = None
    return _redis_client


def generate_cache_key(query: str, top_k: int) -> str:
    """Generate a unique cache key for a query."""
    content = f"{query.strip().lower()}:{top_k}"
    return f"rag:{hashlib.md5(content.encode()).hexdigest()}"


def get_cache(key: str) -> Optional[dict]:
    """Get cached response."""
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        data = client.get(key)
        if data:
            logger.info(f"Cache HIT for key: {key[:20]}...")
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
    
    return None


def set_cache(key: str, value: dict, ttl: int = None) -> bool:
    """Store response in cache."""
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        ttl = ttl or CACHE_TTL
        client.setex(key, ttl, json.dumps(value))
        logger.info(f"Cache SET for key: {key[:20]}... (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.warning(f"Cache set error: {e}")
        return False
