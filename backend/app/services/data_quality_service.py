from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.models.food import Food, FoodPrice
from app.models.recipe import Recipe
from app.models.enums import NutritionConfidence


# All 18 nutrients tracked in the system
ALL_FOOD_NUTRIENTS = [
    "calories_per_100g", "protein_per_100g", "carbs_per_100g", "fat_per_100g",
    "fiber_per_100g", "sodium_per_100g",
    "calcium_mg_per_100g", "iron_mg_per_100g", "magnesium_mg_per_100g",
    "potassium_mg_per_100g", "zinc_mg_per_100g", "vitamin_a_mcg_per_100g",
    "vitamin_b12_mcg_per_100g", "vitamin_c_mg_per_100g", "vitamin_d_mcg_per_100g",
    "folate_mcg_per_100g", "phosphorus_mg_per_100g", "sugar_g_per_100g",
]

ALL_RECIPE_NUTRIENTS = [
    "calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sodium_mg",
    "calcium_mg", "iron_mg", "magnesium_mg", "potassium_mg", "zinc_mg",
    "vitamin_a_mcg", "vitamin_b12_mcg", "vitamin_c_mg", "vitamin_d_mcg",
    "folate_mcg", "phosphorus_mg", "sugar_g",
]

PRICE_FRESHNESS_DAYS = 90  # Prices older than this are considered stale


@dataclass
class FoodDataQuality:
    """Quality assessment for a single food item."""
    source: Optional[str]
    source_id: Optional[str]
    source_date: Optional[datetime]
    nutrient_completeness: float        # 0.0 to 1.0
    missing_nutrients: List[str]
    unit_validity: bool
    serving_validity: bool
    overall_confidence: NutritionConfidence
    last_verified_at: Optional[datetime]
    flags: List[str] = field(default_factory=list)


@dataclass
class RecipeDataQuality:
    """Quality assessment for a recipe, derived from its ingredients."""
    nutrition_confidence: NutritionConfidence
    ingredient_count: int
    ingredients_with_data: int
    missing_nutrients: List[str]
    nutrient_completeness: float
    nutrition_computed_at: Optional[datetime]
    flags: List[str] = field(default_factory=list)


@dataclass
class PriceFreshness:
    """Freshness assessment for a food price entry."""
    is_fresh: bool
    staleness_days: int
    source: Optional[str]
    last_verified_at: Optional[datetime]


