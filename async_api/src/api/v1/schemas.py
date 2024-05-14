from typing import List
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel, Field


class BaseModel(PydanticBaseModel):
    uuid: UUID = Field(alias='id')

    class Config:
        from_attributes = True


class Film(BaseModel):
    title: str
    imdb_rating: float


class Genre(BaseModel):
    name: str


class Person(BaseModel):
    full_name: str = Field(alias='name')


class FilmDetailed(Film):
    title: str
    imdb_rating: float
    description: str
    genres: List[Genre]
    actors: List[Person]
    writers: List[Person]
    directors: List[Person]


class PersonFilm(BaseModel):
    roles: List[str]


class PersonWithFilms(Person):
    films: List[PersonFilm]
