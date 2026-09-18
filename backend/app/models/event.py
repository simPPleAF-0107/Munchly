import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, UUIDMixin
from app.models.enums import EventType


class UserEvent(UUIDMixin, Base):
    """Immutable behavioral event log.
    
    Never updated, never deleted. Source of truth for all behavioral analysis.
    Raw events feed into the behavioral aggregation service (Phase 5).
    """
    __tablename__ = "user_events"
    __table_args__ = (
        Index("ix_user_events_user_type", "user_id", "event_type"),
        Index("ix_user_events_user_created", "user_id", "created_at"),
        Index("ix_user_events_entity", "entity_type", "entity_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[EventType] = mapped_column(nullable=False)
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="recipe | meal | ingredient | plan | feedback",
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata", JSONB, nullable=True,
        comment="Flexible payload per event type",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
