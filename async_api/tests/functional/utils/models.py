from typing import List
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel, Field, AliasChoices


class BaseModel(PydanticBaseModel):
    uuid: UUID = Field(validation_alias=AliasChoices('id', 'uuid'), serialization_alias='id')


class PersonFilm(BaseModel):
    roles: List[str]


class Person(BaseModel):
    full_name: str
    films: List[PersonFilm]


class FilmPerson(BaseModel):
    name: str = Field(validation_alias=AliasChoices('name', 'full_name'), serialization_alias='name')


class FilmGenre(BaseModel):
    name: str


class Film(BaseModel):
    title: str
    description: str
    imdb_rating: float
    genres: List[FilmGenre] = []
    actors: List[FilmPerson] = []
    writers: List[FilmPerson] = []
    directors: List[FilmPerson] = []
