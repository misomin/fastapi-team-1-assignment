from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from wapang.database.common import Base

if TYPE_CHECKING:
    from wapang.app.orders.models import OrderItem
    from wapang.app.stores.models import Store


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("stock >= 0", name="ck_items_stock_non_negative"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid7())
    )
    store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stores.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="2글자 이상 50글자 이하"
    )
    price: Mapped[int] = mapped_column(Integer, nullable=False, comment="0 이상의 정수")
    stock: Mapped[int] = mapped_column(Integer, nullable=False, comment="0 이상의 정수")

    store: Mapped[Store] = relationship(back_populates="items")
    order_items: Mapped[list[OrderItem]] = relationship(
        back_populates="item", passive_deletes=True
    )
