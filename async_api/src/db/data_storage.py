from abc import ABC, abstractmethod
from typing import Any, Dict, List
import logging
from enum import Enum

from elasticsearch import AsyncElasticsearch, ConnectionError

from backoff import backoff

logger = logging.getLogger(__name__)


class DataStorageEntity(str, Enum):
    PERSON = 'person'
    FILM = 'film'
    GENRE = 'genre'


class DataStorageError(Exception):
    pass


class AbstractDataStorage(ABC):
    @abstractmethod
    async def get(
        self,
        entity: DataStorageEntity,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = '',
        **query_params
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def search(
        self,
        entity: DataStorageEntity,
        query: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        pass


class ElasticDataStorage(AbstractDataStorage):
    _STORAGE_ENTITY_INDEX_MAP = {
        DataStorageEntity.PERSON: 'personas',
        DataStorageEntity.FILM: 'movies',
        DataStorageEntity.GENRE: 'genres',
    }

    def __init__(self, elastic: AsyncElasticsearch):
        self._elastic = elastic

    async def get(
        self,
        entity: DataStorageEntity,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = 'id',
        **query_params
    ) -> List[Dict[str, Any]]:
        logger.info('Getting %s with query params: %s', entity, query_params)
        query_body = {
            **self._get_elastic_pagination_fields(limit, offset),
        }
        if sort_by:
            if sort_by.startswith('-'):
                sort_by = sort_by[1:]
                sort_direction = 'desc'
            else:
                sort_direction = 'asc'
            query_body['sort'] = {sort_by: sort_direction}

        if query_params:
            # consider just one for now
            param, value = next(iter(query_params.items()))
            if value:
                query_body['query'] = {}
                if len(param.split('__')) == 2:
                    nested_path, nested_field = param.split('__')
                    query_body['query']['nested'] = {
                        'path': nested_path,
                        'query': {'match': {f'{nested_path}.{nested_field}': {'query': value}}},
                    }
                else:
                    query_body['query']['match'] = {param: {'query': value}}

        return await self._make_request(entity, query_body)

    async def search(
        self,
        entity: DataStorageEntity,
        query: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        logger.info('Searching %s by query: %s', entity, query)
        query_body = {
            'query': {'query_string': {'query': query}},
            **self._get_elastic_pagination_fields(limit, offset),
        }
        return await self._make_request(entity, query_body)

    async def _make_request(self, entity: DataStorageEntity, query_body: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info('Requesting %s with query body: %s', entity, query_body)
        index = self._get_index_by_entity(entity)
        try:
            response = await self._make_search_request(index, query_body)
        except ConnectionError as e:
            logger.error('Failed to request %s with query body: %s', entity, query_body)
            raise DataStorageError(e)
        return [f['_source'] for f in ((response.get('hits') or {}).get('hits') or [])]

    @backoff(exceptions=(ConnectionError,))
    async def _make_search_request(self, index: str, query_body: Dict[str, Any]) -> Dict[str, Any]:
        return await self._elastic.search(index=index, body=query_body)

    def _get_index_by_entity(self, entity: DataStorageEntity) -> str:
        return self._STORAGE_ENTITY_INDEX_MAP[entity]

    @staticmethod
    def _get_elastic_pagination_fields(limit: int, offset: int) -> Dict[str, int]:
        return {
            'from': offset,
            'size': limit,
        }
