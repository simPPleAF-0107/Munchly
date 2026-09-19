import pytest
from app.services.adequacy_validator import AdequacyValidator
from app.services.nutrient_profile_service import NutrientProfileService
from app.models.enums import HealthGoal, Gender, ActivityLevel, MedicalCondition

@pytest.fixture
def base_profile():
    return NutrientProfileService.build_profile(
        weight_kg=70,
        height_cm=175,
        age=30,
        gender=Gender.MALE.value,
        activity_level=ActivityLevel.MODERATELY_ACTIVE.value,
        health_goal=HealthGoal.MAINTAIN_WEIGHT.value,
        medical_conditions=["NONE"]
    )

def test_severe_calorie_deficit(base_profile):
    """1. Severe calorie deficit (50% of target) -> VIOLATION"""
    target_cals = base_profile.calorie_target
    meal_plan = [
        {"day_of_week": 1, "meal_type": "BREAKFAST", "recipe": {"calories": target_cals * 0.5, "protein_g": base_profile.protein_g.target}}
    ]
    result = AdequacyValidator.validate_plan(meal_plan, base_profile)
    assert not result.passed
    calorie_violations = [v for v in result.violations if v.nutrient == "calories"]
    assert len(calorie_violations) > 0
    assert calorie_violations[0].severity == "VIOLATION"

def test_low_protein(base_profile):
    """2. Low protein (60% of target) -> VIOLATION"""
    target_cals = base_profile.calorie_target
    target_protein = base_profile.protein_g.target
    meal_plan = [
        {"day_of_week": 1, "meal_type": "BREAKFAST", "recipe": {"calories": target_cals, "protein_g": target_protein * 0.6}}
    ]
    result = AdequacyValidator.validate_plan(meal_plan, base_profile)
    assert not result.passed
    protein_violations = [v for v in result.violations if v.nutrient == "protein_g"]
    assert len(protein_violations) > 0
    assert protein_violations[0].severity == "VIOLATION"

def test_micro_gap_high_priority():
    """3. Micro gap (all macros OK but calcium < 60%) -> VIOLATION for high-priority micro"""
    profile = NutrientProfileService.build_profile(
        weight_kg=70, height_cm=175, age=30, gender=Gender.MALE.value,
        activity_level=ActivityLevel.MODERATELY_ACTIVE.value, health_goal=HealthGoal.MAINTAIN_WEIGHT.value,
        medical_conditions=["NONE"]
    )
    # Force calcium to be HIGH priority for testing
    profile.micros["calcium_mg"].priority = "HIGH"
    
    target_cals = profile.calorie_target
    target_protein = profile.protein_g.target
    meal_plan = [
        {
            "day_of_week": 1, "meal_type": "BREAKFAST", 
            "recipe": {
                "calories": target_cals, "protein_g": target_protein,
                "calcium_mg": profile.micros["calcium_mg"].target * 0.5 # 50%
            }
        }
    ]
    result = AdequacyValidator.validate_plan(meal_plan, profile)
    assert not result.passed
    calcium_violations = [v for v in result.violations if v.nutrient == "calcium_mg"]
    assert len(calcium_violations) > 0
    assert calcium_violations[0].severity == "VIOLATION"

def test_allergen_present_in_plan(base_profile):
    """4. Allergen present in plan -> FAIL immediately"""
    target_cals = base_profile.calorie_target
    target_protein = base_profile.protein_g.target
    meal_plan = [
        {
            "day_of_week": 1, "meal_type": "BREAKFAST", 
            "recipe": {
                "calories": target_cals, "protein_g": target_protein,
                "allergens": ["PEANUT"]
            }
        }
    ]
    # Assuming validator accepts user_allergens as a kwarg
    result = AdequacyValidator.validate_plan(meal_plan, base_profile, user_allergens=["PEANUT"])
    assert not result.passed
    allergen_violations = [v for v in result.violations if v.nutrient == "allergen"]
    assert len(allergen_violations) > 0
    assert "PEANUT" in allergen_violations[0].message

