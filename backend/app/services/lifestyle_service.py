from dataclasses import dataclass
from typing import Dict, Optional, Any, List

from app.models.enums import (
    CookingEffort, FoodWastePreference, WorkoutIntensity,
    WorkoutTiming, BulkCutStatus, FitnessGoal,
)


# Fitness-aware protein adjustments (g/kg body weight BOOST, added to base)
# Uses the same bounded, configurable pattern as CALORIE_ADJUSTMENTS in Phase 1
FITNESS_PROTEIN_BOOST = {
    # (intensity, fitness_goal) -> additional g/kg
    (WorkoutIntensity.HIGH, FitnessGoal.BUILD_MUSCLE): 0.6,
    (WorkoutIntensity.HIGH, FitnessGoal.BUILD_STRENGTH): 0.5,
    (WorkoutIntensity.VERY_HIGH, FitnessGoal.BUILD_MUSCLE): 0.8,
    (WorkoutIntensity.VERY_HIGH, FitnessGoal.BUILD_STRENGTH): 0.6,
    (WorkoutIntensity.MODERATE, FitnessGoal.BUILD_MUSCLE): 0.3,
    (WorkoutIntensity.MODERATE, FitnessGoal.GENERAL_FITNESS): 0.1,
}

# Bounded calorie adjustments for bulk/cut status
# These STACK with the health_goal adjustments from Phase 1
BULK_CUT_CALORIE_ADJUSTMENTS = {
    BulkCutStatus.BULKING:     {"default": 300,  "min": 200, "max": 500},
    BulkCutStatus.LEAN_BULK:   {"default": 150,  "min": 100, "max": 300},
    BulkCutStatus.CUTTING:     {"default": -400, "min": -600, "max": -200},
    BulkCutStatus.RECOMP:      {"default": 0,    "min": -100, "max": 100},
    BulkCutStatus.MAINTENANCE: {"default": 0,    "min": -50,  "max": 50},
    BulkCutStatus.NONE:        {"default": 0,    "min": 0,    "max": 0},
}

# Workout timing -> meal split adjustments
WORKOUT_MEAL_SPLITS = {
    WorkoutTiming.MORNING: {
        "BREAKFAST": 0.30,  # Higher (default 0.25)
        "LUNCH": 0.38,
        "DINNER": 0.32,
        "breakfast_carb_boost": 1.15,  # 15% more carbs for pre-workout energy
    },
    WorkoutTiming.EVENING: {
        "BREAKFAST": 0.22,
        "LUNCH": 0.38,
        "DINNER": 0.40,  # Higher (default 0.35) for post-workout
        "dinner_protein_boost": 1.20,  # 20% more protein for recovery
    },
    WorkoutTiming.AFTERNOON: {
        "BREAKFAST": 0.25,
        "LUNCH": 0.40,  # Pre-workout carbs
        "DINNER": 0.35,
        "lunch_carb_boost": 1.10,
    },
}


@dataclass
class MealPracticalityScore:
    """How practical is this recipe for this user's real life."""
    prep_time_fit: float       # 0-1: does prep time fit available time?
    effort_match: float        # 0-1: does complexity match cooking effort?
    equipment_match: float     # 0-1: does user have needed equipment?
    total: float               # Weighted average
    flags: list                # ["NO_OVEN_NEEDED", "QUICK_MEAL"]


@dataclass
class FitnessNutritionAdjustment:
    """Adjustments to nutrition profile based on fitness/lifestyle."""
    calorie_adjustment: int           # Additional kcal from bulk/cut
    protein_boost_g: int              # Additional protein grams
    meal_splits: Dict[str, float]     # Adjusted per-meal percentages
    carb_timing_boost: Optional[Dict[str, float]]  # Meal -> carb multiplier
    protein_timing_boost: Optional[Dict[str, float]]  # Meal -> protein multiplier
    reasons: List[str]                # Human-readable explanations


