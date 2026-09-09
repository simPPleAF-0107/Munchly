import uuid
from pydantic import BaseModel, Field
from .nutrition import NutritionTargetsResponse

class OnboardingBasicInfo(BaseModel):
    name: str
    age: int = Field(ge=13, le=120)
    gender: str
    country_code: str = "IN"
    state_code: str | None = None
    city: str | None = None

class OnboardingBodyInfo(BaseModel):
    height_cm: float = Field(gt=50, lt=300)
    weight_kg: float = Field(gt=10, lt=500)
    activity_level: str

class OnboardingGoal(BaseModel):
    health_goal: str

class OnboardingDietaryPreference(BaseModel):
    diet_type: str
    eats_chicken: bool = False
    eats_mutton: bool = False
    eats_fish: bool = False
    eats_seafood: bool = False

class OnboardingAllergy(BaseModel):
    allergen: str
    custom_allergen: str | None = None

class OnboardingRestriction(BaseModel):
    restriction: str

class OnboardingMedicalCondition(BaseModel):
    condition: str

class OnboardingFoodPreference(BaseModel):
    food_id: uuid.UUID
    preference: str  # LIKE, DISLIKE, NEVER

class OnboardingCuisinePreference(BaseModel):
    cuisine: str
    preference_strength: float = Field(ge=0, le=1)  # 1.0=Love, 0.7=Like, 0.3=Don't Care

class OnboardingCooking(BaseModel):
    cooking_ability: str
    max_prep_time_min: int = Field(ge=5, le=120)

class OnboardingBudget(BaseModel):
    weekly_grocery_limit: float = Field(gt=0)
    weekly_grocery_limit_currency: str = "INR"
    budget_type: str

class OnboardingPantryItem(BaseModel):
    food_id: uuid.UUID
    quantity_g: float = Field(gt=0)
    unit: str = "g"

class OnboardingCompleteRequest(BaseModel):
    \"\"\"Full onboarding payload — submitted as a single request.\"\"\"
    basic_info: OnboardingBasicInfo
    body_info: OnboardingBodyInfo
    goal: OnboardingGoal
    dietary_preference: OnboardingDietaryPreference
    allergies: list[OnboardingAllergy] = []
    restrictions: list[OnboardingRestriction] = []
    medical_conditions: list[OnboardingMedicalCondition] = []
    food_preferences: list[OnboardingFoodPreference] = []
    cuisine_preferences: list[OnboardingCuisinePreference]
    cooking: OnboardingCooking
    budget: OnboardingBudget
    pantry_items: list[OnboardingPantryItem] = []

class OnboardingCompleteResponse(BaseModel):
    message: str
    nutrition_targets: NutritionTargetsResponse
