import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get(self, id: uuid.UUID) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find(self, **filters) -> Optional[ModelType]:
        stmt = select(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
    ) -> tuple[List[ModelType], int]:
        count_stmt = select(self.model)
        stmt = select(self.model)

        if filters:
            for key, value in filters.items():
                condition = getattr(self.model, key) == value
                count_stmt = count_stmt.where(condition)
                stmt = stmt.where(condition)

        count_result = await self.session.execute(count_stmt)
        total = len(count_result.scalars().all())

        if order_by:
            order_column = getattr(self.model, order_by)
            stmt = stmt.order_by(order_column.desc() if descending else order_column)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def update(self, id: uuid.UUID, **kwargs) -> Optional[ModelType]:
        kwargs["updated_at"] = datetime.now(timezone.utc)
        stmt = update(self.model).where(self.model.id == id).values(**kwargs).returning(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, id: uuid.UUID, soft: bool = True) -> bool:
        if soft:
            stmt = (
                update(self.model)
                .where(self.model.id == id)
                .values(deleted_at=datetime.now(timezone.utc))
            )
        else:
            stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
