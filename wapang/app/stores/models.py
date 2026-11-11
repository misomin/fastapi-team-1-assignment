from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from wapang.database.common import Base

if TYPE_CHECKING:
    from wapang.app.items.models import Item
    from wapang.app.orders.models import OrderStore
    from wapang.app.users.models import User


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid7())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, unique=True
    )
    name: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, comment="3~20글자"
    )
    address: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(
        String(13), nullable=False, unique=True, comment="010-xxxx-xxxx 형식"
    )
    delivery_fee: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="0 이상의 정수"
    )

    user: Mapped[User] = relationship(back_populates="store")
    items: Mapped[list[Item]] = relationship(
        back_populates="store", passive_deletes="all"
    )
    order_stores: Mapped[list[OrderStore]] = relationship(
        back_populates="store", passive_deletes="all"
    )
