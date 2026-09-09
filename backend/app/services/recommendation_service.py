import uuid
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.recipe import Recipe
from app.models.user import User
from app.models.enums import PreferenceType, Cuisine, RuleScope, RuleOperator
from app.models.medical_rule import MedicalRule, MedicalRuleConstraint
from app.models.health import UserHealthCondition
from app.core.scoring_config import DEFAULT_SCORING_WEIGHTS

@dataclass
class ScoredRecipe:
    recipe: Recipe
    scores: Dict[str, float]
    total_score: float

class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def score_recipes(
        self,
        recipes: List[Recipe],
        user_id: uuid.UUID,
        meal_type: str,
        daily_targets: dict,  # from NutritionService.calculate_full_targets
        weekly_context: Optional[dict] = None,  # Already selected meals this week
        weights: Optional[dict] = None  # Override scoring weights
    ) -> List[ScoredRecipe]:
        if not recipes:
            return []

        scoring_weights = weights if weights else DEFAULT_SCORING_WEIGHTS

        # 1. Load user preferences for scoring
        user_query = select(User).where(User.id == user_id).options(
            selectinload(User.profile),
            selectinload(User.food_preferences),
            selectinload(User.cuisine_preferences),
            selectinload(User.available_ingredients),
            selectinload(User.health_conditions)
        )
        result = await self.db.execute(user_query)
        user = result.scalar_one_or_none()
        if not user:
            return []

        # Extract useful pre-computed maps
        user_food_prefs = {fp.food_id: fp.preference for fp in user.food_preferences}
        user_cuisine_prefs = {cp.cuisine: cp.preference_strength for cp in user.cuisine_preferences}
        user_pantry = {ing.food_id: float(ing.quantity_g) for ing in user.available_ingredients}
        
        user_state = user.profile.state_code if user.profile else None
        per_meal_budget = float(user.profile.weekly_grocery_limit / 21) if user.profile and user.profile.weekly_grocery_limit else 100.0 # Placeholder calculation
        user_max_prep_time = user.profile.max_prep_time_min if user.profile and user.profile.max_prep_time_min else 60

        # Load medical rules for soft scoring
        medical_rules = []
        if user.health_conditions:
            condition_names = [hc.condition for hc in user.health_conditions]
            rules_stmt = select(MedicalRule).where(
                MedicalRule.condition.in_(condition_names),
                MedicalRule.is_active == True
            ).options(selectinload(MedicalRule.constraints))
            rules_result = await self.db.execute(rules_stmt)
            medical_rules = list(rules_result.scalars().all())

        # Extract weekly context
        weekly_ingredients: Set[uuid.UUID] = set()
        recently_used_recipes: Set[uuid.UUID] = set()
        if weekly_context:
            weekly_ingredients = set(weekly_context.get("ingredients", []))
            recently_used_recipes = set(weekly_context.get("recipe_ids", []))

        # Target mapping for meal
        meal_targets = daily_targets.get(meal_type, {})

        scored_recipes = []
        for recipe in recipes:
            scores = {}

            # Calculate individual scores
            scores["nutrition_fit"] = self._score_nutrition_fit(recipe, meal_targets)
            scores["budget_efficiency"] = self._score_budget_efficiency(recipe, per_meal_budget)
            scores["food_preference"] = self._score_food_preference(recipe, user_food_prefs)
            scores["cuisine_preference"] = self._score_cuisine_preference([c.cuisine for c in recipe.cuisines], user_cuisine_prefs)
            scores["regional_relevance"] = self._score_regional_relevance(recipe.regions, user_state)
            
            # Placeholder for local_availability
            scores["local_availability"] = 0.5 
            
            scores["ingredient_reuse"] = self._score_ingredient_reuse(recipe, weekly_ingredients)
            scores["prep_time_fit"] = self._score_prep_time_fit(recipe.prep_time_min or 30, user_max_prep_time)
            scores["pantry_overlap"] = self._score_pantry_overlap(recipe, user_pantry)
            scores["variety"] = self._score_variety(recipe, recently_used_recipes)
            scores["medical_fit"] = self._score_medical_fit(recipe, medical_rules, scope=RuleScope.PER_DAY)
            scores["protein_source_rotation"] = 0.5  # Placeholder

            # Calculate total weighted score
            total = 0.0
            weight_sum = 0.0
            for dimension, score in scores.items():
                if dimension in scoring_weights:
                    weight = scoring_weights[dimension]
                    total += score * weight
                    weight_sum += weight
            
            total_score = (total / weight_sum) * 100 if weight_sum > 0 else 0.0

            scored_recipes.append(ScoredRecipe(
                recipe=recipe,
                scores=scores,
                total_score=total_score
            ))

        # Sort by total_score descending
        scored_recipes.sort(key=lambda x: x.total_score, reverse=True)
        return scored_recipes

    def _score_nutrition_fit(self, recipe: Recipe, meal_targets: dict) -> float:
        target_cal = meal_targets.get("calories", 500)
        target_pro = meal_targets.get("protein_g", 20)
        
        cal = float(recipe.calories) if recipe.calories else target_cal
        pro = float(recipe.protein_g) if recipe.protein_g else target_pro

        calorie_fit = 1.0 - min(1.0, abs(cal - target_cal) / target_cal if target_cal else 0)
        protein_fit = 1.0 - min(1.0, abs(pro - target_pro) / target_pro if target_pro else 0)
        
        macro_balance = 0.8 # Placeholder for macro balance calculation
        
        return float(calorie_fit * 0.5 + protein_fit * 0.3 + macro_balance * 0.2)

    def _score_budget_efficiency(self, recipe: Recipe, per_meal_budget: float) -> float:
        cost = float(recipe.estimated_cost) if recipe.estimated_cost else 0
        if cost == 0 or per_meal_budget == 0:
            return 0.5
            
        ratio = cost / per_meal_budget
        if ratio < 0.5:
            return 0.7  # Suspiciously cheap penalty
        elif 0.5 <= ratio <= 0.9:
            return 1.0  # Sweet spot
        elif ratio <= 1.0:
            return 0.8
        else:
            return max(0.0, 1.0 - (ratio - 1.0)) # Drops off as it gets more expensive

    def _score_food_preference(self, recipe: Recipe, user_food_prefs: Dict[uuid.UUID, PreferenceType]) -> float:
        if not recipe.ingredients:
            return 0.5
            
        score = 0.5
        for ing in recipe.ingredients:
            pref = user_food_prefs.get(ing.food_id)
            if pref == PreferenceType.LIKE:
                score += 0.1
            elif pref == PreferenceType.DISLIKE:
                score -= 0.1
        return max(0.0, min(1.0, score))

    def _score_cuisine_preference(self, recipe_cuisines: List[Cuisine], user_cuisine_prefs: Dict[Cuisine, float]) -> float:
        if not recipe_cuisines:
            return 0.1
            
        max_score = 0.1
        for c in recipe_cuisines:
            strength = float(user_cuisine_prefs.get(c, 0.1))
            if strength > max_score:
                max_score = strength
        return max_score

    def _score_regional_relevance(self, recipe_regions: list, user_state: Optional[str]) -> float:
        if not user_state or not recipe_regions:
            return 0.2
            
        for region in recipe_regions:
            if region.state_code == user_state:
                return float(region.relevance_score) if region.relevance_score else 0.8
        return 0.2

    def _score_local_availability(self, recipe_ingredients: list, user_state: str, food_regions: dict) -> float:
        # Placeholder implementation
        return 0.5

    def _score_ingredient_reuse(self, recipe: Recipe, weekly_ingredients: Set[uuid.UUID]) -> float:
        if not weekly_ingredients or not recipe.ingredients:
            return 0.0
            
        overlap = sum(1 for ing in recipe.ingredients if ing.food_id in weekly_ingredients)
        return min(1.0, overlap / len(recipe.ingredients))

    def _score_prep_time_fit(self, recipe_prep_time: int, user_max_prep_time: int) -> float:
        if recipe_prep_time <= user_max_prep_time:
            return 1.0
        return max(0.0, 1.0 - ((recipe_prep_time - user_max_prep_time) / 30.0))

    def _score_pantry_overlap(self, recipe: Recipe, user_pantry: Dict[uuid.UUID, float]) -> float:
        if not recipe.ingredients or not user_pantry:
            return 0.0
            
        overlap = sum(1 for ing in recipe.ingredients if ing.food_id in user_pantry)
        return overlap / len(recipe.ingredients)

    def _score_variety(self, recipe: Recipe, recently_used_recipes: Set[uuid.UUID]) -> float:
        if recipe.id in recently_used_recipes:
            return 0.0
        return 1.0

    def _score_medical_fit(self, recipe: Recipe, medical_rules: list, scope: RuleScope = RuleScope.PER_DAY) -> float:
        score = 1.0
        for rule in medical_rules:
            for constraint in rule.constraints:
                if constraint.scope == scope and constraint.nutrient:
                    val = getattr(recipe, constraint.nutrient.lower(), None)
                    if val is not None and constraint.value is not None:
                        # Simple soft penalty if over MAX or under MIN
                        if constraint.operator == RuleOperator.MAX and float(val) > float(constraint.value):
                            score -= 0.2
                        elif constraint.operator == RuleOperator.MIN and float(val) < float(constraint.value):
                            score -= 0.2
        return max(0.0, score)
