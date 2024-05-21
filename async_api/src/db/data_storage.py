from typing import Any, Dict, List
import logging
from uuid import UUID

from pydantic import BaseModel
from elasticsearch import AsyncElasticsearch, ConnectionError

from backoff import backoff

logger = logging.getLogger(__name__)


class DataStorageError(Exception):
    pass


class Filters(BaseModel):
    pass


class FilmFilters(Filters):
    genre_id: UUID | None


class DataStorage:
    def __init__(self, elastic: AsyncElasticsearch, index: str):
        self._elastic = elastic
        self._index = index

    async def get(self, id: UUID) -> Dict[str, Any] | None:
        logger.info('Getting %s by id %s', self._index, id)
        query_body = {'query': {'match': {'id': {'query': id}}}}
        films = await self._make_request(query_body)
        return films[0] if films else None

    async def list(
        self, limit: int = 50, offset: int = 0, sort_by: str = 'id', filters: Filters | None = None
    ) -> List[Dict[str, Any]]:
        query_body = {
            **self._get_sort_field(sort_by),
            **self._get_elastic_pagination_fields(limit, offset),
            **self._apply_filters(filters),
        }
        return await self._make_request(query_body)

    async def search(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        logger.info('Searching in %s by query: %s', self._index, query)
        query_body = {
            'query': {'query_string': {'query': query}},
            **self._get_elastic_pagination_fields(limit, offset),
        }
        return await self._make_request(query_body)

    async def _make_request(self, query_body: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info('Requesting %s with query body: %s', self._index, query_body)
        try:
            response = await self._make_search_request(query_body)
        except ConnectionError as e:
            logger.error('Failed to request %s with query body: %s', self._index, query_body)
            raise DataStorageError(e)
        return [f['_source'] for f in ((response.get('hits') or {}).get('hits') or [])]

    @backoff(exceptions=(ConnectionError,))
    async def _make_search_request(self, query_body: Dict[str, Any]) -> Dict[str, Any]:
        return await self._elastic.search(index=self._index, body=query_body)

    @staticmethod
    def _get_elastic_pagination_fields(limit: int, offset: int) -> Dict[str, int]:
        return {
            'from': offset,
            'size': limit,
        }

    @staticmethod
    def _get_sort_field(sort_by: str) -> Dict[str, Any]:
        if sort_by.startswith('-'):
            sort_by = sort_by[1:]
            sort_direction = 'desc'
        else:
            sort_direction = 'asc'
        return {
            'sort': {sort_by: sort_direction},
        }

    @staticmethod
    def _apply_filters(filters: Filters | None) -> Dict[str, Any]:
        return {}


class FilmDataStorage(DataStorage):
    @staticmethod
    def _apply_filters(filters: FilmFilters | None) -> Dict[str, Any]:
        if not filters:
            return {}
        if filters.genre_id:
            return {
                'query': {
                    'nested': {
                        'path': 'genres',
                        'query': {'match': {'genres.id': {'query': filters.genre_id}}}}}}
        return {}
