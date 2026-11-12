from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from wapang.app.orders.exceptions import EmptyItemListException
from wapang.app.orders.models import OrderStatus
from wapang.common.exceptions import (
    InvalidFormatException,
    MissingRequiredFieldException,
    WapangException,
)


# ---------- 요청 ----------

class OrderItemRequest(BaseModel):
    item_id: str
    quantity: int

    @model_validator(mode="before")
    @classmethod
    def validate_item(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise InvalidFormatException()

        if "item_id" not in data or "quantity" not in data:
            raise MissingRequiredFieldException()

        item_id = data["item_id"]
        quantity = data["quantity"]

        if not isinstance(item_id, str) or not item_id.strip():
            raise InvalidFormatException()

        # bool과 소수, 문자열도 거절한다.
        if type(quantity) is not int or quantity < 1:
            raise InvalidFormatException()

        return data


class OrderCreateRequest(BaseModel):
    items: list[OrderItemRequest]

    @model_validator(mode="before")
    @classmethod
    def validate_items(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise InvalidFormatException()

        if "items" not in data:
            raise MissingRequiredFieldException()

        items = data["items"]

        if not isinstance(items, list):
            raise InvalidFormatException()

        if not items:
            raise EmptyItemListException()

        return data

    @model_validator(mode="after")
    def reject_duplicate_items(self) -> "OrderCreateRequest":
        item_ids = [item.item_id for item in self.items]

        if len(item_ids) != len(set(item_ids)):
            raise InvalidFormatException()

        return self


class OrderStatusUpdateRequest(BaseModel):
    status: Literal["CANCELED", "COMPLETE"]

    @model_validator(mode="before")
    @classmethod
    def validate_status(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise InvalidFormatException()

        if "status" not in data:
            raise MissingRequiredFieldException()

        if data["status"] not in ("CANCELED", "COMPLETE"):
            raise InvalidFormatException()

        return data


# ---------- 응답 ----------

class OrderItemResponse(BaseModel):
    item_id: str | None
    item_name: str
    price: int
    quantity: int
    subtotal: int


class OrderStoreResponse(BaseModel):
    store_id: str
    store_name: str
    delivery_fee: int
    store_total_price: int
    items: list[OrderItemResponse]


class OrderResponse(BaseModel):
    order_id: str
    details: list[OrderStoreResponse]
    total_price: int
    status: OrderStatus


class OrderSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: str
    total_price: int
    status: OrderStatus