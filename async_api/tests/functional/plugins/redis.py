import pytest_asyncio
from redis.asyncio import Redis

from tests.functional.settings import test_settings


_TEST_REDIS_KEY_EXPIRE_IN_SECONDS = 10


@pytest_asyncio.fixture(scope="session")
async def redis_client():
    redis_client = Redis(host=test_settings.redis_host, port=test_settings.redis_port)
    yield redis_client
    await redis_client.aclose()


@pytest_asyncio.fixture
def redis_write_data(redis_client):
    async def inner(key: str, data: str) -> None:
        await redis_client.set(key, data, _TEST_REDIS_KEY_EXPIRE_IN_SECONDS)
    return inner
