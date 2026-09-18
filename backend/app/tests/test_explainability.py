import pytest
from app.services.explainability_service import ExplainabilityService


class TestRecommendationExplanation:
    def test_top_reasons_returned(self):
        """Should return top reasons from scoring dimensions."""
        scores = {
            "nutrition_fit": 0.95,
            "cuisine_preference": 0.80,
            "budget_efficiency": 0.70,
            "prep_time_fit": 0.60,
            "variety": 0.10,
        }
        result = ExplainabilityService.explain_recommendation(
            recipe_id="r1", recipe_name="Dal Tadka", scores=scores
        )
        assert len(result.reasons) >= 3
        assert len(result.reason_labels) == len(result.reasons)
        assert result.reasons[0] in ["NUTRIENT_COVERAGE"]  # Highest score

    def test_zero_score_excluded(self):
        """Dimensions with score 0 should not appear in reasons."""
        scores = {
            "nutrition_fit": 0.5,
            "pantry_overlap": 0.0,
            "medical_fit": 0.0,
        }
        result = ExplainabilityService.explain_recommendation(
            recipe_id="r1", recipe_name="Test", scores=scores
        )
        assert "MEDICAL_FIT" not in result.reasons
        assert "PANTRY_OVERLAP" not in result.reasons


class TestExclusionExplanation:
    def test_hard_exclusion(self):
        """Allergen exclusion should be marked as hard."""
        result = ExplainabilityService.explain_exclusion(
            recipe_id="r1", recipe_name="Peanut Curry",
            exclusion_reasons=["ALLERGEN_PRESENT"],
        )
        assert result.is_hard_exclusion is True

    def test_soft_exclusion(self):
        """Budget exclusion should NOT be hard."""
        result = ExplainabilityService.explain_exclusion(
            recipe_id="r1", recipe_name="Expensive Dish",
            exclusion_reasons=["OVER_BUDGET"],
        )
        assert result.is_hard_exclusion is False

    def test_why_not_favorite(self):
        """Why-not-favorite should combine constraint and scoring reasons."""
        result = ExplainabilityService.explain_why_not_favorite(
            recipe_id="r1", recipe_name="Fish Curry",
            constraint_failures=["EXCEEDS_SODIUM", "REPEATED_RECENTLY"],
            scoring_issues={"OVER_BUDGET": "Would exceed budget by \u20b9200"},
        )
        assert "EXCEEDS_SODIUM" in result.reasons
        assert "REPEATED_RECENTLY" in result.reasons
        assert "OVER_BUDGET" in result.reasons
        assert len(result.reason_labels) == 3
