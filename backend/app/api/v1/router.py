from fastapi import APIRouter

from app.api.v1.routes import auth, users, items

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(items.router)
