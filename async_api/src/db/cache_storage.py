from abc import ABC, abstractmethod

from redis.asyncio import Redis

CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 minutes


class AbstractCacheStorage(ABC):
    @abstractmethod
    def set(self, key, value):
        pass

    @abstractmethod
    def get(self, key):
        pass


class RedisCacheStorage(AbstractCacheStorage):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def set(self, key: str, value: str, expire_in: int = CACHE_EXPIRE_IN_SECONDS):
        await self.redis.set(key, value, expire_in)

    async def get(self, key: str):
        return await self.redis.get(key)
