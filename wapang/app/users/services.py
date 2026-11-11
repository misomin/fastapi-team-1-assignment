from typing import Annotated
from argon2 import PasswordHasher

from fastapi import Depends
from wapang.app.users.models import User
from wapang.app.users.repositories import UserRepository
from wapang.app.users.exceptions import EmailAlreadyExistsException

class UserService:
    def __init__(self, user_repository: Annotated[UserRepository, Depends()]) -> None:
        self.user_repository = user_repository

    def create_user(self, email: str, password: str) -> User:        
        if self.user_repository.get_user_by_email(email):
            raise EmailAlreadyExistsException()

        hashed_password = PasswordHasher().hash(password)

        return self.user_repository.create_user(email, hashed_password)

    def get_user_by_id(self, user_id: str) -> User | None:
        return self.user_repository.get_user_by_id(user_id)