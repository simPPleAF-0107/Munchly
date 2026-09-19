import time
import uuid
import pytest
from unittest.mock import MagicMock
from app.services.recommendation_service import RecommendationService
from app.services.nutrient_profile_service import NutrientProfileService
from app.services.adequacy_validator import AdequacyValidator
from app.services.behavioral_service import BehavioralService
from app.services.conflict_resolver import ConflictResolver


def make_mock_recipe(**kwargs):
    recipe = MagicMock()
    recipe.id = kwargs.get('id', uuid.uuid4())
    recipe.calories = kwargs.get('calories', 500)
    recipe.protein_g = kwargs.get('protein_g', 25)
    recipe.carbs_g = kwargs.get('carbs_g', 60)
    recipe.fat_g = kwargs.get('fat_g', 15)
    recipe.fiber_g = kwargs.get('fiber_g', 8)
    recipe.estimated_cost = kwargs.get('estimated_cost', 80)
    recipe.prep_time_min = kwargs.get('prep_time_min', 30)
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
    recipe.sodium_mg = kwargs.get('sodium_mg', 400)
    recipe.ingredients = []
    recipe.cuisines = []
    recipe.regions = []
    return recipe


class TestPerformanceBenchmarks:
    
    def test_scoring_100_recipes_under_1s(self):
        service = RecommendationService(db=MagicMock())
        recipes = [make_mock_recipe() for _ in range(100)]
        targets = {"calories": 500, "protein_g": 25, "carbs_g": 60, "fat_g": 15}
        micros = {
            "calcium_mg": {"target": 1000},
            "iron_mg": {"target": 17},
            "zinc_mg": {"target": 12},
        }
        
        start = time.perf_counter()
        for recipe in recipes:
            service._score_nutrition_fit(recipe, targets)
            service._score_nutrient_coverage(recipe, targets, micros, 0.33)
            service._score_nutrient_gap_fill(recipe, {"calcium_mg": 200}, micros)
            service._score_budget_efficiency(recipe, 100.0)
            service._score_prep_time_fit(30, 60)
            service._score_variety(recipe, set())
            service._score_local_availability(recipe, "WB")
            service._score_protein_source_rotation(recipe, set())
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"Scoring 100 recipes took {elapsed:.2f}s (limit: 1.0s)"

    def test_nutrient_profile_build_under_100ms(self):
        start = time.perf_counter()
        for _ in range(10):
            NutrientProfileService.build_profile(
                weight_kg=70, height_cm=170, age=30,
                gender="MALE", activity_level="MODERATELY_ACTIVE",
                health_goal="MAINTAIN_WEIGHT",
                medical_conditions=["DIABETES", "HIGH_BLOOD_PRESSURE"],
            )
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, f"Building 10 profiles took {elapsed:.3f}s (limit: 0.1s)"

    def test_adequacy_validation_under_200ms(self):
        profile = NutrientProfileService.build_profile(
            weight_kg=70, height_cm=170, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
        )
        meals = []
        per_meal_cal = profile.calorie_target / 3
        for day in range(1, 8):
            for mt in ["BREAKFAST", "LUNCH", "DINNER"]:
                meals.append({
                    "day_of_week": day, "meal_type": mt,
                    "recipe": {
                        "calories": per_meal_cal,
                        "protein_g": profile.protein_g.target / 3,
                        "carbs_g": profile.carbs_g.target / 3,
                        "fat_g": profile.fat_g.target / 3,
                        "fiber_g": profile.fiber_g.target / 3,
                        "sodium_mg": 500,
                    },
                })
        start = time.perf_counter()
        for _ in range(10):
            AdequacyValidator.validate_plan(meals, profile)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.2, f"10 validations took {elapsed:.3f}s (limit: 0.2s)"

    def test_behavioral_confidence_1000_under_100ms(self):
        start = time.perf_counter()
        for count in range(1, 1001):
            BehavioralService.compute_confidence(count)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, f"1000 confidence calcs took {elapsed:.3f}s (limit: 0.1s)"

    def test_conflict_detection_under_100ms(self):
        start = time.perf_counter()
        for _ in range(100):
            ConflictResolver.detect_conflicts(
                diet_type="VEGAN",
                health_goal="BUILD_MUSCLE",
                weekly_budget=500,
            )
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, f"100 conflict detections took {elapsed:.3f}s (limit: 0.1s)"
