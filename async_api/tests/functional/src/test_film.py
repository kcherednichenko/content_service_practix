import uuid
import random

import pytest

from tests.functional.utils.models import Film, FilmGenre, FilmPerson

_MOVIES_INDEX_NAME = 'movies'
_FILM_CACHE_PREFIX = 'films'


@pytest.mark.asyncio
@pytest.mark.usefixtures('films_index')
async def test_get_existing_film_by_id_from_db(es_write_data, make_get_request):
    film_id = uuid.uuid4()
    film = Film(
        id=film_id,
        title='title',
        description='description',
        imdb_rating=10.0,
        genres=[FilmGenre(id=uuid.uuid4(), name='Comedy'), FilmGenre(id=uuid.uuid4(), name='TV Show')],
        actors=[FilmPerson(id=uuid.uuid4(), name='Actor 1'), FilmPerson(id=uuid.uuid4(), name='Actor 2')],
        writers=[FilmPerson(id=uuid.uuid4(), name='Writer 1'), FilmPerson(id=uuid.uuid4(), name='Writer 2')],
        directors=[FilmPerson(id=uuid.uuid4(), name='Director 1'), FilmPerson(id=uuid.uuid4(), name='Director 2')],
    )
    await es_write_data([{'_index': _MOVIES_INDEX_NAME, '_id': str(film_id), '_source': film.model_dump()}])

    response = await make_get_request(f'api/v1/films/{film_id}')

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


def generate_films(keyword=None, cnt=10):
    film_genres = generate_film_genres(2)
    film_persons = generate_film_persons(2)
    titles = ['title', 'title ' + keyword] if keyword else ['title']
    films = []
    for i in range(cnt):
        film_id = uuid.uuid4()
        film = Film(
            id=film_id,
            title=random.choice(titles),
            description='description',
            imdb_rating=round(random.uniform(0.0, 10.0), 2),
            genres=[random.choice(film_genres) for _ in range(random.randint(0, 9))],
            actors=[random.choice(film_persons) for _ in range(random.randint(0, 9))],
            writers=[random.choice(film_persons) for _ in range(random.randint(0, 9))],
            directors=[random.choice(film_persons) for _ in range(random.randint(0, 9))],
        )
        films.append(film)

    return films


def generate_film_genres(cnt=10):
    genres_names = ['Comedy', 'Horror', 'TV Show', 'News', 'Drama', 'Fantasy']
    genres = []
    for i in range(cnt):
        genres.append(FilmGenre(id=uuid.uuid4(), name=random.choice(genres_names)))

    return genres


def generate_film_persons(cnt=10):
    film_persons_names = ['Sasha', 'Ira', 'Vasya', 'Natasha', 'Afanasiy', 'Zoya', 'Alex', 'Dasha', 'Denis', 'Olga']
    film_persons = []
    for i in range(cnt):
        film_persons.append(FilmPerson(id=uuid.uuid4(), name=random.choice(film_persons_names)))

    return film_persons
