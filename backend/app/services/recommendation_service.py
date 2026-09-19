import uuid
from typing import List, Dict, Set, Optional, Any
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

        # Extract nutrient profile data for scoring
        nutrient_profile_micros = weekly_context.get("nutrient_profile_micros") if weekly_context else None
        daily_nutrients_so_far = weekly_context.get("daily_nutrients_so_far") if weekly_context else None
        weekly_protein_sources = set(weekly_context.get("protein_sources", [])) if weekly_context else None
        meal_split = {"BREAKFAST": 0.25, "LUNCH": 0.40, "DINNER": 0.35}.get(meal_type, 0.33)

        scored_recipes = []
        for recipe in recipes:
            scores = {}

            # Calculate individual scores - ALL 14 dimensions with real calculations
            scores["nutrition_fit"] = self._score_nutrition_fit(recipe, meal_targets)
            scores["nutrient_coverage"] = self._score_nutrient_coverage(
                recipe, meal_targets, nutrient_profile_micros, meal_split,
            )
            scores["nutrient_gap_fill"] = self._score_nutrient_gap_fill(
                recipe, daily_nutrients_so_far, nutrient_profile_micros,
            )
            scores["budget_efficiency"] = self._score_budget_efficiency(recipe, per_meal_budget)
            scores["food_preference"] = self._score_food_preference(recipe, user_food_prefs)
            scores["cuisine_preference"] = self._score_cuisine_preference(
                [c.cuisine for c in recipe.cuisines], user_cuisine_prefs,
            )
            scores["regional_relevance"] = self._score_regional_relevance(recipe.regions, user_state)
            scores["local_availability"] = self._score_local_availability(recipe, user_state)
            scores["ingredient_reuse"] = self._score_ingredient_reuse(recipe, weekly_ingredients)
            scores["prep_time_fit"] = self._score_prep_time_fit(recipe.prep_time_min or 30, user_max_prep_time)
            scores["pantry_overlap"] = self._score_pantry_overlap(recipe, user_pantry)
            scores["variety"] = self._score_variety(recipe, recently_used_recipes)
            scores["medical_fit"] = self._score_medical_fit(recipe, medical_rules, scope=RuleScope.PER_DAY)
            scores["protein_source_rotation"] = self._score_protein_source_rotation(
                recipe, weekly_protein_sources,
            )

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
        target_carbs = meal_targets.get("carbs_g", 60)
        target_fat = meal_targets.get("fat_g", 15)
        
        cal = float(recipe.calories) if recipe.calories else target_cal
        pro = float(recipe.protein_g) if recipe.protein_g else target_pro
        carbs = float(recipe.carbs_g) if recipe.carbs_g else target_carbs
        fat = float(recipe.fat_g) if recipe.fat_g else target_fat

        calorie_fit = 1.0 - min(1.0, abs(cal - target_cal) / target_cal if target_cal else 0)
        protein_fit = 1.0 - min(1.0, abs(pro - target_pro) / target_pro if target_pro else 0)
        
        # Calculate actual macro balance against user's targets
        carb_fit = 1.0 - min(1.0, abs(carbs - target_carbs) / target_carbs if target_carbs else 0)
        fat_fit = 1.0 - min(1.0, abs(fat - target_fat) / target_fat if target_fat else 0)
        macro_balance = (carb_fit + fat_fit) / 2.0
        
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

    def _score_local_availability(
        self,
        recipe: Recipe,
        user_state: Optional[str],
    ) -> float:
        """Score based on regional availability of recipe ingredients.
        
        Uses existing recipe.regions and ingredient food.regions data.
        Available locally -> high. Unknown -> neutral. No data -> low-confidence neutral.
        """
        if not recipe.ingredients:
            return 0.5  # No ingredients, can't assess
        
        if not user_state:
            return 0.5  # No location, can't assess
        
        available_count = 0
        total_count = len(recipe.ingredients)
        
        for ing in recipe.ingredients:
            food = ing.food if hasattr(ing, 'food') and ing.food else None
            if food and hasattr(food, 'regions') and food.regions:
                # Check if food has regional availability for user's state
                for region in food.regions:
                    if hasattr(region, 'state_code') and region.state_code == user_state:
                        available_count += 1
                        break
                else:
                    # Food exists but not confirmed in user's region
                    available_count += 0.3  # Partial credit for having data
            else:
                # No regional data at all - neutral
                available_count += 0.5
        
        return min(1.0, available_count / total_count) if total_count > 0 else 0.5

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

    def _score_nutrient_coverage(
        self,
        recipe: Recipe,
        meal_targets: dict,
        nutrient_profile_micros: Optional[Dict[str, Any]] = None,
        meal_split: float = 0.33,
    ) -> float:
        """How well does this recipe contribute to daily nutrient needs?
        
        Evaluates both macro coverage (from meal_targets) and micro coverage
        (from nutrient_profile_micros). This is a SCORING dimension, not a constraint.
        """
        if not nutrient_profile_micros:
            return 0.5  # No micro data available, neutral score
        
        # Check how many micronutrients this recipe meaningfully contributes to
        micro_nutrients = [
            ("calcium_mg", getattr(recipe, 'calcium_mg', None)),
            ("iron_mg", getattr(recipe, 'iron_mg', None)),
            ("magnesium_mg", getattr(recipe, 'magnesium_mg', None)),
            ("potassium_mg", getattr(recipe, 'potassium_mg', None)),
            ("zinc_mg", getattr(recipe, 'zinc_mg', None)),
            ("vitamin_a_mcg", getattr(recipe, 'vitamin_a_mcg', None)),
            ("vitamin_b12_mcg", getattr(recipe, 'vitamin_b12_mcg', None)),
            ("vitamin_c_mg", getattr(recipe, 'vitamin_c_mg', None)),
            ("vitamin_d_mcg", getattr(recipe, 'vitamin_d_mcg', None)),
            ("folate_mcg", getattr(recipe, 'folate_mcg', None)),
            ("phosphorus_mg", getattr(recipe, 'phosphorus_mg', None)),
        ]
        
        covered_count = 0
        total_count = 0
        
        for nutrient_name, recipe_val in micro_nutrients:
            target_info = nutrient_profile_micros.get(nutrient_name)
            if not target_info:
                continue
            
            daily_target = target_info.get("target", 0) if isinstance(target_info, dict) else getattr(target_info, 'target', 0)
            if daily_target <= 0:
                continue
            
            total_count += 1
            meal_target = daily_target * meal_split
            
            if recipe_val is not None and float(recipe_val) > 0:
                contribution_pct = float(recipe_val) / meal_target if meal_target > 0 else 0
                # Reward recipes that contribute meaningfully (>= 20% of meal target)
                if contribution_pct >= 0.5:
                    covered_count += 1
                elif contribution_pct >= 0.2:
                    covered_count += 0.5
        
        if total_count == 0:
            return 0.5
        
        return min(1.0, covered_count / total_count)

    def _score_nutrient_gap_fill(
        self,
        recipe: Recipe,
        daily_nutrients_so_far: Optional[Dict[str, float]] = None,
        nutrient_profile_micros: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Does this recipe fill nutrient gaps from earlier meals today?
        
        If earlier meals already covered protein, but calcium is low,
        a calcium-rich recipe scores higher than another protein-heavy one.
        """
        if not daily_nutrients_so_far or not nutrient_profile_micros:
            return 0.5  # No context, neutral
        
        # Find which nutrients are currently most under-covered
        gaps = []
        for nutrient_name, target_info in nutrient_profile_micros.items():
            daily_target = target_info.get("target", 0) if isinstance(target_info, dict) else getattr(target_info, 'target', 0)
            if daily_target <= 0:
                continue
            
            consumed = daily_nutrients_so_far.get(nutrient_name, 0)
            coverage_pct = consumed / daily_target if daily_target > 0 else 1.0
            gap = max(0, 1.0 - coverage_pct)  # 0 = fully covered, 1 = nothing consumed
            gaps.append((nutrient_name, gap))
        
        if not gaps:
            return 0.5
        
        # Score: how well does this recipe fill the biggest gaps?
        gap_fill_score = 0.0
        total_gap_weight = 0.0
        
        for nutrient_name, gap in gaps:
            if gap <= 0:
                continue  # Already fully covered
            
            recipe_val = getattr(recipe, nutrient_name, None)
            if recipe_val is None or float(recipe_val) <= 0:
                continue
            
            target_info = nutrient_profile_micros[nutrient_name]
            daily_target = target_info.get("target", 0) if isinstance(target_info, dict) else getattr(target_info, 'target', 0)
            
            if daily_target <= 0:
                continue
            
            # How much of the gap does this recipe fill?
            fill_pct = float(recipe_val) / (daily_target * gap) if (daily_target * gap) > 0 else 0
            fill_pct = min(fill_pct, 1.0)
            
            # Weight by the size of the gap (bigger gaps matter more)
            gap_fill_score += fill_pct * gap
            total_gap_weight += gap
        
        if total_gap_weight == 0:
            return 0.8  # Everything already covered, mild positive
        
        return min(1.0, gap_fill_score / total_gap_weight)

    def _score_protein_source_rotation(
        self,
        recipe: Recipe,
        weekly_protein_sources: Optional[set] = None,
    ) -> float:
        """Score diversity of protein sources across the week.
        
        Mon:eggs, Tue:chicken, Wed:dal, Thu:paneer, Fri:fish = HIGH rotation
        Mon:chicken, Tue:chicken, Wed:chicken = LOW rotation
        
        This is a soft diversity preference, not a medical constraint.
        """
        if not recipe.ingredients:
            return 0.5
        
        if weekly_protein_sources is None:
            return 0.5  # First meal of the week, no context
        
        # Identify protein-rich ingredients in this recipe
        recipe_protein_sources = set()
        for ing in recipe.ingredients:
            food = ing.food if hasattr(ing, 'food') and ing.food else None
            if food:
                # Check if food is protein-rich (>= 10g protein per 100g)
                protein_per_100g = getattr(food, 'protein_per_100g', None)
                if protein_per_100g is not None and float(protein_per_100g) >= 10:
                    # Use food category or name as the protein "source"
                    source_key = getattr(food, 'category', None) or getattr(food, 'name', 'unknown')
                    recipe_protein_sources.add(str(source_key))
        
        if not recipe_protein_sources:
            return 0.5  # No significant protein sources, neutral
        
        if not weekly_protein_sources:
            return 1.0  # First protein source this week, maximum diversity
        
        # How many of this recipe's protein sources are already used this week?
        already_used = recipe_protein_sources & weekly_protein_sources
        new_sources = recipe_protein_sources - weekly_protein_sources
        
        if new_sources:
            return 1.0  # Introduces a new protein source
        elif already_used:
            # All protein sources already used, penalize based on how many total exist
            diversity = len(weekly_protein_sources)
            # If we've already used 5+ different sources, repeating is less bad
            if diversity >= 5:
                return 0.6
            elif diversity >= 3:
                return 0.4
            else:
                return 0.2  # Low diversity, penalize repeat
        
        return 0.5
