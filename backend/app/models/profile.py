import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import Gender, ActivityLevel, HealthGoal, CookingAbility, BudgetType

class UserProfile(UUIDMixin, Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), default="IN")
    state_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Numeric(5, 1), nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Numeric(5, 1), nullable=True)
    activity_level: Mapped[Optional[ActivityLevel]] = mapped_column(nullable=True)
    health_goal: Mapped[Optional[HealthGoal]] = mapped_column(nullable=True)
    cooking_ability: Mapped[Optional[CookingAbility]] = mapped_column(nullable=True)
    max_prep_time_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weekly_grocery_limit: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    weekly_grocery_limit_currency: Mapped[str] = mapped_column(String(3), default="INR")
    budget_type: Mapped[Optional[BudgetType]] = mapped_column(nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="profile")
