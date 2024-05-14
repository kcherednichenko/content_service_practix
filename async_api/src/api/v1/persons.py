from http import HTTPStatus
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from services.person import PersonService, get_person_service
from api.v1.schemas import Film, PersonWithFilms
from api.v1.dependencies import get_pagination_params, PaginationParams

router = APIRouter()


@router.get('/search', response_model=List[PersonWithFilms], response_model_by_alias=False)
async def person_search(query: str,
                        pagination_params: PaginationParams = Depends(get_pagination_params),
                        person_service: PersonService = Depends(get_person_service)) -> List[PersonWithFilms]:
    persons = await person_service.search(query, pagination_params.limit, pagination_params.offset)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='persons not found')
    return [PersonWithFilms(id=p.id, name=p.name, films=p.films) for p in persons]


@router.get('/{person_id}/film', response_model=List[Film], response_model_by_alias=False)
async def person_films(person_id: UUID, person_service: PersonService = Depends(get_person_service)) -> List[Film]:
    films = await person_service.get_films(person_id)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')
    return [Film(id=f.id, title=f.title, imdb_rating=f.imdb_rating) for f in films]


@router.get('/{person_id}', response_model=PersonWithFilms, response_model_by_alias=False)
async def person_details(
    person_id: UUID,
    person_service: PersonService = Depends(get_person_service)
) -> PersonWithFilms:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')
    return PersonWithFilms(id=person.id, name=person.name, films=person.films)
