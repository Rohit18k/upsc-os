import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class AICostLedger(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_cost_ledger"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cache_hit: Mapped[str] = mapped_column(String(50), default="miss", nullable=False)  # "hit", "miss"
    feature: Mapped[str] = mapped_column(String(100), nullable=False)  # "chat", "tutor", "socratic", etc.
