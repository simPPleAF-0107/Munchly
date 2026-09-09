from dataclasses import dataclass, field
from typing import Dict

@dataclass
class ScoringWeights:
    weights: Dict[str, float] = field(default_factory=lambda: {
        "nutrition_fit": 0.20,
        "budget_efficiency": 0.15,
        "food_preference": 0.12,
        "cuisine_preference": 0.10,
        "regional_relevance": 0.08,
        "local_availability": 0.05,
        "ingredient_reuse": 0.05,
        "prep_time_fit": 0.05,
        "pantry_overlap": 0.05,
        "variety": 0.05,
        "medical_fit": 0.05,
        "protein_source_rotation": 0.05,
    })

DEFAULT_SCORING_WEIGHTS = ScoringWeights().weights
