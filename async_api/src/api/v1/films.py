from http import HTTPStatus
from uuid import UUID
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Path

from services.film import FilmService, get_film_service, FilmServiceError
from api.v1.schemas import Film, FilmDetailed
from api.v1.dependencies import get_pagination_params, PaginationParams

router = APIRouter()


@router.get('/', response_model=List[Film], response_model_by_alias=False)
async def films(
    genre: Annotated[UUID | None, Query(description="genre id")] = None,
    pagination_params: PaginationParams = Depends(get_pagination_params),
    film_service: FilmService = Depends(get_film_service)
) -> List[Film]:
    """
    Get list with all films with such genre
    """
    try:
        films = await film_service.get_films(genre, pagination_params.limit, pagination_params.offset)
    except FilmServiceError:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    return [Film.from_orm(f) for f in films]


@router.get('/search', response_model=List[Film], response_model_by_alias=False)
async def search(
    query: Annotated[str, Query(description="query containing a film's title")],
    pagination_params: PaginationParams = Depends(get_pagination_params),
    film_service: FilmService = Depends(get_film_service)
) -> List[Film]:
    """
    Search by title of the film
    """
    try:
        films = await film_service.get_films_by_query(query, pagination_params.limit, pagination_params.offset)
    except FilmServiceError:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    return [Film.from_orm(f) for f in films]


@router.get('/{film_id}', response_model=FilmDetailed, response_model_by_alias=False)
async def film_details(
    film_id: Annotated[UUID, Path(description="film id")],
    film_service: FilmService = Depends(get_film_service)
) -> FilmDetailed:
    """
    Get film by id
    """
    try:
        film = await film_service.get_film_by_id(film_id)
    except FilmServiceError:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')
    return FilmDetailed.from_orm(film)
