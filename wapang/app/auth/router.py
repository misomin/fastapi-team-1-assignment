from typing import Annotated

from fastapi import APIRouter, Depends, Header
from fastapi import status

from wapang.app.auth.schemas import TokenResponse, UserSigninRequest
from wapang.app.auth.services import AuthService
from wapang.app.auth.settings import AUTH_SETTINGS

auth_router = APIRouter()

ACCESS_TOKEN_SECRET = AUTH_SETTINGS.ACCESS_TOKEN_SECRET
REFRESH_TOKEN_SECRET = AUTH_SETTINGS.REFRESH_TOKEN_SECRET
SHORT_SESSION_LIFESPAN = AUTH_SETTINGS.SHORT_SESSION_LIFESPAN
LONG_SESSION_LIFESPAN = AUTH_SETTINGS.LONG_SESSION_LIFESPAN

@auth_router.post("/tokens")
def signin(
    signin_request: UserSigninRequest, auth_service: Annotated[AuthService, Depends()]
) -> TokenResponse:
    access_token, refresh_token = auth_service.signin(
        signin_request.email, signin_request.password
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )

@auth_router.get("/tokens/refresh", response_model=TokenResponse)
def refresh_token(
    auth_service: Annotated[AuthService, Depends()],
    authorization: Annotated[str | None, Header()] = None,
) -> TokenResponse:
    access_token, refresh_token = auth_service.refresh_tokens(authorization)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@auth_router.delete("/tokens", status_code=status.HTTP_204_NO_CONTENT)
def delete_token(
    auth_service: Annotated[AuthService, Depends()],
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    auth_service.delete_token(authorization)
    return
