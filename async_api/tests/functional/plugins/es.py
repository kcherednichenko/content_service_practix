from typing import Any, Dict, List
from pathlib import Path

import pytest_asyncio

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from tests.functional.settings import test_settings


@pytest_asyncio.fixture(scope="session")
async def es_client():
    es_client = AsyncElasticsearch(f'http://{test_settings.elastic_host}:{test_settings.elastic_port}',
                                   verify_certs=False)
    yield es_client
    await es_client.close()


@pytest_asyncio.fixture
def es_write_data(es_client):
    async def inner(data: List[Dict[str, Any]]) -> None:
        _, errors = await async_bulk(client=es_client, actions=data, refresh='wait_for')
        if errors:
            raise Exception('Ошибка записи данных в Elasticsearch')
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
