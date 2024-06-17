from typing import Annotated
from http import HTTPStatus

from fastapi import Query, HTTPException, Request, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from services.token import TokenService, get_token_service
from models.user import User


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> str:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials:
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail='Invalid authorization code')
        if credentials.scheme != 'Bearer':
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail='Only Bearer token might be accepted')
        return credentials.credentials


security_jwt = JWTBearer()


class PaginationParams(BaseModel):
    limit: int
    offset: int


def get_pagination_params(
    page_number: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1)
) -> PaginationParams:
    limit, offset = page_size, (page_number - 1) * page_size
    return PaginationParams(limit=limit, offset=offset)


def get_authenticated_user(
    token: Annotated[str, Depends(security_jwt)],
    token_service: Annotated[TokenService, Depends(get_token_service)]
) -> User:
    user = token_service.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail='Invalid token')
    return user
