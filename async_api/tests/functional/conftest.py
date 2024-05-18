from typing import Any, Dict, List
from pathlib import Path
import asyncio

import aiohttp
import pytest_asyncio
from redis.asyncio import Redis

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from tests.functional.settings import test_settings


_TEST_REDIS_KEY_EXPIRE_IN_SECONDS = 10


@pytest_asyncio.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def es_client():
    es_client = AsyncElasticsearch(f'http://{test_settings.elastic_host}:{test_settings.elastic_port}',
                                   verify_certs=False)
    yield es_client
    await es_client.close()


@pytest_asyncio.fixture(scope="session")
async def redis_client():
    redis_client = Redis(host=test_settings.redis_host, port=test_settings.redis_port)
    yield redis_client
    await redis_client.aclose()


@pytest_asyncio.fixture
def es_write_data(es_client):
    async def inner(data: List[Dict[str, Any]]) -> None:
        _, errors = await async_bulk(client=es_client, actions=data, refresh='wait_for')
        if errors:
            raise Exception('Ошибка записи данных в Elasticsearch')
    return inner


@pytest_asyncio.fixture
def redis_write_data(redis_client):
    async def inner(key: str, data: str) -> None:
        await redis_client.set(key, data, _TEST_REDIS_KEY_EXPIRE_IN_SECONDS)
    return inner


@pytest_asyncio.fixture(scope="session")
async def aiohttp_session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest_asyncio.fixture
async def make_get_request(aiohttp_session):
    async def inner(path: str, params: Dict[str, str] | None = None):
        url = f'http://{test_settings.service_host}:{test_settings.service_port}/{path}'
        return await aiohttp_session.get(url, params=(params or {}))
    return inner


@pytest_asyncio.fixture
async def create_index(es_client):
    async def inner(index: str) -> None:
        path = (Path('.') / 'testdata').resolve()
        with open(f'{path}/schema_{index}_es.json', encoding='utf-8') as f:
            schema = f.read()
        if await es_client.indices.exists(index=index):
            await es_client.indices.delete(index=index)
        await es_client.indices.create(index=index, body=schema)
    return inner


@pytest_asyncio.fixture
async def remove_index(es_client):
    async def inner(index: str) -> None:
        await es_client.indices.delete(index=index)
    return inner


@pytest_asyncio.fixture
async def films_index(create_index, remove_index):
    index = "movies"
    await create_index(index)
    yield
    await remove_index(index)


@pytest_asyncio.fixture
async def persons_index(create_index, remove_index):
    index = "personas"
    await create_index(index)
    yield
    await remove_index(index)


@pytest_asyncio.fixture
async def genres_index(create_index, remove_index):
    index = "genres"
    await create_index(index)
    yield
    await remove_index(index)
