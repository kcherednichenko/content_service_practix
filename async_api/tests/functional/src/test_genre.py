import uuid
from http import HTTPStatus

import pytest

from tests.functional.utils.data_generators import generate_genre, generate_genres

GENRE_INDEX_NAME = 'genres'
_GENRE_ID_KEY_PREFIX = 'genre_id_'


@pytest.mark.asyncio
@pytest.mark.usefixtures('genres_index')
async def test_genres_views_status_code(es_write_data, make_get_request):
    id = uuid.uuid4()
    not_found_id = uuid.uuid4()
    genre = generate_genre(id=id)
    await es_write_data(
        [
            {
                '_index': GENRE_INDEX_NAME,
                '_id': genre.id,
                '_source': genre.model_dump(),
            }
        ]
    )
    requests = ((id, HTTPStatus.OK), (not_found_id, HTTPStatus.NOT_FOUND))

    for id, staus_code in requests:
        response = await make_get_request(f'api/v1/genres/{id}')

        assert response.status == staus_code


@pytest.mark.asyncio
@pytest.mark.usefixtures('genres_index')
async def test_genres_list(es_write_data, make_get_request):
    genres = generate_genres(cnt=5)
    await es_write_data(
        [
            {
                '_index': GENRE_INDEX_NAME,
                '_id': genre.id,
                '_source': genre.model_dump(),
            }
            for genre in genres
        ]
    )

    response = await make_get_request('api/v1/genres/')

    assert response.status == HTTPStatus.OK
    body = await response.json()
    assert len(body) == len(genres)


@pytest.mark.asyncio
async def test_get_genre_in_redis(redis_write_data, make_get_request):
    id = uuid.uuid4()
    genre = generate_genre(id=id)
    cache_key = _GENRE_ID_KEY_PREFIX + str(genre.id)
    await redis_write_data(cache_key, genre.model_dump_json())

    response = await make_get_request(f'api/v1/genres/{genre.id}')

    assert response.status == HTTPStatus.OK
