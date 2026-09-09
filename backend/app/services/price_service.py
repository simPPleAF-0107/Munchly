import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.food import FoodPrice
from app.models.recipe import RecipeIngredient

class PriceService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_food_price(
        self, food_id: uuid.UUID, country_code: str, state_code: str | None, city: str | None
    ) -> FoodPrice | None:
        """Regional price resolution with fallback chain:
        1. country + state + city (exact match)
        2. country + state (state average)
        3. country only (national average)
        4. None (no price found)
        """
        # Build query for prices of this food
        stmt = select(FoodPrice).where(FoodPrice.food_id == food_id).where(FoodPrice.country_code == country_code)
        
        result = await self.db.execute(stmt)
        prices = result.scalars().all()
        
        # 1. Exact match
        if city and state_code:
            exact = next((p for p in prices if p.state_code == state_code and p.city == city), None)
            if exact:
                return exact
        
        # 2. State average
        if state_code:
            state_avg = next((p for p in prices if p.state_code == state_code and p.city is None), None)
            if state_avg:
                return state_avg
        
        # 3. National average
        national_avg = next((p for p in prices if p.state_code is None and p.city is None), None)
        return national_avg
    
    async def compute_recipe_cost(
        self, recipe_id: uuid.UUID, country_code: str, state_code: str | None, city: str | None
    ) -> float:
        """Sum ingredient costs using regional pricing."""
        stmt = select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
        result = await self.db.execute(stmt)
        ingredients = result.scalars().all()
        
        total_cost = 0.0
        for ingredient in ingredients:
            price = await self.get_food_price(ingredient.food_id, country_code, state_code, city)
            if price:
                price_val = float(price.price_per_unit)
                unit_str = (price.unit or "kg").lower()
                
                # Convert price to price per gram
                if unit_str == "g":
                    price_per_g = price_val
                elif unit_str == "kg":
                    price_per_g = price_val / 1000.0
                elif unit_str == "mg":
                    price_per_g = price_val * 1000.0
                elif unit_str in ("l", "liter", "liters"):
                    # Approximate 1L = 1000g
                    price_per_g = price_val / 1000.0
                elif unit_str in ("ml", "milliliter"):
                    price_per_g = price_val
                else:
                    # Fallback assuming price is per kg
                    price_per_g = price_val / 1000.0
                
                cost = price_per_g * float(ingredient.quantity_g)
                total_cost += cost
                
        return round(total_cost, 2)
