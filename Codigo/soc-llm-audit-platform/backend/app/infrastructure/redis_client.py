"""
Redis client for sessions and rate limiting.
Falls back to no-op when redis is unavailable.
"""
import structlog
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

try:
    import redis.asyncio as redis
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_session = redis.from_url(
        f"redis://localhost:6379/{settings.REDIS_SESSION_DB}", decode_responses=True
    )
    redis_rate_limit = redis.from_url(
        f"redis://localhost:6379/{settings.REDIS_RATE_LIMIT_DB}", decode_responses=True
    )
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False
    redis_client = None
    redis_session = None
    redis_rate_limit = None
    logger.warning("Redis not available — cache/sessions disabled (dev mode)")


async def get_redis():
    return redis_client
