import redis.asyncio as redis
from app.core.config import settings

redis_url = (
    f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}"
    if settings.REDIS_PASSWORD
    else f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
)

request_pool = redis.ConnectionPool.from_url(
    redis_url,
    encoding="utf-8",
    decode_responses=True
)

async def get_redis_connection():
    return redis.Redis(connection_pool=request_pool)
