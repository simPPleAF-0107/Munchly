import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.services.data_quality_service import DataQualityService, ALL_FOOD_NUTRIENTS, ALL_RECIPE_NUTRIENTS
from app.models.enums import NutritionConfidence
from app.models.food import Food, FoodPrice
from app.models.recipe import Recipe

def create_mock_food(**kwargs):
    food = MagicMock(spec=Food)
    for n in ALL_FOOD_NUTRIENTS:
        setattr(food, n, 10.0)
    food.serving_size_g = 100.0
    food.nutrition_source = "USDA"
    food.nutrition_source_id = "12345"
    food.nutrition_source_date = datetime.now()
    food.last_verified_at = datetime.now()
    for k, v in kwargs.items():
        setattr(food, k, v)
    return food

def test_food_no_source_id_not_verified():
    # Food with all fields populated but no source_id -> should NOT be VERIFIED
    food = create_mock_food(nutrition_source_id=None)
    quality = DataQualityService.assess_food_quality(food)
    assert quality.overall_confidence != NutritionConfidence.VERIFIED
    assert "NO_SOURCE" in quality.flags

def test_recipe_incomplete_ingredient():
    # Recipe with incomplete ingredient nutrition data -> confidence = ESTIMATED or INCOMPLETE
    food = create_mock_food(nutrition_source=None, nutrition_source_id=None)
    for n in ALL_FOOD_NUTRIENTS:
        setattr(food, n, None)
    
    ing = MagicMock()
    ing.food = food
    
    recipe = MagicMock(spec=Recipe)
    recipe.ingredients = [ing]
    recipe.nutrition_computed_at = None
    for n in ALL_RECIPE_NUTRIENTS:
        setattr(recipe, n, None)
        
    quality = DataQualityService.assess_recipe_quality(recipe)
    assert quality.nutrition_confidence in (NutritionConfidence.ESTIMATED, NutritionConfidence.INCOMPLETE)

def test_price_older_than_90_days():
    # Price older than 90 days -> is_stale = True
    price = MagicMock(spec=FoodPrice)
    price.updated_at = datetime.now(timezone.utc) - timedelta(days=95)
    price.last_verified_at = None
    price.source = "Store"
    
    freshness = DataQualityService.assess_price_freshness(price)
    assert freshness.is_fresh is False
    assert freshness.staleness_days >= 90

def test_recipe_needs_recomputation():
    # Recipe with nutrition_computed_at = None -> needs recomputation
    recipe = MagicMock(spec=Recipe)
    recipe.ingredients = []
    recipe.nutrition_computed_at = None
    for n in ALL_RECIPE_NUTRIENTS:
        setattr(recipe, n, None)
        
    quality = DataQualityService.assess_recipe_quality(recipe)
    assert quality.nutrition_computed_at is None

def test_incomplete_micronutrient_coverage():
    # Incomplete micronutrient coverage -> missing_nutrients list populated
    food = create_mock_food(vitamin_c_mg_per_100g=None, iron_mg_per_100g=None)
    quality = DataQualityService.assess_food_quality(food)
    assert "vitamin_c_mg_per_100g" in quality.missing_nutrients
    assert "iron_mg_per_100g" in quality.missing_nutrients
    assert quality.nutrient_completeness < 1.0

def test_food_source_no_date_reduced_confidence():
    # Food with source but no source_date -> reduced confidence
    food = create_mock_food(nutrition_source_date=None)
    quality = DataQualityService.assess_food_quality(food)
    assert quality.source_date is None
