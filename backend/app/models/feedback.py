import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import FeedbackType, FeedbackScope, PreferenceTier


class UserFeedback(UUIDMixin, Base):
    """Structured feedback record.
    
    Each rejection/feedback creates an immutable record here AND emits
    an event to the event store. The feedback record stores the structured
    data; the event store records the behavioral signal.
    
    Phase 4 produces these records. Phase 5 (behavioral learning) consumes them.
    """
    __tablename__ = "user_feedback"
    __table_args__ = (
        Index("ix_feedback_user_recipe", "user_id", "recipe_id"),
        Index("ix_feedback_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipe_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("recipes.id", ondelete="SET NULL"),
        nullable=True,
    )
    meal_plan_meal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("meal_plan_meals.id", ondelete="SET NULL"),
        nullable=True,
        comment="Which specific meal slot this feedback is about",
    )
    feedback_type: Mapped[FeedbackType] = mapped_column(nullable=False)
    scope: Mapped[FeedbackScope] = mapped_column(
        nullable=False,
        default=FeedbackScope.TODAY,
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Human-readable reason category",
    )
    ingredient_ids: Mapped[Optional[List]] = mapped_column(
        JSONB, nullable=True,
        comment='Food UUIDs of rejected ingredients, e.g. ["uuid1", "uuid2"]',
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Optional free-text notes from user",
    )
    applied_tier: Mapped[Optional[PreferenceTier]] = mapped_column(
        nullable=True,
        comment="Which preference tier was applied as a result of this feedback",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UserPreferenceOverride(UUIDMixin, Base):
    """Active preference overrides derived from feedback.
    
    These are the RESULT of feedback processing. The constraint service
    and recommendation service read these to adjust behavior.
    
    PREFERENCE/DISLIKE/AVOIDANCE -> consumed by RecommendationService (scoring)
    MEDICAL/ALLERGY -> consumed by ConstraintService (hard filter)
    
    Critical safety rule: only explicit user action (not behavioral inference)
    can create MEDICAL or ALLERGY overrides.
    """
    __tablename__ = "user_preference_overrides"
    __table_args__ = (
        Index("ix_pref_override_user_entity", "user_id", "entity_type", "entity_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="recipe | ingredient | cuisine",
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    tier: Mapped[PreferenceTier] = mapped_column(nullable=False)
    source_feedback_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("user_feedback.id", ondelete="SET NULL"),
        nullable=True,
        comment="Feedback that created this override",
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="For TODAY scope: auto-expires at end of day",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
