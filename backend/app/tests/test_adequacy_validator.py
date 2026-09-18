import pytest
from unittest.mock import MagicMock
from app.services.adequacy_validator import AdequacyValidator
from app.services.nutrient_profile_service import NutrientProfileService


def _make_profile():
    """Create a standard nutrient profile for testing."""
    return NutrientProfileService.build_profile(
        weight_kg=70, height_cm=175, age=30,
        gender="MALE", activity_level="MODERATELY_ACTIVE",
        health_goal="MAINTAIN_WEIGHT",
    )


def _make_meal(day, meal_type, calories, protein_g, fiber_g=10, **extra_nutrients):
    """Create a mock meal dict."""
    recipe = {
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": 50,
        "fat_g": 20,
        "fiber_g": fiber_g,
        "sodium_mg": 500,
        "calcium_mg": 100,
        "iron_mg": 3,
        "magnesium_mg": 50,
        "potassium_mg": 400,
        "zinc_mg": 2,
        "vitamin_a_mcg": 100,
        "vitamin_b12_mcg": 0.5,
        "vitamin_c_mg": 15,
        "vitamin_d_mcg": 2,
        "folate_mcg": 50,
        "phosphorus_mg": 100,
        "sugar_g": 5,
    }
    recipe.update(extra_nutrients)
    return {"day_of_week": day, "meal_type": meal_type, "recipe": recipe}


class TestAdequacyValidator:
    def test_balanced_plan_passes(self):
        """A well-balanced plan should pass validation."""
        profile = _make_profile()
        target_per_meal = profile.calorie_target / 3
        protein_per_meal = profile.protein_g.target / 3
        
        meals = []
        for day in range(1, 8):
            for mt in ["BREAKFAST", "LUNCH", "DINNER"]:
                meals.append(_make_meal(day, mt, target_per_meal, protein_per_meal))
        
        result = AdequacyValidator.validate_plan(meals, profile)
        assert result.passed is True
        assert len([v for v in result.violations if v.severity == "VIOLATION"]) == 0

    def test_low_calorie_day_fails(self):
        """A day with very low calories should create a violation."""
        profile = _make_profile()
        
        meals = []
        # Day 1: very low calories
        meals.append(_make_meal(1, "BREAKFAST", 100, 5))
        meals.append(_make_meal(1, "LUNCH", 100, 5))
        meals.append(_make_meal(1, "DINNER", 100, 5))
        # Days 2-7: normal
        for day in range(2, 8):
            for mt in ["BREAKFAST", "LUNCH", "DINNER"]:
                meals.append(_make_meal(day, mt, profile.calorie_target / 3, profile.protein_g.target / 3))
        
        result = AdequacyValidator.validate_plan(meals, profile)
        cal_violations = [v for v in result.violations if v.nutrient == "calories" and v.day == 1]
        assert len(cal_violations) > 0

    def test_low_protein_day_fails(self):
        """A day with very low protein should create a violation."""
        profile = _make_profile()
        
        meals = []
        # Day 1: no protein
        meals.append(_make_meal(1, "BREAKFAST", profile.calorie_target / 3, 0))
        meals.append(_make_meal(1, "LUNCH", profile.calorie_target / 3, 0))
        meals.append(_make_meal(1, "DINNER", profile.calorie_target / 3, 0))
        
        result = AdequacyValidator.validate_plan(meals, profile)
        protein_violations = [v for v in result.violations if v.nutrient == "protein_g" and v.day == 1]
        assert len(protein_violations) > 0

    def test_nutrient_coverage_calculated(self):
        """Nutrient coverage dict should be populated."""
        profile = _make_profile()
        meals = [_make_meal(1, "BREAKFAST", 500, 30)]
        
        result = AdequacyValidator.validate_plan(meals, profile)
        assert len(result.nutrient_coverage) > 0
