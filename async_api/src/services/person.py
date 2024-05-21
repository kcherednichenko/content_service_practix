import logging
from functools import lru_cache
from typing import List
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.data_storage import DataStorage
from db.redis import get_redis
from db.cache_storage import RedisCacheStorage, AbstractCacheStorage
from models.person import Person
from models.film import Film
from services.film import get_film_service, FilmService

PERSON_ID_KEY_PREFIX = 'person_id_'

logger = logging.getLogger(__name__)


class PersonService:
    def __init__(
        self, cache_storage: AbstractCacheStorage, person_data_storage: DataStorage, film_service: FilmService
    ) -> None:
        self.cache_storage = cache_storage
        self.person_data_storage = person_data_storage
        self.film_service = film_service

    async def search(self, query: str, limit: int, offset: int) -> List[Person] | None:
        return await self._search_persons_in_storage(query, limit, offset)

    async def get_by_id(self, person_id: UUID) -> Person | None:
        person = await self._person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_storage(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)

        return person

    async def get_films(self, person_id: UUID) -> List[Film] | None:
        person = await self._person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_storage(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)

        films = []
        for film in person.films:
            cur_film = await self.film_service.get_film_by_id(film['id'])
            films.append(cur_film)
        return films

    async def _get_person_from_storage(self, person_id: UUID) -> Person | None:
        try:
            logger.info('Getting person from db by id %s', person_id)
            person = await self.person_data_storage.get(id=person_id)
        except Exception as e:
            logger.exception(e)
            raise
        return Person(**person) if person else None

    async def _person_from_cache(self, person_id: UUID) -> Person | None:
        data = await self.cache_storage.get(f'{PERSON_ID_KEY_PREFIX}{person_id}')
        if not data:
            return None

        logger.info('Got person from cache by id %s', person_id)
        person = Person.parse_raw(data)
        return person

    async def _put_person_to_cache(self, person: Person):
        logger.info('Putting person to cache. person = %s', person.id)
        await self.cache_storage.set(f'{PERSON_ID_KEY_PREFIX}{person.id}', person.json())

    async def _search_persons_in_storage(self, query: str, limit: int, offset: int) -> List[Person]:
        try:
            logging.info('Searching persons by query = %s', query)
            persons = await self.person_data_storage.search(query, limit, offset)
        except Exception as e:
            logger.exception(e)
            raise
        return [Person(**p) for p in persons]


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
        film_service: FilmService = Depends(get_film_service),
) -> PersonService:
    return PersonService(RedisCacheStorage(redis), DataStorage(elastic, 'personas'), film_service)
