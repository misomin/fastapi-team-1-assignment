from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from wapang.app.auth.utils import login_with_header
from wapang.app.orders.schemas import (
    OrderCreateRequest,
    OrderResponse,
    OrderStatusUpdateRequest,
)
from wapang.app.orders.services import OrderService
from wapang.app.users.models import User


order_router = APIRouter()


@order_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=OrderResponse,
)
def create_order(
    request: OrderCreateRequest,
    user: Annotated[User, Depends(login_with_header)],
    order_service: Annotated[OrderService, Depends()],
) -> OrderResponse:
    return order_service.create_order(
        user_id=user.id,
        request=request,
    )


@order_router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: str,
    user: Annotated[User, Depends(login_with_header)],
    order_service: Annotated[OrderService, Depends()],
) -> OrderResponse:
    return order_service.get_order(
        user_id=user.id,
        order_id=order_id,
    )


@order_router.patch(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def update_order_status(
    order_id: str,
    request: OrderStatusUpdateRequest,
    user: Annotated[User, Depends(login_with_header)],
    order_service: Annotated[OrderService, Depends()],
) -> Response:
    order_service.update_order_status(
        user_id=user.id,
        order_id=order_id,
        request=request,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)