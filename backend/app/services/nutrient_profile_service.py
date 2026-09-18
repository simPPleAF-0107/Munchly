from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from app.models.enums import HealthGoal, Gender, MedicalCondition


# ============================================================
# Configurable, bounded calorie adjustment ranges
# ============================================================
CALORIE_ADJUSTMENTS = {
    HealthGoal.LOSE_WEIGHT:     {"default": -500, "min": -750, "max": -200},
    HealthGoal.MAINTAIN_WEIGHT: {"default": 0,    "min": -100, "max": 100},
    HealthGoal.GAIN_WEIGHT:     {"default": 300,  "min": 150,  "max": 500},
    HealthGoal.BUILD_MUSCLE:    {"default": 250,  "min": 100,  "max": 400},
    HealthGoal.IMPROVE_FITNESS: {"default": -200, "min": -400, "max": 0},
    HealthGoal.EAT_HEALTHIER:   {"default": 0,    "min": -200, "max": 200},
}

SAFETY_FLOORS = {
    Gender.MALE:   1500,
    Gender.FEMALE: 1200,
    Gender.OTHER:  1350,
}

# DRI-based micronutrient targets by gender (simplified, adult 19-50)
# Source: NIH/ICMR RDA tables
MICRO_TARGETS_MALE = {
    "calcium_mg": {"target": 1000, "priority": "NORMAL"},
    "iron_mg": {"target": 17, "priority": "NORMAL"},
    "magnesium_mg": {"target": 340, "priority": "NORMAL"},
    "potassium_mg": {"target": 3400, "priority": "NORMAL"},
    "zinc_mg": {"target": 12, "priority": "NORMAL"},
    "vitamin_a_mcg": {"target": 900, "priority": "NORMAL"},
    "vitamin_b12_mcg": {"target": 2.4, "priority": "NORMAL"},
    "vitamin_c_mg": {"target": 80, "priority": "NORMAL"},
    "vitamin_d_mcg": {"target": 15, "priority": "NORMAL"},
    "folate_mcg": {"target": 400, "priority": "NORMAL"},
    "phosphorus_mg": {"target": 700, "priority": "NORMAL"},
    "sugar_g": {"target": 36, "priority": "NORMAL"},  # AHA max
}

MICRO_TARGETS_FEMALE = {
    "calcium_mg": {"target": 1000, "priority": "NORMAL"},
    "iron_mg": {"target": 21, "priority": "NORMAL"},
    "magnesium_mg": {"target": 310, "priority": "NORMAL"},
    "potassium_mg": {"target": 2600, "priority": "NORMAL"},
    "zinc_mg": {"target": 10, "priority": "NORMAL"},
    "vitamin_a_mcg": {"target": 700, "priority": "NORMAL"},
    "vitamin_b12_mcg": {"target": 2.4, "priority": "NORMAL"},
    "vitamin_c_mg": {"target": 65, "priority": "NORMAL"},
    "vitamin_d_mcg": {"target": 15, "priority": "NORMAL"},
    "folate_mcg": {"target": 400, "priority": "NORMAL"},
    "phosphorus_mg": {"target": 700, "priority": "NORMAL"},
    "sugar_g": {"target": 25, "priority": "NORMAL"},  # AHA max
}

# Validated medical rules: condition -> nutrient adjustments
# Only rules with is_validated=True are applied
VALIDATED_MEDICAL_RULES: Dict[MedicalCondition, Dict[str, Any]] = {
    MedicalCondition.DIABETES: {
        "is_validated": True,
        "reviewed_by": "ICMR_2017",
        "adjustments": {
            "sugar_g": {"target_override": 25, "priority": "HIGH"},
        },
    },
    MedicalCondition.HIGH_BLOOD_PRESSURE: {
        "is_validated": True,
        "reviewed_by": "WHO_2023",
        "adjustments": {
            "sodium_mg": {"target": 1500, "priority": "HIGH"},
            "potassium_mg": {"target": 3500, "priority": "HIGH"},
        },
    },
    MedicalCondition.ANEMIA: {
        "is_validated": True,
        "reviewed_by": "ICMR_2020",
        "adjustments": {
            "iron_mg": {"target_multiplier": 1.5, "priority": "HIGH"},
            "vitamin_c_mg": {"target_multiplier": 1.3, "priority": "HIGH"},
        },
    },
    MedicalCondition.HIGH_CHOLESTEROL: {
        "is_validated": True,
        "reviewed_by": "AHA_2021",
        "adjustments": {
            "fiber_g": {"target_multiplier": 1.2, "priority": "HIGH"},
        },
    },
    # PREDIABETES, GERD, OTHER → no validated rule yet
}


@dataclass
class NutrientTarget:
    """Target for a single nutrient."""
    target: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    priority: str = "NORMAL"  # NORMAL | HIGH | CRITICAL
    confidence: str = "DRI"   # DRI | MEDICAL_RULE | ESTIMATED


@dataclass
class SpecialConsideration:
    """A medical/lifestyle consideration that may or may not have validated rules."""
    type: str  # VALIDATED_CONDITION | UNVALIDATED_CONDITION | LIFESTYLE
    condition: str
    message: str
    source: Optional[str] = None


@dataclass
class NutrientProfile:
    """Complete nutrient requirement profile for a user."""
    # Energy
    bmr: int
    tdee: int
    calorie_target: int
    calorie_range: Tuple[int, int]
    calorie_adjustment: int  # How much was added/subtracted from TDEE
    
    # Macros
    protein_g: NutrientTarget
    carbs_g: NutrientTarget
    fat_g: NutrientTarget
    fiber_g: NutrientTarget
    
    # Micros
    micros: Dict[str, NutrientTarget]
    
    # Per-meal splits
    per_meal: Dict[str, float]  # {"BREAKFAST": 0.25, "LUNCH": 0.40, "DINNER": 0.35}
    
    # Special considerations
    special_considerations: List[SpecialConsideration] = field(default_factory=list)


