from http import HTTPStatus
from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path

from services.person import PersonService, get_person_service
from api.v1.schemas import Film, PersonWithFilms
from api.v1.dependencies import get_pagination_params, PaginationParams

router = APIRouter()


@router.get('/search', response_model=List[PersonWithFilms], response_model_by_alias=False)
async def person_search(
    query: Annotated[str, Query(description="query containing a person's name")],
    pagination_params: PaginationParams = Depends(get_pagination_params),
    person_service: PersonService = Depends(get_person_service)
) -> List[PersonWithFilms]:
    """
    Search by name of person
    """
    persons = await person_service.search(query, pagination_params.limit, pagination_params.offset)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='persons not found')
    return [PersonWithFilms(id=p.id, name=p.name, films=p.films) for p in persons]


@router.get('/{person_id}/film', response_model=List[Film], response_model_by_alias=False)
async def person_films(
    person_id: Annotated[UUID, Path(description="person id")],
    person_service: PersonService = Depends(get_person_service)
) -> List[Film]:
    """
    Get list with all films with such person
    """
    films = await person_service.get_films(person_id)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')
    return [Film(id=f.id, title=f.title, imdb_rating=f.imdb_rating) for f in films]


@router.get('/{person_id}', response_model=PersonWithFilms, response_model_by_alias=False)
async def person_details(
    person_id: Annotated[UUID, Path(description="person id")],
    person_service: PersonService = Depends(get_person_service)
) -> PersonWithFilms:
    """
    Get person by id
    """
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')
    return PersonWithFilms(id=person.id, name=person.name, films=person.films)
