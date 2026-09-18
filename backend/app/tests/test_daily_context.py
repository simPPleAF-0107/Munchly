import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, datetime

from app.services.daily_context_service import DailyContextService
from app.models.daily_context import DailyContext
from app.models.enums import (
    DailyCheckInStatus, PlanChangeLevel, FoodMood,
    HungerLevel, EnergyLevel,
)


class TestPlanStability:
    """Plan Stability: daily context should modify today's recommendation
    with the smallest necessary change."""

    def test_no_context_unchanged(self):
        """Empty context = UNCHANGED."""
        ctx = DailyContext(
            user_id=uuid.uuid4(),
            date=date.today(),
            status=DailyCheckInStatus.PENDING,
        )
        service = DailyContextService(db=MagicMock())
        level = service.determine_change_level(ctx)
        assert level == PlanChangeLevel.UNCHANGED

    def test_food_mood_minor_adjustment(self):
        """Food mood change = MINOR_ADJUSTMENT."""
        ctx = DailyContext(
            user_id=uuid.uuid4(),
            date=date.today(),
            status=DailyCheckInStatus.COMPLETED,
            food_mood=FoodMood.COMFORT,
        )
        service = DailyContextService(db=MagicMock())
        level = service.determine_change_level(ctx)
        assert level == PlanChangeLevel.MINOR_ADJUSTMENT

    def test_workout_minor_adjustment(self):
        """Workout today = MINOR_ADJUSTMENT."""
        ctx = DailyContext(
            user_id=uuid.uuid4(),
            date=date.today(),
            status=DailyCheckInStatus.COMPLETED,
            workout_today=True,
        )
        service = DailyContextService(db=MagicMock())
        level = service.determine_change_level(ctx)
        assert level == PlanChangeLevel.MINOR_ADJUSTMENT

    def test_pantry_update_minor_adjustment(self):
        """Pantry update = MINOR_ADJUSTMENT."""
        ctx = DailyContext(
            user_id=uuid.uuid4(),
            date=date.today(),
            status=DailyCheckInStatus.COMPLETED,
            pantry_food_ids=["food-1", "food-2"],
        )
        service = DailyContextService(db=MagicMock())
        level = service.determine_change_level(ctx)
        assert level == PlanChangeLevel.MINOR_ADJUSTMENT

    def test_very_short_cook_time_meal_replaced(self):
        """Very short cooking time (<=10 min) = MEAL_REPLACED."""
        ctx = DailyContext(
            user_id=uuid.uuid4(),
            date=date.today(),
            status=DailyCheckInStatus.COMPLETED,
            available_cook_time_min=5,
        )
        service = DailyContextService(db=MagicMock())
        level = service.determine_change_level(ctx)
        assert level == PlanChangeLevel.MEAL_REPLACED

    def test_craving_override_meal_replaced(self):
        """Craving override = MEAL_REPLACED."""
        ctx = DailyContext(
            user_id=uuid.uuid4(),
            date=date.today(),
            status=DailyCheckInStatus.COMPLETED,
            craving_recipe_id=uuid.uuid4(),
            craving_meal_type="DINNER",
        )
        service = DailyContextService(db=MagicMock())
        level = service.determine_change_level(ctx)
        assert level == PlanChangeLevel.MEAL_REPLACED

    def test_moderate_cook_time_minor_adjustment(self):
        """Moderate cooking time (>10 min) = MINOR_ADJUSTMENT not MEAL_REPLACED."""
        ctx = DailyContext(
            user_id=uuid.uuid4(),
            date=date.today(),
            status=DailyCheckInStatus.COMPLETED,
            available_cook_time_min=25,
        )
        service = DailyContextService(db=MagicMock())
        level = service.determine_change_level(ctx)
        assert level == PlanChangeLevel.MINOR_ADJUSTMENT


class TestDailyContextCheckin:
    """Test check-in creates/updates context correctly."""

    @pytest.mark.asyncio
    async def test_check_in_creates_context(self):
        """Check-in should create a DailyContext and emit event."""
        mock_db = AsyncMock()
        # Mock the select query to return None (no existing context)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()
        
        service = DailyContextService(db=mock_db)
        
        with patch.object(service, 'get_or_create_today') as mock_get:
            ctx = DailyContext(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                date=date.today(),
                status=DailyCheckInStatus.PENDING,
            )
            mock_get.return_value = ctx
            
            with patch('app.services.daily_context_service.EventService.emit', new_callable=AsyncMock) as mock_emit:
                result = await service.check_in(
                    user_id=ctx.user_id,
                    workout_today=True,
                    food_mood="COMFORT",
                    hunger_level="HIGH",
                )
                
                assert result.status == DailyCheckInStatus.COMPLETED
                assert result.workout_today is True
                assert result.food_mood == FoodMood.COMFORT
                assert result.hunger_level == HungerLevel.HIGH
                mock_emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_always_available(self):
        """Skip must always be available."""
        mock_db = AsyncMock()
        service = DailyContextService(db=mock_db)
        
        with patch.object(service, 'get_or_create_today') as mock_get:
            ctx = DailyContext(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                date=date.today(),
                status=DailyCheckInStatus.PENDING,
            )
            mock_get.return_value = ctx
            
            result = await service.skip_check_in(user_id=ctx.user_id)
            assert result.status == DailyCheckInStatus.SKIPPED


class TestPantryAndCraving:
    @pytest.mark.asyncio
    async def test_pantry_update_emits_event(self):
        """Pantry update should emit PANTRY_UPDATED event."""
        mock_db = AsyncMock()
        service = DailyContextService(db=mock_db)
        
        with patch.object(service, 'get_or_create_today') as mock_get:
            ctx = DailyContext(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                date=date.today(),
                status=DailyCheckInStatus.COMPLETED,
            )
            mock_get.return_value = ctx
            
            with patch('app.services.daily_context_service.EventService.emit', new_callable=AsyncMock) as mock_emit:
                result = await service.update_pantry_today(
                    user_id=ctx.user_id,
                    food_ids=["food-1", "food-2"],
                )
                assert result.pantry_food_ids == ["food-1", "food-2"]
                mock_emit.assert_called_once()
                # Verify event type
                call_kwargs = mock_emit.call_args
                assert call_kwargs.kwargs["event_type"].value == "PANTRY_UPDATED"

    @pytest.mark.asyncio
    async def test_craving_override_emits_event(self):
        """Craving override should emit CRAVING_OVERRIDE event."""
        mock_db = AsyncMock()
        service = DailyContextService(db=mock_db)
        recipe_id = uuid.uuid4()
        
        with patch.object(service, 'get_or_create_today') as mock_get:
            ctx = DailyContext(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                date=date.today(),
                status=DailyCheckInStatus.COMPLETED,
            )
            mock_get.return_value = ctx
            
            with patch('app.services.daily_context_service.EventService.emit', new_callable=AsyncMock) as mock_emit:
                result = await service.craving_override(
                    user_id=ctx.user_id,
                    recipe_id=recipe_id,
                    meal_type="DINNER",
                )
                assert result.craving_recipe_id == recipe_id
                assert result.craving_meal_type == "DINNER"
                mock_emit.assert_called_once()
                call_kwargs = mock_emit.call_args
                assert call_kwargs.kwargs["event_type"].value == "CRAVING_OVERRIDE"
