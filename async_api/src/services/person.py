import logging
from functools import lru_cache
from typing import List, Dict
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from db.cache_storage import RedisCacheStorage, CacheStorage
from models.person import Person
from models.film import Film
from services.film import FilmService

PERSON_ID_KEY_PREFIX = 'person_id_'
INDEX_NAME = 'personas'

logger = logging.getLogger(__name__)


class PersonService:
    def __init__(self, cache_storage: CacheStorage, elastic: AsyncElasticsearch):
        self.cache_storage = cache_storage
        self.elastic = elastic

    async def search(self, query: str, limit: int, offset: int) -> List[Person] | None:
        return await self._search_persons_in_elastic(query, limit, offset)

    async def get_by_id(self, person_id: UUID) -> Person | None:
        person = await self._person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)

        return person

    async def get_films(self, person_id: UUID) -> List[Film] | None:
        person = await self._person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)

        films = []
        film_service = FilmService(redis=self.cache_storage, elastic=self.elastic)
        for film in person.films:
            cur_film = await film_service.get_film_by_id(film['id'])
            films.append(cur_film)
        return films

    async def _get_person_from_elastic(self, person_id: UUID) -> Person | None:
        try:
            logger.info('Getting person from db by id %s', person_id)
            doc = await self.elastic.get(index=INDEX_NAME, id=str(person_id))
        except NotFoundError:
            return None
        except Exception as e:
            logger.exception(e)
            raise
        return Person(**doc['_source'])

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

    async def _search_persons_in_elastic(self, query: str, limit: int, offset: int) -> List[Person] | None:
        query = {
            'query': {'query_string': {'query': query}},
            **self._get_elastic_pagination_fields(limit, offset),
        }

        try:
            logging.info('Searching persons by query = %s', query)
            docs = await self.elastic.search(index=INDEX_NAME, body=query)
        except NotFoundError:
            return None
        except Exception as e:
            logger.exception(e)
            raise
        all_persons = []
        for doc in docs['hits']['hits']:
            all_persons.append(Person(**doc['_source']))
        return all_persons

    @staticmethod
    def _get_elastic_pagination_fields(limit: int, offset: int) -> Dict[str, int]:
        return {
            'from': offset,
            'size': limit,
        }


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(RedisCacheStorage(redis), elastic)
