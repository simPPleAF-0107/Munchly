from pydantic import BaseModel, ConfigDict

class MealTargets(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int

class NutritionTargetsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    daily_calories: int
    daily_calories_range: tuple[int, int]
    protein_g: int
    protein_range: tuple[int, int]
    carbs_g: int
    fat_g: int
    fat_min_g: int
    fiber_g: int
    fiber_min_g: int
    bmi: float
    bmi_category: str
    bmr: int
    tdee: int
    per_meal: dict[str, MealTargets]
