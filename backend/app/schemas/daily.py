import uuid
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CheckInRequest(BaseModel):
    """Daily check-in payload — designed for 3-4 taps."""
    workout_today: bool = False
    workout_type: Optional[str] = None       # ExerciseType value
    workout_intensity: Optional[str] = None  # WorkoutIntensity value
    hunger_level: Optional[str] = None       # HungerLevel value
    energy_level: Optional[str] = None       # EnergyLevel value
    food_mood: Optional[str] = None          # FoodMood value
    eating_location: Optional[str] = None    # EatingLocation value
    available_cook_time_min: Optional[int] = Field(None, ge=0, le=180)


class PantryTodayRequest(BaseModel):
    """Update today's available pantry ingredients."""
    food_ids: List[str] = Field(..., min_length=0)


class CravingOverrideRequest(BaseModel):
    """User has a craving for a specific recipe."""
    recipe_id: uuid.UUID
    meal_type: str  # BREAKFAST, LUNCH, DINNER


class DailyContextResponse(BaseModel):
    """Response for today's context."""
    id: uuid.UUID
    user_id: uuid.UUID
    date: date
    status: str
    workout_today: bool
    workout_type: Optional[str] = None
    workout_intensity: Optional[str] = None
    hunger_level: Optional[str] = None
    energy_level: Optional[str] = None
    food_mood: Optional[str] = None
    eating_location: Optional[str] = None
    available_cook_time_min: Optional[int] = None
    adjusted_calorie_target: Optional[int] = None
    pantry_food_ids: Optional[List[str]] = None
    craving_recipe_id: Optional[uuid.UUID] = None
    craving_meal_type: Optional[str] = None
    change_level: Optional[str] = None  # Populated when context is applied
    checked_in_at: Optional[datetime] = None

    class Config:
        from_attributes = True
