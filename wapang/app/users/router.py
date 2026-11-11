from typing import Annotated
from fastapi import APIRouter, Depends, status

from wapang.app.auth.utils import login_with_header
from wapang.app.users.models import User
from wapang.app.users.schemas import UserSignupRequest, UserResponse
from wapang.app.users.services import UserService

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
