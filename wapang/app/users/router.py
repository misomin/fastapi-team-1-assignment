from typing import Annotated
from fastapi import APIRouter, Depends, status

from wapang.app.auth.utils import login_with_header
from wapang.app.users.models import User
from wapang.app.users.schemas import UserSignupRequest, UserResponse, UserUpdateRequest, UserOrderResponse
from wapang.app.users.services import UserService
from wapang.common.exceptions import MissingRequiredFieldException

user_router = APIRouter()


@user_router.post("/", status_code=status.HTTP_201_CREATED)
def signup(
    signup_request: UserSignupRequest, user_service: Annotated[UserService, Depends()]
) -> UserResponse:
    user = user_service.create_user(
        signup_request.email, signup_request.password,
    )
    return UserResponse(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        address=user.address,
        phone_number=user.phone_number,
    )

@user_router.get("/me")
def get_me(
    user: Annotated[User, Depends(login_with_header)],
    ) -> UserResponse:
    return UserResponse.model_validate(user)

@user_router.patch("/me")
def update_me(
    update_request: UserUpdateRequest,
    user: Annotated[User, Depends(login_with_header)],
    user_service: Annotated[UserService, Depends()],
) -> UserResponse:
    updates = update_request.model_dump(exclude_unset=True)

    if not updates:
        raise MissingRequiredFieldException()

    updated_user = user_service.update_user(user, updates)
    return UserResponse.model_validate(updated_user)


@user_router.get("/me/orders")
def get_my_orders(
    user: Annotated[User, Depends(login_with_header)],
    user_service: Annotated[UserService, Depends()],
) -> list[UserOrderResponse]:
    return [
        UserOrderResponse(
            order_id=order.id,
            total_price=order.total_price,
            status=order.status,
        )
        for order in user_service.get_user_orders(user.id)
    ]
