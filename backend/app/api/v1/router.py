from fastapi import APIRouter

from app.api.v1.routes import auth, totp, totp_recovery, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(totp.router)
api_router.include_router(totp_recovery.router)
api_router.include_router(users.router)
