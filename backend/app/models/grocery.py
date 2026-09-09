import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin
from app.models.enums import FoodCategory

class ShoppingList(UUIDMixin, Base):
    __tablename__ = "shopping_lists"

    meal_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meal_plans.id", ondelete="CASCADE"), unique=True)
    consumed_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    actual_shopping_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    remaining_inventory_value: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    cost_currency: Mapped[str] = mapped_column(String(3), default="INR")
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    meal_plan: Mapped["MealPlan"] = relationship(back_populates="shopping_list")
    items: Mapped[List["ShoppingListItem"]] = relationship(back_populates="shopping_list", cascade="all, delete-orphan")

class ShoppingListItem(UUIDMixin, Base):
    __tablename__ = "shopping_list_items"

    shopping_list_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shopping_lists.id", ondelete="CASCADE"))
    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"))
    consumed_quantity_g: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    purchase_quantity_g: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    purchase_unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    estimated_item_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    category: Mapped[Optional[FoodCategory]] = mapped_column(nullable=True)

    # Relationships
    shopping_list: Mapped["ShoppingList"] = relationship(back_populates="items")
    food: Mapped["Food"] = relationship()
