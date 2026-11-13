from typing import Annotated

from fastapi import Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from wapang.app.items.models import Item
from wapang.app.stores.models import Store
from wapang.database.connection import get_db_session


class StoreRepository:
    def __init__(self, session: Annotated[Session, Depends(get_db_session)]) -> None:
        self.session = session

    def get_by_id(self, store_id: str) -> Store | None:
        return self.session.get(Store, store_id)

    def get_by_user_id(self, user_id: str) -> Store | None:
        return self.session.scalar(
            select(Store).where(Store.user_id == user_id)
        )

    def get_conflicting_store(
        self, values: dict[str, object], exclude_id: str | None = None
    ) -> Store | None:
        conditions = [
            getattr(Store, field) == values[field]
            for field in ("name", "email", "phone_number")
            if field in values
        ]

        if not conditions:
            return None

        statement = select(Store).where(or_(*conditions))
        if exclude_id is not None:
            statement = statement.where(Store.id != exclude_id)

        return self.session.scalar(statement)

    def create(self, user_id: str, values: dict[str, object]) -> Store:
        store = Store(user_id=user_id, **values)
        self.session.add(store)
        self.session.flush()
        return store

    def update(self, store: Store, values: dict[str, object]) -> Store:
        for field, value in values.items():
            setattr(store, field, value)

        self.session.flush()
        return store

    def list_items(self, store_id: str) -> list[Item]:
        statement = select(Item).where(Item.store_id == store_id)
        return list(self.session.scalars(statement).all())