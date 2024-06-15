from typing import Annotated, List
from uuid import UUID
from functools import lru_cache
import logging

from fastapi import Depends
from aiohttp import ClientSession, ClientError
from services.token import TokenService, get_token_service, TokenServiceError

from http_client import get_session
from core.config import settings
from models.user import User


logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, http_session: ClientSession, token_service: TokenService):
        self._http_session = http_session
        self._token_service = token_service

    async def is_subscriber(self, user: User) -> bool:
        logger.info('Checking if user %s is subscriber', user.id)
        user_roles = await self._get_actual_user_roles(user.id) or user.roles
        if len(set(user_roles) & {'subscriber', 'admin', 'superuser'}) == 0:
            return False
        return True

    async def _get_actual_user_roles(self, user_id: UUID) -> List[str]:
        logger.info('Getting actual user %s roles', user_id)
        try:
            service_token = await self._token_service.get_service_token()
        except TokenServiceError:
            return []

        try:
            async with self._http_session.get(
                f'http://{settings.auth_service_host}:{settings.auth_service_port}/api/v1/users/{user_id}/roles',
                headers={'Authorization': f'Bearer {service_token}'},
                raise_for_status=True
            ) as resp:
                return [r['name'] for r in await resp.json()]
        except ClientError as e:
            logger.error('Failed to get actual user roles: %s', e)
            return []


@lru_cache()
def get_user_service(
    http_session: Annotated[ClientSession, Depends(get_session)],
    token_service: Annotated[TokenService, Depends(get_token_service)]
) -> UserService:
    return UserService(http_session, token_service)
