from dataclasses import dataclass, field
from typing import Dict

@dataclass
class ScoringWeights:
    """14-dimensional recommendation scoring weights.
    
    Phase 1 additions:
    - nutrient_coverage: How well the recipe contributes to daily nutrient needs
    - nutrient_gap_fill: How well the recipe fills specific nutrient gaps this week
    
    Weights must sum to 1.0.
    """
    weights: Dict[str, float] = field(default_factory=lambda: {
        "nutrition_fit": 0.12,           # Macro fit (calories, protein, carbs, fat)
        "nutrient_coverage": 0.08,       # NEW: Overall micro contribution
        "nutrient_gap_fill": 0.08,       # NEW: Fills specific gaps this week
        "budget_efficiency": 0.12,
        "food_preference": 0.10,
        "cuisine_preference": 0.08,
        "regional_relevance": 0.07,
        "local_availability": 0.05,
        "ingredient_reuse": 0.05,
        "prep_time_fit": 0.05,
        "pantry_overlap": 0.05,
        "variety": 0.05,
        "medical_fit": 0.05,
        "protein_source_rotation": 0.05,
    })

DEFAULT_SCORING_WEIGHTS = ScoringWeights().weights

