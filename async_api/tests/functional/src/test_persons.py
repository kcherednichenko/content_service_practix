import uuid
import random
from typing import Any, Dict, List
import asyncio

import pytest

from tests.functional.utils.models import Person, PersonFilm

_PERSONS_INDEX_NAME = "personas"
_PERSON_ID_KEY_PREFIX = 'person_id_'


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index')
async def test_get_existing_person_by_id(es_write_data, make_get_request):
    person = _build_person()
    await es_write_data([_build_es_person(person)])

    response = await make_get_request(f'api/v1/persons/{person.uuid}')

    assert response.status == 200
    body = await response.json()
    assert person == Person(**body)


@pytest.mark.asyncio
async def test_get_person_by_id_from_cache(redis_write_data, make_get_request):
    person = _build_person()
    redis_key = _PERSON_ID_KEY_PREFIX + str(person.uuid)
    await redis_write_data(redis_key, person.model_dump_json(by_alias=True))

    response = await make_get_request(f'api/v1/persons/{person.uuid}')

    assert response.status == 200
    body = await response.json()
    assert person == Person(**body)


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index')
async def test_get_not_existing_person_by_id(make_get_request):
    response = await make_get_request(f'api/v1/persons/{uuid.uuid4()}')
    assert response.status == 404


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index')
async def test_search_returns_correct_persons(es_write_data, make_get_request):
    searched_persons = [
        _build_person("Tom Cucurus"),
        _build_person("Tom Crus"),
        _build_person("Tom Shruz"),
    ]
    not_searched_person = _build_person("Someone Else")
    await es_write_data([_build_es_person(p) for p in [*searched_persons, not_searched_person]])

    response = await make_get_request('api/v1/persons/search', {'query': 'Tom'})

    assert response.status == 200
    body = await response.json()
    assert len(body) == len(searched_persons)


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index')
async def test_search_no_persons(es_write_data, make_get_request):
    persons = [_build_person("Tom Cucurus") for _ in range(5)]
    await es_write_data([_build_es_person(p) for p in persons])

    response = await make_get_request('api/v1/persons/search', {'query': 'Someone Else'})

    assert response.status == 404


def _build_es_person(person: Person) -> List[Dict[str, Any]]:
    return {
        '_index': _PERSONS_INDEX_NAME,
        '_id': str(person.uuid),
        '_source': person.model_dump(by_alias=True)
    }


def _build_person(full_name: str = 'full name') -> Person:
    return Person(
        uuid=uuid.uuid4(),
        full_name=full_name,
        films=[_build_person_film() for _ in range(random.randint(1, 3))]
    )


def _build_person_film() -> PersonFilm:
    film_roles = ['writer', 'director', 'actor']
    return PersonFilm(uuid=uuid.uuid4(), roles=random.sample(film_roles, random.randint(1, len(film_roles))))