class DataQualityService:
    """Validates and scores the trustworthiness of food/nutrition data.
    
    A recipe should not become VERIFIED merely because every field is populated.
    The source and calculation chain need to be valid.
    """

    @staticmethod
    def assess_food_quality(food: Food) -> FoodDataQuality:
        """Assess trustworthiness of a food item's nutrition data."""
        present = [n for n in ALL_FOOD_NUTRIENTS if getattr(food, n, None) is not None]
        missing = [n for n in ALL_FOOD_NUTRIENTS if getattr(food, n, None) is None]
        completeness = len(present) / len(ALL_FOOD_NUTRIENTS) if ALL_FOOD_NUTRIENTS else 0.0
        
        # Source validity
        has_source = bool(food.nutrition_source and food.nutrition_source_id)
        
        # Serving validity
        serving_valid = (
            food.serving_size_g is not None
            and float(food.serving_size_g) > 0
            and float(food.serving_size_g) <= 5000
        )
        
        # Unit validity (basic check: no negative nutrient values)
        unit_valid = all(
            getattr(food, n, None) is None or float(getattr(food, n)) >= 0
            for n in ALL_FOOD_NUTRIENTS
        )
        
        # Determine confidence
        flags = []
        if has_source and completeness >= 0.8:
            confidence = NutritionConfidence.VERIFIED
        elif completeness >= 0.5:
            confidence = NutritionConfidence.CALCULATED
        elif completeness > 0:
            confidence = NutritionConfidence.ESTIMATED
            flags.append("LOW_NUTRIENT_COVERAGE")
        else:
            confidence = NutritionConfidence.INCOMPLETE
            flags.append("NO_NUTRIENT_DATA")
        
        if not has_source:
            flags.append("NO_SOURCE")
        if not serving_valid:
            flags.append("INVALID_SERVING_SIZE")
        if not unit_valid:
            flags.append("NEGATIVE_NUTRIENT_VALUES")
        
        return FoodDataQuality(
            source=food.nutrition_source,
            source_id=food.nutrition_source_id,
            source_date=getattr(food, 'nutrition_source_date', None),
            nutrient_completeness=round(completeness, 3),
            missing_nutrients=missing,
            unit_validity=unit_valid,
            serving_validity=serving_valid,
            overall_confidence=confidence,
            last_verified_at=getattr(food, 'last_verified_at', None),
            flags=flags,
        )

    @classmethod
    def assess_recipe_quality(cls, recipe: Recipe) -> RecipeDataQuality:
        """Compute recipe confidence from ingredient chain.
        
        Rules:
        - All ingredients VERIFIED → recipe CALCULATED
        - Any ingredient ESTIMATED → recipe ESTIMATED
        - >30% ingredients INCOMPLETE → recipe INCOMPLETE
        """
        ingredients = recipe.ingredients or []
        total = len(ingredients)
        
        if total == 0:
            return RecipeDataQuality(
                nutrition_confidence=NutritionConfidence.INCOMPLETE,
                ingredient_count=0,
                ingredients_with_data=0,
                missing_nutrients=[],
                nutrient_completeness=0.0,
                nutrition_computed_at=recipe.nutrition_computed_at,
                flags=["NO_INGREDIENTS"],
            )
        
        # Assess each ingredient's food quality
        food_qualities = []
        for ing in ingredients:
            if hasattr(ing, 'food') and ing.food:
                fq = cls.assess_food_quality(ing.food)
                food_qualities.append(fq)
        
        with_data = sum(1 for fq in food_qualities if fq.overall_confidence != NutritionConfidence.INCOMPLETE)
        incomplete_count = sum(1 for fq in food_qualities if fq.overall_confidence == NutritionConfidence.INCOMPLETE)
        estimated_count = sum(1 for fq in food_qualities if fq.overall_confidence == NutritionConfidence.ESTIMATED)
        
        # Check recipe-level nutrient presence
        present_recipe = [n for n in ALL_RECIPE_NUTRIENTS if getattr(recipe, n, None) is not None]
        missing_recipe = [n for n in ALL_RECIPE_NUTRIENTS if getattr(recipe, n, None) is None]
        recipe_completeness = len(present_recipe) / len(ALL_RECIPE_NUTRIENTS) if ALL_RECIPE_NUTRIENTS else 0.0
        
        # Determine confidence from ingredient chain
        flags = []
        if incomplete_count / total > 0.3:
            confidence = NutritionConfidence.INCOMPLETE
            flags.append("HIGH_INCOMPLETE_INGREDIENT_RATIO")
        elif estimated_count > 0:
            confidence = NutritionConfidence.ESTIMATED
        elif all(fq.overall_confidence == NutritionConfidence.VERIFIED for fq in food_qualities):
            confidence = NutritionConfidence.CALCULATED
        else:
            confidence = NutritionConfidence.CALCULATED
        
        return RecipeDataQuality(
            nutrition_confidence=confidence,
            ingredient_count=total,
            ingredients_with_data=with_data,
            missing_nutrients=missing_recipe,
            nutrient_completeness=round(recipe_completeness, 3),
            nutrition_computed_at=recipe.nutrition_computed_at,
            flags=flags,
        )

    @staticmethod
    def assess_price_freshness(food_price: FoodPrice) -> PriceFreshness:
        """Check how fresh/stale a price entry is."""
        now = datetime.now(timezone.utc)
        
        # Use last_verified_at if available, else updated_at
        check_date = getattr(food_price, 'last_verified_at', None) or food_price.updated_at
        
        if check_date is None:
            return PriceFreshness(
                is_fresh=False,
                staleness_days=-1,
                source=food_price.source,
                last_verified_at=None,
            )
        
        # Handle timezone-aware vs naive datetimes
        if check_date.tzinfo is not None:
            now = datetime.now(timezone.utc)
        
        delta = now - check_date
        staleness = delta.days
        
        return PriceFreshness(
            is_fresh=staleness <= PRICE_FRESHNESS_DAYS,
            staleness_days=staleness,
            source=food_price.source,
            last_verified_at=getattr(food_price, 'last_verified_at', None),
        )
