import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.schemas.meal_plan import (
    GenerateMealPlanRequest, MealPlanResponse, ReplaceMealRequest,
    SelectMealOptionRequest, MealActionRequest, MealPlanMealResponse
)
from app.services.meal_plan_service import MealPlanService
from app.api.deps import get_current_user
from app.core.rate_limiter import limiter
from app.models.enums import SubscriptionTier
from app.core.feature_gate import check_feature_limit

router = APIRouter(prefix="/meal-plans", tags=["meal_plans"])

def get_generate_limit(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user and getattr(user, "subscription_tier", None) == SubscriptionTier.PLUS:
        return "1000/hour"
    return "5/hour"

def get_replace_limit(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user and getattr(user, "subscription_tier", None) == SubscriptionTier.PLUS:
        return "1000/hour"
    return "30/hour"

@router.post("/generate", response_model=MealPlanResponse, status_code=201, dependencies=[Depends(check_feature_limit("plan_regenerations_per_week"))])
@limiter.limit(get_generate_limit)
async def generate_meal_plan(
    request: Request,
    payload: GenerateMealPlanRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user)
):
    service = MealPlanService(db)
    try:
        meal_plan = await service.generate_meal_plan(user_id, payload.week_start_date)
        return meal_plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/active", response_model=MealPlanResponse)
async def get_active_meal_plan(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user)
):
    service = MealPlanService(db)
    meal_plan = await service.get_active_meal_plan(user_id)
    if not meal_plan:
        raise HTTPException(status_code=404, detail="No active meal plan found")
    return meal_plan

@router.post("/meals/{meal_id}/replace", response_model=MealPlanMealResponse, dependencies=[Depends(check_feature_limit("meal_replacements_per_day"))])
@limiter.limit(get_replace_limit)
async def replace_meal(
    meal_id: uuid.UUID,
    request: Request,
    payload: ReplaceMealRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user)
):
    service = MealPlanService(db)
    try:
        meal = await service.replace_meal(meal_id, user_id, payload.reason, payload.exclude_recipe_ids)
        return meal
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/meals/{meal_id}/select", response_model=MealPlanMealResponse)
async def select_meal_option(
    meal_id: uuid.UUID,
    request: SelectMealOptionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user)
):
    service = MealPlanService(db)
    try:
        meal = await service.select_option(meal_id, user_id, request.recipe_id)
        return meal
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/meals/{meal_id}/action")
async def record_meal_action(
    meal_id: uuid.UUID,
    request: MealActionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user)
):
    service = MealPlanService(db)
    try:
        await service.record_meal_action(meal_id, user_id, request.action)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
