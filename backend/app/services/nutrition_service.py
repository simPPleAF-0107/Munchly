from decimal import Decimal
from typing import Dict, Any, Tuple

class NutritionService:
    """Deterministic nutrition calculator. No AI involved."""
    
    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> float:
        """BMI = weight_kg / (height_m)^2"""
        height_m = height_cm / 100
        return round(weight_kg / (height_m ** 2), 1)
    
    @staticmethod
    def bmi_category(bmi: float) -> str:
        """Underweight / Normal / Overweight / Obese"""
        if bmi < 18.5: return "Underweight"
        elif bmi < 25: return "Normal"
        elif bmi < 30: return "Overweight"
        else: return "Obese"
    
    @staticmethod
    def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> int:
        """Mifflin-St Jeor equation.
        Male:   10 * weight + 6.25 * height - 5 * age + 5
        Female: 10 * weight + 6.25 * height - 5 * age - 161
        Other:  average of male and female
        """
        male_bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        female_bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        
        if gender.upper() == "MALE":
            return int(male_bmr)
        elif gender.upper() == "FEMALE":
            return int(female_bmr)
        else:
            return int((male_bmr + female_bmr) / 2)
    
    @staticmethod
    def calculate_tdee(bmr: int, activity_level: str) -> int:
        """TDEE = BMR * activity multiplier.
        SEDENTARY: 1.2
        LIGHTLY_ACTIVE: 1.375
        MODERATELY_ACTIVE: 1.55
        VERY_ACTIVE: 1.725
        EXTREMELY_ACTIVE: 1.9
        """
        multipliers = {
            "SEDENTARY": 1.2,
            "LIGHTLY_ACTIVE": 1.375,
            "MODERATELY_ACTIVE": 1.55,
            "VERY_ACTIVE": 1.725,
            "EXTREMELY_ACTIVE": 1.9
        }
        multiplier = multipliers.get(activity_level.upper(), 1.2)
        return int(bmr * multiplier)
    
    @staticmethod
    def calculate_calorie_target(tdee: int, health_goal: str, gender: str) -> Tuple[int, int, int]:
        """Returns (target_calories, min_calories, max_calories) based on goal.
        LOSE_WEIGHT: TDEE - 500 (moderate deficit)
        MAINTAIN_WEIGHT: TDEE
        GAIN_WEIGHT: TDEE + 300
        BUILD_MUSCLE: TDEE + 250
        IMPROVE_FITNESS: TDEE - 200
        EAT_HEALTHIER: TDEE
        
        Safety floors: 1500 kcal/day male, 1200 kcal/day female
        Range: target ± 10%
        """
        adjustments = {
            "LOSE_WEIGHT": -500,
            "MAINTAIN_WEIGHT": 0,
            "GAIN_WEIGHT": 300,
            "BUILD_MUSCLE": 250,
            "IMPROVE_FITNESS": -200,
            "EAT_HEALTHIER": 0
        }
        
        adjustment = adjustments.get(health_goal.upper(), 0)
        target = tdee + adjustment
        
        # Safety floors
        floor = 1500 if gender.upper() == "MALE" else 1200
        target = max(target, floor)
        
        min_cals = int(target * 0.9)
        max_cals = int(target * 1.1)
        
        return target, min_cals, max_cals
    
    @staticmethod
    def calculate_macros(target_calories: int, weight_kg: float, health_goal: str, gender: str) -> Dict[str, int]:
        """Returns protein_g, carbs_g, fat_g, fiber_g targets.
        
        Protein:
        - LOSE_WEIGHT: 1.6 g/kg
        - BUILD_MUSCLE: 2.0 g/kg
        - MAINTAIN_WEIGHT: 1.2 g/kg
        - Default: 1.0 g/kg
        
        Fat: 25-30% of calories
        Carbs: remainder
        Fiber: 25g minimum (30g for males)
        """
        protein_multipliers = {
            "LOSE_WEIGHT": 1.6,
            "BUILD_MUSCLE": 2.0,
            "MAINTAIN_WEIGHT": 1.2
        }
        
        protein_multiplier = protein_multipliers.get(health_goal.upper(), 1.0)
        protein_g = int(weight_kg * protein_multiplier)
        
        # Fat is 27.5% of calories on average (between 25% and 30%)
        fat_calories = target_calories * 0.275
        fat_g = int(fat_calories / 9)
        
        # Carbs are the remainder
        protein_calories = protein_g * 4
        carbs_calories = target_calories - protein_calories - fat_calories
        carbs_g = int(carbs_calories / 4)
        
        # Fiber
        fiber_g = 30 if gender.upper() == "MALE" else 25
        
        return {
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g,
            "fiber_g": fiber_g
        }
    
    @classmethod
    def calculate_full_targets(
        cls,
        weight_kg: float,
        height_cm: float,
        age: int,
        gender: str,
        activity_level: str,
        health_goal: str
    ) -> Dict[str, Any]:
        """Calculate complete nutrition targets.
        Returns dict with: bmi, bmi_category, bmr, tdee, daily_calories,
        daily_calories_range, protein_g, protein_range, carbs_g, fat_g,
        fat_min_g, fiber_g, fiber_min_g, per_meal (breakfast/lunch/dinner targets).
        
        Per-meal split:
        - Breakfast: 25% of daily calories
        - Lunch: 40% of daily calories
        - Dinner: 35% of daily calories
        """
        bmi = cls.calculate_bmi(weight_kg, height_cm)
        category = cls.bmi_category(bmi)
        bmr = cls.calculate_bmr(weight_kg, height_cm, age, gender)
        tdee = cls.calculate_tdee(bmr, activity_level)
        
        target_calories, min_calories, max_calories = cls.calculate_calorie_target(tdee, health_goal, gender)
        
        macros = cls.calculate_macros(target_calories, weight_kg, health_goal, gender)
        protein_g = macros["protein_g"]
        carbs_g = macros["carbs_g"]
        fat_g = macros["fat_g"]
        fiber_g = macros["fiber_g"]
        
        # Per meal split
        def get_meal_targets(percentage: float) -> Dict[str, int]:
            return {
                "calories": int(target_calories * percentage),
                "protein_g": int(protein_g * percentage),
                "carbs_g": int(carbs_g * percentage),
                "fat_g": int(fat_g * percentage)
            }
        
        per_meal = {
            "BREAKFAST": get_meal_targets(0.25),
            "LUNCH": get_meal_targets(0.40),
            "DINNER": get_meal_targets(0.35)
        }
        
        return {
            "bmi": bmi,
            "bmi_category": category,
            "bmr": bmr,
            "tdee": tdee,
            "daily_calories": target_calories,
            "daily_calories_range": (min_calories, max_calories),
            "protein_g": protein_g,
            "protein_range": (int(protein_g * 0.9), int(protein_g * 1.1)),
            "carbs_g": carbs_g,
            "fat_g": fat_g,
            "fat_min_g": int(fat_g * 0.9),
            "fiber_g": fiber_g,
            "fiber_min_g": fiber_g,
            "per_meal": per_meal
        }
