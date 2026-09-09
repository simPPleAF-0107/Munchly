import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import DietType, Allergen, DietaryRestriction, PreferenceType, Cuisine

class UserDietaryPreference(UUIDMixin, Base):
    __tablename__ = "user_dietary_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    diet_type: Mapped[DietType] = mapped_column(nullable=False)
    eats_chicken: Mapped[bool] = mapped_column(Boolean, default=False)
    eats_mutton: Mapped[bool] = mapped_column(Boolean, default=False)
    eats_fish: Mapped[bool] = mapped_column(Boolean, default=False)
    eats_seafood: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="dietary_preference")

class UserAllergy(UUIDMixin, Base):
    __tablename__ = "user_allergies"
    __table_args__ = (
        UniqueConstraint("user_id", "allergen", name="uq_user_allergy"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    allergen: Mapped[Allergen]
    custom_allergen: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="allergies")

class UserDietaryRestriction(UUIDMixin, Base):
    __tablename__ = "user_dietary_restrictions"
    __table_args__ = (
        UniqueConstraint("user_id", "restriction", name="uq_user_dietary_restriction"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    restriction: Mapped[DietaryRestriction]

    # Relationships
    user: Mapped["User"] = relationship(back_populates="dietary_restrictions")

class UserFoodPreference(UUIDMixin, Base):
    __tablename__ = "user_food_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "food_id", name="uq_user_food_preference"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"))
    preference: Mapped[PreferenceType]

    # Relationships
    user: Mapped["User"] = relationship(back_populates="food_preferences")
    food: Mapped["Food"] = relationship(back_populates="user_preferences")

class UserCuisinePreference(UUIDMixin, Base):
    __tablename__ = "user_cuisine_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "cuisine", name="uq_user_cuisine_preference"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    cuisine: Mapped[Cuisine]
    preference_strength: Mapped[float] = mapped_column(Numeric(2, 1), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="cuisine_preferences")

class UserAvailableIngredient(UUIDMixin, Base):
    __tablename__ = "user_available_ingredients"
    __table_args__ = (
        UniqueConstraint("user_id", "food_id", name="uq_user_available_ingredient"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"))
    quantity_g: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="g")
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="available_ingredients")
    food: Mapped["Food"] = relationship(back_populates="user_available_ingredients")
