import pytest
from app.services.nutrient_profile_service import NutrientProfileService, SAFETY_FLOORS
from app.services.adequacy_validator import AdequacyValidator
from app.services.conflict_resolver import ConflictResolver
from app.services.behavioral_service import BehavioralService
from app.models.enums import Gender


def build_adequate_plan(profile, days=7):
    """Build a plan that exactly meets the profile's targets."""
    meals = []
    for day in range(1, days + 1):
        for mt, split in profile.per_meal.items():
            meals.append({
                "day_of_week": day,
                "meal_type": mt,
                "recipe": {
                    "calories": profile.calorie_target * split,
                    "protein_g": profile.protein_g.target * split,
                    "carbs_g": profile.carbs_g.target * split,
                    "fat_g": profile.fat_g.target * split,
                    "fiber_g": profile.fiber_g.target * split,
                    "sodium_mg": 500 * split,
                    "calcium_mg": profile.micros.get('calcium_mg', type('', (), {'target': 1000})).target * split,
                    "iron_mg": profile.micros.get('iron_mg', type('', (), {'target': 17})).target * split,
                },
            })
    return meals


class TestPersona1_VegetarianWeightLoss:
    """Vegetarian, 80kg male, weight loss, Rs 1500/week budget."""
    
    def test_profile_has_calorie_deficit(self):
        profile = NutrientProfileService.build_profile(
            weight_kg=80, height_cm=175, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="LOSE_WEIGHT",
        )
        assert profile.calorie_adjustment < 0
        assert profile.calorie_target >= SAFETY_FLOORS[Gender.MALE]
    
    def test_adequate_plan_passes(self):
        profile = NutrientProfileService.build_profile(
            weight_kg=80, height_cm=175, age=30,
            gender="MALE", activity_level="MODERATELY_ACTIVE",
            health_goal="LOSE_WEIGHT",
        )
        meals = build_adequate_plan(profile)
        result = AdequacyValidator.validate_plan(meals, profile)
        assert result.passed


class TestPersona2_NonVegMuscleGain:
    """Non-veg, 70kg male, muscle gain, gym 5x/week."""
    
    def test_high_protein_target(self):
        profile = NutrientProfileService.build_profile(
            weight_kg=70, height_cm=178, age=25,
            gender="MALE", activity_level="VERY_ACTIVE",
            health_goal="BUILD_MUSCLE",
        )
        # BUILD_MUSCLE: 2.0g/kg = 140g protein
        assert profile.protein_g.target >= 140
    
    def test_calorie_surplus(self):
        profile = NutrientProfileService.build_profile(
            weight_kg=70, height_cm=178, age=25,
            gender="MALE", activity_level="VERY_ACTIVE",
            health_goal="BUILD_MUSCLE",
        )
        assert profile.calorie_adjustment > 0


class TestPersona3_VeganLowBudget:
    """Vegan, 55kg female, Rs 800/week budget."""
    
    def test_safety_floor_respected(self):
        profile = NutrientProfileService.build_profile(
            weight_kg=55, height_cm=160, age=28,
            gender="FEMALE", activity_level="LIGHTLY_ACTIVE",
            health_goal="LOSE_WEIGHT",
        )
        assert profile.calorie_target >= SAFETY_FLOORS[Gender.FEMALE]
    
    def test_conflict_detection_for_vegan_muscle(self):
        report = ConflictResolver.detect_conflicts(
            diet_type="VEGAN",
            health_goal="BUILD_MUSCLE",
        )
        assert report.has_conflicts


class TestPersona5_DiabetesBengali:
    """Diabetic user, Bengali cuisine preference."""
    
    def test_sugar_target_adjusted(self):
        profile = NutrientProfileService.build_profile(
            weight_kg=75, height_cm=170, age=45,
            gender="MALE", activity_level="SEDENTARY",
            health_goal="MAINTAIN_WEIGHT",
            medical_conditions=["DIABETES"],
        )
        # DIABETES should reduce sugar target
        sugar_target = profile.micros.get("sugar_g")
        assert sugar_target is not None
        assert sugar_target.target <= 25
        assert sugar_target.priority == "HIGH"
    
    def test_validated_condition_noted(self):
        profile = NutrientProfileService.build_profile(
            weight_kg=75, height_cm=170, age=45,
            gender="MALE", activity_level="SEDENTARY",
            health_goal="MAINTAIN_WEIGHT",
            medical_conditions=["DIABETES"],
        )
        validated = [c for c in profile.special_considerations if c.type == "VALIDATED_CONDITION"]
        assert len(validated) >= 1


class TestPersona12_PregnancyIron:
    """Pregnancy + iron deficiency (anemia)."""
    
    def test_iron_boosted(self):
        profile = NutrientProfileService.build_profile(
            weight_kg=65, height_cm=165, age=28,
            gender="FEMALE", activity_level="LIGHTLY_ACTIVE",
            health_goal="MAINTAIN_WEIGHT",
            medical_conditions=["ANEMIA"],
        )
        iron = profile.micros.get("iron_mg")
        assert iron is not None
        # ANEMIA boosts iron by 1.5x. Female default = 21, so target should be ~31.5
        assert iron.target > 21
        assert iron.confidence == "MEDICAL_RULE"


class TestPersona15_HypertensionSouthIndian:
    """Hypertension + South Indian cuisine."""
    
    def test_hypertension_considerations(self):
        profile = NutrientProfileService.build_profile(
            weight_kg=80, height_cm=172, age=50,
            gender="MALE", activity_level="SEDENTARY",
            health_goal="LOSE_WEIGHT",
            medical_conditions=["HIGH_BLOOD_PRESSURE"],
        )
        validated = [c for c in profile.special_considerations if c.type == "VALIDATED_CONDITION"]
        assert len(validated) >= 1
        # Potassium should be boosted
        potassium = profile.micros.get("potassium_mg")
        assert potassium is not None
        assert potassium.target >= 3400


class TestPersona19_AcceptsAllInsights:
    """User who accepts all behavioral insights."""
    
    def test_high_behavioral_confidence(self):
        conf = BehavioralService.compute_confidence(100)
        assert conf > 0.5
        assert conf <= 0.9
    
    def test_behavioral_augments_not_replaces(self):
        combined = BehavioralService.combine_preferences(
            explicit_strength=0.7,
            behavioral_strength=0.9,
            confidence=0.85,
        )
        # Should blend, not fully replace explicit
        assert combined > 0.7  # Behavioral pulls it up
        assert combined < 0.9  # But doesn't fully override


class TestPersona20_ResetsLearning:
    """User who resets behavioral learning."""
    
    def test_reset_zeroes_behavioral(self):
        from unittest.mock import MagicMock
        profile = MagicMock()
        profile.observed_strength = 0.8
        profile.confidence = 0.7
        profile.sample_count = 50
        
        reset = BehavioralService.reset_behavioral_profiles([profile])
        for p in reset:
            assert p.observed_strength == 0.0
            assert p.confidence == 0.0
            assert p.sample_count == 0
    
    def test_after_reset_explicit_only(self):
        combined = BehavioralService.combine_preferences(
            explicit_strength=0.8,
            behavioral_strength=0.0,
            confidence=0.0,  # Reset
        )
        assert combined == 0.8  # 100% explicit
