from typing import Annotated

from fastapi import APIRouter, Depends, status

from wapang.app.auth.utils import login_with_header
from wapang.app.stores.schemas import (
    StoreCreateRequest,
    StoreItemResponse,
    StoreResponse,
    StoreUpdateRequest,
)
from wapang.app.stores.services import StoreService
from wapang.app.users.models import User


store_router = APIRouter()


@store_router.post("", status_code=status.HTTP_201_CREATED)
def create_store(
    request: StoreCreateRequest,
    user: Annotated[User, Depends(login_with_header)],
    service: Annotated[StoreService, Depends()],
) -> StoreResponse:
    values = request.model_dump()
    values["name"] = values.pop("store_name")
    return StoreResponse.model_validate(service.create(user.id, values))


@store_router.patch("/{store_id}")
def update_store(
    store_id: str,
    request: StoreUpdateRequest,
    user: Annotated[User, Depends(login_with_header)],
    service: Annotated[StoreService, Depends()],
) -> StoreResponse:
    values = request.model_dump(exclude_unset=True)

    if "store_name" in values:
        values["name"] = values.pop("store_name")

    return StoreResponse.model_validate(
        service.update(user.id, store_id, values)
    )


@store_router.get("/{store_id}")
def get_store(
    store_id: str,
    service: Annotated[StoreService, Depends()],
) -> StoreResponse:
    return StoreResponse.model_validate(service.get(store_id))


@store_router.get("/{store_id}/items")
def list_store_items(
    store_id: str,
    service: Annotated[StoreService, Depends()],
) -> list[StoreItemResponse]:
    return [
        StoreItemResponse.model_validate(item)
        for item in service.list_items(store_id)
    ]