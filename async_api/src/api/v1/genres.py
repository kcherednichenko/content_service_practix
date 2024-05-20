from http import HTTPStatus
from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path

from services.genre import GenreService, get_genre_service
from api.v1.schemas import Genre

router = APIRouter()


@router.get('/{genre_id}', response_model=Genre, response_model_by_alias=False)
async def genre_details(
    genre_id: Annotated[UUID, Path(description="genre id")],
    genre_service: GenreService = Depends(get_genre_service)
) -> Genre:
    """
    Get genre by id
    """
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')
    return Genre(id=genre.id, name=genre.name)


@router.get('/', response_model=List[Genre], response_model_by_alias=False)
async def get_all_genres(genre_service: GenreService = Depends(get_genre_service)) -> List[Genre]:
    """
    Get all genres
    """
    genres = await genre_service.get_all_genres()
    if not genres:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genres not found')
    return [Genre(id=g.id, name=g.name) for g in genres]
