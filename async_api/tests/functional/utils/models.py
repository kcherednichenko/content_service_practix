from typing import List, Dict, Any
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel, Field, AliasChoices, root_validator, field_validator


class BaseModel(PydanticBaseModel):
    id: UUID = Field(validation_alias=AliasChoices('id', 'uuid'))


class PersonFilm(BaseModel):
    roles: List[str]


class Person(BaseModel):
    full_name: str
    films: List[PersonFilm]


class FilmPerson(BaseModel):
    name: str

    @root_validator(pre=True)
    def name_alias(cls, values: Dict[str, Any]):
        if 'full_name' in values:
            values['name'] = values['full_name']
        return values


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

    @field_validator('description', mode='before')
    @classmethod
    def apply_default_description_on_none(cls, v: Any) -> Any:
        return '' if v is None else v
