import uuid
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload

from app.models.meal_plan import MealPlan, MealPlanMeal, MealOption, MealHistory
from app.models.recipe import Recipe
from app.models.user import User
from app.models.enums import MealType, OptionType, MealAction, MealPlanStatus

from app.services.constraint_service import ConstraintService
from app.services.recommendation_service import RecommendationService
from app.services.nutrition_service import NutritionService
from app.services.price_service import PriceService
from app.services.grocery_service import GroceryService

class MealPlanService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.constraint_service = ConstraintService(db)
        self.recommendation_service = RecommendationService(db)
        self.nutrition_service = NutritionService()
        self.price_service = PriceService(db)
        self.grocery_service = GroceryService(db)
    
    async def generate_meal_plan(
        self, user_id: uuid.UUID, week_start_date: date | None = None
    ) -> MealPlan:
        """Generate a complete 7-day meal plan with 3 meals/day and 3 options/meal."""
        if week_start_date is None:
            week_start_date = date.today()
            
        # 1. Load user profile + calculate nutrition targets
        user_query = select(User).where(User.id == user_id).options(
            selectinload(User.profile),
            selectinload(User.health_conditions)
        )
        result = await self.db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user or not user.profile:
            raise ValueError("User profile not found")
            
        profile = user.profile
        daily_targets = self.nutrition_service.calculate_full_targets(
            weight_kg=float(profile.weight_kg) if profile.weight_kg else 70.0,
            height_cm=float(profile.height_cm) if profile.height_cm else 170.0,
            age=profile.age if profile.age else 30,
            gender=profile.gender.value if profile.gender else "MALE",
            activity_level=profile.activity_level.value if profile.activity_level else "SEDENTARY",
            health_goal=profile.health_goal.value if profile.health_goal else "MAINTAIN_WEIGHT"
        )
        
        weekly_limit = float(profile.weekly_grocery_limit) if profile.weekly_grocery_limit else 100.0
        per_meal_budget = self._calculate_per_meal_budget(weekly_limit)
        
        # Deactivate existing active meal plans
        await self._deactivate_old_plans(user_id)
        
        # Create new MealPlan
        meal_plan = MealPlan(
            id=uuid.uuid4(),
            user_id=user_id,
            week_start_date=week_start_date,
            cost_currency="INR", # Default
            status=MealPlanStatus.ACTIVE,
            created_at=datetime.utcnow()
        )
        self.db.add(meal_plan)
        
        weekly_context = {
            "ingredients": [],
            "recipe_ids": []
        }
        
        # 2. For each day (1-7)
        for day in range(1, 8):
            for meal_type_str in ["BREAKFAST", "LUNCH", "DINNER"]:
                meal_type = MealType[meal_type_str]
                
                # a. Get eligible recipes
                eligible_recipes = await self.constraint_service.get_eligible_recipes(
                    user_id=user_id,
                    meal_type=meal_type_str,
                    exclude_recipe_ids=weekly_context["recipe_ids"]
                )
                
                if not eligible_recipes:
                    # Try without exclusion if needed
                    eligible_recipes = await self.constraint_service.get_eligible_recipes(
                        user_id=user_id,
                        meal_type=meal_type_str
                    )
                    
                # b. Score recipes
                scored_recipes = await self.recommendation_service.score_recipes(
                    recipes=eligible_recipes,
                    user_id=user_id,
                    meal_type=meal_type_str,
                    daily_targets=daily_targets.get("per_meal", {}),
                    weekly_context=weekly_context
                )
                
                if not scored_recipes:
                    continue # Handle empty case gracefully
                
                # c. Select top 3 options
                best_option = scored_recipes[0]
                
                budget_options = [sr for sr in scored_recipes if float(sr.recipe.estimated_cost or 0) <= per_meal_budget[meal_type_str]]
                budget_option = budget_options[0] if budget_options else best_option
                
                variety_option = self._select_variety_option(scored_recipes, best_option.recipe, set(weekly_context["ingredients"]))
                if not variety_option:
                    variety_option = best_option
                    
                # d. Create MealPlanMeal + 3 MealOptions
                meal_plan_meal = MealPlanMeal(
                    id=uuid.uuid4(),
                    meal_plan_id=meal_plan.id,
                    day_of_week=day,
                    meal_type=meal_type,
                    selected_recipe_id=best_option.recipe.id
                )
                self.db.add(meal_plan_meal)
                
                self.db.add(MealOption(id=uuid.uuid4(), meal_plan_meal_id=meal_plan_meal.id, recipe_id=best_option.recipe.id, option_type=OptionType.BEST, score=best_option.total_score))
                if budget_option.recipe.id != best_option.recipe.id:
                    self.db.add(MealOption(id=uuid.uuid4(), meal_plan_meal_id=meal_plan_meal.id, recipe_id=budget_option.recipe.id, option_type=OptionType.BUDGET, score=budget_option.total_score))
                if variety_option.recipe.id not in [best_option.recipe.id, budget_option.recipe.id]:
                    self.db.add(MealOption(id=uuid.uuid4(), meal_plan_meal_id=meal_plan_meal.id, recipe_id=variety_option.recipe.id, option_type=OptionType.VARIETY, score=variety_option.total_score))
                    
                # f. Update weekly_context
                weekly_context["recipe_ids"].append(best_option.recipe.id)
                for ing in best_option.recipe.ingredients:
                    weekly_context["ingredients"].append(ing.food_id)
        
        await self.db.commit()
        await self.db.refresh(meal_plan)
        
        # 4, 5, 7. Check budget, recalculate, generate grocery list
        await self.grocery_service.generate_shopping_list(meal_plan.id, user_id)
        await self._recalculate_plan_costs(meal_plan.id)
        
        # Fetch fully loaded
        return await self.get_active_meal_plan(user_id)
        
    async def replace_meal(
        self, meal_plan_meal_id: uuid.UUID, user_id: uuid.UUID, reason: str,
        exclude_recipe_ids: list[uuid.UUID] | None = None
    ) -> MealPlanMeal:
        meal_query = select(MealPlanMeal).where(MealPlanMeal.id == meal_plan_meal_id).options(
            selectinload(MealPlanMeal.meal_plan),
            selectinload(MealPlanMeal.options)
        )
        result = await self.db.execute(meal_query)
        meal_plan_meal = result.scalar_one_or_none()
        
        if not meal_plan_meal:
            raise ValueError("Meal slot not found")
            
        current_recipe_id = meal_plan_meal.selected_recipe_id
        excludes = (exclude_recipe_ids or []) + [current_recipe_id] if current_recipe_id else exclude_recipe_ids or []
        
        # Find user targets
        user_query = select(User).where(User.id == user_id).options(
            selectinload(User.profile)
        )
        user_res = await self.db.execute(user_query)
        user = user_res.scalar_one()
        profile = user.profile
        
        daily_targets = self.nutrition_service.calculate_full_targets(
            weight_kg=float(profile.weight_kg) if profile.weight_kg else 70.0,
            height_cm=float(profile.height_cm) if profile.height_cm else 170.0,
            age=profile.age if profile.age else 30,
            gender=profile.gender.value if profile.gender else "MALE",
            activity_level=profile.activity_level.value if profile.activity_level else "SEDENTARY",
            health_goal=profile.health_goal.value if profile.health_goal else "MAINTAIN_WEIGHT"
        )
        
        weekly_limit = float(profile.weekly_grocery_limit) if profile.weekly_grocery_limit else 100.0
        per_meal_budget = self._calculate_per_meal_budget(weekly_limit)
        
        weights = None
        if reason == "use_pantry":
            weights = {"pantry_overlap": 2.0} # Boost
            
        eligible_recipes = await self.constraint_service.get_eligible_recipes(
            user_id=user_id,
            meal_type=meal_plan_meal.meal_type.name,
            exclude_recipe_ids=excludes
        )
        
        # Get weekly context
        weekly_context = await self._build_weekly_context(meal_plan_meal.meal_plan_id)
        
        scored_recipes = await self.recommendation_service.score_recipes(
            recipes=eligible_recipes,
            user_id=user_id,
            meal_type=meal_plan_meal.meal_type.name,
            daily_targets=daily_targets.get("per_meal", {}),
            weekly_context=weekly_context,
            weights=weights
        )
        
        if not scored_recipes:
            return meal_plan_meal
            
        # Delete old options
        await self.db.execute(delete(MealOption).where(MealOption.meal_plan_meal_id == meal_plan_meal.id))
        
        best_option = scored_recipes[0]
        budget_options = [sr for sr in scored_recipes if float(sr.recipe.estimated_cost or 0) <= per_meal_budget[meal_plan_meal.meal_type.name]]
        budget_option = budget_options[0] if budget_options else best_option
        variety_option = self._select_variety_option(scored_recipes, best_option.recipe, set(weekly_context["ingredients"]))
        if not variety_option:
            variety_option = best_option
            
        meal_plan_meal.selected_recipe_id = best_option.recipe.id
        self.db.add(MealOption(id=uuid.uuid4(), meal_plan_meal_id=meal_plan_meal.id, recipe_id=best_option.recipe.id, option_type=OptionType.BEST, score=best_option.total_score))
        if budget_option.recipe.id != best_option.recipe.id:
            self.db.add(MealOption(id=uuid.uuid4(), meal_plan_meal_id=meal_plan_meal.id, recipe_id=budget_option.recipe.id, option_type=OptionType.BUDGET, score=budget_option.total_score))
        if variety_option.recipe.id not in [best_option.recipe.id, budget_option.recipe.id]:
            self.db.add(MealOption(id=uuid.uuid4(), meal_plan_meal_id=meal_plan_meal.id, recipe_id=variety_option.recipe.id, option_type=OptionType.VARIETY, score=variety_option.total_score))
        
        history = MealHistory(
            id=uuid.uuid4(),
            user_id=user_id,
            recipe_id=best_option.recipe.id,
            meal_plan_meal_id=meal_plan_meal.id,
            action=MealAction.EATEN, # Placeholder for replacement action
            replacement_reason=reason,
            created_at=datetime.utcnow()
        )
        self.db.add(history)
        
        await self.db.commit()
        await self.grocery_service.generate_shopping_list(meal_plan_meal.meal_plan_id, user_id)
        await self._recalculate_plan_costs(meal_plan_meal.meal_plan_id)
        
        await self.db.refresh(meal_plan_meal)
        
        return await self._get_full_meal_plan_meal(meal_plan_meal.id)
    
    async def select_option(
        self, meal_plan_meal_id: uuid.UUID, user_id: uuid.UUID, recipe_id: uuid.UUID
    ) -> MealPlanMeal:
        meal_query = select(MealPlanMeal).where(MealPlanMeal.id == meal_plan_meal_id)
        result = await self.db.execute(meal_query)
        meal_plan_meal = result.scalar_one_or_none()
        if not meal_plan_meal:
            raise ValueError("Meal slot not found")
            
        meal_plan_meal.selected_recipe_id = recipe_id
        await self.db.commit()
        
        await self.grocery_service.generate_shopping_list(meal_plan_meal.meal_plan_id, user_id)
        await self._recalculate_plan_costs(meal_plan_meal.meal_plan_id)
        
        return await self._get_full_meal_plan_meal(meal_plan_meal.id)
    
    async def record_meal_action(
        self, meal_plan_meal_id: uuid.UUID, user_id: uuid.UUID, action: str
    ) -> None:
        meal_query = select(MealPlanMeal).where(MealPlanMeal.id == meal_plan_meal_id)
        result = await self.db.execute(meal_query)
        meal_plan_meal = result.scalar_one_or_none()
        if not meal_plan_meal:
            raise ValueError("Meal slot not found")
            
        action_enum = MealAction[action.upper()]
        
        history = MealHistory(
            id=uuid.uuid4(),
            user_id=user_id,
            recipe_id=meal_plan_meal.selected_recipe_id,
            meal_plan_meal_id=meal_plan_meal.id,
            action=action_enum,
            created_at=datetime.utcnow()
        )
        self.db.add(history)
        await self.db.commit()
    
    async def get_active_meal_plan(self, user_id: uuid.UUID) -> MealPlan | None:
        stmt = select(MealPlan).where(
            MealPlan.user_id == user_id,
            MealPlan.status == MealPlanStatus.ACTIVE
        ).options(
            selectinload(MealPlan.meals).selectinload(MealPlanMeal.options).selectinload(MealOption.recipe),
            selectinload(MealPlan.meals).selectinload(MealPlanMeal.selected_recipe)
        ).order_by(MealPlan.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().first()
        
    async def _get_full_meal_plan_meal(self, meal_plan_meal_id: uuid.UUID) -> MealPlanMeal:
        stmt = select(MealPlanMeal).where(MealPlanMeal.id == meal_plan_meal_id).options(
            selectinload(MealPlanMeal.options).selectinload(MealOption.recipe),
            selectinload(MealPlanMeal.selected_recipe)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one()
    
    def _calculate_per_meal_budget(self, weekly_limit: float) -> dict[str, float]:
        daily_budget = weekly_limit / 7.0
        return {
            "BREAKFAST": daily_budget * 0.20,
            "LUNCH": daily_budget * 0.40,
            "DINNER": daily_budget * 0.40
        }
    
    def _select_variety_option(
        self, scored_recipes: list, best_recipe: Recipe, weekly_ingredients: set
    ) -> Optional[Recipe]:
        best_ingredients = set(ing.food_id for ing in best_recipe.ingredients) if best_recipe.ingredients else set()
        
        variety_option = None
        best_variety_score = -1.0
        
        for sr in scored_recipes:
            if sr.recipe.id == best_recipe.id:
                continue
                
            ingredients = set(ing.food_id for ing in sr.recipe.ingredients) if sr.recipe.ingredients else set()
            overlap = len(ingredients.intersection(best_ingredients))
            overlap_penalty = overlap * 0.1 # Arbitrary penalty
            
            variety_score = sr.total_score - overlap_penalty
            if variety_score > best_variety_score:
                best_variety_score = variety_score
                variety_option = sr
                
        return variety_option
        
    async def _deactivate_old_plans(self, user_id: uuid.UUID):
        stmt = select(MealPlan).where(MealPlan.user_id == user_id, MealPlan.status == MealPlanStatus.ACTIVE)
        res = await self.db.execute(stmt)
        for plan in res.scalars():
            plan.status = MealPlanStatus.ARCHIVED
        await self.db.commit()
        
    async def _build_weekly_context(self, meal_plan_id: uuid.UUID) -> dict:
        stmt = select(MealPlanMeal).where(MealPlanMeal.meal_plan_id == meal_plan_id).options(
            selectinload(MealPlanMeal.selected_recipe).selectinload(Recipe.ingredients)
        )
        res = await self.db.execute(stmt)
        meals = res.scalars().all()
        
        ingredients = []
        recipe_ids = []
        for m in meals:
            if m.selected_recipe_id:
                recipe_ids.append(m.selected_recipe_id)
            if m.selected_recipe and m.selected_recipe.ingredients:
                for ing in m.selected_recipe.ingredients:
                    ingredients.append(ing.food_id)
        
        return {
            "ingredients": ingredients,
            "recipe_ids": recipe_ids
        }
        
    async def _recalculate_plan_costs(self, meal_plan_id: uuid.UUID):
        from app.models.grocery import ShoppingList
        
        plan_stmt = select(MealPlan).where(MealPlan.id == meal_plan_id)
        res = await self.db.execute(plan_stmt)
        plan = res.scalar_one()
        
        shop_stmt = select(ShoppingList).where(ShoppingList.meal_plan_id == meal_plan_id)
        shop_res = await self.db.execute(shop_stmt)
        shop_list = shop_res.scalar_one_or_none()
        
        if shop_list:
            plan.total_consumed_cost = shop_list.consumed_cost
            plan.total_purchase_cost = shop_list.actual_shopping_cost
            
        await self.db.commit()
