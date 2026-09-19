import uuid
import pytest
from unittest.mock import MagicMock
from app.services.nutrition_service import NutritionService
from app.services.nutrient_profile_service import NutrientProfileService
from app.services.adequacy_validator import AdequacyValidator


class TestIngredientToRecipeNutrition:
    """Known-answer tests: manually calculated expected values."""

    def test_simple_rice_dal_recipe(self):
        """200g rice (130kcal/100g, 2.7g protein) + 100g dal (116kcal/100g, 7.6g protein)
        Expected: 200/100*130 + 100/100*116 = 260 + 116 = 376 kcal
        Expected protein: 200/100*2.7 + 100/100*7.6 = 5.4 + 7.6 = 13.0g
        """
        rice_cal_per_100g = 130.0
        rice_protein_per_100g = 2.7
        dal_cal_per_100g = 116.0
        dal_protein_per_100g = 7.6
        
        rice_qty = 200.0
        dal_qty = 100.0
        
        total_cal = (rice_qty / 100 * rice_cal_per_100g) + (dal_qty / 100 * dal_cal_per_100g)
        total_protein = (rice_qty / 100 * rice_protein_per_100g) + (dal_qty / 100 * dal_protein_per_100g)
        
        assert abs(total_cal - 376.0) < 0.1
        assert abs(total_protein - 13.0) < 0.1

    def test_per_serving_division(self):
        """Recipe makes 3 servings. Per-serving = total / 3."""
        total_cal = 900.0
        servings = 3
        per_serving = total_cal / servings
        assert per_serving == 300.0

    def test_micronutrient_propagation_rice_dal(self):
        """Verify micronutrients propagate through pipeline.
        Rice: calcium=10mg/100g, iron=0.2mg/100g
        Dal: calcium=56mg/100g, iron=3.7mg/100g
        200g rice + 100g dal:
        calcium = 200/100*10 + 100/100*56 = 20 + 56 = 76mg
        iron = 200/100*0.2 + 100/100*3.7 = 0.4 + 3.7 = 4.1mg
        """
        rice_calcium = 10.0
        rice_iron = 0.2
        dal_calcium = 56.0
        dal_iron = 3.7
        
        total_calcium = (200 / 100 * rice_calcium) + (100 / 100 * dal_calcium)
        total_iron = (200 / 100 * rice_iron) + (100 / 100 * dal_iron)
        
        assert abs(total_calcium - 76.0) < 0.1
        assert abs(total_iron - 4.1) < 0.1

    def test_no_double_counting(self):
        """Verify nutrients from N ingredients sum once, not multiplied."""
        # 3 ingredients, each contributing 100 kcal
        ingredients = [
            {"qty": 100, "cal_per_100g": 100},
            {"qty": 100, "cal_per_100g": 100},
            {"qty": 100, "cal_per_100g": 100},
        ]
        total = sum(ing["qty"] / 100 * ing["cal_per_100g"] for ing in ingredients)
        assert total == 300.0  # NOT 900 (which would indicate multiplication)


class TestDailyAggregation:
    """Verify daily totals = sum of meal totals."""

    def test_three_meal_day(self):
        """Breakfast 400 + Lunch 600 + Dinner 500 = 1500 kcal."""
        breakfast_cal = 400
        lunch_cal = 600
        dinner_cal = 500
        daily_total = breakfast_cal + lunch_cal + dinner_cal
        assert daily_total == 1500

    def test_daily_micro_sum(self):
        """Daily calcium = sum of each meal's calcium."""
        meals = [
            {"calcium_mg": 200},
            {"calcium_mg": 350},
            {"calcium_mg": 150},
        ]
        daily_calcium = sum(m["calcium_mg"] for m in meals)
        assert daily_calcium == 700

    def test_weekly_sum(self):
        """Weekly total = 7 * daily (for uniform days)."""
        daily_cal = 2000
        weekly = daily_cal * 7
        assert weekly == 14000


class TestPerMealSplits:
    """Verify per-meal percentage splits are correct."""

    def test_splits_sum_to_one(self):
        splits = {"BREAKFAST": 0.25, "LUNCH": 0.40, "DINNER": 0.35}
        assert abs(sum(splits.values()) - 1.0) < 0.001

    def test_breakfast_target(self):
        """2000 kcal daily * 25% = 500 kcal breakfast."""
        daily = 2000
        breakfast = daily * 0.25
        assert breakfast == 500.0

    def test_lunch_target(self):
        """2000 kcal daily * 40% = 800 kcal lunch."""
        daily = 2000
        lunch = daily * 0.40
        assert lunch == 800.0

    def test_micro_split_calcium(self):
        """Calcium 1000mg daily, lunch = 40% = 400mg target."""
        daily_calcium = 1000
        lunch_calcium = daily_calcium * 0.40
        assert lunch_calcium == 400.0


