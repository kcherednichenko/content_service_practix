import uuid

import pytest

from tests.functional.utils.models import Film
from tests.functional.utils.data_generators import generate_films

_MOVIES_INDEX_NAME = 'movies'
_FILM_CACHE_PREFIX = 'films'


@pytest.mark.asyncio
@pytest.mark.usefixtures('films_index')
async def test_get_existing_film_by_id_from_db(es_write_data, make_get_request):
    film = generate_films(cnt=1)[0]
    await es_write_data([{'_index': _MOVIES_INDEX_NAME, '_id': str(film.id), '_source': film.model_dump()}])

    response = await make_get_request(f'api/v1/films/{film.id}')

    assert response.status == 200
    body = await response.json()
    assert film == Film(**body)


@pytest.mark.asyncio
@pytest.mark.usefixtures('films_index')
async def test_get_existing_film_by_id_from_cache(redis_write_data, make_get_request):
    film = generate_films(cnt=1)[0]
    cache_key = f'{_FILM_CACHE_PREFIX}:{film.id}'
    await redis_write_data(cache_key, film.model_dump_json())

    response = await make_get_request(f'api/v1/films/{film.id}')

    assert response.status == 200
    body = await response.json()
    assert film == Film(**body)


@pytest.mark.asyncio
@pytest.mark.usefixtures('films_index')
async def test_get_not_existing_film_by_id(make_get_request):
    response = await make_get_request(f'api/v1/films/{uuid.uuid4()}')

    assert response.status == 404


@pytest.mark.asyncio
@pytest.mark.usefixtures('films_index')
async def test_search_existing_film(es_write_data, make_get_request):
    query = 'test'
    films = generate_films(keyword=query, cnt=10)
    cnt_films_with_keyword = 0
    for film in films:
        if query in film.title:
            cnt_films_with_keyword += 1

        await es_write_data([{'_index': _MOVIES_INDEX_NAME, '_id': str(film.id), '_source': film.model_dump()}])

    response = await make_get_request(f'api/v1/films/search?query={query}')

    assert response.status == 200
    body = await response.json()
    assert cnt_films_with_keyword == len(body)

    for film in body:
        assert query in film['title']


@pytest.mark.asyncio
@pytest.mark.usefixtures('films_index')
async def test_search_not_existing_film(es_write_data, make_get_request):
    query = 'no_such_film'
    response = await make_get_request(f'api/v1/films/search?query={query}')

    assert response.status == 200
    body = await response.json()
    assert len(body) == 0
