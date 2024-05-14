from fastapi import Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    limit: int
    offset: int


def get_pagination_params(
    page_number: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1)
) -> PaginationParams:
    limit, offset = page_size, (page_number - 1) * page_size
    return PaginationParams(limit=limit, offset=offset)
