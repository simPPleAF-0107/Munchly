import pytest
from app.services.lifestyle_service import LifestyleService


class TestFitnessAdjustments:
    def test_bulking_adds_calories(self):
        """Bulking status should add calories."""
        adj = LifestyleService.calculate_fitness_adjustments(
            weight_kg=80,
            bulk_cut_status="BULKING",
        )
        assert adj.calorie_adjustment > 0
        assert any("bulking" in r.lower() for r in adj.reasons)

    def test_cutting_reduces_calories(self):
        """Cutting status should reduce calories."""
        adj = LifestyleService.calculate_fitness_adjustments(
            weight_kg=80,
            bulk_cut_status="CUTTING",
        )
        assert adj.calorie_adjustment < 0

    def test_high_intensity_muscle_boosts_protein(self):
        """High intensity + build muscle = protein boost."""
        adj = LifestyleService.calculate_fitness_adjustments(
            weight_kg=80,
            workout_intensity="HIGH",
            fitness_goal="BUILD_MUSCLE",
        )
        assert adj.protein_boost_g > 0
        assert any("protein" in r.lower() for r in adj.reasons)

    def test_no_fitness_no_adjustments(self):
        """No fitness data = no adjustments."""
        adj = LifestyleService.calculate_fitness_adjustments(
            weight_kg=70,
        )
        assert adj.calorie_adjustment == 0
        assert adj.protein_boost_g == 0

    def test_morning_workout_adjusts_breakfast(self):
        """Morning workout should increase breakfast split."""
        adj = LifestyleService.calculate_fitness_adjustments(
            weight_kg=70,
            workout_timing="MORNING",
        )
        assert adj.meal_splits["BREAKFAST"] > 0.25  # Default is 0.25
        assert any("morning" in r.lower() for r in adj.reasons)

    def test_evening_workout_adjusts_dinner(self):
        """Evening workout should increase dinner split."""
        adj = LifestyleService.calculate_fitness_adjustments(
            weight_kg=70,
            workout_timing="EVENING",
        )
        assert adj.meal_splits["DINNER"] > 0.35  # Default is 0.35

    def test_protein_scales_with_frequency(self):
        """Low exercise frequency should scale down protein boost."""
        full = LifestyleService.calculate_fitness_adjustments(
            weight_kg=80,
            workout_intensity="HIGH",
            fitness_goal="BUILD_MUSCLE",
            exercise_frequency=6,
        )
        scaled = LifestyleService.calculate_fitness_adjustments(
            weight_kg=80,
            workout_intensity="HIGH",
            fitness_goal="BUILD_MUSCLE",
            exercise_frequency=2,
        )
        assert scaled.protein_boost_g < full.protein_boost_g

    def test_meal_splits_sum_to_one(self):
        """Meal splits should always sum to ~1.0."""
        for timing in ["MORNING", "AFTERNOON", "EVENING", None]:
            adj = LifestyleService.calculate_fitness_adjustments(
                weight_kg=70,
                workout_timing=timing,
            )
            total = sum(adj.meal_splits.values())
            assert abs(total - 1.0) < 0.01, f"Splits sum to {total} for timing={timing}"


class TestMealPracticality:
    def test_fast_recipe_scores_high(self):
        """Recipe within time limit should score well."""
        score = LifestyleService.score_meal_practicality(
            recipe_prep_time_min=15,
            recipe_difficulty="EASY",
            user_max_prep_time=30,
            user_cooking_effort="MODERATE",
        )
        assert score.prep_time_fit == 1.0
        assert score.total > 0.8

    def test_slow_recipe_scores_low(self):
        """Recipe way over time limit should score poorly."""
        score = LifestyleService.score_meal_practicality(
            recipe_prep_time_min=60,
            recipe_difficulty="HARD",
            user_max_prep_time=15,
            user_cooking_effort="MINIMAL",
        )
        assert score.prep_time_fit < 0.5
        assert score.total < 0.5

    def test_missing_equipment_flagged(self):
        """Missing required equipment should reduce score."""
        score = LifestyleService.score_meal_practicality(
            recipe_prep_time_min=30,
            recipe_difficulty="MEDIUM",
            recipe_needs_oven=True,
            user_has_oven=False,
        )
        assert score.equipment_match < 1.0
        assert "NEEDS_OVEN" in score.flags

    def test_quick_meal_flag(self):
        """Very fast recipe should get QUICK_MEAL flag."""
        score = LifestyleService.score_meal_practicality(
            recipe_prep_time_min=10,
            recipe_difficulty="EASY",
            user_max_prep_time=30,
        )
        assert "QUICK_MEAL" in score.flags


class TestIngredientReuseBoost:
    def test_very_important_doubles_weight(self):
        """VERY_IMPORTANT food waste preference should 2x ingredient reuse weight."""
        boost = LifestyleService.get_ingredient_reuse_weight_boost("VERY_IMPORTANT")
        assert boost == 2.0

    def test_not_important_no_boost(self):
        """NOT_IMPORTANT should give 1.0x (no boost)."""
        boost = LifestyleService.get_ingredient_reuse_weight_boost("NOT_IMPORTANT")
        assert boost == 1.0

    def test_none_defaults(self):
        """None should default to 1.0."""
        boost = LifestyleService.get_ingredient_reuse_weight_boost(None)
        assert boost == 1.0
