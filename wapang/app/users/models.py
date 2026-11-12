from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from wapang.database.common import Base

if TYPE_CHECKING:
    from wapang.app.orders.models import Order
    from wapang.app.stores.models import Store


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid7()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Argon2로 해싱된 비밀번호"
    )
    nickname: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(
        String(13), nullable=True, comment="010-xxxx-xxxx 형식"
    )

    store: Mapped[Store | None] = relationship(
        back_populates="user", uselist=False, passive_deletes="all"
    )
    orders: Mapped[list[Order]] = relationship(
        back_populates="user", passive_deletes="all"
    )
