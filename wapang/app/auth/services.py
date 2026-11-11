from typing import Annotated
from datetime import datetime

from fastapi import Depends

from wapang.app.auth.utils import (
    verify_password,
    issue_token,
    get_token_from_authorization_header,
    verify_and_decode_token
)
from wapang.app.auth.exceptions import (
    InvalidAccountException,
    UnauthenticatedException,
    InvalidTokenException
)
from wapang.app.auth.repositories import AuthRepository
from wapang.app.auth.settings import AUTH_SETTINGS
from wapang.app.users.repositories import UserRepository

ACCESS_TOKEN_SECRET = AUTH_SETTINGS.ACCESS_TOKEN_SECRET
REFRESH_TOKEN_SECRET = AUTH_SETTINGS.REFRESH_TOKEN_SECRET
SHORT_SESSION_LIFESPAN = AUTH_SETTINGS.SHORT_SESSION_LIFESPAN
LONG_SESSION_LIFESPAN = AUTH_SETTINGS.LONG_SESSION_LIFESPAN

class AuthService:
    def __init__(self, 
                 auth_repository: Annotated[AuthRepository, Depends()],
                 user_repository: Annotated[UserRepository, Depends()]) -> None:
        self.auth_repository = auth_repository
        self.user_repository = user_repository

    def signin(self, email: str, password: str) -> tuple[str, str]:
        user = self.user_repository.get_user_by_email(email)
        if user is None:
            raise InvalidAccountException()

        verify_password(password, user.hashed_password)

        access_token = issue_token(user.id, SHORT_SESSION_LIFESPAN, ACCESS_TOKEN_SECRET)
        refresh_token = issue_token(user.id, LONG_SESSION_LIFESPAN, REFRESH_TOKEN_SECRET)

        return access_token, refresh_token
    
    def block_refresh_token(self, token: str, exp: datetime) -> None:
        self.auth_repository.block_refresh_token(token, exp)
    
    def refresh_tokens(self, authorization: str | None) -> tuple[str, str]:
        if authorization is None:
            raise UnauthenticatedException()
        token = get_token_from_authorization_header(authorization)
        claims = verify_and_decode_token(token, REFRESH_TOKEN_SECRET)
        
        exp = claims.get("exp", None)
        if exp is None:
            raise InvalidTokenException()
        exp_datetime = datetime.fromtimestamp(exp)

        user_id = claims.get("sub", None)
        if user_id is None:
            raise InvalidTokenException()

        self.block_refresh_token(token, exp_datetime)
        access_token = issue_token(user_id, SHORT_SESSION_LIFESPAN, ACCESS_TOKEN_SECRET)
        refresh_token = issue_token(user_id, LONG_SESSION_LIFESPAN, REFRESH_TOKEN_SECRET)
        return access_token, refresh_token
    
    def delete_token(self, authorization: str | None) -> None:
        if authorization is None:
            raise UnauthenticatedException()
        token = get_token_from_authorization_header(authorization)
        claims = verify_and_decode_token(token, REFRESH_TOKEN_SECRET)

        exp = claims.get("exp", None)
        if exp is None:
            raise InvalidTokenException()
        exp_datetime = datetime.fromtimestamp(exp)
        self.block_refresh_token(token, exp_datetime)