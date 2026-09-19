import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, PropertyMock
from app.services.recommendation_service import RecommendationService
from app.core.scoring_config import DEFAULT_SCORING_WEIGHTS, ScoringWeights
from app.models.enums import PreferenceType, RuleScope, RuleOperator


def make_mock_recipe(**kwargs):
    """Create a mock Recipe with nutrition attributes."""
    recipe = MagicMock()
    recipe.id = kwargs.get('id', uuid.uuid4())
    recipe.name = kwargs.get('name', 'Test Recipe')
    recipe.calories = kwargs.get('calories', 500)
    recipe.protein_g = kwargs.get('protein_g', 25)
    recipe.carbs_g = kwargs.get('carbs_g', 60)
    recipe.fat_g = kwargs.get('fat_g', 15)
    recipe.fiber_g = kwargs.get('fiber_g', 8)
    recipe.sodium_mg = kwargs.get('sodium_mg', 400)
    recipe.estimated_cost = kwargs.get('estimated_cost', 80)
    recipe.prep_time_min = kwargs.get('prep_time_min', 30)
    recipe.difficulty = kwargs.get('difficulty', 'MEDIUM')
    recipe.servings = kwargs.get('servings', 1)
    recipe.image_url = None
    
    # Micronutrients
    recipe.calcium_mg = kwargs.get('calcium_mg', 200)
    recipe.iron_mg = kwargs.get('iron_mg', 5)
    recipe.magnesium_mg = kwargs.get('magnesium_mg', 80)
    recipe.potassium_mg = kwargs.get('potassium_mg', 500)
    recipe.zinc_mg = kwargs.get('zinc_mg', 3)
    recipe.vitamin_a_mcg = kwargs.get('vitamin_a_mcg', 200)
    recipe.vitamin_b12_mcg = kwargs.get('vitamin_b12_mcg', 0.8)
    recipe.vitamin_c_mg = kwargs.get('vitamin_c_mg', 20)
    recipe.vitamin_d_mcg = kwargs.get('vitamin_d_mcg', 2)
    recipe.folate_mcg = kwargs.get('folate_mcg', 100)
    recipe.phosphorus_mg = kwargs.get('phosphorus_mg', 200)
    recipe.sugar_g = kwargs.get('sugar_g', 8)
    
    # Relationships (mocked)
    recipe.ingredients = kwargs.get('ingredients', [])
    recipe.cuisines = kwargs.get('cuisines', [])
    recipe.regions = kwargs.get('regions', [])
    recipe.diet_compatibility = []
    recipe.meal_types = []
    
    return recipe


def make_mock_ingredient(food_id=None, protein_per_100g=15, category='LEGUME', name='dal',
                         food_regions=None):
    """Create a mock RecipeIngredient."""
    ing = MagicMock()
    ing.food_id = food_id or uuid.uuid4()
    food = MagicMock()
    food.protein_per_100g = protein_per_100g
    food.category = category
    food.name = name
    food.regions = food_regions or []
    food.allergens = []
    ing.food = food
    return ing


