
import os
import json
import redis
from dotenv import load_dotenv
from .logger_config import logger

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )
    r.ping()
    logger.info("Redis connected successfully")
except Exception as e:
    r = None
    logger.warning(f"Redis not available: {e}")


def get_cache(key: str):
    if r:
        return r.get(key)
    return None


def set_cache(key: str, value, expire: int = 60):
    if r:
        r.set(key, json.dumps(value), ex=expire)


def delete_cache(key: str):
    if r:
        r.delete(key)


def delete_cache_pattern(pattern: str):
    if r:
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)