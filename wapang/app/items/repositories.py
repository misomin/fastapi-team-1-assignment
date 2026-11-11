from typing import Annotated
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from wapang.app.items.models import Item
from wapang.app.stores.models import Store
from wapang.database.connection import get_db_session

class ItemRepository:
    def __init__(
        self,
        session: Annotated[Session, Depends(get_db_session)],
    ) -> None:
        self.session = session

    def get_store_by_user_id(self, user_id: str) -> Store | None:
        return self.session.scalar(
            select(Store).where(Store.user_id == user_id)
        )

    def get_store_by_id(self, store_id: str) -> Store | None:
        return self.session.get(Store, store_id)

    def create_item(
        self, store_id: str, name: str, price: int, stock: int
    ) -> Item:
        item = Item(
            store_id=store_id,
            name=name,
            price=price,
            stock=stock,
        )
        self.session.add(item)
        self.session.flush()
        return item

    def get_item_by_id(self, item_id: str) -> Item | None:
        return self.session.get(Item, item_id)

    def list_items(
        self,
        store_id: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        in_stock: bool = False,
    ) -> list[Item]:
        statement = select(Item).options(joinedload(Item.store))

        if store_id is not None:
            statement = statement.where(Item.store_id == store_id)
        if min_price is not None:
            statement = statement.where(Item.price >= min_price)
        if max_price is not None:
            statement = statement.where(Item.price <= max_price)
        if in_stock:
            statement = statement.where(Item.stock > 0)

        return list(self.session.scalars(statement).all())

    def update_item(self, item: Item, changes: dict) -> Item:
        for field_name, value in changes.items():
            setattr(item, field_name, value)

        self.session.flush()
        return item

    def delete_item(self, item: Item) -> None:
        self.session.delete(item)
        self.session.flush()