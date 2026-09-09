import pytest
from app.services.recommendation_service import RecommendationService
from app.models.recipe import Recipe
from app.core.scoring_config import DEFAULT_SCORING_WEIGHTS

@pytest.fixture
def recipes():
    r1 = Recipe(
        id="1", name="Cheap Italian", cuisine_type="Italian", 
        nutritional_info={"calories": 500, "protein": 30, "carbs": 50, "fat": 20},
        estimated_price_per_serving=5.0
    )
    r2 = Recipe(
        id="2", name="Expensive Italian", cuisine_type="Italian", 
        nutritional_info={"calories": 500, "protein": 30, "carbs": 50, "fat": 20},
        estimated_price_per_serving=25.0
    )
    r3 = Recipe(
        id="3", name="Mexican Spicy", cuisine_type="Mexican", 
        nutritional_info={"calories": 800, "protein": 20, "carbs": 100, "fat": 30},
        estimated_price_per_serving=10.0
    )
    return [r1, r2, r3]

@pytest.mark.asyncio
async def test_cuisine_scoring(recipes):
    user_preferences = {"Italian": 1.0, "Mexican": 0.5} # 1.0 is highest strength
    # Mock context
    context = {"cuisine_prefs": user_preferences, "region": "US", "budget": 15.0, "target_nutrition": {"calories": 500, "protein": 30, "carbs": 50, "fat": 20}}
    
    score1 = RecommendationService.score_cuisine(recipes[0], context)
    score3 = RecommendationService.score_cuisine(recipes[2], context)
    
    assert score1 > score3

@pytest.mark.asyncio
async def test_regional_relevance_scoring(recipes):
    # If recipe has regional alignment
    recipes[0].region = "US"
    recipes[2].region = "MX"
    
    context = {"region": "US"}
    score1 = RecommendationService.score_region(recipes[0], context)
    score3 = RecommendationService.score_region(recipes[2], context)
    
    assert score1 > score3

@pytest.mark.asyncio
async def test_budget_scoring(recipes):
    context = {"budget": 15.0} # $15 per meal
    
    # Cheap is under budget (5 < 15), Expensive is over (25 > 15)
    score1 = RecommendationService.score_budget(recipes[0], context)
    score2 = RecommendationService.score_budget(recipes[1], context)
    
    # Should penalize over-budget
    assert score1 > score2
    assert score2 < 0.5 # or however the penalty is designed

@pytest.mark.asyncio
async def test_nutrition_fit_scoring(recipes):
    # Target exactly matches r1 and r2
    target = {"calories": 500, "protein": 30, "carbs": 50, "fat": 20}
    context = {"target_nutrition": target}
    
    score1 = RecommendationService.score_nutrition(recipes[0], context)
    score3 = RecommendationService.score_nutrition(recipes[2], context)
    
    # r1 perfectly matches, r3 is way off (800 cals vs 500)
    assert score1 > score3

@pytest.mark.asyncio
async def test_overall_scoring(recipes):
    context = {
        "cuisine_prefs": {"Italian": 1.0},
        "region": "US",
        "budget": 15.0,
        "target_nutrition": {"calories": 500, "protein": 30, "carbs": 50, "fat": 20}
    }
    recipes[0].region = "US"
    recipes[1].region = "US"
    recipes[2].region = "MX"
    
    service = RecommendationService()
    scores = [(r.id, service.calculate_score(r, context)) for r in recipes]
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # r1 is perfect (cheap, italian, us, good nutrition)
    assert scores[0][0] == "1"
    # r2 is expensive, so it gets penalized
    # r3 is wrong cuisine, region, and nutrition
    assert scores[-1][0] == "2" or scores[-1][0] == "3"
