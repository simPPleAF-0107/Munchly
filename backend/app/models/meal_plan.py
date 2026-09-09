import uuid
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import String, Integer, Numeric, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import MealPlanStatus, MealType, OptionType, MealAction

class MealPlan(UUIDMixin, Base):
    __tablename__ = "meal_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_consumed_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    total_purchase_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    cost_currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[MealPlanStatus] = mapped_column(default=MealPlanStatus.ACTIVE)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="meal_plans")
    meals: Mapped[List["MealPlanMeal"]] = relationship(back_populates="meal_plan", cascade="all, delete-orphan")
    shopping_list: Mapped["ShoppingList"] = relationship(back_populates="meal_plan", uselist=False, cascade="all, delete-orphan")

class MealPlanMeal(UUIDMixin, Base):
    __tablename__ = "meal_plan_meals"
    __table_args__ = (
        UniqueConstraint("meal_plan_id", "day_of_week", "meal_type", name="uq_meal_plan_meal"),
    )

    meal_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meal_plans.id", ondelete="CASCADE"))
    day_of_week: Mapped[int] = mapped_column(Integer) # 1-7
    meal_type: Mapped[MealType]
    selected_recipe_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    meal_plan: Mapped["MealPlan"] = relationship(back_populates="meals")
    selected_recipe: Mapped[Optional["Recipe"]] = relationship()
    options: Mapped[List["MealOption"]] = relationship(back_populates="meal_plan_meal", cascade="all, delete-orphan")
    history_entries: Mapped[List["MealHistory"]] = relationship(back_populates="meal_plan_meal")

class MealOption(UUIDMixin, Base):
    __tablename__ = "meal_options"
    __table_args__ = (
        UniqueConstraint("meal_plan_meal_id", "option_type", name="uq_meal_option"),
    )

    meal_plan_meal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meal_plan_meals.id", ondelete="CASCADE"))
    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    option_type: Mapped[OptionType]
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)

    # Relationships
    meal_plan_meal: Mapped["MealPlanMeal"] = relationship(back_populates="options")
    recipe: Mapped["Recipe"] = relationship(back_populates="meal_options")

class MealHistory(UUIDMixin, Base):
    __tablename__ = "meal_history"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    meal_plan_meal_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("meal_plan_meals.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[MealAction]
    replacement_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="meal_history")
    recipe: Mapped["Recipe"] = relationship()
    meal_plan_meal: Mapped[Optional["MealPlanMeal"]] = relationship(back_populates="history_entries")
