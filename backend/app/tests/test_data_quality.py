import pytest
from unittest.mock import MagicMock
from app.services.data_quality_service import DataQualityService, ALL_FOOD_NUTRIENTS
from app.models.enums import NutritionConfidence


def _make_food(**overrides):
    """Create a mock Food object with default values."""
    defaults = {
        "name": "Test Food",
        "nutrition_source": "IFCT_2017",
        "nutrition_source_id": "A001",
        "nutrition_source_date": None,
        "serving_size_g": 100,
        "last_verified_at": None,
    }
    # Set all nutrients to None by default
    for n in ALL_FOOD_NUTRIENTS:
        defaults[n] = None
    defaults.update(overrides)
    
    food = MagicMock()
    for key, val in defaults.items():
        setattr(food, key, val)
    return food


def _make_recipe(**overrides):
    """Create a mock Recipe object."""
    defaults = {
        "name": "Test Recipe",
        "ingredients": [],
        "nutrition_computed_at": None,
        "calories": None, "protein_g": None, "carbs_g": None,
        "fat_g": None, "fiber_g": None, "sodium_mg": None,
        "calcium_mg": None, "iron_mg": None, "magnesium_mg": None,
        "potassium_mg": None, "zinc_mg": None, "vitamin_a_mcg": None,
        "vitamin_b12_mcg": None, "vitamin_c_mg": None, "vitamin_d_mcg": None,
        "folate_mcg": None, "phosphorus_mg": None, "sugar_g": None,
    }
    defaults.update(overrides)
    recipe = MagicMock()
    for key, val in defaults.items():
        setattr(recipe, key, val)
    return recipe


class TestFoodDataQuality:
    def test_verified_food_with_full_data(self):
        """Food with source + >80% nutrients = VERIFIED."""
        nutrient_vals = {n: 10.0 for n in ALL_FOOD_NUTRIENTS}
        food = _make_food(**nutrient_vals)
        result = DataQualityService.assess_food_quality(food)
        assert result.overall_confidence == NutritionConfidence.VERIFIED
        assert result.nutrient_completeness == 1.0
        assert len(result.missing_nutrients) == 0

    def test_estimated_food_missing_some_nutrients(self):
        """Food with <50% nutrients = ESTIMATED."""
        # Set only 3 of 18 nutrients
        food = _make_food(
            calories_per_100g=100, protein_per_100g=10, fat_per_100g=5
        )
        result = DataQualityService.assess_food_quality(food)
        assert result.overall_confidence == NutritionConfidence.ESTIMATED
        assert result.nutrient_completeness < 0.5

    def test_incomplete_food_no_data(self):
        """Food with no nutrients = INCOMPLETE."""
        food = _make_food()
        result = DataQualityService.assess_food_quality(food)
        assert result.overall_confidence == NutritionConfidence.INCOMPLETE
        assert "NO_NUTRIENT_DATA" in result.flags

    def test_no_source_flag(self):
        """Food without source gets NO_SOURCE flag."""
        nutrient_vals = {n: 10.0 for n in ALL_FOOD_NUTRIENTS}
        food = _make_food(nutrition_source=None, nutrition_source_id=None, **nutrient_vals)
        result = DataQualityService.assess_food_quality(food)
        assert "NO_SOURCE" in result.flags
        # Without source, even full data is CALCULATED not VERIFIED
        assert result.overall_confidence == NutritionConfidence.CALCULATED

    def test_invalid_serving_size(self):
        """Food with serving_size_g=0 gets flag."""
        food = _make_food(serving_size_g=0)
        result = DataQualityService.assess_food_quality(food)
        assert "INVALID_SERVING_SIZE" in result.flags


class TestRecipeDataQuality:
    def test_empty_recipe(self):
        """Recipe with no ingredients = INCOMPLETE."""
        recipe = _make_recipe()
        result = DataQualityService.assess_recipe_quality(recipe)
        assert result.nutrition_confidence == NutritionConfidence.INCOMPLETE
        assert "NO_INGREDIENTS" in result.flags

    def test_recipe_with_verified_ingredients(self):
        """Recipe where all ingredients are VERIFIED -> CALCULATED."""
        # Create mock ingredients with verified food
        nutrient_vals = {n: 10.0 for n in ALL_FOOD_NUTRIENTS}
        foods = [_make_food(**nutrient_vals) for _ in range(3)]
        ingredients = []
        for f in foods:
            ing = MagicMock()
            ing.food = f
            ingredients.append(ing)
        
        recipe = _make_recipe(ingredients=ingredients)
        result = DataQualityService.assess_recipe_quality(recipe)
        assert result.nutrition_confidence == NutritionConfidence.CALCULATED
        assert result.ingredient_count == 3
        assert result.ingredients_with_data == 3


class TestPriceFreshness:
    def test_fresh_price(self):
        """Price updated recently = fresh."""
        from datetime import datetime, timedelta, timezone
        price = MagicMock()
        price.updated_at = datetime.now(timezone.utc) - timedelta(days=30)
        price.source = "manual_survey"
        price.last_verified_at = None
        
        result = DataQualityService.assess_price_freshness(price)
        assert result.is_fresh is True
        assert result.staleness_days <= 30

    def test_stale_price(self):
        """Price updated 120 days ago = stale."""
        from datetime import datetime, timedelta, timezone
        price = MagicMock()
        price.updated_at = datetime.now(timezone.utc) - timedelta(days=120)
        price.source = "manual_survey"
        price.last_verified_at = None
        
        result = DataQualityService.assess_price_freshness(price)
        assert result.is_fresh is False
        assert result.staleness_days >= 120
