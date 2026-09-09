import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import FoodCategory, Allergen

class Food(UUIDMixin, Base):
    __tablename__ = "foods"

    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    category: Mapped[Optional[FoodCategory]] = mapped_column(nullable=True)
    calories_per_100g: Mapped[Optional[float]] = mapped_column(Numeric(7, 2), nullable=True)
    protein_per_100g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    carbs_per_100g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    fat_per_100g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    fiber_per_100g: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    sodium_per_100g: Mapped[Optional[float]] = mapped_column(Numeric(7, 2), nullable=True)
    serving_size_g: Mapped[float] = mapped_column(Numeric(6, 1), default=100)
    is_vegan: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vegetarian: Mapped[bool] = mapped_column(Boolean, default=False)
    seasonality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    nutrition_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    nutrition_source_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    allergens: Mapped[List["FoodAllergen"]] = relationship(back_populates="food", cascade="all, delete-orphan")
    regions: Mapped[List["FoodRegion"]] = relationship(back_populates="food", cascade="all, delete-orphan")
    prices: Mapped[List["FoodPrice"]] = relationship(back_populates="food", cascade="all, delete-orphan")
    recipe_ingredients: Mapped[List["RecipeIngredient"]] = relationship(back_populates="food")
    user_preferences: Mapped[List["UserFoodPreference"]] = relationship(back_populates="food")
    user_available_ingredients: Mapped[List["UserAvailableIngredient"]] = relationship(back_populates="food")

class FoodAllergen(UUIDMixin, Base):
    __tablename__ = "food_allergens"
    __table_args__ = (
        UniqueConstraint("food_id", "allergen", name="uq_food_allergy"),
    )

    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"))
    allergen: Mapped[Allergen]

    # Relationships
    food: Mapped["Food"] = relationship(back_populates="allergens")

class FoodRegion(UUIDMixin, Base):
    __tablename__ = "food_regions"
    __table_args__ = (
        UniqueConstraint("food_id", "country_code", "state_code", name="uq_food_region"),
    )

    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"))
    country_code: Mapped[str] = mapped_column(String(2))
    state_code: Mapped[str] = mapped_column(String(10))
    availability_score: Mapped[Optional[float]] = mapped_column(Numeric(2, 1), nullable=True)

    # Relationships
    food: Mapped["Food"] = relationship(back_populates="regions")

class FoodPrice(UUIDMixin, Base):
    __tablename__ = "food_prices"

    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"))
    country_code: Mapped[str] = mapped_column(String(2))
    state_code: Mapped[str] = mapped_column(String(10))
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    typical_package_size_g: Mapped[Optional[float]] = mapped_column(Numeric(10, 1), nullable=True)
    typical_package_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    food: Mapped["Food"] = relationship(back_populates="prices")
