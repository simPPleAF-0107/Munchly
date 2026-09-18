import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.daily import (
    CheckInRequest, PantryTodayRequest, CravingOverrideRequest,
    DailyContextResponse,
)
from app.services.daily_context_service import DailyContextService

router = APIRouter(prefix="/daily", tags=["daily"])


@router.post("/check-in", response_model=DailyContextResponse, status_code=200)
async def daily_check_in(
    payload: CheckInRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Daily check-in: 3-4 taps, sets today's context.
    
    Determines minimum plan change and adjusts today's recommendations.
    """
    service = DailyContextService(db)
    ctx = await service.check_in(
        user_id=current_user.id,
        workout_today=payload.workout_today,
        workout_type=payload.workout_type,
        workout_intensity=payload.workout_intensity,
        hunger_level=payload.hunger_level,
        energy_level=payload.energy_level,
        food_mood=payload.food_mood,
        eating_location=payload.eating_location,
        available_cook_time_min=payload.available_cook_time_min,
    )
    change_level = service.determine_change_level(ctx)
    await db.commit()
    
    response = DailyContextResponse.model_validate(ctx)
    response.change_level = change_level.value
    return response


@router.post("/skip", response_model=DailyContextResponse, status_code=200)
async def skip_check_in(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Skip today's check-in. Skip must ALWAYS be available."""
    service = DailyContextService(db)
    ctx = await service.skip_check_in(user_id=current_user.id)
    await db.commit()
    return DailyContextResponse.model_validate(ctx)


@router.get("/today", response_model=DailyContextResponse)
async def get_today(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get today's context + adjusted meals."""
    service = DailyContextService(db)
    ctx = await service.get_today_context(user_id=current_user.id)
    if ctx is None:
        # Create a pending context
        ctx = await service.get_or_create_today(user_id=current_user.id)
        await db.commit()
    
    change_level = service.determine_change_level(ctx)
    response = DailyContextResponse.model_validate(ctx)
    response.change_level = change_level.value
    return response


@router.post("/pantry-today", response_model=DailyContextResponse, status_code=200)
async def pantry_today(
    payload: PantryTodayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update today's available pantry ingredients.
    
    Plan change: MINOR_ADJUSTMENT — re-score for pantry overlap.
    """
    service = DailyContextService(db)
    ctx = await service.update_pantry_today(
        user_id=current_user.id,
        food_ids=payload.food_ids,
    )
    change_level = service.determine_change_level(ctx)
    await db.commit()
    
    response = DailyContextResponse.model_validate(ctx)
    response.change_level = change_level.value
    return response


@router.post("/override", response_model=DailyContextResponse, status_code=200)
async def craving_override(
    payload: CravingOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """User has a craving — fit this recipe into today's plan.
    
    Plan change: MEAL_REPLACED for the target slot.
    Other slots may get MINOR_ADJUSTMENT to compensate nutritionally.
    """
    service = DailyContextService(db)
    ctx = await service.craving_override(
        user_id=current_user.id,
        recipe_id=payload.recipe_id,
        meal_type=payload.meal_type,
    )
    change_level = service.determine_change_level(ctx)
    await db.commit()
    
    response = DailyContextResponse.model_validate(ctx)
    response.change_level = change_level.value
    return response
