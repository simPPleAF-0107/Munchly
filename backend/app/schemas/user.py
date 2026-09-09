from pydantic import BaseModel, ConfigDict

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    age: int
    gender: str
    country_code: str
    state_code: str | None
    city: str | None
    height_cm: float
    weight_kg: float
    activity_level: str
    health_goal: str
    cooking_ability: str
    max_prep_time_min: int
    weekly_grocery_limit: float
    weekly_grocery_limit_currency: str
    budget_type: str
    onboarding_completed: bool

class UserProfileUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    country_code: str | None = None
    state_code: str | None = None
    city: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    activity_level: str | None = None
    health_goal: str | None = None
    cooking_ability: str | None = None
    max_prep_time_min: int | None = None
    weekly_grocery_limit: float | None = None
    weekly_grocery_limit_currency: str | None = None
    budget_type: str | None = None
    onboarding_completed: bool | None = None
