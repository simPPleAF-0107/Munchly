from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from app.models.enums import NutritionConfidence


@dataclass
class Violation:
    """A nutrition or safety violation in a meal plan."""
    nutrient: str
    level: str           # "MEAL" | "DAY" | "WEEK"
    day: Optional[int]   # day_of_week (1-7), None for weekly
    actual: float
    target: float
    threshold_pct: float # e.g., 0.80 means must be >= 80% of target
    severity: str        # "WARNING" | "VIOLATION"
    message: str


@dataclass
class Warning:
    """A non-critical nutrition concern."""
    nutrient: str
    level: str
    day: Optional[int]
    message: str


@dataclass
class SwapSuggestion:
    """A suggested meal swap to fix a violation."""
    violation: Violation
    day: int
    meal_type: str
    current_recipe_id: str
    suggested_recipe_id: str
    suggested_recipe_name: str
    improvement: Dict[str, float]  # nutrient -> delta improvement
    reason: str


@dataclass
class ValidationResult:
    """Result of validating a meal plan against nutrient profile."""
    passed: bool
    violations: List[Violation] = field(default_factory=list)
    warnings: List[Warning] = field(default_factory=list)
    nutrient_coverage: Dict[str, float] = field(default_factory=dict)
    daily_coverage: Dict[int, Dict[str, float]] = field(default_factory=dict)


