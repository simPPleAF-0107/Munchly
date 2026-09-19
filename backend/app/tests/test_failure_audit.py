import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.recommendation_service import RecommendationService
from app.services.behavioral_service import BehavioralService
from app.services.daily_context_service import DailyContextService
from app.services.adequacy_validator import AdequacyValidator
from app.services.conflict_resolver import ConflictResolver
from app.services.nutrient_profile_service import NutrientProfileService
from app.models.enums import HealthGoal, Gender, ActivityLevel
from app.models.recipe import Recipe
from app.models.daily_context import DailyContext

@pytest.mark.asyncio
async def test_recommendation_zero_candidates():
    db = AsyncMock()
    service = RecommendationService(db)
    user_id = uuid.uuid4()
    
    result = await service.score_recipes(
        recipes=[],
        user_id=user_id,
        meal_type="LUNCH",
        daily_targets={"LUNCH": {"calories": 500}}
    )
    
    assert result == []

@pytest.mark.asyncio
async def test_recommendation_no_user_found():
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result
    
    service = RecommendationService(db)
    recipe = MagicMock()
    recipe.id = uuid.uuid4()
    
    result = await service.score_recipes(
        recipes=[recipe],
        user_id=uuid.uuid4(),
        meal_type="LUNCH",
        daily_targets={"LUNCH": {"calories": 500}}
    )
    
    assert result == []

@pytest.mark.asyncio
async def test_recommendation_missing_nutrient_data():
    db = AsyncMock()
    mock_user = MagicMock()
    mock_user.profile = None
    mock_user.food_preferences = []
    mock_user.cuisine_preferences = []
    mock_user.available_ingredients = []
    mock_user.health_conditions = []
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    db.execute.return_value = mock_result
    
    service = RecommendationService(db)
    
    recipe = MagicMock(spec=Recipe)
    recipe.id = uuid.uuid4()
    recipe.calories = None
    recipe.protein_g = None
    recipe.carbs_g = None
    recipe.fat_g = None
    recipe.calcium_mg = None
    recipe.iron_mg = None
    recipe.magnesium_mg = None
    recipe.potassium_mg = None
    recipe.zinc_mg = None
    recipe.vitamin_a_mcg = None
    recipe.vitamin_b12_mcg = None
    recipe.vitamin_c_mg = None
    recipe.vitamin_d_mcg = None
    recipe.folate_mcg = None
    recipe.phosphorus_mg = None
    recipe.estimated_cost = None
    recipe.prep_time_min = None
    recipe.ingredients = []
    recipe.regions = []
    recipe.cuisines = []
    
    result = await service.score_recipes(
        recipes=[recipe],
        user_id=uuid.uuid4(),
        meal_type="LUNCH",
        daily_targets={"LUNCH": {"calories": 500, "protein_g": 20, "carbs_g": 60, "fat_g": 15}}
    )
    
    assert len(result) == 1
    assert result[0].total_score >= 0

def test_behavioral_no_data():
    profiles = []
    insights = BehavioralService.check_for_insights(profiles)
    assert insights == []
    
    confidence = BehavioralService.compute_confidence(0)
    assert confidence == 0.0

@pytest.mark.asyncio
async def test_daily_context_missing():
    db = AsyncMock()
    db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result
    
    service = DailyContextService(db)
    context = await service.get_today_context(uuid.uuid4())
    assert context is None
    
    # get_or_create_today should create one if missing
    ctx = await service.get_or_create_today(uuid.uuid4())
    assert ctx is not None
    assert isinstance(ctx, DailyContext)

def test_adequacy_validator_empty_plan():
    profile = NutrientProfileService.build_profile(
        weight_kg=70, height_cm=175, age=30, gender="MALE",
        activity_level="SEDENTARY", health_goal="MAINTAIN_WEIGHT"
    )
    
    result = AdequacyValidator.validate_plan(
        plan_meals=[],
        nutrient_profile=profile
    )
    
    # Should flag warnings for missing weekly micronutrients since nothing is eaten
    assert len(result.warnings) > 0
    # No meal-level or daily-level violations because no days are present
    assert result.passed

def test_conflict_resolver_none_inputs():
    report = ConflictResolver.detect_conflicts(
        diet_type=None,
        health_goal=None,
        weekly_budget=None,
        max_prep_time_min=None,
        dietary_restrictions=None,
        allergens=None,
        avoidance_count=0
    )
    assert not report.has_conflicts
    assert len(report.conflicts) == 0

def test_nutrient_profile_edge_values():
    # very low weight
    p1 = NutrientProfileService.build_profile(
        weight_kg=20, height_cm=150, age=30, gender="FEMALE",
        activity_level="SEDENTARY", health_goal="MAINTAIN_WEIGHT"
    )
    assert p1.calorie_target >= 1200 # Safety floor female
    
    # very high age
    p2 = NutrientProfileService.build_profile(
        weight_kg=70, height_cm=175, age=120, gender="MALE",
        activity_level="SEDENTARY", health_goal="MAINTAIN_WEIGHT"
    )
    assert p2.calorie_target >= 1500 # Safety floor male
