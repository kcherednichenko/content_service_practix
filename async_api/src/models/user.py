from typing import List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel


class Role(str, Enum):
    SUBSCRIBER = 'subscriber'
    ADMIN = 'admin'
    SUPERUSER = 'superuser'
    SERVICE = 'service'


class User(BaseModel):
    id: UUID
    roles: List[str]
