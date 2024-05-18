import random
import uuid
from typing import List
from uuid import UUID

from tests.functional.utils.models import Film, FilmGenre, FilmPerson, Person, PersonFilm


def generate_films(keyword: str | None = None,
                   actors: List[FilmPerson] | None = None,
                   writers: List[FilmPerson] | None = None,
                   directors: List[FilmPerson] | None = None,
                   cnt: int = 10) -> List[Film]:
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
            actors=actors or [random.choice(film_persons) for _ in range(random.randint(0, 9))],
            writers=writers or [random.choice(film_persons) for _ in range(random.randint(0, 9))],
            directors=directors or [random.choice(film_persons) for _ in range(random.randint(0, 9))],
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


def generate_person(id: UUID | None = None,
                    full_name: str = 'full name',
                    films: List[Film] | None = None) -> Person:
    person_id = id or uuid.uuid4()
    person_films = (_build_person_films_by_films(films, person_id)
                    if films is not None
                    else [_generate_person_film() for _ in range(random.randint(1, 3))])
    return Person(uuid=person_id, full_name=full_name, films=person_films)


def generate_persons(full_name: str = 'full name', cnt: int = 1) -> List[Person]:
    return [generate_person(full_name=full_name) for _ in range(cnt)]


def _generate_person_film(id: UUID | None = None, roles: List[str] | None = None) -> PersonFilm:
    film_roles = ['writer', 'director', 'actor']
    return PersonFilm(
        uuid=id or uuid.uuid4(),
        roles=roles or random.sample(film_roles, random.randint(1, len(film_roles)))
    )


def _build_person_films_by_films(films: List[Film], person_id: UUID) -> List[PersonFilm]:
    person_films = []
    for film in films:
        film_roles = []
        if person_id in [p.uuid for p in film.actors]:
            film_roles.append('actor')
        if person_id in [p.uuid for p in film.writers]:
            film_roles.append('writer')
        if person_id in [p.uuid for p in film.directors]:
            film_roles.append('director')
        if film_roles:
            person_films.append(PersonFilm(id=film.uuid, roles=film_roles))
    return person_films
