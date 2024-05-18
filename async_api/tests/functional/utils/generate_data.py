import random
import uuid

from tests.functional.utils.models import Film, FilmGenre, FilmPerson


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
