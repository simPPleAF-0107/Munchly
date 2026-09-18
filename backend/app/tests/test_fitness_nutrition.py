import pytest
from app.services.nutrient_profile_service import NutrientProfileService, SAFETY_FLOORS
from app.models.enums import Gender


class TestFitnessAwareProfile:
    def test_bulking_increases_calories(self):
        """Bulking should add calories ON TOP of health goal."""
        base = NutrientProfileService.build_profile(
            weight_kg=80, height_cm=180, age=25,
            gender="MALE", activity_level="VERY_ACTIVE",
            health_goal="GAIN_WEIGHT",
        )
        with_fitness = NutrientProfileService.build_profile_with_lifestyle(
            weight_kg=80, height_cm=180, age=25,
            gender="MALE", activity_level="VERY_ACTIVE",
            health_goal="GAIN_WEIGHT",
            bulk_cut_status="BULKING",
        )
        assert with_fitness.calorie_target > base.calorie_target

    def test_cutting_decreases_calories(self):
        """Cutting should reduce calories ON TOP of health goal."""
        base = NutrientProfileService.build_profile(
            weight_kg=80, height_cm=180, age=25,
            gender="MALE", activity_level="VERY_ACTIVE",
            health_goal="LOSE_WEIGHT",
        )
        with_fitness = NutrientProfileService.build_profile_with_lifestyle(
            weight_kg=80, height_cm=180, age=25,
            gender="MALE", activity_level="VERY_ACTIVE",
            health_goal="LOSE_WEIGHT",
            bulk_cut_status="CUTTING",
        )
        # Should be lower, but not below safety floor
        assert with_fitness.calorie_target <= base.calorie_target
        assert with_fitness.calorie_target >= SAFETY_FLOORS[Gender.MALE]

    def test_gym_boosts_protein(self):
        """High intensity gym + build muscle should increase protein."""
        base = NutrientProfileService.build_profile(
            weight_kg=80, height_cm=180, age=25,
            gender="MALE", activity_level="VERY_ACTIVE",
            health_goal="BUILD_MUSCLE",
        )
        with_fitness = NutrientProfileService.build_profile_with_lifestyle(
            weight_kg=80, height_cm=180, age=25,
            gender="MALE", activity_level="VERY_ACTIVE",
            health_goal="BUILD_MUSCLE",
            workout_intensity="HIGH",
            fitness_goal="BUILD_MUSCLE",
        )
        assert with_fitness.protein_g.target > base.protein_g.target

    def test_safety_floor_preserved_with_extreme_cutting(self):
        """Even extreme cutting + lose weight should not go below safety floor."""
        profile = NutrientProfileService.build_profile_with_lifestyle(
            weight_kg=50, height_cm=155, age=60,
            gender="FEMALE", activity_level="SEDENTARY",
            health_goal="LOSE_WEIGHT",
            bulk_cut_status="CUTTING",
        )
        assert profile.calorie_target >= SAFETY_FLOORS[Gender.FEMALE]

    def test_morning_workout_shifts_breakfast(self):
        """Morning workout should shift meal splits."""
        with_fitness = NutrientProfileService.build_profile_with_lifestyle(
            weight_kg=70, height_cm=175, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
            workout_timing="MORNING",
        )
        assert with_fitness.per_meal["BREAKFAST"] > 0.25

    def test_no_fitness_same_as_base(self):
        """No fitness data should produce same results as base build_profile."""
        base = NutrientProfileService.build_profile(
            weight_kg=70, height_cm=170, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
        )
        with_fitness = NutrientProfileService.build_profile_with_lifestyle(
            weight_kg=70, height_cm=170, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
        )
        assert with_fitness.calorie_target == base.calorie_target
        assert with_fitness.protein_g.target == base.protein_g.target

    def test_fitness_considerations_added(self):
        """Fitness adjustments should add special considerations."""
        profile = NutrientProfileService.build_profile_with_lifestyle(
            weight_kg=80, height_cm=180, age=25,
            gender="MALE", activity_level="VERY_ACTIVE",
            health_goal="BUILD_MUSCLE",
            workout_intensity="HIGH",
            fitness_goal="BUILD_MUSCLE",
            bulk_cut_status="BULKING",
            workout_timing="EVENING",
        )
        lifestyle_considerations = [sc for sc in profile.special_considerations if sc.type == "LIFESTYLE"]
        assert len(lifestyle_considerations) >= 2  # At least bulking + protein boost
