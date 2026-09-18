import uuid
from datetime import date, datetime, time
from typing import Optional, List
from sqlalchemy import String, Integer, Numeric, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import (
    EnergyLevel, FoodMood, EatingLocation, DailyCheckInStatus,
    WorkoutIntensity, ExerciseType, HungerLevel,
)


class DailyContext(UUIDMixin, Base):
    """Daily context for a user — one row per user per day.
    
    Captures what the user tells us at the start of the day (check-in)
    plus any mid-day overrides (pantry, craving). Used to adjust
    today's recommendations with minimum plan change.
    
    This is the infrastructure that Phase 4 (feedback) and Phase 5
    (behavioral learning) will consume. Phase 3 only records and
    applies context — it does NOT learn from it.
    """
    __tablename__ = "daily_contexts"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_context_user_date"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # --- Check-in status ---
    status: Mapped[DailyCheckInStatus] = mapped_column(
        default=DailyCheckInStatus.PENDING,
    )
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # --- Today's workout ---
    workout_today: Mapped[bool] = mapped_column(Boolean, default=False)
    workout_type: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True,
        comment="ExerciseType value for today's workout",
    )
    workout_intensity: Mapped[Optional[WorkoutIntensity]] = mapped_column(
        nullable=True,
    )

    # --- Today's state ---
    hunger_level: Mapped[Optional[HungerLevel]] = mapped_column(nullable=True)
    energy_level: Mapped[Optional[EnergyLevel]] = mapped_column(nullable=True)
    food_mood: Mapped[Optional[FoodMood]] = mapped_column(nullable=True)
    eating_location: Mapped[Optional[EatingLocation]] = mapped_column(nullable=True)

    # --- Today's constraints ---
    available_cook_time_min: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="How much time does the user have to cook today? (minutes)",
    )

    # --- Adjusted targets ---
    adjusted_calorie_target: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="Calorie target adjusted for today's context (workout, mood, etc.)",
    )

    # --- Pantry today ---
    pantry_food_ids: Mapped[Optional[List]] = mapped_column(
        JSONB, nullable=True,
        comment='Food UUIDs available today, e.g. ["uuid1", "uuid2"]',
    )

    # --- Craving override ---
    craving_recipe_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("recipes.id", ondelete="SET NULL"),
        nullable=True,
        comment="Recipe the user is craving — fit it in if possible",
    )
    craving_meal_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="Which meal slot should the craving go into?",
    )

    # --- Metadata ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship()
