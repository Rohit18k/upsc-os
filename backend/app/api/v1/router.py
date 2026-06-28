from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, users

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["users"])