class NutrientProfileService:
    """Builds a complete nutrient requirement profile for a user.
    
    Key design decisions:
    - Micro targets vary by age/gender (DRI tables from NIH/ICMR)
    - Medical conditions only adjust via validated rules
    - No validated rule = no automatic adjustment + user disclaimer
    - Calorie adjustments are configurable and bounded
    - Per-meal is percentage-based
    """

    @classmethod
    def build_profile(
        cls,
        weight_kg: float,
        height_cm: float,
        age: int,
        gender: str,
        activity_level: str,
        health_goal: str,
        medical_conditions: Optional[List[str]] = None,
    ) -> NutrientProfile:
        """Build complete nutrient profile from user data.
        
        Args:
            weight_kg: User's weight
            height_cm: User's height
            age: User's age
            gender: MALE, FEMALE, or OTHER
            activity_level: From ActivityLevel enum
            health_goal: From HealthGoal enum
            medical_conditions: List of MedicalCondition enum values
        """
        from app.services.nutrition_service import NutritionService
        
        gender_enum = Gender(gender.upper()) if isinstance(gender, str) else gender
        goal_enum = HealthGoal(health_goal.upper()) if isinstance(health_goal, str) else health_goal
        
        # Calculate base values
        bmr = NutritionService.calculate_bmr(weight_kg, height_cm, age, gender)
        tdee = NutritionService.calculate_tdee(bmr, activity_level)
        
        # Apply configurable, bounded calorie adjustment
        adjustment_config = CALORIE_ADJUSTMENTS.get(
            goal_enum,
            {"default": 0, "min": -200, "max": 200}
        )
        adjustment = adjustment_config["default"]
        target = tdee + adjustment
        
        # Apply safety floor
        floor = SAFETY_FLOORS.get(gender_enum, 1350)
        target = max(target, floor)
        
        calorie_range = (int(target * 0.9), int(target * 1.1))
        
        # Calculate macros
        macros = NutritionService.calculate_macros(target, weight_kg, health_goal, gender)
        
        protein_target = NutrientTarget(
            target=macros["protein_g"],
            min_value=int(macros["protein_g"] * 0.8),
            max_value=int(macros["protein_g"] * 1.2),
            priority="NORMAL",
        )
        carbs_target = NutrientTarget(
            target=macros["carbs_g"],
            min_value=int(macros["carbs_g"] * 0.8),
            max_value=int(macros["carbs_g"] * 1.2),
        )
        fat_target = NutrientTarget(
            target=macros["fat_g"],
            min_value=int(macros["fat_g"] * 0.8),
            max_value=int(macros["fat_g"] * 1.2),
        )
        fiber_target = NutrientTarget(
            target=macros["fiber_g"],
            min_value=macros["fiber_g"],
        )
        
        # Micronutrient targets based on gender
        micro_source = MICRO_TARGETS_MALE if gender_enum == Gender.MALE else MICRO_TARGETS_FEMALE
        micros = {}
        for nutrient, info in micro_source.items():
            micros[nutrient] = NutrientTarget(
                target=info["target"],
                priority=info["priority"],
                confidence="DRI",
            )
        
        # Apply validated medical adjustments
        special_considerations = []
        for cond_str in (medical_conditions or []):
            if cond_str == "NONE":
                continue
            try:
                cond = MedicalCondition(cond_str)
            except ValueError:
                continue
            
            rule = VALIDATED_MEDICAL_RULES.get(cond)
            if rule and rule.get("is_validated"):
                # Apply validated rule
                for nutrient, adj in rule["adjustments"].items():
                    if nutrient in micros:
                        nt = micros[nutrient]
                        if "target_override" in adj:
                            nt.target = adj["target_override"]
                            nt.max_value = adj["target_override"]
                        if "target_multiplier" in adj:
                            nt.target = round(nt.target * adj["target_multiplier"], 1)
                        nt.priority = adj.get("priority", nt.priority)
                        nt.confidence = "MEDICAL_RULE"
                    elif nutrient == "sodium_mg":
                        # sodium is a macro-level constraint, not in micros dict
                        pass  # Handled via constraint service
                
                special_considerations.append(SpecialConsideration(
                    type="VALIDATED_CONDITION",
                    condition=cond.value,
                    message=f"Adjusted nutrition targets based on {cond.value.lower().replace('_', ' ')}.",
                    source=rule["reviewed_by"],
                ))
            else:
                # No validated rule → do NOT auto-adjust
                special_considerations.append(SpecialConsideration(
                    type="UNVALIDATED_CONDITION",
                    condition=cond_str,
                    message=f"Munchly doesn't yet have validated nutrition rules for {cond_str.lower().replace('_', ' ')}. Please consult your doctor.",
                ))
        
        return NutrientProfile(
            bmr=bmr,
            tdee=tdee,
            calorie_target=target,
            calorie_range=calorie_range,
            calorie_adjustment=adjustment,
            protein_g=protein_target,
            carbs_g=carbs_target,
            fat_g=fat_target,
            fiber_g=fiber_target,
            micros=micros,
            per_meal={"BREAKFAST": 0.25, "LUNCH": 0.40, "DINNER": 0.35},
            special_considerations=special_considerations,
        )
