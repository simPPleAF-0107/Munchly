import uuid
from pydantic import BaseModel, ConfigDict

class FoodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    fiber_per_100g: float
    is_vegan: bool
    is_vegetarian: bool

class FoodSearchResponse(BaseModel):
    foods: list[FoodResponse]
    total: int
