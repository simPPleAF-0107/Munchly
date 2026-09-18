import uuid
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_context import DailyContext
from app.models.enums import (
    DailyCheckInStatus, EventType, EnergyLevel, FoodMood,
    EatingLocation, HungerLevel, WorkoutIntensity, PlanChangeLevel,
)
from app.services.event_service import EventService


class DailyContextService:
    """Manages daily check-in context and recommendation adjustments.
    
    Architecture:
        Daily Context -> Recommendation -> Plan Stability -> Adequacy Validation
        NOT: Daily Context -> Gemini -> Meal
    
    Every check-in action emits an immutable event.
    Phase 3 only records and applies context — it does NOT learn from it.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_today(
        self, user_id: uuid.UUID, today: Optional[date] = None,
    ) -> DailyContext:
        """Get today's context or create a PENDING one."""
        today = today or date.today()
        stmt = select(DailyContext).where(
            DailyContext.user_id == user_id,
            DailyContext.date == today,
        )
        result = await self.db.execute(stmt)
        ctx = result.scalar_one_or_none()
        
        if ctx is None:
            ctx = DailyContext(
                user_id=user_id,
                date=today,
                status=DailyCheckInStatus.PENDING,
            )
            self.db.add(ctx)
            await self.db.flush()
        
        return ctx

    async def check_in(
        self,
        user_id: uuid.UUID,
        workout_today: bool = False,
        workout_type: Optional[str] = None,
        workout_intensity: Optional[str] = None,
        hunger_level: Optional[str] = None,
        energy_level: Optional[str] = None,
        food_mood: Optional[str] = None,
        eating_location: Optional[str] = None,
        available_cook_time_min: Optional[int] = None,
    ) -> DailyContext:
        """Process a daily check-in (3-4 taps).
        
        Determines the minimum plan change needed and applies it.
        """
        ctx = await self.get_or_create_today(user_id)
        
        # Update context fields
        ctx.workout_today = workout_today
        if workout_type:
            ctx.workout_type = workout_type
        if workout_intensity:
            ctx.workout_intensity = WorkoutIntensity(workout_intensity)
        if hunger_level:
            ctx.hunger_level = HungerLevel(hunger_level)
        if energy_level:
            ctx.energy_level = EnergyLevel(energy_level)
        if food_mood:
            ctx.food_mood = FoodMood(food_mood)
        if eating_location:
            ctx.eating_location = EatingLocation(eating_location)
        if available_cook_time_min is not None:
            ctx.available_cook_time_min = available_cook_time_min
        
        # Calculate adjusted calorie target based on context
        ctx.adjusted_calorie_target = await self._calculate_adjusted_calories(
            user_id, ctx,
        )
        
        ctx.status = DailyCheckInStatus.COMPLETED
        ctx.checked_in_at = datetime.utcnow()
        ctx.updated_at = datetime.utcnow()
        
        await self.db.flush()
        
        # Emit event
        await EventService.emit(
            db=self.db,
            user_id=user_id,
            event_type=EventType.DAILY_CHECKIN,
            entity_type="daily_context",
            entity_id=ctx.id,
            metadata={
                "workout_today": workout_today,
                "food_mood": food_mood,
                "energy_level": energy_level,
                "hunger_level": hunger_level,
                "available_cook_time_min": available_cook_time_min,
                "eating_location": eating_location,
            },
        )
        
        return ctx

    async def skip_check_in(self, user_id: uuid.UUID) -> DailyContext:
        """Skip today's check-in. Skip must always be available."""
        ctx = await self.get_or_create_today(user_id)
        ctx.status = DailyCheckInStatus.SKIPPED
        ctx.checked_in_at = datetime.utcnow()
        ctx.updated_at = datetime.utcnow()
        await self.db.flush()
        return ctx

    async def update_pantry_today(
        self,
        user_id: uuid.UUID,
        food_ids: List[str],
    ) -> DailyContext:
        """Update today's available pantry ingredients.
        
        Plan change: MINOR_ADJUSTMENT — re-score for pantry overlap.
        """
        ctx = await self.get_or_create_today(user_id)
        ctx.pantry_food_ids = food_ids
        ctx.updated_at = datetime.utcnow()
        await self.db.flush()
        
        # Emit event
        await EventService.emit(
            db=self.db,
            user_id=user_id,
            event_type=EventType.PANTRY_UPDATED,
            entity_type="daily_context",
            entity_id=ctx.id,
            metadata={"food_ids": food_ids, "count": len(food_ids)},
        )
        
        return ctx

    async def craving_override(
        self,
        user_id: uuid.UUID,
        recipe_id: uuid.UUID,
        meal_type: str,
    ) -> DailyContext:
        """User has a craving — fit this recipe into today's plan.
        
        Plan change: MEAL_REPLACED for the target slot,
        then MINOR_ADJUSTMENT for other slots to compensate nutritionally.
        """
        ctx = await self.get_or_create_today(user_id)
        ctx.craving_recipe_id = recipe_id
        ctx.craving_meal_type = meal_type
        ctx.updated_at = datetime.utcnow()
        await self.db.flush()
        
        # Emit event
        await EventService.emit(
            db=self.db,
            user_id=user_id,
            event_type=EventType.CRAVING_OVERRIDE,
            entity_type="recipe",
            entity_id=recipe_id,
            metadata={"meal_type": meal_type},
        )
        
        return ctx

    async def get_today_context(
        self, user_id: uuid.UUID,
    ) -> Optional[DailyContext]:
        """Get today's context if it exists."""
        today = date.today()
        stmt = select(DailyContext).where(
            DailyContext.user_id == user_id,
            DailyContext.date == today,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def determine_change_level(
        self, ctx: DailyContext, previous_ctx: Optional[DailyContext] = None,
    ) -> PlanChangeLevel:
        """Determine the minimum plan change needed based on today's context.
        
        Plan Stability rules from the frozen architecture:
        - Food mood change -> MINOR_ADJUSTMENT (re-score options)
        - Available time shrinks -> MINOR_ADJUSTMENT or MEAL_REPLACED
        - Pantry update -> MINOR_ADJUSTMENT (re-score for pantry overlap)
        - Workout added -> MINOR_ADJUSTMENT (adjust post-workout meal protein)
        - Craving override -> MEAL_REPLACED (for the craving slot)
        """
        if ctx.craving_recipe_id:
            return PlanChangeLevel.MEAL_REPLACED
        
        if ctx.available_cook_time_min is not None and ctx.available_cook_time_min <= 10:
            # Very short cooking time — may need to replace meals
            return PlanChangeLevel.MEAL_REPLACED
        
        # Check if anything meaningful changed vs. default
        has_changes = any([
            ctx.workout_today,
            ctx.food_mood is not None,
            ctx.pantry_food_ids is not None,
            ctx.available_cook_time_min is not None,
            ctx.hunger_level is not None,
            ctx.energy_level is not None,
        ])
        
        if has_changes:
            return PlanChangeLevel.MINOR_ADJUSTMENT
        
        return PlanChangeLevel.UNCHANGED

    async def _calculate_adjusted_calories(
        self, user_id: uuid.UUID, ctx: DailyContext,
    ) -> Optional[int]:
        """Calculate adjusted calorie target for today.
        
        Uses bounded adjustments — never bypasses safety floors.
        This is a lightweight calculation; the full profile comes from
        NutrientProfileService.
        """
        # For now, return None to use the base profile target.
        # The full integration with NutrientProfileService.build_profile_with_lifestyle()
        # happens when the daily API endpoint calls the meal plan service.
        # This placeholder exists for Phase 3 — the full implementation will
        # compute the delta from workout_today + hunger_level + energy_level.
        return None