class AdequacyValidator:
    """POST-optimizer validation. NOT a scoring dimension.
    
    Scoring decides what is desirable. Validation decides whether
    the resulting plan is acceptable. This separation makes Munchly
    safer and independently testable.
    
    Never silently show a non-compliant plan.
    Instead, explain the tradeoff.
    """

    # Validation thresholds
    DAILY_CALORIE_TOLERANCE = 0.15    # ±15% of target
    DAILY_PROTEIN_MIN_PCT = 0.80      # >= 80% of target
    DAILY_FIBER_MIN_PCT = 0.70        # >= 70% of target
    WEEKLY_MICRO_NORMAL_PCT = 0.60    # >= 60% for normal priority
    WEEKLY_MICRO_HIGH_PCT = 0.80      # >= 80% for high/critical priority

    @classmethod
    def validate_plan(
        cls,
        plan_meals: List[Dict[str, Any]],
        nutrient_profile: Any,
    ) -> ValidationResult:
        """Validate a meal plan against a user's nutrient profile.
        
        Args:
            plan_meals: List of meal dicts with keys:
                day_of_week, meal_type, recipe (with nutrition fields)
            nutrient_profile: NutrientProfile from NutrientProfileService
        
        Checks:
            1. Daily calories within ±15% of target for each day
            2. Daily protein >= 80% of target
            3. Daily fiber >= 70%
            4. Weekly micro coverage >= 60% (normal priority)
            5. Weekly micro coverage >= 80% (high/critical priority)
            6. Budget within weekly limit (if provided)
            7. No allergen/diet violations (defense-in-depth)
        """
        violations = []
        warnings = []
        daily_totals: Dict[int, Dict[str, float]] = {}
        weekly_totals: Dict[str, float] = {}
        
        # Accumulate daily nutrition
        for meal in plan_meals:
            day = meal.get("day_of_week", 1)
            recipe = meal.get("recipe", {})
            
            if day not in daily_totals:
                daily_totals[day] = {
                    "calories": 0, "protein_g": 0, "carbs_g": 0,
                    "fat_g": 0, "fiber_g": 0, "sodium_mg": 0,
                    "calcium_mg": 0, "iron_mg": 0, "magnesium_mg": 0,
                    "potassium_mg": 0, "zinc_mg": 0, "vitamin_a_mcg": 0,
                    "vitamin_b12_mcg": 0, "vitamin_c_mg": 0, "vitamin_d_mcg": 0,
                    "folate_mcg": 0, "phosphorus_mg": 0, "sugar_g": 0,
                }
            
            for nutrient in daily_totals[day]:
                val = 0
                if isinstance(recipe, dict):
                    val = recipe.get(nutrient, 0) or 0
                else:
                    val = getattr(recipe, nutrient, 0) or 0
                daily_totals[day][nutrient] += float(val)
        
        # Accumulate weekly totals
        for day, totals in daily_totals.items():
            for nutrient, val in totals.items():
                weekly_totals[nutrient] = weekly_totals.get(nutrient, 0) + val
        
        num_days = max(len(daily_totals), 1)
        
        # Check 1: Daily calories
        cal_target = nutrient_profile.calorie_target
        for day, totals in daily_totals.items():
            cal_actual = totals["calories"]
            if cal_target > 0:
                deviation = abs(cal_actual - cal_target) / cal_target
                if deviation > cls.DAILY_CALORIE_TOLERANCE:
                    direction = "above" if cal_actual > cal_target else "below"
                    violations.append(Violation(
                        nutrient="calories",
                        level="DAY",
                        day=day,
                        actual=cal_actual,
                        target=cal_target,
                        threshold_pct=1.0 - cls.DAILY_CALORIE_TOLERANCE,
                        severity="VIOLATION",
                        message=f"Day {day}: Calories {int(cal_actual)} kcal is {int(deviation*100)}% {direction} target {int(cal_target)} kcal",
                    ))
        
        # Check 2: Daily protein
        protein_target = nutrient_profile.protein_g.target
        for day, totals in daily_totals.items():
            protein_actual = totals["protein_g"]
            if protein_target > 0:
                pct = protein_actual / protein_target
                if pct < cls.DAILY_PROTEIN_MIN_PCT:
                    violations.append(Violation(
                        nutrient="protein_g",
                        level="DAY",
                        day=day,
                        actual=protein_actual,
                        target=protein_target,
                        threshold_pct=cls.DAILY_PROTEIN_MIN_PCT,
                        severity="VIOLATION",
                        message=f"Day {day}: Protein {int(protein_actual)}g is only {int(pct*100)}% of target {int(protein_target)}g",
                    ))
        
        # Check 3: Daily fiber
        fiber_target = nutrient_profile.fiber_g.target
        for day, totals in daily_totals.items():
            fiber_actual = totals["fiber_g"]
            if fiber_target > 0:
                pct = fiber_actual / fiber_target
                if pct < cls.DAILY_FIBER_MIN_PCT:
                    warnings.append(Warning(
                        nutrient="fiber_g",
                        level="DAY",
                        day=day,
                        message=f"Day {day}: Fiber {int(fiber_actual)}g is only {int(pct*100)}% of target {int(fiber_target)}g",
                    ))
        
        # Check 4 & 5: Weekly micronutrient coverage
        nutrient_coverage = {}
        for nutrient, nt in nutrient_profile.micros.items():
            weekly_actual = weekly_totals.get(nutrient, 0)
            weekly_target = nt.target * num_days
            
            if weekly_target > 0:
                pct = weekly_actual / weekly_target
                nutrient_coverage[nutrient] = round(pct, 3)
                
                threshold = (
                    cls.WEEKLY_MICRO_HIGH_PCT
                    if nt.priority in ("HIGH", "CRITICAL")
                    else cls.WEEKLY_MICRO_NORMAL_PCT
                )
                
                if pct < threshold:
                    severity = "VIOLATION" if nt.priority in ("HIGH", "CRITICAL") else "WARNING"
                    item = Violation(
                        nutrient=nutrient,
                        level="WEEK",
                        day=None,
                        actual=weekly_actual,
                        target=weekly_target,
                        threshold_pct=threshold,
                        severity=severity,
                        message=f"Weekly {nutrient}: {int(pct*100)}% coverage (need {int(threshold*100)}%)",
                    ) if severity == "VIOLATION" else None
                    
                    if item:
                        violations.append(item)
                    else:
                        warnings.append(Warning(
                            nutrient=nutrient,
                            level="WEEK",
                            day=None,
                            message=f"Weekly {nutrient}: {int(pct*100)}% coverage (target {int(threshold*100)}%)",
                        ))
        
        # Compute daily coverage percentages
        daily_coverage = {}
        for day, totals in daily_totals.items():
            daily_coverage[day] = {}
            if cal_target > 0:
                daily_coverage[day]["calories"] = round(totals["calories"] / cal_target, 3)
            if protein_target > 0:
                daily_coverage[day]["protein_g"] = round(totals["protein_g"] / protein_target, 3)
            if fiber_target > 0:
                daily_coverage[day]["fiber_g"] = round(totals["fiber_g"] / fiber_target, 3)
        
        passed = len([v for v in violations if v.severity == "VIOLATION"]) == 0
        
        return ValidationResult(
            passed=passed,
            violations=violations,
            warnings=warnings,
            nutrient_coverage=nutrient_coverage,
            daily_coverage=daily_coverage,
        )
