import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import DietType, MealType, Cuisine, Difficulty

class Recipe(UUIDMixin, Base):
    __tablename__ = "recipes"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    calories: Mapped[Optional[float]] = mapped_column(Numeric(7, 1), nullable=True)
    protein_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    carbs_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    fat_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    fiber_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    sodium_mg: Mapped[Optional[float]] = mapped_column(Numeric(7, 1), nullable=True)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    cost_currency: Mapped[str] = mapped_column(String(3), default="INR")
    prep_time_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[Optional[Difficulty]] = mapped_column(nullable=True)
    servings: Mapped[int] = mapped_column(Integer, default=1)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    nutrition_computed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Nutrition confidence
    nutrition_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True,
        comment="VERIFIED | CALCULATED | ESTIMATED | INCOMPLETE")
    
    # Cached micronutrient totals (computed from ingredients)
    calcium_mg: Mapped[Optional[float]] = mapped_column(Numeric(7, 1), nullable=True)
    iron_mg: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    magnesium_mg: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    potassium_mg: Mapped[Optional[float]] = mapped_column(Numeric(7, 1), nullable=True)
    zinc_mg: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    vitamin_a_mcg: Mapped[Optional[float]] = mapped_column(Numeric(7, 1), nullable=True)
    vitamin_b12_mcg: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    vitamin_c_mg: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    vitamin_d_mcg: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    folate_mcg: Mapped[Optional[float]] = mapped_column(Numeric(7, 1), nullable=True)
    phosphorus_mg: Mapped[Optional[float]] = mapped_column(Numeric(7, 1), nullable=True)
    sugar_g: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    ingredients: Mapped[List["RecipeIngredient"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")
    diet_compatibility: Mapped[List["RecipeDietCompatibility"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")
    meal_types: Mapped[List["RecipeMealType"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")
    cuisines: Mapped[List["RecipeCuisine"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")
    regions: Mapped[List["RecipeRegion"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")
    meal_options: Mapped[List["MealOption"]] = relationship(back_populates="recipe")

class RecipeIngredient(UUIDMixin, Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        UniqueConstraint("recipe_id", "food_id", name="uq_recipe_ingredient"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id", ondelete="RESTRICT"))
    quantity_g: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), default="g")
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
    food: Mapped["Food"] = relationship(back_populates="recipe_ingredients")

class RecipeDietCompatibility(UUIDMixin, Base):
    __tablename__ = "recipe_diet_compatibility"
    __table_args__ = (
        UniqueConstraint("recipe_id", "diet_type", name="uq_recipe_diet_type"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    diet_type: Mapped[DietType]

    # Relationships
    recipe: Mapped["Recipe"] = relationship(back_populates="diet_compatibility")

class RecipeMealType(UUIDMixin, Base):
    __tablename__ = "recipe_meal_types"
    __table_args__ = (
        UniqueConstraint("recipe_id", "meal_type", name="uq_recipe_meal_type"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    meal_type: Mapped[MealType]

    # Relationships
    recipe: Mapped["Recipe"] = relationship(back_populates="meal_types")

class RecipeCuisine(UUIDMixin, Base):
    __tablename__ = "recipe_cuisines"
    __table_args__ = (
        UniqueConstraint("recipe_id", "cuisine", name="uq_recipe_cuisine"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    cuisine: Mapped[Cuisine]

    # Relationships
    recipe: Mapped["Recipe"] = relationship(back_populates="cuisines")

class RecipeRegion(UUIDMixin, Base):
    __tablename__ = "recipe_regions"
    __table_args__ = (
        UniqueConstraint("recipe_id", "country_code", "state_code", name="uq_recipe_region"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    country_code: Mapped[str] = mapped_column(String(2))
    state_code: Mapped[str] = mapped_column(String(10))
    relevance_score: Mapped[Optional[float]] = mapped_column(Numeric(2, 1), nullable=True)

    # Relationships
    recipe: Mapped["Recipe"] = relationship(back_populates="regions")
