from functools import lru_cache
from typing import List
from uuid import UUID
import logging
import orjson

from fastapi import Depends
from redis.asyncio import Redis
from redis import RedisError

from elasticsearch import AsyncElasticsearch
from db.elastic import get_elastic
from db.data_storage import AbstractDataStorage, ElasticDataStorage, DataStorageError, DataStorageEntity
from db.redis import get_redis
from db.cache_storage import RedisCacheStorage, AbstractCacheStorage
from models.film import Film

_FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 minutes
_CACHE_PREFIX = 'films'

logger = logging.getLogger(__name__)


class FilmServiceError(Exception):
    pass


class FilmService:
    def __init__(self, cache_storage: AbstractCacheStorage, data_storage: AbstractDataStorage):
        self.cache_storage = cache_storage
        self.data_storage = data_storage

    async def get_films(self, genre_id: UUID | None, limit: int = 50, offset: int = 0) -> List[Film]:
        logger.info('Getting films, genre %s, limit %s offset %s', genre_id, limit, offset)
        films = await self._get_films_from_cache(genre_id, limit, offset)
        if films is None:
            films = await self._get_films_from_storage(genre_id, limit, offset)
            if films:
                await self._put_films_to_cache(films, genre_id, limit, offset)
        return films

    async def get_films_by_query(self, query: str, limit: int = 50, offset: int = 0) -> List[Film]:
        logger.info('Getting films by query %s, limit %s offset %s', query, limit, offset)
        return await self._get_films_by_query_from_storage(query, limit, offset)

    async def get_film_by_id(self, film_id: UUID) -> Film | None:
        logger.info('Getting film by id %s', film_id)
        film = await self._get_film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_storage(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)
        return film

    async def _get_films_from_storage(self, genre_id: UUID | None, limit: int, offset: int) -> List[Film]:
        logger.info('Getting films from storage, genre %s, limit %s, offset %s', genre_id, limit, offset)
        try:
            films = await self.data_storage.get(
                DataStorageEntity.FILM, genres__id=genre_id, limit=limit, offset=offset, sort_by='-imdb_rating')
        except DataStorageError as e:
            logger.error('Failed to get films from storage, genre %s, limit %s, offset %s: %s',
                         genre_id, limit, offset, e)
            raise FilmServiceError
        return [Film(**f) for f in films]

    async def _get_films_from_cache(self, genre_id: UUID | None, limit: int, offset: int) -> List[Film] | None:
        logger.info('Checking cache to get films by params, genre %s, limit %s, offset %s', genre_id, limit, offset)
        try:
            data = await self.cache_storage.get(self._films_cache_key(genre_id, limit, offset))
        except RedisError as e:
            logger.error('Failed to check cache to get films by params, genre %s, limit %s, offset %s: %s',
                         genre_id, limit, offset, e)
            return None
        if not data:
            return None
        return [Film.parse_obj(f) for f in orjson.loads(data)]

    async def _put_films_to_cache(self, films: List[Film], genre_id: UUID | None, limit: int, offset: int) -> None:
        logger.info('Putting films got by params genre %s, limit %s, offset %s to cache', genre_id, limit, offset)
        key = self._films_cache_key(genre_id, limit, offset)
        data = orjson.dumps([f.dict() for f in films])
        try:
            await self.cache_storage.set(key, data)
        except RedisError as e:
            logger.error('Failed to put films got by params genre %s, limit %s, offset %s to cache: %s',
                         genre_id, limit, offset, e)

    async def _get_films_by_query_from_storage(self, query: str, limit: int, offset: int) -> List[Film]:
        logger.info('Getting films from storage by query %s, limit %s, offset %s', query, limit, offset)
        try:
            films = await self.data_storage.search(DataStorageEntity.FILM, query, limit=limit, offset=offset)
        except DataStorageError as e:
            logger.error('Failed to get films from storage by query %s, limit %s, offset %s: %s',
                         query, limit, offset, e)
            raise FilmServiceError
        return [Film(**f) for f in films]

    async def _get_film_from_storage(self, film_id: UUID) -> Film | None:
        logger.info('Getting film from storage by id %s', film_id)
        try:
            films = await self.data_storage.get(DataStorageEntity.FILM, id=film_id)
        except DataStorageError as e:
            logger.error('Failed to get film from storage by id %s: %s', film_id, e)
            return None
        return Film(**films[0]) if films else None

    async def _get_film_from_cache(self, film_id: UUID) -> Film | None:
        logger.info('Checking cache to get film by id %s', film_id)
        try:
            data = await self.cache_storage.get(self._film_cache_key(film_id))
        except RedisError as e:
            logger.error('Failed to check cache to get film by id %s: %s', film_id, e)
            return None

        if not data:
            return None
        return Film.parse_raw(data)

    async def _put_film_to_cache(self, film: Film) -> None:
        logger.info('Putting film with id %s to cache', film.id)
        try:
            await self.cache_storage.set(self._film_cache_key(film.id), film.json())
        except RedisError as e:
            logger.error('Failed to put film with id %s to cache: %s', film.id, e)

    @staticmethod
    def _film_cache_key(film_id: UUID) -> str:
        return f'{_CACHE_PREFIX}:{film_id}'

    @staticmethod
    def _films_cache_key(genre_id: UUID | None, limit: int, offset: int) -> str:
        return f'{_CACHE_PREFIX}:{genre_id or ""}_{limit}_{offset}'


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(RedisCacheStorage(redis), ElasticDataStorage(elastic))
