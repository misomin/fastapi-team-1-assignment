from typing import Annotated

from fastapi import Depends
from sqlalchemy.exc import IntegrityError

from wapang.app.items.models import Item
from wapang.app.stores.exceptions import (
    NoStoreOwnedException,
    NotYourStoreException,
    StoreAlreadyExistsException,
    StoreInfoConflictException,
    StoreNotFoundException,
)
from wapang.app.stores.models import Store
from wapang.app.stores.repositories import StoreRepository
from wapang.common.exceptions import MissingRequiredFieldException


class StoreService:
    def __init__(self, repository: Annotated[StoreRepository, Depends()]) -> None:
        self.repository = repository

    def create(self, user_id: str, values: dict[str, object]) -> Store:
        if self.repository.get_by_user_id(user_id) is not None:
            raise StoreAlreadyExistsException()

        if self.repository.get_conflicting_store(values) is not None:
            raise StoreInfoConflictException()

        try:
            return self.repository.create(user_id, values)
        except IntegrityError as error:
            self.repository.session.rollback()

            if self.repository.get_by_user_id(user_id) is not None:
                raise StoreAlreadyExistsException() from error

            raise StoreInfoConflictException() from error

    def update(
        self, user_id: str, store_id: str, values: dict[str, object]
    ) -> Store:
        if self.repository.get_by_user_id(user_id) is None:
            raise NoStoreOwnedException()

        store = self.repository.get_by_id(store_id)
        if store is None:
            raise StoreNotFoundException()

        if store.user_id != user_id:
            raise NotYourStoreException()

        if not values:
            raise MissingRequiredFieldException()

        if self.repository.get_conflicting_store(values, exclude_id=store_id) is not None:
            raise StoreInfoConflictException()

        try:
            return self.repository.update(store, values)
        except IntegrityError as error:
            self.repository.session.rollback()
            raise StoreInfoConflictException() from error

    def get(self, store_id: str) -> Store:
        store = self.repository.get_by_id(store_id)
        if store is None:
            raise StoreNotFoundException()
        return store

    def list_items(self, store_id: str) -> list[Item]:
        self.get(store_id)
        return self.repository.list_items(store_id)