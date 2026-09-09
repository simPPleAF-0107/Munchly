import uuid
from pydantic import BaseModel, ConfigDict

class RecipeIngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    food_id: uuid.UUID
    food_name: str
    quantity_g: float
    unit: str
    is_optional: bool

class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    estimated_cost: float
    cost_currency: str
    prep_time_min: int
    difficulty: str
    servings: int
    instructions: str | None
    image_url: str | None
    diet_compatibility: list[str]
    meal_types: list[str]
    cuisines: list[str]
    ingredients: list[RecipeIngredientResponse]
    allergens: list[str]
