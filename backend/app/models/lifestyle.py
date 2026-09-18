import uuid
from datetime import time, datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, Time, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import (
    ExerciseType, WorkoutIntensity, FitnessGoal, BulkCutStatus,
    CookingEffort, FoodWastePreference, HungerLevel,
    PreferenceStrictness, WorkoutTiming,
)


class UserLifestyle(UUIDMixin, Base):
    """Real-world constraints that shape what food makes sense for this person.
    
    Captures exercise, fitness goals, daily schedule, cooking constraints,
    and meta-preferences that affect HOW recommendations are made.
    """
    __tablename__ = "user_lifestyles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True,
    )

    # --- Exercise & Fitness ---
    exercise_frequency: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="Days per week with intentional exercise (0-7)",
    )
    exercise_types: Mapped[Optional[List]] = mapped_column(
        JSONB, nullable=True,
        comment='List of ExerciseType values, e.g. ["GYM_WEIGHTS", "CARDIO"]',
    )
    workout_intensity: Mapped[Optional[WorkoutIntensity]] = mapped_column(nullable=True)
    workout_timing: Mapped[Optional[WorkoutTiming]] = mapped_column(nullable=True)
    fitness_goal: Mapped[Optional[FitnessGoal]] = mapped_column(nullable=True)
    bulk_cut_status: Mapped[Optional[BulkCutStatus]] = mapped_column(nullable=True)

    # --- Daily Schedule ---
    wake_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    sleep_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    breakfast_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    lunch_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    dinner_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    # --- Cooking Constraints ---
    cooking_effort: Mapped[Optional[CookingEffort]] = mapped_column(nullable=True)
    meals_cooked_per_day: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="How many meals does user actually cook? (0-3)",
    )
    cooks_themselves: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True,
        comment="Does the user cook their own food?",
    )
    has_microwave: Mapped[bool] = mapped_column(Boolean, default=True)
    has_oven: Mapped[bool] = mapped_column(Boolean, default=False)
    has_blender: Mapped[bool] = mapped_column(Boolean, default=False)
    has_air_fryer: Mapped[bool] = mapped_column(Boolean, default=False)
    has_pressure_cooker: Mapped[bool] = mapped_column(Boolean, default=True)
    has_gas_stove: Mapped[bool] = mapped_column(Boolean, default=True)

    # --- Meal Preferences ---
    food_waste_preference: Mapped[Optional[FoodWastePreference]] = mapped_column(nullable=True)
    leftover_tolerance: Mapped[bool] = mapped_column(
        Boolean, default=True,
        comment="Willing to eat leftovers?",
    )
    meal_prep_willing: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="Willing to batch-cook on weekends?",
    )

    # --- Meta Preferences ---
    hunger_level: Mapped[Optional[HungerLevel]] = mapped_column(nullable=True)
    preference_strictness: Mapped[Optional[PreferenceStrictness]] = mapped_column(nullable=True)

    # --- Timestamps ---
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="lifestyle")
