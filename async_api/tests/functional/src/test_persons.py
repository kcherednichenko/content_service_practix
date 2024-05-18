import uuid
from uuid import UUID
import random
from typing import Any, Dict, List

import pytest
from pydantic import BaseModel as PydanticBaseModel, ConfigDict, field_validator

from tests.functional.utils.models import Person, PersonFilm, Film, FilmPerson, FilmGenre

_PERSONS_INDEX_NAME = 'personas'
_FILMS_INDEX_NAME = 'movies'
_PERSON_ID_KEY_PREFIX = 'person_id_'
_FILMS_ID_KEY_PREFIX = 'films'


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index')
async def test_get_existing_person_by_id(es_write_data, make_get_request) -> None:
    person = _build_person()
    await es_write_data([_build_es_person(person)])

    response = await make_get_request(f'api/v1/persons/{person.uuid}')

    assert response.status == 200
    body = await response.json()
    assert body == _expected_person(person)


@pytest.mark.asyncio
async def test_get_person_by_id_from_cache(redis_write_data, make_get_request) -> None:
    person = _build_person()
    redis_key = _PERSON_ID_KEY_PREFIX + str(person.uuid)
    await redis_write_data(redis_key, person.model_dump_json(by_alias=True))

    response = await make_get_request(f'api/v1/persons/{person.uuid}')

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
    first_name = 'Tom'
    searched_persons = _build_persons(first_name, quantity=3)
    not_searched_persons = _build_persons(quantity=3)
    await es_write_data([_build_es_person(p) for p in [*searched_persons, *not_searched_persons]])

    response = await make_get_request('api/v1/persons/search', {'query': first_name})

    assert response.status == 200
    body = await response.json()
    assert len(body) == len(searched_persons)
    assert body == _expected_persons(searched_persons)


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index')
async def test_search_no_persons(es_write_data, make_get_request) -> None:
    persons = [_build_person('Tom Cucurus') for _ in range(5)]
    await es_write_data([_build_es_person(p) for p in persons])

    response = await make_get_request('api/v1/persons/search', {'query': 'Someone Else'})

    assert response.status == 404


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index', 'films_index')
async def test_no_films_for_person(es_write_data, make_get_request) -> None:
    person = _build_person(films=[])
    await es_write_data([_build_es_person(person)])

    response = await make_get_request(f'api/v1/persons/{person.uuid}/film')

    assert response.status == 404


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index', 'films_index')
async def test_get_films_for_person(es_write_data, make_get_request) -> None:
    person_id, person_full_name = uuid.uuid4(), 'Tom Cucurus'
    films = [
        _build_film(actors=[_build_film_person(id=person_id, name=person_full_name)]),
        _build_film(writers=[_build_film_person(id=person_id, name=person_full_name)]),
        _build_film(directors=[_build_film_person(id=person_id, name=person_full_name)]),
    ]
    person = _build_person(full_name=person_full_name, films=[
        _build_person_film(id=films[0].uuid, roles=['actor']),
        _build_person_film(id=films[1].uuid, roles=['writer']),
        _build_person_film(id=films[2].uuid, roles=['director']),
    ])
    await es_write_data([_build_es_person(person)])
    await es_write_data([_build_es_film(film) for film in films])

    response = await make_get_request(f'api/v1/persons/{person.uuid}/film')

    assert response.status == 200
    body = await response.json()
    assert len(body) == len(films)
    assert body == _expected_films(films)


@pytest.mark.asyncio
async def test_get_films_for_person_from_cache(redis_write_data, make_get_request) -> None:
    person_id, person_full_name = uuid.uuid4(), 'Tom Cucurus'
    films = [
        _build_film(actors=[_build_film_person(id=person_id, name=person_full_name)]),
        _build_film(writers=[_build_film_person(id=person_id, name=person_full_name)]),
        _build_film(directors=[_build_film_person(id=person_id, name=person_full_name)]),
    ]
    person = _build_person(full_name=person_full_name, films=[
        _build_person_film(id=films[0].uuid, roles=['actor']),
        _build_person_film(id=films[1].uuid, roles=['writer']),
        _build_person_film(id=films[2].uuid, roles=['director']),
    ])
    person_redis_key = _PERSON_ID_KEY_PREFIX + str(person.uuid)
    await redis_write_data(person_redis_key, person.model_dump_json(by_alias=True))
    for film in films:
        film_redis_key = _FILMS_ID_KEY_PREFIX + ':' + str(film.uuid)
        await redis_write_data(film_redis_key, film.model_dump_json(by_alias=True))

    response = await make_get_request(f'api/v1/persons/{person.uuid}/film')

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
        '_id': str(model.uuid),
        '_source': model.model_dump(by_alias=True)
    }


def _build_person(full_name: str = 'full name', films: List[PersonFilm] | None = None) -> Person:
    return Person(
        uuid=uuid.uuid4(),
        full_name=full_name,
        films=films if films is not None else [_build_person_film() for _ in range(random.randint(1, 3))]
    )


def _build_persons(first_name: str = '',  last_name: str = '', quantity: int = 1) -> List[Person]:
    full_name = f'{first_name or uuid.uuid4()} {last_name or uuid.uuid4()}'
    return [_build_person(full_name=full_name) for _ in range(quantity)]


def _build_person_film(id: UUID | None = None, roles: List[str] | None = None) -> PersonFilm:
    film_roles = ['writer', 'director', 'actor']
    return PersonFilm(
        uuid=id or uuid.uuid4(),
        roles=roles or random.sample(film_roles, random.randint(1, len(film_roles)))
    )


def _build_film(actors: List[FilmPerson] | None = None,
                writers: List[FilmPerson] | None = None,
                directors: List[FilmPerson] | None = None) -> Film:
    return Film(
        uuid=uuid.uuid4(),
        title='title',
        description='description',
        imdb_rating=round(random.uniform(0.0, 10.0), 1),
        genres=[_build_film_genre() for _ in range(random.randint(1, 3))],
        actors=actors or [_build_film_person() for _ in range(random.randint(1, 3))],
        writers=writers or [_build_film_person() for _ in range(random.randint(1, 3))],
        directors=directors or [_build_film_person() for _ in range(random.randint(1, 3))],
    )


def _build_film_person(id: UUID | None = None, name: str = 'Tom Cruise') -> FilmPerson:
    return FilmPerson(uuid=id or uuid.uuid4(), name=name)


def _build_film_genre() -> FilmGenre:
    return FilmGenre(uuid=uuid.uuid4(), name='comedy')


def _expected_person(person: Person) -> Dict[str, Any]:
    return _PersonResponse.model_validate(person).model_dump()


def _expected_persons(persons: List[Person]) -> Dict[str, Any]:
    return [_PersonResponse.model_validate(person).model_dump() for person in persons]


def _expected_films(films: List[Film]) -> Dict[str, Any]:
    return [_FilmResponse.model_validate(film).model_dump() for film in films]


class _BaseModel(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str

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