def test_unvalidated_medical_condition():
    """5. Unvalidated medical condition -> NO automatic adjustment"""
    profile = NutrientProfileService.build_profile(
        weight_kg=70, height_cm=175, age=30, gender=Gender.MALE.value,
        activity_level=ActivityLevel.MODERATELY_ACTIVE.value, health_goal=HealthGoal.MAINTAIN_WEIGHT.value,
        medical_conditions=["PREDIABETES"] # Unvalidated
    )
    unvalidated_msgs = [c for c in profile.special_considerations if c.type == "UNVALIDATED_CONDITION"]
    assert len(unvalidated_msgs) > 0
    assert "PREDIABETES" in unvalidated_msgs[0].condition

def test_marginal_pass(base_profile):
    """6. Marginal pass (calories = 86% within ±15% tolerance) -> PASS"""
    target_cals = base_profile.calorie_target
    target_protein = base_profile.protein_g.target
    meal_plan = [
        {"day_of_week": 1, "meal_type": "BREAKFAST", "recipe": {"calories": target_cals * 0.86, "protein_g": target_protein}}
    ]
    # Provide all other micros to avoid weekly violation
    for micro, nt in base_profile.micros.items():
        meal_plan[0]["recipe"][micro] = nt.target
        
    result = AdequacyValidator.validate_plan(meal_plan, base_profile)
    # Check that there are no violations
    assert len(result.violations) == 0
    assert result.passed

def test_fiber_warning(base_profile):
    """7. Fiber warning (65% - below 70% but above 60%) -> WARNING not VIOLATION"""
    target_cals = base_profile.calorie_target
    target_protein = base_profile.protein_g.target
    target_fiber = base_profile.fiber_g.target
    
    meal_plan = [
        {"day_of_week": 1, "meal_type": "BREAKFAST", "recipe": {"calories": target_cals, "protein_g": target_protein, "fiber_g": target_fiber * 0.65}}
    ]
    # Provide all other micros to avoid weekly violation
    for micro, nt in base_profile.micros.items():
        meal_plan[0]["recipe"][micro] = nt.target
        
    result = AdequacyValidator.validate_plan(meal_plan, base_profile)
    assert result.passed
    fiber_warnings = [w for w in result.warnings if w.nutrient == "fiber_g"]
    assert len(fiber_warnings) > 0

def test_score_not_acceptability(base_profile):
    """8. Score != acceptability (High score but fails adequacy)"""
    # Just a conceptual test showing a plan that might be "good" (e.g. perfect calories) but misses a critical micro
    target_cals = base_profile.calorie_target
    target_protein = base_profile.protein_g.target
    base_profile.micros["iron_mg"].priority = "HIGH"
    
    meal_plan = [
        {
            "day_of_week": 1, "meal_type": "BREAKFAST", 
            "recipe": {
                "calories": target_cals, "protein_g": target_protein,
                "iron_mg": 0  # Fails critical micro
            }
        }
    ]
    result = AdequacyValidator.validate_plan(meal_plan, base_profile)
    assert not result.passed

def test_budget_exceeded(base_profile):
    """9. Budget exceeded (total cost > weekly_grocery_limit) -> VIOLATION"""
    target_cals = base_profile.calorie_target
    target_protein = base_profile.protein_g.target
    meal_plan = [
        {
            "day_of_week": 1, "meal_type": "BREAKFAST", 
            "recipe": {
                "calories": target_cals, "protein_g": target_protein,
                "price": 105.00
            }
        }
    ]
    # Provide all other micros to avoid weekly violation
    for micro, nt in base_profile.micros.items():
        meal_plan[0]["recipe"][micro] = nt.target
        
    result = AdequacyValidator.validate_plan(meal_plan, base_profile, weekly_budget=100.00)
    assert not result.passed
    budget_violations = [v for v in result.violations if v.nutrient == "budget"]
    assert len(budget_violations) > 0
    assert budget_violations[0].severity == "VIOLATION"
