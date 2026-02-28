"""Redis async cache layer."""
import json
import logging
from typing import Any, Optional

from utils.config import settings

logger = logging.getLogger(__name__)


class Cache:
    def __init__(self):
        self._redis = None

    async def connect(self):
        try:
            import redis.asyncio as aioredis
            self._redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await self._redis.ping()
            logger.info("Redis connected successfully.")
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}). Cache disabled — using in-memory fallback.")
            self._redis = None
            self._memory: dict = {}

    async def disconnect(self):
        if self._redis:
            await self._redis.aclose()

    async def get(self, key: str) -> Optional[Any]:
        try:
            if self._redis:
                val = await self._redis.get(key)
                return json.loads(val) if val else None
            else:
                return self._memory.get(key)
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 60):
        try:
            if self._redis:
                await self._redis.setex(key, ttl, json.dumps(value))
            else:
                self._memory[key] = value
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")

    async def delete(self, key: str):
        try:
            if self._redis:
                await self._redis.delete(key)
            elif hasattr(self, '_memory'):
                self._memory.pop(key, None)
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")


cache = Cache()
