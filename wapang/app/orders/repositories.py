from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from wapang.app.items.models import Item
from wapang.app.orders.models import Order, OrderStore
from wapang.app.stores.models import Store
from wapang.database.connection import get_db_session


class OrderRepository:
    def __init__(
        self,
        session: Annotated[Session, Depends(get_db_session)],
    ) -> None:
        self.session = session

    def get_items_for_update(
        self,
        item_ids: list[str],
    ) -> list[Item]:
        """주문할 상품들을 재고 변경을 위한 잠금과 함께 조회한다."""
        if not item_ids:
            return []

        statement = (
            select(Item)
            .where(Item.id.in_(item_ids))
            .order_by(Item.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        return list(self.session.scalars(statement).all())

    def get_stores_by_ids(
        self,
        store_ids: list[str],
    ) -> list[Store]:
        """주문에 포함된 상점들의 이름과 배송비를 조회한다."""
        if not store_ids:
            return []

        statement = (
            select(Store)
            .where(Store.id.in_(store_ids))
            .order_by(Store.id)
        )

        return list(self.session.scalars(statement).all())

    def get_order_by_id(
        self,
        order_id: str,
    ) -> Order | None:
        """주문과 상점별·상품별 주문 내역을 함께 조회한다."""
        statement = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.order_stores).selectinload(
                    OrderStore.order_items
                )
            )
        )

        return self.session.scalar(statement)

    def get_order_for_update(
        self,
        order_id: str,
    ) -> Order | None:
        """상태를 변경할 주문을 잠금과 함께 조회한다."""
        statement = (
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        return self.session.scalar(statement)

    def decrease_stock(
        self,
        item: Item,
        quantity: int,
    ) -> None:
        """서비스에서 재고 검사를 마친 상품의 수량을 차감한다."""
        item.stock -= quantity

    def save_order(self, order: Order) -> Order:
        """주문과 연결된 내역, 같은 세션의 재고 변경을 DB에 반영한다."""
        self.session.add(order)
        self.session.flush()

        return order