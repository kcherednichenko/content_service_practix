import uuid
from uuid import UUID
from typing import Any, Dict, List

import pytest
from pydantic import BaseModel as PydanticBaseModel, ConfigDict, field_validator, Field

from tests.functional.utils.models import Person, Film, FilmPerson
from tests.functional.utils.data_generators import generate_films, generate_persons, generate_person

_PERSONS_INDEX_NAME = 'personas'
_FILMS_INDEX_NAME = 'movies'
_PERSON_ID_KEY_PREFIX = 'person_id_'
_FILMS_ID_KEY_PREFIX = 'films'


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index')
async def test_get_existing_person_by_id(es_write_data, make_get_request) -> None:
    person = generate_person()
    await es_write_data([_build_es_person(person)])

    response = await make_get_request(f'api/v1/persons/{person.id}')

    assert response.status == 200
    body = await response.json()
    assert body == _expected_person(person)


@pytest.mark.asyncio
async def test_get_person_by_id_from_cache(redis_write_data, make_get_request) -> None:
    person = generate_person()
    redis_key = _PERSON_ID_KEY_PREFIX + str(person.id)
    await redis_write_data(redis_key, person.model_dump_json())

    response = await make_get_request(f'api/v1/persons/{person.id}')

    assert response.status == 200
    body = await response.json()
    assert body == _expected_person(person)


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index')
async def test_get_not_existing_person_by_id(make_get_request) -> None:
    response = await make_get_request(f'api/v1/persons/{uuid.uuid4()}')
    assert response.status == 404


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index')
async def test_search_returns_correct_persons(es_write_data, make_get_request) -> None:
    full_name = 'Tom Cucurus'
    searched_persons = generate_persons(full_name, cnt=3)
    not_searched_persons = generate_persons(cnt=3)
    await es_write_data([_build_es_person(p) for p in [*searched_persons, *not_searched_persons]])

    response = await make_get_request('api/v1/persons/search', {'query': full_name})

    assert response.status == 200
    body = await response.json()
    assert len(body) == len(searched_persons)
    assert body == _expected_persons(searched_persons)


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index')
async def test_search_no_persons(es_write_data, make_get_request) -> None:
    persons = generate_persons(cnt=5)
    await es_write_data([_build_es_person(p) for p in persons])

    response = await make_get_request('api/v1/persons/search', {'query': 'Someone'})

    assert response.status == 404


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index', 'films_index')
async def test_no_films_for_person(es_write_data, make_get_request) -> None:
    person = generate_person(films=[])
    await es_write_data([_build_es_person(person)])

    response = await make_get_request(f'api/v1/persons/{person.id}/film')

    assert response.status == 404


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index', 'films_index')
async def test_get_films_for_person(es_write_data, make_get_request) -> None:
    person_id, person_full_name = uuid.uuid4(), 'Tom Cucurus'
    films = [
        *generate_films(actors=[FilmPerson(id=person_id, name=person_full_name)], cnt=1),
        *generate_films(writers=[FilmPerson(id=person_id, name=person_full_name)], cnt=2),
        *generate_films(directors=[FilmPerson(id=person_id, name=person_full_name)], cnt=3),
    ]
    person = generate_person(id=person_id, full_name=person_full_name, films=films)
    await es_write_data([_build_es_person(person)])
    await es_write_data([_build_es_film(film) for film in films])

    response = await make_get_request(f'api/v1/persons/{person.id}/film')

    assert response.status == 200
    body = await response.json()
    assert len(body) == len(films)
    assert body == _expected_films(films)


@pytest.mark.asyncio
async def test_get_films_for_person_from_cache(redis_write_data, make_get_request) -> None:
    person_id, person_full_name = uuid.uuid4(), 'Tom Cucurus'
    films = [
        *generate_films(actors=[FilmPerson(id=person_id, name=person_full_name)], cnt=1),
        *generate_films(writers=[FilmPerson(id=person_id, name=person_full_name)], cnt=2),
        *generate_films(directors=[FilmPerson(id=person_id, name=person_full_name)], cnt=3),
    ]
    person = generate_person(id=person_id, full_name=person_full_name, films=films)
    person_redis_key = _PERSON_ID_KEY_PREFIX + str(person.id)
    await redis_write_data(person_redis_key, person.model_dump_json())
    for film in films:
        film_redis_key = _FILMS_ID_KEY_PREFIX + ':' + str(film.id)
        await redis_write_data(film_redis_key, film.model_dump_json())

    response = await make_get_request(f'api/v1/persons/{person.id}/film')

    assert response.status == 200
    body = await response.json()
    assert len(body) == len(films)
    assert body == _expected_films(films)


def _build_es_person(person: Person) -> List[Dict[str, Any]]:
    return _build_es_item(person, _PERSONS_INDEX_NAME)


def _build_es_film(film: Film) -> List[Dict[str, Any]]:
    return _build_es_item(film, _FILMS_INDEX_NAME)


def _build_es_item(model: Person | Film, index_name: str) -> List[Dict[str, Any]]:
    return {
        '_index': index_name,
        '_id': str(model.id),
        '_source': model.model_dump()
    }


def _expected_person(person: Person) -> Dict[str, Any]:
    return _PersonResponse.model_validate(person).model_dump()


def _expected_persons(persons: List[Person]) -> Dict[str, Any]:
    return [_PersonResponse.model_validate(person).model_dump() for person in persons]


def _expected_films(films: List[Film]) -> Dict[str, Any]:
    return [_FilmResponse.model_validate(film).model_dump() for film in films]


class _BaseModel(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str = Field(validation_alias='id')

    @field_validator('uuid', mode='before')
    @classmethod
    def uuid_to_str(cls, v: UUID) -> Any:
        return str(v)


class _PersonFilmResponse(_BaseModel):
    roles: List[str]


class _PersonResponse(_BaseModel):
    full_name: str
    films: List[_PersonFilmResponse]


class _FilmResponse(_BaseModel):
    title: str
    imdb_rating: float
