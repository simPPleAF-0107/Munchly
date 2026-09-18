from typing import List, Dict, Optional, Any
from dataclasses import dataclass


# Human-readable reason labels
REASON_LABELS = {
    # Positive reasons (why recommended)
    "HIGH_PROTEIN": "High in protein for your goals",
    "CUISINE_LOVE": "Matches your cuisine preferences",
    "IRON_GAP_FILL": "Helps fill your iron gap",
    "CALCIUM_GAP_FILL": "Helps fill your calcium gap",
    "VITAMIN_GAP_FILL": "Helps fill a vitamin gap",
    "PANTRY_OVERLAP": "Uses ingredients you already have",
    "BUDGET_FRIENDLY": "Great value for your budget",
    "QUICK_PREP": "Quick to prepare",
    "REGIONAL_MATCH": "Popular in your region",
    "VARIETY_BOOST": "Adds variety to your week",
    "NUTRIENT_COVERAGE": "Good contribution to daily nutrient needs",
    "INGREDIENT_REUSE": "Shares ingredients with other meals this week",
    "FIBER_RICH": "Good source of fiber",
    "MEDICAL_FIT": "Fits your health requirements",
    
    # Negative reasons (why excluded)
    "EXCEEDS_CALORIES": "Would exceed your calorie target",
    "EXCEEDS_SODIUM": "Would exceed today's sodium target",
    "EXCEEDS_SUGAR": "Would exceed today's sugar limit",
    "OVER_BUDGET": "Would push your weekly grocery cost above budget",
    "ALLERGEN_PRESENT": "Contains an allergen",
    "DIET_INCOMPATIBLE": "Not compatible with your diet type",
    "TOO_LONG_PREP": "Takes too long to prepare",
    "REPEATED_RECENTLY": "You've already had this recently",
    "PROTEIN_SOURCE_REPEAT": "Same protein source already used this week",
    "MEDICAL_CONFLICT": "Conflicts with a medical nutrition constraint",
    "LOW_AVAILABILITY": "Hard to find ingredients in your area",
}


@dataclass
class RecommendationExplanation:
    """Human-readable explanation for why a recipe was recommended."""
    recipe_id: str
    recipe_name: str
    reasons: List[str]         # Top 3-5 reason codes
    reason_labels: List[str]   # Human-readable labels
    top_scores: Dict[str, float]  # Top scoring dimensions


@dataclass
class ExclusionExplanation:
    """Human-readable explanation for why a recipe was NOT recommended."""
    recipe_id: str
    recipe_name: str
    reasons: List[str]         # Reason codes
    reason_labels: List[str]   # Human-readable labels
    is_hard_exclusion: bool    # True if excluded by constraints, False if just scored low


class ExplainabilityService:
    """Provides deterministic explanations for meal recommendations.
    
    Every recommendation explanation comes from scoring data,
    not from AI generation. Gemini can EXPLAIN these to users
    in natural language, but the reasons themselves are deterministic.
    """

    @staticmethod
    def explain_recommendation(
        recipe_id: str,
        recipe_name: str,
        scores: Dict[str, float],
        max_reasons: int = 5,
    ) -> RecommendationExplanation:
        """Generate top reasons why a recipe was recommended.
        
        Takes the per-dimension scores from the recommendation engine
        and converts them to human-readable reasons.
        """
        # Map scoring dimensions to reason codes
        dimension_to_reason = {
            "nutrition_fit": "NUTRIENT_COVERAGE",
            "budget_efficiency": "BUDGET_FRIENDLY",
            "food_preference": "CUISINE_LOVE",
            "cuisine_preference": "CUISINE_LOVE",
            "regional_relevance": "REGIONAL_MATCH",
            "local_availability": "REGIONAL_MATCH",
            "ingredient_reuse": "INGREDIENT_REUSE",
            "prep_time_fit": "QUICK_PREP",
            "pantry_overlap": "PANTRY_OVERLAP",
            "variety": "VARIETY_BOOST",
            "medical_fit": "MEDICAL_FIT",
            "protein_source_rotation": "HIGH_PROTEIN",
            "nutrient_coverage": "NUTRIENT_COVERAGE",
            "nutrient_gap_fill": "VITAMIN_GAP_FILL",
        }
        
        # Sort by score descending, take top N
        sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        reasons = []
        seen_reasons = set()
        top_scores = {}
        
        for dim, score in sorted_dims:
            if score <= 0:
                continue
            reason = dimension_to_reason.get(dim)
            if reason and reason not in seen_reasons:
                reasons.append(reason)
                seen_reasons.add(reason)
                top_scores[dim] = round(score, 3)
            if len(reasons) >= max_reasons:
                break
        
        reason_labels = [
            REASON_LABELS.get(r, r.replace("_", " ").title())
            for r in reasons
        ]
        
        return RecommendationExplanation(
            recipe_id=recipe_id,
            recipe_name=recipe_name,
            reasons=reasons,
            reason_labels=reason_labels,
            top_scores=top_scores,
        )

    @staticmethod
    def explain_exclusion(
        recipe_id: str,
        recipe_name: str,
        exclusion_reasons: List[str],
    ) -> ExclusionExplanation:
        """Explain why a recipe was NOT recommended.
        
        Called for recipes a user might expect to see (favorites,
        frequently eaten) but were filtered out or scored low.
        """
        hard_exclusion_reasons = {
            "ALLERGEN_PRESENT", "DIET_INCOMPATIBLE", "MEDICAL_CONFLICT",
        }
        
        is_hard = any(r in hard_exclusion_reasons for r in exclusion_reasons)
        
        reason_labels = [
            REASON_LABELS.get(r, r.replace("_", " ").title())
            for r in exclusion_reasons
        ]
        
        return ExclusionExplanation(
            recipe_id=recipe_id,
            recipe_name=recipe_name,
            reasons=exclusion_reasons,
            reason_labels=reason_labels,
            is_hard_exclusion=is_hard,
        )

    @classmethod
    def explain_why_not_favorite(
        cls,
        recipe_id: str,
        recipe_name: str,
        constraint_failures: Optional[List[str]] = None,
        scoring_issues: Optional[Dict[str, str]] = None,
    ) -> ExclusionExplanation:
        """Specifically for 'Why wasn't my favorite recommended?'
        
        Example output:
            You usually like Fish Curry, but Munchly didn't recommend it tonight because:
            - It would exceed today's sodium target
            - You've already had fish twice this week
            - It would push your weekly grocery cost above budget
        """
        reasons = []
        
        if constraint_failures:
            reasons.extend(constraint_failures)
        
        if scoring_issues:
            for issue_type, _ in scoring_issues.items():
                if issue_type not in reasons:
                    reasons.append(issue_type)
        
        if not reasons:
            reasons = ["SCORED_LOW_OVERALL"]
        
        return cls.explain_exclusion(recipe_id, recipe_name, reasons)
