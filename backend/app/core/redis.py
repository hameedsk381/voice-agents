import redis.asyncio as redis
from app.core.config import settings

request_pool = redis.ConnectionPool.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    encoding="utf-8",
    decode_responses=True
)

async def get_redis_connection():
    return redis.Redis(connection_pool=request_pool)
