import pytest
from app.services.nutrient_profile_service import (
    NutrientProfileService, CALORIE_ADJUSTMENTS, SAFETY_FLOORS,
    VALIDATED_MEDICAL_RULES,
)
from app.models.enums import HealthGoal, Gender


class TestCalorieBounds:
    def test_lose_weight_creates_deficit(self):
        """LOSE_WEIGHT goal should reduce calories below TDEE."""
        profile = NutrientProfileService.build_profile(
            weight_kg=80, height_cm=175, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="LOSE_WEIGHT",
        )
        assert profile.calorie_adjustment < 0
        assert profile.calorie_target < profile.tdee

    def test_gain_weight_creates_surplus(self):
        """GAIN_WEIGHT goal should increase calories above TDEE."""
        profile = NutrientProfileService.build_profile(
            weight_kg=60, height_cm=165, age=25,
            gender="MALE", activity_level="LIGHTLY_ACTIVE",
            health_goal="GAIN_WEIGHT",
        )
        assert profile.calorie_adjustment > 0
        assert profile.calorie_target > profile.tdee

    def test_safety_floor_male(self):
        """Male calorie target never goes below 1500."""
        profile = NutrientProfileService.build_profile(
            weight_kg=50, height_cm=155, age=65,
            gender="MALE", activity_level="SEDENTARY",
            health_goal="LOSE_WEIGHT",
        )
        assert profile.calorie_target >= SAFETY_FLOORS[Gender.MALE]

    def test_safety_floor_female(self):
        """Female calorie target never goes below 1200."""
        profile = NutrientProfileService.build_profile(
            weight_kg=45, height_cm=150, age=60,
            gender="FEMALE", activity_level="SEDENTARY",
            health_goal="LOSE_WEIGHT",
        )
        assert profile.calorie_target >= SAFETY_FLOORS[Gender.FEMALE]

    def test_calorie_range_is_symmetric(self):
        """Calorie range should be target \u00b110%."""
        profile = NutrientProfileService.build_profile(
            weight_kg=70, height_cm=170, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
        )
        low, high = profile.calorie_range
        assert low == int(profile.calorie_target * 0.9)
        assert high == int(profile.calorie_target * 1.1)


class TestMedicalBoundary:
    def test_validated_condition_applies_adjustment(self):
        """Diabetes (validated) should adjust sugar target."""
        profile = NutrientProfileService.build_profile(
            weight_kg=80, height_cm=175, age=45,
            gender="MALE", activity_level="LIGHTLY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
            medical_conditions=["DIABETES"],
        )
        # Sugar should be adjusted
        sugar = profile.micros.get("sugar_g")
        assert sugar is not None
        assert sugar.priority == "HIGH"
        assert sugar.confidence == "MEDICAL_RULE"
        # Should have a validated consideration
        validated = [sc for sc in profile.special_considerations if sc.type == "VALIDATED_CONDITION"]
        assert len(validated) >= 1

    def test_unvalidated_condition_no_adjustment(self):
        """GERD (unvalidated) should NOT auto-adjust but should warn."""
        profile = NutrientProfileService.build_profile(
            weight_kg=70, height_cm=170, age=35,
            gender="FEMALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
            medical_conditions=["GERD"],
        )
        # Should have unvalidated consideration
        unvalidated = [sc for sc in profile.special_considerations if sc.type == "UNVALIDATED_CONDITION"]
        assert len(unvalidated) >= 1
        assert "consult your doctor" in unvalidated[0].message.lower()

    def test_none_condition_ignored(self):
        """NONE medical condition should be silently ignored."""
        profile = NutrientProfileService.build_profile(
            weight_kg=70, height_cm=170, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
            medical_conditions=["NONE"],
        )
        assert len(profile.special_considerations) == 0

    def test_anemia_boosts_iron(self):
        """Anemia (validated) should boost iron target."""
        # Without anemia
        base = NutrientProfileService.build_profile(
            weight_kg=55, height_cm=160, age=28,
            gender="FEMALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
        )
        # With anemia
        anemia = NutrientProfileService.build_profile(
            weight_kg=55, height_cm=160, age=28,
            gender="FEMALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
            medical_conditions=["ANEMIA"],
        )
        assert anemia.micros["iron_mg"].target > base.micros["iron_mg"].target
        assert anemia.micros["iron_mg"].priority == "HIGH"


class TestMicronutrients:
    def test_has_all_micro_targets(self):
        """Profile should have targets for all 12 tracked micronutrients."""
        profile = NutrientProfileService.build_profile(
            weight_kg=70, height_cm=170, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
        )
        expected_micros = [
            "calcium_mg", "iron_mg", "magnesium_mg", "potassium_mg",
            "zinc_mg", "vitamin_a_mcg", "vitamin_b12_mcg", "vitamin_c_mg",
            "vitamin_d_mcg", "folate_mcg", "phosphorus_mg", "sugar_g",
        ]
        for nutrient in expected_micros:
            assert nutrient in profile.micros, f"Missing micro: {nutrient}"
            assert profile.micros[nutrient].target > 0

    def test_per_meal_splits_sum_to_one(self):
        """Meal splits should sum to 1.0."""
        profile = NutrientProfileService.build_profile(
            weight_kg=70, height_cm=170, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
        )
        total = sum(profile.per_meal.values())
        assert abs(total - 1.0) < 0.01
