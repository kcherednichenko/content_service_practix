import json
import logging
from functools import lru_cache
from typing import List
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.genre import Genre, Genres

GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 minutes
GENRE_ID_KEY_PREFIX = 'genre_id_'
ALL_GENRES_KEY = 'all_genres'
INDEX_NAME = 'genres'

logger = logging.getLogger(__name__)


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, genre_id: UUID) -> Genre | None:
        genre = await self._genre_from_cache(genre_id)
        if not genre:
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                return None
            await self._put_genre_to_cache(genre)

        return genre

    async def get_all_genres(self) -> List[Genre] | None:
        genres = await self._all_genres_from_cache()
        if not genres:
            genres = await self._get_all_genres_from_elastic()
            if not genres:
                return None
            await self._put_all_genres_to_cache(Genres(genres=genres))

        return genres

    async def _get_genre_from_elastic(self, genre_id: UUID) -> Genre | None:
        try:
            logger.info('Getting genre from db by id %s', genre_id)
            doc = await self.elastic.get(index=INDEX_NAME, id=str(genre_id))
        except NotFoundError:
            return None
        except Exception as e:
            logger.exception(e)
            raise
        return Genre(**doc['_source'])

    async def _get_all_genres_from_elastic(self):
        query = {'query': {'match_all': {}}}
        try:
            logger.info('Getting all genres from db')
            docs = await self.elastic.search(index=INDEX_NAME, body=query)
        except NotFoundError:
            return None
        except Exception as e:
            logger.exception(e)
            raise
        all_genres = []
        for doc in docs['hits']['hits']:
            all_genres.append(Genre(**doc['_source']))
        return all_genres

    async def _genre_from_cache(self, genre_id: UUID) -> Genre | None:
        data = await self.redis.get(f'{GENRE_ID_KEY_PREFIX}{genre_id}')
        if not data:
            return None

        logger.info('Got genre from cache by id %s', genre_id)
        genre = Genre.parse_raw(data)
        return genre

    async def _put_genre_to_cache(self, genre: Genre):
        logger.info('Putting genre to cache. genre_id = %s', genre.id)
        await self.redis.set(f'{GENRE_ID_KEY_PREFIX}{genre.id}', genre.json(), GENRE_CACHE_EXPIRE_IN_SECONDS)

    async def _all_genres_from_cache(self) -> List[Genre] | None:
        data = await self.redis.get(ALL_GENRES_KEY)
        if not data:
            return None

        logger.info('Got all genres from cache')
        genres = Genres.parse_raw(data)
        return genres.genres

    async def _put_all_genres_to_cache(self, genres: Genres):
        logger.info('Putting all genres to cache')
        await self.redis.set(ALL_GENRES_KEY, json.dumps(genres.__dict__, default=lambda o: o.__dict__),
                             GENRE_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
