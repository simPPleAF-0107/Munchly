import uuid
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from .recipe import RecipeResponse

class MealOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recipe_id: uuid.UUID
    recipe: RecipeResponse
    option_type: str
    score: float

class MealPlanMealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    day_of_week: int
    meal_type: str
    selected_recipe_id: uuid.UUID | None
    options: list[MealOptionResponse]

class MealPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    week_start_date: date
    total_consumed_cost: float | None
    total_purchase_cost: float | None
    cost_currency: str
    status: str
    meals: list[MealPlanMealResponse]
    created_at: datetime

class GenerateMealPlanRequest(BaseModel):
    week_start_date: date | None = None

class ReplaceMealRequest(BaseModel):
    reason: str
    exclude_recipe_ids: list[uuid.UUID] = []

class SelectMealOptionRequest(BaseModel):
    recipe_id: uuid.UUID

class MealActionRequest(BaseModel):
    action: str
