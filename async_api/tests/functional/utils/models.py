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
