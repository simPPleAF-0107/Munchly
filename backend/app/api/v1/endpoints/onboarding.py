from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.api.v1.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.models.dietary import (
    UserDietaryPreference, UserAllergy, UserDietaryRestriction,
    UserFoodPreference, UserCuisinePreference, UserAvailableIngredient
)
from app.models.health import UserHealthCondition
from app.schemas.onboarding import OnboardingCompleteRequest, OnboardingCompleteResponse
from app.schemas.nutrition import NutritionTargetsResponse
from app.services.nutrition_service import NutritionService
from typing import Optional

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

@router.post("/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    data: OnboardingCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Complete onboarding - saves all user data in a single transaction."""
    
    # Update or Create UserProfile
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.name = data.basic_info.name
    profile.age = data.basic_info.age
    profile.gender = data.basic_info.gender
    profile.country_code = data.basic_info.country_code
    profile.state_code = data.basic_info.state_code
    profile.city = data.basic_info.city
    profile.height_cm = data.body_info.height_cm
    profile.weight_kg = data.body_info.weight_kg
    profile.activity_level = data.body_info.activity_level
    profile.health_goal = data.goal.health_goal
    profile.cooking_ability = data.cooking.cooking_ability
    profile.max_prep_time_min = data.cooking.max_prep_time_min
    profile.weekly_grocery_limit = data.budget.weekly_grocery_limit
    profile.weekly_grocery_limit_currency = data.budget.weekly_grocery_limit_currency
    profile.budget_type = data.budget.budget_type
    profile.onboarding_completed = True
    
    # Update Dietary Preference
    diet_stmt = select(UserDietaryPreference).where(UserDietaryPreference.user_id == current_user.id)
    diet_result = await db.execute(diet_stmt)
    diet_pref = diet_result.scalar_one_or_none()
    
    if not diet_pref:
        diet_pref = UserDietaryPreference(user_id=current_user.id)
        db.add(diet_pref)
    
    diet_pref.diet_type = data.dietary_preference.diet_type
    diet_pref.eats_chicken = data.dietary_preference.eats_chicken
    diet_pref.eats_mutton = data.dietary_preference.eats_mutton
    diet_pref.eats_fish = data.dietary_preference.eats_fish
    diet_pref.eats_seafood = data.dietary_preference.eats_seafood
    
    # Clean and recreate lists
    await db.execute(delete(UserHealthCondition).where(UserHealthCondition.user_id == current_user.id))
    await db.execute(delete(UserAllergy).where(UserAllergy.user_id == current_user.id))
    await db.execute(delete(UserDietaryRestriction).where(UserDietaryRestriction.user_id == current_user.id))
    await db.execute(delete(UserFoodPreference).where(UserFoodPreference.user_id == current_user.id))
    await db.execute(delete(UserCuisinePreference).where(UserCuisinePreference.user_id == current_user.id))
    await db.execute(delete(UserAvailableIngredient).where(UserAvailableIngredient.user_id == current_user.id))
    
    # Add new list items
    for cond in data.medical_conditions:
        db.add(UserHealthCondition(user_id=current_user.id, condition=cond.condition))
        
    for allergy in data.allergies:
        db.add(UserAllergy(user_id=current_user.id, allergen=allergy.allergen, custom_allergen=allergy.custom_allergen))
        
    for restriction in data.restrictions:
        db.add(UserDietaryRestriction(user_id=current_user.id, restriction=restriction.restriction))
        
    for fp in data.food_preferences:
        db.add(UserFoodPreference(user_id=current_user.id, food_id=fp.food_id, preference=fp.preference))
        
    for cp in data.cuisine_preferences:
        db.add(UserCuisinePreference(user_id=current_user.id, cuisine=cp.cuisine, preference_strength=cp.preference_strength))
        
    for pantry in data.pantry_items:
        db.add(UserAvailableIngredient(user_id=current_user.id, food_id=pantry.food_id, quantity_g=pantry.quantity_g, unit=pantry.unit))
    
    await db.commit()
    
    # Calculate nutrition targets
    targets = NutritionService.calculate_full_targets(
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
        age=profile.age,
        gender=profile.gender,
        activity_level=profile.activity_level,
        health_goal=profile.health_goal
    )
    
    nutrition_response = NutritionTargetsResponse(**targets)
    
    return OnboardingCompleteResponse(
        message="Onboarding completed successfully.",
        nutrition_targets=nutrition_response
    )

@router.get("/preview", response_model=NutritionTargetsResponse)
async def get_nutrition_preview(
    height_cm: float,
    weight_kg: float,
    age: int,
    gender: str,
    activity_level: str,
    health_goal: str
):
    """Preview nutrition targets (used during onboarding step 4→preview).
    No auth required — public endpoint for preview."""
    targets = NutritionService.calculate_full_targets(
        weight_kg=weight_kg,
        height_cm=height_cm,
        age=age,
        gender=gender,
        activity_level=activity_level,
        health_goal=health_goal
    )
    return NutritionTargetsResponse(**targets)

@router.get("/foods")
async def search_foods(
    q: str = "",
    category: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Search foods for the food preferences and pantry steps."""
    from app.models.food import Food
    stmt = select(Food).limit(limit)
    if q:
        stmt = stmt.where(Food.name.ilike(f"%{q}%"))
    if category:
        stmt = stmt.where(Food.category == category)
        
    result = await db.execute(stmt)
    foods = result.scalars().all()
    # We don't have a strict FoodSearchResponse schema imported, so we return a list.
    return foods

@router.get("/locations")
async def get_locations():
    """Return available countries, states, cities for the location picker."""
    # Placeholder for a real implementation that would query regions.
    return {
        "countries": [{"code": "IN", "name": "India"}],
        "states": [],
        "cities": []
    }
