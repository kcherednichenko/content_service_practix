from typing import Dict
import asyncio

import aiohttp
import pytest_asyncio

from tests.functional.settings import test_settings

pytest_plugins = ['tests.functional.plugins.es', 'tests.functional.plugins.redis']


@pytest_asyncio.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


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