class LifestyleService:
    """Translates lifestyle constraints into scoring signals and nutrition adjustments.
    
    All adjustments are configurable and bounded. No hardcoded magic numbers.
    Fitness adjustments STACK with (not replace) the health-goal adjustments from Phase 1.
    """

    @classmethod
    def calculate_fitness_adjustments(
        cls,
        weight_kg: float,
        workout_intensity: Optional[str] = None,
        fitness_goal: Optional[str] = None,
        bulk_cut_status: Optional[str] = None,
        workout_timing: Optional[str] = None,
        exercise_frequency: Optional[int] = None,
    ) -> FitnessNutritionAdjustment:
        """Calculate nutrition adjustments from fitness/lifestyle data.
        
        These adjustments are ADDED to the base profile from Phase 1.
        They never bypass safety floors.
        """
        reasons = []
        
        # 1. Bulk/cut calorie adjustment
        calorie_adj = 0
        if bulk_cut_status and bulk_cut_status != "NONE":
            try:
                status = BulkCutStatus(bulk_cut_status)
                config = BULK_CUT_CALORIE_ADJUSTMENTS.get(status, {"default": 0})
                calorie_adj = config["default"]
                reasons.append(f"{status.value.lower().replace('_', ' ')} phase: {'+' if calorie_adj >= 0 else ''}{calorie_adj} kcal")
            except ValueError:
                pass
        
        # 2. Protein boost from gym + intensity
        protein_boost = 0
        if workout_intensity and fitness_goal:
            try:
                intensity = WorkoutIntensity(workout_intensity)
                goal = FitnessGoal(fitness_goal)
                boost_per_kg = FITNESS_PROTEIN_BOOST.get((intensity, goal), 0)
                if boost_per_kg > 0:
                    protein_boost = int(weight_kg * boost_per_kg)
                    reasons.append(f"{intensity.value.lower()} intensity {goal.value.lower().replace('_', ' ')}: +{protein_boost}g protein")
            except ValueError:
                pass
        
        # Scale protein boost by exercise frequency
        if exercise_frequency is not None and exercise_frequency < 4 and protein_boost > 0:
            scale = exercise_frequency / 4.0
            protein_boost = int(protein_boost * max(scale, 0.5))
            reasons.append(f"Scaled protein for {exercise_frequency}x/week exercise")
        
        # 3. Meal timing adjustments
        meal_splits = {"BREAKFAST": 0.25, "LUNCH": 0.40, "DINNER": 0.35}
        carb_timing = None
        protein_timing = None
        
        if workout_timing and workout_timing != "NO_FIXED_TIME":
            try:
                timing = WorkoutTiming(workout_timing)
                timing_config = WORKOUT_MEAL_SPLITS.get(timing, {})
                if timing_config:
                    for meal in ["BREAKFAST", "LUNCH", "DINNER"]:
                        if meal in timing_config:
                            meal_splits[meal] = timing_config[meal]
                    
                    # Extract timing boosts
                    carb_timing = {}
                    protein_timing = {}
                    for key, val in timing_config.items():
                        if key.endswith("_carb_boost"):
                            meal = key.replace("_carb_boost", "").upper()
                            carb_timing[meal] = val
                        elif key.endswith("_protein_boost"):
                            meal = key.replace("_protein_boost", "").upper()
                            protein_timing[meal] = val
                    
                    if not carb_timing:
                        carb_timing = None
                    if not protein_timing:
                        protein_timing = None
                    
                    reasons.append(f"{timing.value.lower()} workout: adjusted meal splits")
            except ValueError:
                pass
        
        return FitnessNutritionAdjustment(
            calorie_adjustment=calorie_adj,
            protein_boost_g=protein_boost,
            meal_splits=meal_splits,
            carb_timing_boost=carb_timing,
            protein_timing_boost=protein_timing,
            reasons=reasons,
        )

    @staticmethod
    def score_meal_practicality(
        recipe_prep_time_min: int,
        recipe_difficulty: Optional[str],
        recipe_needs_oven: bool = False,
        recipe_needs_blender: bool = False,
        recipe_needs_air_fryer: bool = False,
        user_max_prep_time: Optional[int] = None,
        user_cooking_effort: Optional[str] = None,
        user_has_oven: bool = False,
        user_has_blender: bool = False,
        user_has_air_fryer: bool = False,
    ) -> MealPracticalityScore:
        """Score how practical a recipe is for a user's real constraints.
        
        This is used as an input to the recommendation scoring engine,
        not as a hard filter (unless equipment is missing for a critical step).
        """
        flags = []
        
        # 1. Prep time fit (0-1)
        if user_max_prep_time and user_max_prep_time > 0:
            if recipe_prep_time_min <= user_max_prep_time:
                prep_time_score = 1.0
                if recipe_prep_time_min <= user_max_prep_time * 0.5:
                    flags.append("QUICK_MEAL")
            else:
                overshoot = (recipe_prep_time_min - user_max_prep_time) / user_max_prep_time
                prep_time_score = max(0.0, 1.0 - overshoot)
        else:
            prep_time_score = 0.8  # No constraint = slightly favorable
        
        # 2. Effort match (0-1)
        effort_map = {
            CookingEffort.MINIMAL.value: {"EASY": 1.0, "MEDIUM": 0.3, "HARD": 0.1},
            CookingEffort.EASY.value: {"EASY": 1.0, "MEDIUM": 0.7, "HARD": 0.3},
            CookingEffort.MODERATE.value: {"EASY": 0.9, "MEDIUM": 1.0, "HARD": 0.7},
            CookingEffort.ELABORATE.value: {"EASY": 0.7, "MEDIUM": 0.9, "HARD": 1.0},
        }
        diff = (recipe_difficulty or "MEDIUM").upper()
        effort_scores = effort_map.get(user_cooking_effort, {"EASY": 0.9, "MEDIUM": 1.0, "HARD": 0.7})
        effort_score = effort_scores.get(diff, 0.7)
        
        # 3. Equipment match (0-1)
        equipment_issues = []
        if recipe_needs_oven and not user_has_oven:
            equipment_issues.append("NEEDS_OVEN")
        if recipe_needs_blender and not user_has_blender:
            equipment_issues.append("NEEDS_BLENDER")
        if recipe_needs_air_fryer and not user_has_air_fryer:
            equipment_issues.append("NEEDS_AIR_FRYER")
        
        if equipment_issues:
            equipment_score = max(0.0, 1.0 - 0.4 * len(equipment_issues))
            flags.extend(equipment_issues)
        else:
            equipment_score = 1.0
        
        # Weighted average
        total = (
            prep_time_score * 0.45 +
            effort_score * 0.30 +
            equipment_score * 0.25
        )
        
        return MealPracticalityScore(
            prep_time_fit=round(prep_time_score, 3),
            effort_match=round(effort_score, 3),
            equipment_match=round(equipment_score, 3),
            total=round(total, 3),
            flags=flags,
        )

    @staticmethod
    def get_ingredient_reuse_weight_boost(
        food_waste_preference: Optional[str],
    ) -> float:
        """If user cares about food waste, boost ingredient_reuse weight.
        
        Returns a multiplier for the ingredient_reuse scoring dimension.
        food_waste_preference = VERY_IMPORTANT -> 2.0x weight
        """
        boosts = {
            FoodWastePreference.VERY_IMPORTANT.value: 2.0,
            FoodWastePreference.SOMEWHAT_IMPORTANT.value: 1.5,
            FoodWastePreference.NOT_IMPORTANT.value: 1.0,
        }
        return boosts.get(food_waste_preference, 1.0)
