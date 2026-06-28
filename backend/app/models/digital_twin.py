import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String, Table, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

# Many-to-many relationship table for Knowledge Node dependencies (prerequisites)
knowledge_node_dependencies = Table(
    "knowledge_node_dependencies",
    Base.metadata,
    Column(
        "node_id",
        UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "prerequisite_id",
        UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class KnowledgeNode(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_nodes"

    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # 'subject', 'topic', 'concept'
    subject: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Self-referencing relationship for hierarchy
    parent = relationship(
        "KnowledgeNode",
        remote_side="KnowledgeNode.id",
        back_populates="children",
    )
    children = relationship(
        "KnowledgeNode",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    # Dependencies (prerequisites) mapping
    prerequisites = relationship(
        "KnowledgeNode",
        secondary=knowledge_node_dependencies,
        primaryjoin="KnowledgeNode.id == knowledge_node_dependencies.c.node_id",
        secondaryjoin="KnowledgeNode.id == knowledge_node_dependencies.c.prerequisite_id",
        backref="dependent_nodes",
    )


class StudentDigitalTwin(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "student_digital_twins"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Modular state representation as JSON (compatible with both PostgreSQL JSONB and SQLite JSON)
    knowledge_state: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    memory_state: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    practice_state: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    writing_state: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    behaviour_state: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    learning_profile: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Independent Readiness Signals
    knowledge_readiness: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    memory_readiness: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    practice_readiness: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    writing_readiness: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    behaviour_readiness: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)

    # Relationships
    user = relationship("User", backref="digital_twin")


class StudentEventLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "student_event_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    user = relationship("User", backref="event_logs")
