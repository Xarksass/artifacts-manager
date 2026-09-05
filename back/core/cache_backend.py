# core/cache_backend.py
from fastapi_cache.backends.redis import RedisBackend

from core.logger import get_logger

logger = get_logger(__name__,'redis')

class LoggingRedisBackend(RedisBackend):
    async def get_with_ttl(self, key: str) -> tuple[int, bytes | None]:
        ttl, value = await super().get_with_ttl(key)
        if value is not None:
            logger.debug(f"[REDIS HIT] {key}")
        else:
            logger.debug(f"[REDIS MISS] {key}")
        return ttl, value

    async def set(self, key: str, value: bytes, expire: int | None = None) -> None:
        await super().set(key, value, expire)
        logger.debug(f"[REDIS SET] {key} (expire={expire}s)")