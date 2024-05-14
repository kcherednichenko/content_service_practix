from typing import Any, List

from pydantic import BaseModel, field_validator

from models.genre import Genre
from models.person import PersonBase


class Film(BaseModel):
    id: str
    title: str
    description: str
    imdb_rating: float
    genres: List[Genre] = []
    actors: List[PersonBase] = []
    writers: List[PersonBase] = []
    directors: List[PersonBase] = []

    @field_validator('description', mode='before')
    @classmethod
    def apply_default_description_on_none(cls, v: Any) -> Any:
        return '' if v is None else v
