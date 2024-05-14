from typing import Any, List, Dict
from uuid import UUID

from pydantic import BaseModel, root_validator


class PersonBase(BaseModel):
    id: UUID
    name: str

    @root_validator(pre=True)
    def name_alias(cls, values: Dict[str, Any]):
        if 'full_name' in values:
            values['name'] = values['full_name']
        return values


class Person(PersonBase):
    films: List = []
