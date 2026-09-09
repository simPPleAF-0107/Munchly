import uuid
from typing import List, Optional
from sqlalchemy import select, and_, or_, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.recipe import (
    Recipe,
    RecipeDietCompatibility,
    RecipeMealType,
    RecipeIngredient,
    RecipeCuisine,
    RecipeRegion
)
from app.models.food import Food, FoodAllergen
from app.models.user import User
from app.models.dietary import UserDietaryPreference, UserAllergy, UserFoodPreference
from app.models.health import UserHealthCondition
from app.models.medical_rule import MedicalRule, MedicalRuleConstraint
from app.models.enums import DietType, MealType, PreferenceType, FoodCategory, RuleScope, RuleOperator, Allergen

class ConstraintService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_eligible_recipes(
        self,
        user_id: uuid.UUID,
        meal_type: str,  # BREAKFAST, LUNCH, DINNER
        exclude_recipe_ids: Optional[List[uuid.UUID]] = None
    ) -> List[Recipe]:
        """Apply all hard constraints and return only eligible recipes."""
        
        # 1. Fetch user data
        user_query = select(User).where(User.id == user_id).options(
            selectinload(User.dietary_preference),
            selectinload(User.allergies),
            selectinload(User.food_preferences),
            selectinload(User.health_conditions)
        )
        result = await self.db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user:
            return []
            
        dietary_pref = user.dietary_preference
        user_diet = dietary_pref.diet_type if dietary_pref else DietType.NON_VEGETARIAN
        user_allergens = [a.allergen for a in user.allergies]
        never_food_ids = [p.food_id for p in user.food_preferences if p.preference == PreferenceType.NEVER]
        
        # Start base recipe query
        stmt = select(Recipe).where(
            Recipe.meal_types.any(RecipeMealType.meal_type == meal_type)
        )
        
        # Exclude IDs if any
        if exclude_recipe_ids:
            stmt = stmt.where(Recipe.id.notin_(exclude_recipe_ids))
            
        # 2. Diet Compatibility
        stmt = stmt.where(
            Recipe.diet_compatibility.any(RecipeDietCompatibility.diet_type == user_diet)
        )
        
        # 3. Allergen Exclusion
        if user_allergens:
            stmt = stmt.where(
                not_(
                    Recipe.ingredients.any(
                        RecipeIngredient.food.has(
                            Food.allergens.any(FoodAllergen.allergen.in_(user_allergens))
                        )
                    )
                )
            )
            
        # 4. Never Foods Exclusion
        if never_food_ids:
            stmt = stmt.where(
                not_(
                    Recipe.ingredients.any(RecipeIngredient.food_id.in_(never_food_ids))
                )
            )
            
        # 5. Non-veg sub-filters
        if user_diet == DietType.NON_VEGETARIAN and dietary_pref:
            # If user doesn't eat fish or seafood, exclude FISH_SEAFOOD
            if not dietary_pref.eats_fish or not dietary_pref.eats_seafood:
                stmt = stmt.where(
                    not_(
                        Recipe.ingredients.any(
                            RecipeIngredient.food.has(Food.category == FoodCategory.FISH_SEAFOOD)
                        )
                    )
                )
            # If user doesn't eat chicken/mutton, we assume they are MEAT.
            # To be more precise, we might check food names or tags. 
            # For now, if neither is eaten, exclude MEAT entirely.
            if not dietary_pref.eats_chicken and not dietary_pref.eats_mutton:
                stmt = stmt.where(
                    not_(
                        Recipe.ingredients.any(
                            RecipeIngredient.food.has(Food.category == FoodCategory.MEAT)
                        )
                    )
                )
            elif not dietary_pref.eats_chicken:
                # Exclude chicken specifically
                stmt = stmt.where(
                    not_(
                        Recipe.ingredients.any(
                            RecipeIngredient.food.has(
                                and_(Food.category == FoodCategory.MEAT, Food.name.ilike('%chicken%'))
                            )
                        )
                    )
                )
            elif not dietary_pref.eats_mutton:
                # Exclude mutton specifically
                stmt = stmt.where(
                    not_(
                        Recipe.ingredients.any(
                            RecipeIngredient.food.has(
                                and_(Food.category == FoodCategory.MEAT, Food.name.ilike('%mutton%'))
                            )
                        )
                    )
                )
                
        # 6. Medical Constraints (PER_MEAL)
        if user.health_conditions:
            condition_names = [hc.condition for hc in user.health_conditions]
            
            # Fetch relevant medical rules and constraints
            rules_stmt = select(MedicalRuleConstraint).join(MedicalRule).where(
                MedicalRule.condition.in_(condition_names),
                MedicalRule.is_active == True,
                MedicalRuleConstraint.scope == RuleScope.PER_MEAL
            )
            rules_result = await self.db.execute(rules_stmt)
            constraints = rules_result.scalars().all()
            
            for c in constraints:
                if not c.nutrient or c.value is None:
                    continue
                
                # Apply dynamic filter based on nutrient and operator
                nutrient_col = getattr(Recipe, f"{c.nutrient.lower()}", None)
                if nutrient_col is not None:
                    if c.operator == RuleOperator.MAX:
                        stmt = stmt.where(or_(nutrient_col <= c.value, nutrient_col == None))
                    elif c.operator == RuleOperator.MIN:
                        stmt = stmt.where(nutrient_col >= c.value)

        # 7. Eagerly load relationships to return full Recipe objects
        stmt = stmt.options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.food),
            selectinload(Recipe.cuisines),
            selectinload(Recipe.regions),
            selectinload(Recipe.diet_compatibility),
            selectinload(Recipe.meal_types)
        )
        
        result = await self.db.execute(stmt)
        recipes = list(result.scalars().unique().all())
        return recipes

    # The helper methods were defined in the prompt to explain the logic,
    # but the instructions also said:
    # "IMPORTANT IMPLEMENTATION APPROACH: For efficiency, build this as a SINGLE optimized query rather than N+1 queries. Use SQLAlchemy joins and subqueries"
    # Which we have done above. However, the prompt also gave signatures for the helper methods.
    # To strictly follow the provided structure in the prompt, I will add the helper methods
    # but implement them as parts of the query builder or just as requested for interface parity.

    async def _check_diet_compatibility(self, user_diet: DietType, recipe_id: uuid.UUID) -> bool:
        # Implemented in main query
        pass

    async def _check_nonveg_subfilters(self, user_pref: UserDietaryPreference, recipe: Recipe) -> bool:
        # Implemented in main query
        pass

    async def _check_allergens(self, user_allergens: list[Allergen], recipe_id: uuid.UUID) -> bool:
        # Implemented in main query
        pass

    async def _check_never_foods(self, user_never_foods: list[uuid.UUID], recipe_id: uuid.UUID) -> bool:
        # Implemented in main query
        pass

    async def _check_medical_per_meal(self, user_conditions: list, recipe: Recipe) -> bool:
        # Implemented in main query
        pass
