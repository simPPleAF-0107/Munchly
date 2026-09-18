from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import SubscriptionTier

class User(UUIDMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(20), default="email")
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(default=SubscriptionTier.FREE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    health_conditions: Mapped[List["UserHealthCondition"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    dietary_preference: Mapped["UserDietaryPreference"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    allergies: Mapped[List["UserAllergy"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    dietary_restrictions: Mapped[List["UserDietaryRestriction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    food_preferences: Mapped[List["UserFoodPreference"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    cuisine_preferences: Mapped[List["UserCuisinePreference"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    available_ingredients: Mapped[List["UserAvailableIngredient"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    meal_plans: Mapped[List["MealPlan"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    meal_history: Mapped[List["MealHistory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    lifestyle: Mapped["UserLifestyle"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
