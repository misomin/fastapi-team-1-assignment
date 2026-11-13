from fastapi import APIRouter

from wapang.app.users.router import user_router
from wapang.app.auth.router import auth_router
from wapang.app.stores.router import store_router

api_router = APIRouter()

api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(store_router, prefix="/stores", tags=["stores"])