class TestScoringWeightsIntegrity:
    """Verify scoring configuration is valid."""

    def test_weights_sum_to_one(self):
        total = sum(DEFAULT_SCORING_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001, f"Weights sum to {total}, not 1.0"

    def test_all_14_dimensions_present(self):
        expected = {
            "nutrition_fit", "nutrient_coverage", "nutrient_gap_fill",
            "budget_efficiency", "food_preference", "cuisine_preference",
            "regional_relevance", "local_availability", "ingredient_reuse",
            "prep_time_fit", "pantry_overlap", "variety",
            "medical_fit", "protein_source_rotation",
        }
        assert set(DEFAULT_SCORING_WEIGHTS.keys()) == expected

    def test_no_zero_weights(self):
        for dim, weight in DEFAULT_SCORING_WEIGHTS.items():
            assert weight > 0, f"Dimension {dim} has zero weight"


class TestNutritionFitSensitivity:
    """nutrition_fit must change when macro composition changes."""

    def setup_method(self):
        self.service = RecommendationService(db=MagicMock())
        self.targets = {"calories": 500, "protein_g": 25, "carbs_g": 60, "fat_g": 15}

    def test_perfect_fit_scores_high(self):
        recipe = make_mock_recipe(calories=500, protein_g=25, carbs_g=60, fat_g=15)
        score = self.service._score_nutrition_fit(recipe, self.targets)
        assert score >= 0.9

    def test_poor_fit_scores_low(self):
        recipe = make_mock_recipe(calories=1200, protein_g=5, carbs_g=200, fat_g=50)
        score = self.service._score_nutrition_fit(recipe, self.targets)
        assert score < 0.5

    def test_macro_balance_changes_score(self):
        """Two recipes with same calories but different macro distribution should score differently."""
        balanced = make_mock_recipe(calories=500, protein_g=25, carbs_g=60, fat_g=15)
        unbalanced = make_mock_recipe(calories=500, protein_g=25, carbs_g=120, fat_g=2)
        
        s1 = self.service._score_nutrition_fit(balanced, self.targets)
        s2 = self.service._score_nutrition_fit(unbalanced, self.targets)
        assert s1 != s2, "macro_balance must affect score"


class TestNutrientCoverageSensitivity:
    """nutrient_coverage must change when recipe micronutrients change."""

    def setup_method(self):
        self.service = RecommendationService(db=MagicMock())
        self.micros = {
            "calcium_mg": {"target": 1000},
            "iron_mg": {"target": 17},
            "vitamin_c_mg": {"target": 80},
            "zinc_mg": {"target": 12},
        }

    def test_micro_rich_scores_higher(self):
        rich = make_mock_recipe(calcium_mg=400, iron_mg=8, vitamin_c_mg=40, zinc_mg=5)
        poor = make_mock_recipe(calcium_mg=10, iron_mg=0.5, vitamin_c_mg=2, zinc_mg=0.3)
        
        s1 = self.service._score_nutrient_coverage(rich, {}, self.micros, 0.33)
        s2 = self.service._score_nutrient_coverage(poor, {}, self.micros, 0.33)
        assert s1 > s2, "Micro-rich recipe must score higher"

    def test_no_micro_data_returns_neutral(self):
        recipe = make_mock_recipe()
        score = self.service._score_nutrient_coverage(recipe, {}, None, 0.33)
        assert score == 0.5


class TestNutrientGapFillSensitivity:
    """nutrient_gap_fill must change based on what's already consumed."""

    def setup_method(self):
        self.service = RecommendationService(db=MagicMock())
        self.micros = {
            "calcium_mg": {"target": 1000},
            "iron_mg": {"target": 17},
        }

    def test_fills_gap_scores_higher(self):
        """If calcium is low today, calcium-rich recipe should score higher."""
        # Calcium is very low, iron is adequate
        consumed = {"calcium_mg": 100, "iron_mg": 15}
        
        calcium_rich = make_mock_recipe(calcium_mg=500, iron_mg=2)
        iron_rich = make_mock_recipe(calcium_mg=20, iron_mg=8)
        
        s_calcium = self.service._score_nutrient_gap_fill(calcium_rich, consumed, self.micros)
        s_iron = self.service._score_nutrient_gap_fill(iron_rich, consumed, self.micros)
        
        assert s_calcium > s_iron, "Calcium-rich recipe should fill the calcium gap better"

    def test_no_gaps_returns_high(self):
        """When all nutrients are met, score should be high (mildly positive)."""
        consumed = {"calcium_mg": 1000, "iron_mg": 17}
        recipe = make_mock_recipe(calcium_mg=200, iron_mg=5)
        score = self.service._score_nutrient_gap_fill(recipe, consumed, self.micros)
        assert score >= 0.7

    def test_no_context_returns_neutral(self):
        recipe = make_mock_recipe()
        score = self.service._score_nutrient_gap_fill(recipe, None, None)
        assert score == 0.5


class TestLocalAvailabilitySensitivity:
    """local_availability must change when regional data changes."""

    def setup_method(self):
        self.service = RecommendationService(db=MagicMock())

    def test_local_ingredients_score_higher(self):
        """Recipe with locally available ingredients should score higher."""
        local_region = MagicMock()
        local_region.state_code = "WB"
        
        local_ing = make_mock_ingredient(food_regions=[local_region])
        remote_ing = make_mock_ingredient(food_regions=[])
        
        local_recipe = make_mock_recipe(ingredients=[local_ing])
        remote_recipe = make_mock_recipe(ingredients=[remote_ing])
        
        s1 = self.service._score_local_availability(local_recipe, "WB")
        s2 = self.service._score_local_availability(remote_recipe, "WB")
        assert s1 > s2

    def test_no_location_returns_neutral(self):
        recipe = make_mock_recipe(ingredients=[make_mock_ingredient()])
        score = self.service._score_local_availability(recipe, None)
        assert score == 0.5


class TestProteinSourceRotationSensitivity:
    """protein_source_rotation must change with weekly protein diversity."""

    def setup_method(self):
        self.service = RecommendationService(db=MagicMock())

    def test_new_source_scores_higher(self):
        """Recipe introducing new protein source should score higher than repeat."""
        chicken_ing = make_mock_ingredient(protein_per_100g=25, category='MEAT', name='chicken')
        dal_ing = make_mock_ingredient(protein_per_100g=22, category='LEGUME', name='dal')
        
        chicken_recipe = make_mock_recipe(ingredients=[chicken_ing])
        dal_recipe = make_mock_recipe(ingredients=[dal_ing])
        
        # Week already has chicken but not dal
        weekly_sources = {'MEAT'}
        
        s_chicken = self.service._score_protein_source_rotation(chicken_recipe, weekly_sources)
        s_dal = self.service._score_protein_source_rotation(dal_recipe, weekly_sources)
        
        assert s_dal > s_chicken, "New protein source should score higher"

    def test_first_meal_of_week_max_score(self):
        """First protein source of the week should get maximum score."""
        ing = make_mock_ingredient(protein_per_100g=20)
        recipe = make_mock_recipe(ingredients=[ing])
        score = self.service._score_protein_source_rotation(recipe, set())
        assert score == 1.0

    def test_no_protein_returns_neutral(self):
        ing = make_mock_ingredient(protein_per_100g=2)  # Not protein-rich
        recipe = make_mock_recipe(ingredients=[ing])
        score = self.service._score_protein_source_rotation(recipe, {'MEAT', 'LEGUME'})
        assert score == 0.5


class TestBudgetEfficiencySensitivity:
    def setup_method(self):
        self.service = RecommendationService(db=MagicMock())

    def test_sweet_spot_scores_highest(self):
        recipe = make_mock_recipe(estimated_cost=70)  # 70% of 100 budget
        score = self.service._score_budget_efficiency(recipe, 100.0)
        assert score == 1.0

    def test_expensive_scores_lower(self):
        cheap = make_mock_recipe(estimated_cost=70)
        expensive = make_mock_recipe(estimated_cost=150)
        s1 = self.service._score_budget_efficiency(cheap, 100.0)
        s2 = self.service._score_budget_efficiency(expensive, 100.0)
        assert s1 > s2


class TestVarietySensitivity:
    def setup_method(self):
        self.service = RecommendationService(db=MagicMock())

    def test_new_recipe_scores_higher(self):
        recipe = make_mock_recipe()
        s_new = self.service._score_variety(recipe, set())
        s_repeat = self.service._score_variety(recipe, {recipe.id})
        assert s_new > s_repeat


class TestPrepTimeSensitivity:
    def setup_method(self):
        self.service = RecommendationService(db=MagicMock())

    def test_within_time_scores_high(self):
        assert self.service._score_prep_time_fit(20, 30) == 1.0

    def test_over_time_scores_lower(self):
        s_over = self.service._score_prep_time_fit(60, 30)
        assert s_over < 1.0
