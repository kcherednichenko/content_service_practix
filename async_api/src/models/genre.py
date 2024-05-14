from typing import List

from pydantic import BaseModel


class Genre(BaseModel):
    id: str
    name: str


class Genres(BaseModel):
    genres: List[Genre]
