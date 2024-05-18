from functools import lru_cache
from typing import Any, Dict, List
from uuid import UUID
import logging
import orjson

from elasticsearch import AsyncElasticsearch, NotFoundError, ConnectionError
from fastapi import Depends
from redis.asyncio import Redis
from redis import RedisError

from db.elastic import get_elastic
from db.redis import get_redis
from db.cache_storage import RedisCacheStorage
from models.film import Film

_FILM_INDEX = 'movies'
_CACHE_PREFIX = 'films'

logger = logging.getLogger(__name__)


class FilmServiceError(Exception):
    pass


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = RedisCacheStorage(redis)
        self.elastic = elastic

    async def get_films(self, genre_id: UUID | None, limit: int = 50, offset: int = 0) -> List[Film]:
        logger.info('Getting films, genre %s, limit %s offset %s', genre_id, limit, offset)
        films = await self._get_films_from_cache(genre_id, limit, offset)
        if films is None:
            films = await self._get_films_from_elastic(genre_id, limit, offset)
            if films:
                await self._put_films_to_cache(films, genre_id, limit, offset)
        return films

    async def get_films_by_query(self, query: str, limit: int = 50, offset: int = 0) -> List[Film]:
        logger.info('Getting films by query %s, limit %s offset %s', query, limit, offset)
        return await self._get_films_by_query_from_elastic(query, limit, offset)

    async def get_film_by_id(self, film_id: UUID) -> Film | None:
        logger.info('Getting film by id %s', film_id)
        film = await self._get_film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)
        return film

    async def _get_films_from_elastic(self, genre_id: UUID | None, limit: int, offset: int) -> List[Film]:
        query_body = {
            'sort': {'imdb_rating': 'desc'},
            **self._get_elastic_pagination_fields(limit, offset),
        }
        if genre_id:
            query_body.update({
                'query': {
                    'nested': {
                        'path': 'genres',
                        'query': {'match': {'genres.id': {'query': genre_id}}}
                    }
                }})
        return await self._request_films_from_elastic(query_body)

    async def _get_films_from_cache(self, genre_id: UUID | None, limit: int, offset: int) -> List[Film] | None:
        logger.info('Checking cache to get films by params, genre %s, limit %s, offset %s', genre_id, limit, offset)
        try:
            data = await self.redis.get(self._films_cache_key(genre_id, limit, offset))
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
            await self.redis.set(key, data)
        except RedisError as e:
            logger.error('Failed to put films got by params genre %s, limit %s, offset %s to cache: %s',
                         genre_id, limit, offset, e)

    async def _get_films_by_query_from_elastic(self, query: str, limit: int, offset: int) -> List[Film]:
        query_body = {
            'query': {'query_string': {'query': query}},
            **self._get_elastic_pagination_fields(limit, offset),
        }
        return await self._request_films_from_elastic(query_body)

    async def _request_films_from_elastic(self, query_body: Dict[str, Any]) -> List[Film]:
        logger.info('Searching films from elastic by query: %s', query_body)
        try:
            response = await self.elastic.search(index=_FILM_INDEX, body=query_body)
        except ConnectionError:
            logger.error('Failed to search films from elastic by query: %s', query_body)
            raise FilmServiceError
        films = (response.get('hits') or {}).get('hits') or []
        return [Film(**f['_source']) for f in films]

    async def _get_film_from_elastic(self, film_id: UUID) -> Film | None:
        logger.info('Getting film by id %s from elastic', film_id)
        try:
            doc = await self.elastic.get(index=_FILM_INDEX, id=film_id)
        except NotFoundError:
            return None
        except ConnectionError as e:
            logger.error('Failed to get film by id %s from elastic: %s', film_id, e)
            raise FilmServiceError
        return Film(**doc['_source'])

    async def _get_film_from_cache(self, film_id: UUID) -> Film | None:
        logger.info('Checking cache to get film by id %s', film_id)
        try:
            data = await self.redis.get(self._film_cache_key(film_id))
        except RedisError as e:
            logger.error('Failed to check cache to get film by id %s: %s', film_id, e)
            return None

        if not data:
            return None
        return Film.parse_raw(data)

    async def _put_film_to_cache(self, film: Film) -> None:
        logger.info('Putting film with id %s to cache', film.id)
        try:
            await self.redis.set(self._film_cache_key(film.id), film.json())
        except RedisError as e:
            logger.error('Failed to put film with id %s to cache: %s', film.id, e)

    @staticmethod
    def _get_elastic_pagination_fields(limit: int, offset: int) -> Dict[str, int]:
        return {
            'from': offset,
            'size': limit,
        }

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
    return FilmService(redis, elastic)
