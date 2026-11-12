from fastapi import APIRouter

from wapang.app.users.router import user_router
from wapang.app.auth.router import auth_router
from wapang.app.orders.router import order_router

api_router = APIRouter()

api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(order_router, prefix="/orders", tags=["orders"])