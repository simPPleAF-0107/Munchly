import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import InsightStatus, BehavioralDimension


class UserBehavioralProfile(UUIDMixin, Base):
    """Learned behavioral preference from observing user actions.
    
    Consumed by BehavioralService from the immutable event store.
    Updated via EMA (Exponential Moving Average), not raw counts.
    
    Critical safety rule:
    - These profiles feed into the RECOMMENDATION SCORING layer only
    - They NEVER feed into the CONSTRAINT/SAFETY layer
    - Behavioral learning can NEVER escalate to MEDICAL or ALLERGY tier
    
    Confidence is computed from sample_count:
    - sample_count < 10 (MIN_ACTIONS) -> confidence = 0 (use explicit only)
    - sample_count 10-30 -> confidence grows from 0 to ~0.7
    - sample_count 30+ -> confidence saturates near 0.8-0.9
    - confidence is CAPPED at 0.9 so explicit preferences always have weight
    """
    __tablename__ = "user_behavioral_profiles"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "dimension", "meal_type", "entity_key",
            name="uq_behavioral_profile_user_dim_meal_entity",
        ),
        Index("ix_behavioral_user_dimension", "user_id", "dimension"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dimension: Mapped[BehavioralDimension] = mapped_column(
        nullable=False,
        comment="What type of behavior was observed",
    )
    meal_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="BREAKFAST | LUNCH | DINNER | None (for meal-agnostic patterns)",
    )
    entity_key: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="The entity being observed: cuisine name, ingredient ID, recipe pattern, etc.",
    )
    observed_strength: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="EMA-smoothed preference strength: -1.0 (strong avoidance) to +1.0 (strong preference)",
    )
    sample_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Number of MEANINGFUL behavioral observations (not views, only actions)",
    )
    confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="Computed from sample_count. 0.0 until MIN_ACTIONS, caps at 0.9",
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UserBehavioralInsight(UUIDMixin, Base):
    """A 'Munchly Learned...' insight generated from behavioral patterns.
    
    Generated when a pattern is strong enough (confidence > 0.5).
    User can Accept (confirm), Dismiss (ignore), or trigger Reset.
    """
    __tablename__ = "user_behavioral_insights"
    __table_args__ = (
        Index("ix_insight_user_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dimension: Mapped[BehavioralDimension] = mapped_column(nullable=False)
    meal_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
    )
    entity_key: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    message: Mapped[str] = mapped_column(
        String(500), nullable=False,
        comment='e.g. "Munchly learned that you usually prefer lighter breakfasts."',
    )
    observed_strength: Mapped[float] = mapped_column(
        Float, nullable=False,
    )
    confidence: Mapped[float] = mapped_column(
        Float, nullable=False,
    )
    status: Mapped[InsightStatus] = mapped_column(
        default=InsightStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
