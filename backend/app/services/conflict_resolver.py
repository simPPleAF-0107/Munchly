from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from app.models.enums import (
    DietType, HealthGoal, DietaryRestriction, ConflictType,
)


@dataclass
class Conflict:
    """A detected conflict between user requirements."""
    conflict_type: ConflictType
    severity: str             # "WARNING" | "BLOCKING"
    description: str
    constraint_a: str         # First conflicting constraint
    constraint_b: str         # Second conflicting constraint
    options: List[Dict[str, str]]  # Possible resolutions
    recommendation: Optional[str] = None


@dataclass
class ConflictReport:
    """Summary of all detected conflicts for a user profile."""
    has_conflicts: bool
    conflicts: List[Conflict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ConflictResolver:
    """Detects incompatible combinations of user requirements/preferences.
    
    When conflicts are detected, they are surfaced EXPLICITLY to the user.
    The user picks the tradeoff — the system never silently weakens a constraint.
    
    Examples:
    - Vegan + high protein + low budget -> conflict
    - Keto + low fat -> contradiction
    - Many food avoidances + variety goal -> tension
    """

    # Known conflict patterns
    CONFLICT_RULES = [
        {
            "type": ConflictType.DIET_VS_PROTEIN,
            "condition": lambda ctx: (
                ctx.get("diet_type") == DietType.VEGAN.value
                and ctx.get("health_goal") in (
                    HealthGoal.BUILD_MUSCLE.value,
                    HealthGoal.GAIN_WEIGHT.value,
                )
            ),
            "severity": "WARNING",
            "description": "Vegan diet with muscle-building goal requires careful protein planning.",
            "a": "Vegan diet",
            "b": "High protein goal",
            "options": [
                {"label": "Keep both — Munchly will prioritize plant protein sources", "action": "KEEP_BOTH"},
                {"label": "Relax diet to vegetarian (adds dairy/eggs for protein)", "action": "RELAX_DIET"},
                {"label": "Reduce protein target slightly", "action": "REDUCE_PROTEIN"},
            ],
            "recommendation": "Keep both — Munchly will prioritize dal, tofu, tempeh, soy chunks, and other plant proteins.",
        },
        {
            "type": ConflictType.BUDGET_VS_NUTRITION,
            "condition": lambda ctx: (
                ctx.get("weekly_budget", float('inf')) < 800
                and ctx.get("health_goal") in (
                    HealthGoal.BUILD_MUSCLE.value,
                    HealthGoal.GAIN_WEIGHT.value,
                )
            ),
            "severity": "WARNING",
            "description": "Very tight budget with high-calorie goal may limit food variety and protein sources.",
            "a": "Budget under ₹800/week",
            "b": "Muscle/weight gain goal",
            "options": [
                {"label": "Keep budget — Munchly will find affordable high-protein options", "action": "KEEP_BUDGET"},
                {"label": "Increase budget slightly for better protein sources", "action": "INCREASE_BUDGET"},
                {"label": "Adjust goal to maintenance", "action": "ADJUST_GOAL"},
            ],
        },
        {
            "type": ConflictType.RESTRICTIONS_VS_VARIETY,
            "condition": lambda ctx: (
                len(ctx.get("dietary_restrictions", [])) >= 3
            ),
            "severity": "WARNING",
            "description": "Multiple dietary restrictions significantly reduce available recipes.",
            "a": "Multiple dietary restrictions",
            "b": "Recipe variety",
            "options": [
                {"label": "Keep all restrictions — accept less variety", "action": "KEEP_ALL"},
                {"label": "Review and relax non-essential restrictions", "action": "REVIEW_RESTRICTIONS"},
            ],
        },
        {
            "type": ConflictType.TIME_VS_NUTRITION,
            "condition": lambda ctx: (
                ctx.get("max_prep_time_min", 60) <= 10
                and ctx.get("health_goal") != HealthGoal.EAT_HEALTHIER.value
            ),
            "severity": "WARNING",
            "description": "Very short cooking time (≤10 min) limits nutritionally complete meals.",
            "a": "Max 10 min prep time",
            "b": "Nutritional targets",
            "options": [
                {"label": "Keep time limit — focus on no-cook/quick meals", "action": "KEEP_TIME"},
                {"label": "Allow slightly longer prep (15-20 min)", "action": "EXTEND_TIME"},
                {"label": "Consider meal prep on weekends", "action": "MEAL_PREP"},
            ],
        },
        {
            "type": ConflictType.MULTIPLE_RESTRICTIONS,
            "condition": lambda ctx: (
                DietaryRestriction.KETO.value in ctx.get("dietary_restrictions", [])
                and DietaryRestriction.LOW_CARB.value in ctx.get("dietary_restrictions", [])
            ),
            "severity": "WARNING",
            "description": "Keto and low-carb are redundant — keto is already very low carb.",
            "a": "Keto diet",
            "b": "Low-carb restriction",
            "options": [
                {"label": "Keep just keto (stricter)", "action": "KEEP_KETO"},
                {"label": "Keep just low-carb (more flexible)", "action": "KEEP_LOW_CARB"},
            ],
        },
    ]

    @classmethod
    def detect_conflicts(
        cls,
        diet_type: Optional[str] = None,
        health_goal: Optional[str] = None,
        weekly_budget: Optional[float] = None,
        max_prep_time_min: Optional[int] = None,
        dietary_restrictions: Optional[List[str]] = None,
        allergens: Optional[List[str]] = None,
        avoidance_count: int = 0,
    ) -> ConflictReport:
        """Detect conflicts in user's requirement combination.
        
        Surfaces conflicts EXPLICITLY. Never silently weakens a constraint.
        The user picks the tradeoff.
        """
        ctx = {
            "diet_type": diet_type,
            "health_goal": health_goal,
            "weekly_budget": weekly_budget,
            "max_prep_time_min": max_prep_time_min,
            "dietary_restrictions": dietary_restrictions or [],
            "allergens": allergens or [],
            "avoidance_count": avoidance_count,
        }
        
        conflicts = []
        warnings = []
        
        for rule in cls.CONFLICT_RULES:
            try:
                if rule["condition"](ctx):
                    conflicts.append(Conflict(
                        conflict_type=rule["type"],
                        severity=rule["severity"],
                        description=rule["description"],
                        constraint_a=rule["a"],
                        constraint_b=rule["b"],
                        options=rule["options"],
                        recommendation=rule.get("recommendation"),
                    ))
            except (KeyError, TypeError):
                continue
        
        # Additional warnings
        if avoidance_count >= 5:
            warnings.append(
                f"You have {avoidance_count} food avoidances. "
                "This significantly limits meal variety. "
                "Consider reviewing whether all avoidances are still relevant."
            )
        
        return ConflictReport(
            has_conflicts=len(conflicts) > 0,
            conflicts=conflicts,
            warnings=warnings,
        )
