from __future__ import annotations

from enum import Enum as PythonEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from wapang.database.common import Base

if TYPE_CHECKING:
    from wapang.app.items.models import Item
    from wapang.app.stores.models import Store
    from wapang.app.users.models import User


class OrderStatus(str, PythonEnum):
    CANCELED = "CANCELED"
    ORDERED = "ORDERED"
    COMPLETE = "COMPLETE"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid7())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            name="order_status",
            validate_strings=True,
            create_constraint=True,
        ),
        nullable=False,
        default=OrderStatus.ORDERED,
        server_default=OrderStatus.ORDERED.value,
    )
    total_price: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="상품 금액과 상점별 배송비의 합"
    )

    user: Mapped[User] = relationship(back_populates="orders")
    order_stores: Mapped[list[OrderStore]] = relationship(
        back_populates="order", passive_deletes="all"
    )


class OrderStore(Base):
    __tablename__ = "order_stores"
    __table_args__ = (
        UniqueConstraint("order_id", "store_id", name="uq_order_stores_order_store"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid7())
    )
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id"), nullable=False
    )
    store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stores.id"), nullable=False
    )
    store_name: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="주문 당시 상점명"
    )
    delivery_fee: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="주문 당시 배송비"
    )

    order: Mapped[Order] = relationship(back_populates="order_stores")
    store: Mapped[Store] = relationship(back_populates="order_stores")
    order_items: Mapped[list[OrderItem]] = relationship(
        back_populates="order_store", passive_deletes="all"
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint(
            "order_store_id", "item_id", name="uq_order_items_order_store_item"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid7())
    )
    order_store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("order_stores.id"), nullable=False
    )
    item_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("items.id", ondelete="SET NULL"),
        nullable=True,
        comment="상품 삭제 시 NULL",
    )
    item_name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="주문 당시 상품명"
    )
    price: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="주문 당시 상품 단가"
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="1 이상")

    order_store: Mapped[OrderStore] = relationship(back_populates="order_items")
    item: Mapped[Item | None] = relationship(back_populates="order_items")
