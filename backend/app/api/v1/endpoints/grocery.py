import uuid
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.base import get_db
from app.schemas.grocery import ShoppingListResponse
from app.services.grocery_service import GroceryService
from app.api.deps import get_current_user
from app.models.grocery import ShoppingList
from app.models.user import User

router = APIRouter(prefix="/grocery", tags=["grocery"])

@router.get("/{meal_plan_id}", response_model=ShoppingListResponse)
async def get_grocery_list(
    meal_plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user)
):
    service = GroceryService(db)
    shopping_list = await service.get_shopping_list(meal_plan_id, user_id)
    if not shopping_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")
        
    user_stmt = select(User).where(User.id == user_id).options(selectinload(User.profile))
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one()
    limit = float(user.profile.weekly_grocery_limit) if user.profile and user.profile.weekly_grocery_limit else 100.0
    
    items_by_cat = defaultdict(list)
    for item in shopping_list.items:
        items_by_cat[item.category.name if item.category else "OTHER"].append({
            "food_id": item.food_id,
            "food_name": item.food.name if item.food else "Unknown",
            "category": item.category.name if item.category else "OTHER",
            "consumed_quantity_g": float(item.consumed_quantity_g or 0),
            "purchase_quantity_g": float(item.purchase_quantity_g or 0),
            "purchase_unit": item.purchase_unit or "g",
            "estimated_item_cost": float(item.estimated_item_cost or 0)
        })
        
    return {
        "id": shopping_list.id,
        "consumed_cost": float(shopping_list.consumed_cost or 0),
        "actual_shopping_cost": float(shopping_list.actual_shopping_cost or 0),
        "remaining_inventory_value": float(shopping_list.remaining_inventory_value or 0),
        "cost_currency": shopping_list.cost_currency,
        "items": [
            {
                "food_id": i.food_id,
                "food_name": i.food.name if i.food else "Unknown",
                "category": i.category.name if i.category else "OTHER",
                "consumed_quantity_g": float(i.consumed_quantity_g or 0),
                "purchase_quantity_g": float(i.purchase_quantity_g or 0),
                "purchase_unit": i.purchase_unit or "g",
                "estimated_item_cost": float(i.estimated_item_cost or 0)
            } for i in shopping_list.items
        ],
        "items_by_category": dict(items_by_cat),
        "weekly_grocery_limit": limit,
        "within_budget": float(shopping_list.actual_shopping_cost or 0) <= limit
    }

@router.post("/{meal_plan_id}/regenerate", response_model=ShoppingListResponse)
async def regenerate_grocery_list(
    meal_plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user)
):
    service = GroceryService(db)
    await service.generate_shopping_list(meal_plan_id, user_id)
    return await get_grocery_list(meal_plan_id, db, user_id)
