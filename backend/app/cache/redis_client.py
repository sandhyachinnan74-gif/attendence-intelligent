import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        self._client = None
        self._is_fake = False

    async def get_client(self):
        if self._client is None:
            if not settings.USE_FAKEREDIS_FALLBACK:
                try:
                    import redis.asyncio as aioredis
                    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                    await client.ping()
                    self._client = client
                    self._is_fake = False
                    logger.info("Connected to real Redis at %s", settings.REDIS_URL)
                    return self._client
                except Exception as e:
                    logger.warning("Could not connect to Redis: %s. Falling back to FakeRedis.", e)

            # Fallback to fakeredis
            try:
                import fakeredis.aioredis as fake_aioredis
                self._client = fake_aioredis.FakeRedis(decode_responses=True)
                self._is_fake = True
                logger.info("Using in-memory FakeRedis fallback.")
            except Exception as e:
                logger.error("Failed to initialize FakeRedis: %s", e)
                raise e

        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

redis_manager = RedisManager()

async def get_redis():
    return await redis_manager.get_client()