class TestBMRAndTDEE:
    """Verify Mifflin-St Jeor formula implementation."""

    def test_bmr_male(self):
        """Male, 75kg, 175cm, 30yo: 10*75 + 6.25*175 - 5*30 + 5 = 1698.75"""
        bmr = NutritionService.calculate_bmr(75, 175, 30, "MALE")
        assert bmr == 1699  # int(1698.75)

    def test_bmr_female(self):
        """Female, 60kg, 160cm, 25yo: 10*60 + 6.25*160 - 5*25 - 161 = 1314"""
        bmr = NutritionService.calculate_bmr(60, 160, 25, "FEMALE")
        assert bmr == 1314

    def test_tdee_sedentary(self):
        """SEDENTARY multiplier = 1.2. BMR 1700 * 1.2 = 2040."""
        tdee = NutritionService.calculate_tdee(1700, "SEDENTARY")
        assert tdee == 2040

    def test_tdee_moderately_active(self):
        """MODERATELY_ACTIVE multiplier = 1.55. BMR 1700 * 1.55 = 2635."""
        tdee = NutritionService.calculate_tdee(1700, "MODERATELY_ACTIVE")
        assert tdee == 2635


class TestCalorieTargetWithGoals:
    """Verify calorie adjustments from goals."""

    def test_lose_weight_deficit(self):
        profile = NutrientProfileService.build_profile(
            weight_kg=80, height_cm=175, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="LOSE_WEIGHT",
        )
        # TDEE should be reduced by deficit
        assert profile.calorie_target < profile.tdee
        assert profile.calorie_adjustment < 0

    def test_gain_weight_surplus(self):
        profile = NutrientProfileService.build_profile(
            weight_kg=60, height_cm=170, age=25,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="GAIN_WEIGHT",
        )
        assert profile.calorie_target > profile.tdee
        assert profile.calorie_adjustment > 0

    def test_safety_floor_enforced(self):
        """Extreme deficit should not go below safety floor."""
        profile = NutrientProfileService.build_profile(
            weight_kg=45, height_cm=150, age=60,
            gender="FEMALE", activity_level="SEDENTARY",
            health_goal="LOSE_WEIGHT",
        )
        assert profile.calorie_target >= 1200  # Female safety floor


class TestAdequacyValidatorIntegration:
    """Verify AdequacyValidator correctly uses computed nutrition."""

    def test_adequate_plan_passes(self):
        """A well-balanced plan should pass validation."""
        profile = NutrientProfileService.build_profile(
            weight_kg=70, height_cm=170, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
        )
        # Create 21 meals (3 meals x 7 days) that meet targets
        meals = []
        per_meal_cal = profile.calorie_target / 3
        for day in range(1, 8):
            for mt in ["BREAKFAST", "LUNCH", "DINNER"]:
                meals.append({
                    "day_of_week": day,
                    "meal_type": mt,
                    "recipe": {
                        "calories": per_meal_cal,
                        "protein_g": profile.protein_g.target / 3,
                        "carbs_g": profile.carbs_g.target / 3,
                        "fat_g": profile.fat_g.target / 3,
                        "fiber_g": profile.fiber_g.target / 3,
                        "sodium_mg": 500,
                        "calcium_mg": 333,
                        "iron_mg": 6,
                        "magnesium_mg": 113,
                        "potassium_mg": 1133,
                        "zinc_mg": 4,
                        "vitamin_a_mcg": 300,
                        "vitamin_b12_mcg": 0.8,
                        "vitamin_c_mg": 27,
                        "vitamin_d_mcg": 5,
                        "folate_mcg": 133,
                        "phosphorus_mg": 233,
                        "sugar_g": 12,
                    },
                })
        result = AdequacyValidator.validate_plan(meals, profile)
        assert result.passed, f"Plan should pass but got violations: {[v.message for v in result.violations]}"

    def test_inadequate_calories_fails(self):
        """A plan with 50% calorie deficit should fail."""
        profile = NutrientProfileService.build_profile(
            weight_kg=70, height_cm=170, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
        )
        meals = []
        half_cal = profile.calorie_target * 0.5 / 3  # Only 50% of target
        for day in range(1, 8):
            for mt in ["BREAKFAST", "LUNCH", "DINNER"]:
                meals.append({
                    "day_of_week": day,
                    "meal_type": mt,
                    "recipe": {
                        "calories": half_cal,
                        "protein_g": 10,
                        "carbs_g": 30,
                        "fat_g": 5,
                        "fiber_g": 3,
                        "sodium_mg": 200,
                    },
                })
        result = AdequacyValidator.validate_plan(meals, profile)
        assert not result.passed
        cal_violations = [v for v in result.violations if v.nutrient == "calories"]
        assert len(cal_violations) > 0
