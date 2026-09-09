import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.recipe import Recipe, RecipeIngredient
from app.models.food import Food

class RecipeNutritionService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def compute_recipe_nutrition(self, recipe_id: uuid.UUID) -> dict:
        """Compute nutrition by summing all non-optional ingredients.
        For each ingredient: nutrient_value = food.nutrient_per_100g * (quantity_g / 100)
        Returns: {calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg}
        """
        stmt = (
            select(RecipeIngredient, Food)
            .join(Food, RecipeIngredient.food_id == Food.id)
            .where(RecipeIngredient.recipe_id == recipe_id)
            .where(RecipeIngredient.is_optional == False)
        )
        
        result = await self.db.execute(stmt)
        ingredients = result.all()
        
        totals = {
            "calories": 0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0,
            "fiber_g": 0.0,
            "sodium_mg": 0.0
        }
        
        for ingredient, food in ingredients:
            factor = float(ingredient.quantity_g) / 100.0
            totals["calories"] += int(float(food.calories_per_100g) * factor)
            totals["protein_g"] += float(food.protein_per_100g) * factor
            totals["carbs_g"] += float(food.carbs_per_100g) * factor
            totals["fat_g"] += float(food.fat_per_100g) * factor
            totals["fiber_g"] += float(food.fiber_per_100g) * factor
            totals["sodium_mg"] += float(food.sodium_per_100g) * factor
            
        # Round the float values
        return {
            "calories": totals["calories"],
            "protein_g": round(totals["protein_g"], 1),
            "carbs_g": round(totals["carbs_g"], 1),
            "fat_g": round(totals["fat_g"], 1),
            "fiber_g": round(totals["fiber_g"], 1),
            "sodium_mg": round(totals["sodium_mg"], 1)
        }
    
    async def recompute_all_recipes(self) -> int:
        """Recompute nutrition for all recipes. Returns count updated."""
        stmt = select(Recipe.id)
        result = await self.db.execute(stmt)
        recipe_ids = result.scalars().all()
        
        count = 0
        for rid in recipe_ids:
            nutrition = await self.compute_recipe_nutrition(rid)
            recipe_stmt = select(Recipe).where(Recipe.id == rid)
            res = await self.db.execute(recipe_stmt)
            recipe = res.scalar_one_or_none()
            if recipe:
                recipe.calories = nutrition["calories"]
                recipe.protein_g = nutrition["protein_g"]
                recipe.carbs_g = nutrition["carbs_g"]
                recipe.fat_g = nutrition["fat_g"]
                recipe.fiber_g = nutrition["fiber_g"]
                recipe.sodium_mg = nutrition["sodium_mg"]
                count += 1
                
        await self.db.commit()
        return count
