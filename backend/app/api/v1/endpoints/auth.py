from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user_id
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth import AuthService
from app.core.response import success_response

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.register(request)
    return result


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, http_request: Request, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.login(
        request,
        ip_address=http_request.client.host if http_request.client else None,
        user_agent=http_request.headers.get("user-agent"),
    )
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.refresh_token(request)
    return result


@router.post("/logout")
async def logout(request: RefreshTokenRequest, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    await service.logout(request.refresh_token)
    return success_response(message="Successfully logged out")
