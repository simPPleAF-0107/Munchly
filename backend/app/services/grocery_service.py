import uuid
from datetime import datetime
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.grocery import ShoppingList, ShoppingListItem
from app.models.meal_plan import MealPlanMeal
from app.models.recipe import Recipe, RecipeIngredient
from app.models.user import User
from app.models.food import Food

from app.services.price_service import PriceService

class GroceryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.price_service = PriceService(db)
    
    async def generate_shopping_list(
        self, meal_plan_id: uuid.UUID, user_id: uuid.UUID
    ) -> ShoppingList:
        # 1. Load all selected meals
        meal_stmt = select(MealPlanMeal).where(MealPlanMeal.meal_plan_id == meal_plan_id).options(
            selectinload(MealPlanMeal.selected_recipe).selectinload(Recipe.ingredients).selectinload(RecipeIngredient.food)
        )
        meal_res = await self.db.execute(meal_stmt)
        meals = meal_res.scalars().all()
        
        # 2. Aggregate ingredients
        aggregated = defaultdict(float)
        food_map = {}
        for m in meals:
            if m.selected_recipe and m.selected_recipe.ingredients:
                for ing in m.selected_recipe.ingredients:
                    aggregated[ing.food_id] += float(ing.quantity_g)
                    food_map[ing.food_id] = ing.food
                    
        # 3. Load user pantry
        user_stmt = select(User).where(User.id == user_id).options(
            selectinload(User.available_ingredients),
            selectinload(User.profile)
        )
        user_res = await self.db.execute(user_stmt)
        user = user_res.scalar_one()
        
        pantry = {ing.food_id: float(ing.quantity_g) for ing in user.available_ingredients}
        
        country_code = user.profile.country_code if user.profile else "IN"
        state_code = user.profile.state_code if user.profile else None
        city = user.profile.city if user.profile else None
        
        # Delete old shopping list if exists
        old_list_stmt = select(ShoppingList).where(ShoppingList.meal_plan_id == meal_plan_id)
        old_list_res = await self.db.execute(old_list_stmt)
        old_list = old_list_res.scalar_one_or_none()
        if old_list:
            await self.db.delete(old_list)
            await self.db.commit()
            
        shopping_list = ShoppingList(
            id=uuid.uuid4(),
            meal_plan_id=meal_plan_id,
            cost_currency="INR",
            created_at=datetime.utcnow()
        )
        self.db.add(shopping_list)
        await self.db.flush()
        
        consumed_cost = 0.0
        actual_shopping_cost = 0.0
        
        # 4. Process each ingredient
        for food_id, consumed_qty in aggregated.items():
            pantry_qty = pantry.get(food_id, 0.0)
            to_purchase = max(0.0, consumed_qty - pantry_qty)
            
            food = food_map.get(food_id)
            category = food.category if food else None
            
            price_data = await self.price_service.get_food_price(food_id, country_code, state_code, city)
            price_per_g = 0.0
            unit = "g"
            
            if price_data:
                price_val = float(price_data.price_per_unit)
                unit_str = (price_data.unit or "kg").lower()
                
                if unit_str == "g":
                    price_per_g = price_val
                elif unit_str == "kg":
                    price_per_g = price_val / 1000.0
                elif unit_str == "mg":
                    price_per_g = price_val * 1000.0
                elif unit_str in ("l", "liter", "liters"):
                    price_per_g = price_val / 1000.0
                elif unit_str in ("ml", "milliliter"):
                    price_per_g = price_val
                else:
                    price_per_g = price_val / 1000.0
                    
            item_consumed_cost = consumed_qty * price_per_g
            consumed_cost += item_consumed_cost
            
            item_purchase_cost = to_purchase * price_per_g
            actual_shopping_cost += item_purchase_cost
            
            item = ShoppingListItem(
                id=uuid.uuid4(),
                shopping_list_id=shopping_list.id,
                food_id=food_id,
                consumed_quantity_g=consumed_qty,
                purchase_quantity_g=to_purchase,
                purchase_unit="g",
                estimated_item_cost=item_purchase_cost,
                category=category
            )
            self.db.add(item)
            
        shopping_list.consumed_cost = consumed_cost
        shopping_list.actual_shopping_cost = actual_shopping_cost
        shopping_list.remaining_inventory_value = actual_shopping_cost - consumed_cost
        
        await self.db.commit()
        await self.db.refresh(shopping_list)
        return shopping_list
        
    async def get_shopping_list(
        self, meal_plan_id: uuid.UUID, user_id: uuid.UUID
    ) -> ShoppingList | None:
        stmt = select(ShoppingList).where(ShoppingList.meal_plan_id == meal_plan_id).options(
            selectinload(ShoppingList.items).selectinload(ShoppingListItem.food)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()
