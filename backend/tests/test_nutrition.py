import pytest
from app.services.nutrition_service import NutritionService
from app.models.enums import Gender, ActivityLevel, HealthGoal

@pytest.mark.asyncio
async def test_bmi_calculation():
    # 70 kg, 175 cm (1.75 m)
    # BMI = 70 / (1.75^2) = 70 / 3.0625 = 22.86
    bmi = NutritionService.calculate_bmi(70, 175)
    assert round(bmi, 2) == 22.86

@pytest.mark.asyncio
async def test_bmr_calculation():
    # Mifflin-St Jeor Equation
    # Male: (10 * 70) + (6.25 * 175) - (5 * 30) + 5 = 700 + 1093.75 - 150 + 5 = 1648.75
    bmr_male = NutritionService.calculate_bmr(70, 175, 30, Gender.MALE)
    assert round(bmr_male, 2) == 1648.75

    # Female: (10 * 70) + (6.25 * 175) - (5 * 30) - 161 = 700 + 1093.75 - 150 - 161 = 1482.75
    bmr_female = NutritionService.calculate_bmr(70, 175, 30, Gender.FEMALE)
    assert round(bmr_female, 2) == 1482.75

@pytest.mark.asyncio
async def test_tdee_calculation():
    bmr = 1500
    assert NutritionService.calculate_tdee(bmr, ActivityLevel.SEDENTARY) == 1500 * 1.2
    assert NutritionService.calculate_tdee(bmr, ActivityLevel.LIGHTLY_ACTIVE) == 1500 * 1.375
    assert NutritionService.calculate_tdee(bmr, ActivityLevel.MODERATELY_ACTIVE) == 1500 * 1.55
    assert NutritionService.calculate_tdee(bmr, ActivityLevel.VERY_ACTIVE) == 1500 * 1.725
    assert NutritionService.calculate_tdee(bmr, ActivityLevel.EXTRA_ACTIVE) == 1500 * 1.9

@pytest.mark.asyncio
async def test_calorie_targets():
    # tdee = 2000
    assert NutritionService.calculate_target_calories(2000, HealthGoal.MAINTAIN_WEIGHT, Gender.MALE) == 2000
    assert NutritionService.calculate_target_calories(2000, HealthGoal.LOSE_WEIGHT, Gender.MALE) == 1500
    assert NutritionService.calculate_target_calories(2000, HealthGoal.GAIN_WEIGHT, Gender.MALE) == 2500

    # Safety floors
    # Male floor is 1500
    assert NutritionService.calculate_target_calories(1800, HealthGoal.LOSE_WEIGHT, Gender.MALE) == 1500
    # Female floor is 1200
    assert NutritionService.calculate_target_calories(1500, HealthGoal.LOSE_WEIGHT, Gender.FEMALE) == 1200

@pytest.mark.asyncio
async def test_macro_calculations():
    # 2000 calories
    macros = NutritionService.calculate_macros(2000, HealthGoal.MAINTAIN_WEIGHT)
    # Typically 30% protein, 40% carbs, 30% fat
    # Protein: 2000 * 0.3 / 4 = 150g
    # Carbs: 2000 * 0.4 / 4 = 200g
    # Fat: 2000 * 0.3 / 9 = 66.6g
    assert round(macros["protein"]) == 150
    assert round(macros["carbs"]) == 200
    assert round(macros["fat"]) == 67

@pytest.mark.asyncio
async def test_per_meal_split():
    macros = {"calories": 2000, "protein": 150, "carbs": 200, "fat": 67}
    split = NutritionService.calculate_meal_split(macros)
    
    # Breakfast: 25%
    assert split["breakfast"]["calories"] == 500
    assert split["breakfast"]["protein"] == 37.5
    
    # Lunch: 40%
    assert split["lunch"]["calories"] == 800
    assert split["lunch"]["protein"] == 60
    
    # Dinner: 35%
    assert split["dinner"]["calories"] == 700
    assert split["dinner"]["protein"] == 52.5
