import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.exception_handlers import AuthenticationError, ConflictError
from app.models.user import User, UserSession
from app.repositories.base import BaseRepository
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.security.password import hash_password, verify_password

settings = get_settings()


class AuthService:
    def __init__(self, session: AsyncSession):
        self.user_repo = BaseRepository(User, session)
        self.session_repo = BaseRepository(UserSession, session)
        self.session = session

    async def register(self, request: RegisterRequest) -> AuthResponse:
        existing = await self.user_repo.find(email=request.email)
        if existing:
            raise ConflictError("Email already registered")

        user = await self.user_repo.create(
            email=request.email,
            hashed_password=hash_password(request.password),
            full_name=request.full_name,
            role="user",
        )

        tokens = await self._create_tokens(user)
        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    async def login(self, request: LoginRequest, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> AuthResponse:
        user = await self.user_repo.find(email=request.email)
        if not user or not verify_password(request.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        tokens = await self._create_tokens(user, ip_address, user_agent)

        user.last_login_at = datetime.now(timezone.utc)
        await self.session.flush()

        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    async def refresh_token(self, request: RefreshTokenRequest) -> TokenResponse:
        payload = decode_token(request.refresh_token, token_type="refresh")
        user_id = payload.get("sub")

        user = await self.user_repo.get(uuid.UUID(user_id))
        if not user:
            raise AuthenticationError("User not found")

        token_hash = hashlib.sha256(request.refresh_token.encode()).hexdigest()
        session = await self.session_repo.find(
            user_id=uuid.UUID(user_id),
            refresh_token_hash=token_hash,
            is_revoked=False,
        )

        if not session:
            raise AuthenticationError("Invalid session")

        if session.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Session expired")

        tokens = await self._create_tokens(user)
        return tokens

    async def logout(self, refresh_token: str) -> None:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = await self.session_repo.find(refresh_token_hash=token_hash)
        if session:
            await self.session_repo.update(session.id, is_revoked=True, revoked_at=datetime.now(timezone.utc))

    async def _create_tokens(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenResponse:
        extra_claims = {"role": user.role}
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims=extra_claims,
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self.session_repo.create(
            user_id=user.id,
            refresh_token_hash=token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
