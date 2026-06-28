import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user_id
from app.repositories.base import BaseRepository
from app.models.user import User
from app.schemas.auth import UserResponse
from app.core.exception_handlers import NotFoundError
from app.core.response import success_response

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    repo = BaseRepository(User, db)
    user = await repo.get(uuid.UUID(user_id))
    if not user:
        raise NotFoundError("User not found")
    return UserResponse.model_validate(user)
