from datetime import datetime, timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Header
import argon2
from authlib.jose import jwt, JWTClaims
from authlib.jose.errors import JoseError

from wapang.app.users.services import UserService
from wapang.app.auth.settings import AUTH_SETTINGS
from wapang.app.auth.exceptions import (
    BadAuthorizationHeaderException,
	UnauthenticatedException,
    InvalidAccountException,
    InvalidTokenException
)

def verify_password(plain_password: str, hashed_password: str) -> None:
	try:
		argon2.PasswordHasher().verify(hashed_password, plain_password)
	except argon2.exceptions.VerifyMismatchError:
		raise InvalidAccountException()
	
def issue_token(user_id: str, lifespan_minutes: int, secret: str) -> str:
	header = {'alg': 'HS256'}
	payload = {
		'sub': user_id,
		'jti': str(uuid4()),
		'exp': int((datetime.now() + timedelta(minutes=lifespan_minutes)).timestamp())
	}
	return str(jwt.encode(header, payload, key=secret), 'utf-8')

def verify_and_decode_token(token: str, secret: str) -> JWTClaims:
	try:
		claims = jwt.decode(token, key=secret)
		claims.validate()
		return claims
	except JoseError:
		raise InvalidTokenException()
	
def get_token_from_authorization_header(authorization: str) -> str:
	authorization_parts = authorization.split()
	if len(authorization_parts) != 2 \
			or authorization_parts[0].lower() != "bearer":
		raise BadAuthorizationHeaderException()
	token = authorization_parts[1]
	return token

def login_with_header(
        user_service: Annotated[UserService, Depends()],
        authorization: Annotated[str | None, Header()] = None
):
	if authorization is None:
		raise UnauthenticatedException()
	
	token = get_token_from_authorization_header(authorization)
	claims = verify_and_decode_token(token, AUTH_SETTINGS.ACCESS_TOKEN_SECRET)

	user_id = claims.get('sub', None)
	if user_id is None:
		raise InvalidTokenException()
	
	user = user_service.get_user_by_id(user_id)
	if user is None:
		raise InvalidAccountException()
	return user