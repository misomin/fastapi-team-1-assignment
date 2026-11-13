from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from wapang.app.auth.utils import login_with_header
from wapang.app.items.schemas import (
    ItemCreateRequest,
    ItemListResponse,
    ItemResponse,
    ItemUpdateRequest,
)
from wapang.app.items.services import ItemService
from wapang.app.users.models import User

item_router = APIRouter()

@item_router.post("/", status_code=status.HTTP_201_CREATED)
def create_item(
    request: ItemCreateRequest,
    user: Annotated[User, Depends(login_with_header)],
    service: Annotated[ItemService, Depends()],
) -> ItemResponse:
    item = service.create_item(
        user.id, request.item_name, request.price, request.stock
    )
    return ItemResponse.model_validate(item)

@item_router.patch("/{item_id}")
def update_item(
    item_id: str,
    request: ItemUpdateRequest,
    user: Annotated[User, Depends(login_with_header)],
    service: Annotated[ItemService, Depends()],
) -> ItemResponse:
    changes = request.model_dump(exclude_unset=True)
    item = service.update_item(user.id, item_id, changes)
    return ItemResponse.model_validate(item)

@item_router.get("/")
def list_items(
    service: Annotated[ItemService, Depends()],
    store_id: str | None = None,
    min_price: Annotated[int | None, Query(ge=0)] = None,
    max_price: Annotated[int | None, Query(ge=0)] = None,
    in_stock: bool = False,
) -> list[ItemListResponse]:
    items = service.list_items(store_id, min_price, max_price, in_stock)
    return [
        ItemListResponse(
            id=item.id,
            item_name=item.name,
            price=item.price,
            stock=item.stock,
            store_id=item.store_id,
            store_name=item.store.name,
        )
        for item in items
    ]

@item_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: str,
    user: Annotated[User, Depends(login_with_header)],
    service: Annotated[ItemService, Depends()],
) -> None:
    service.delete_item(user.id, item_id)