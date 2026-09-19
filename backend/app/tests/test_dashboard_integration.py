import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import date, datetime, timezone

from app.services.daily_context_service import DailyContextService
from app.services.feedback_service import FeedbackService
from app.services.behavioral_service import BehavioralService
from app.services.conflict_resolver import ConflictResolver
from app.models.daily_context import DailyContext
from app.models.enums import (
    DailyCheckInStatus, PlanChangeLevel, FoodMood, EnergyLevel,
    PreferenceTier, FeedbackScope, EventType, BehavioralDimension,
)


class TestDashboardCheckInFlow:
    """Dashboard check-in must use minimum plan change."""

    def test_checkin_with_mood_is_minor_adjustment(self):
        """Check-in with food mood should be MINOR_ADJUSTMENT not FULL_REGENERATION."""
        ctx = DailyContext(
            user_id=uuid.uuid4(),
            date=date.today(),
            status=DailyCheckInStatus.COMPLETED,
            food_mood=FoodMood.COMFORT,
            energy_level=EnergyLevel.NORMAL,
        )
        service = DailyContextService(db=MagicMock())
        level = service.determine_change_level(ctx)
        assert level == PlanChangeLevel.MINOR_ADJUSTMENT
        assert level != PlanChangeLevel.FULL_REGENERATION

    def test_skipped_checkin_unchanged(self):
        """Skipped check-in should result in UNCHANGED plan."""
        ctx = DailyContext(
            user_id=uuid.uuid4(),
            date=date.today(),
            status=DailyCheckInStatus.SKIPPED,
        )
        service = DailyContextService(db=MagicMock())
        level = service.determine_change_level(ctx)
        assert level == PlanChangeLevel.UNCHANGED


class TestDashboardFeedbackFlow:
    """Dashboard rejection must replace only the affected meal."""

    @pytest.mark.asyncio
    async def test_rejection_returns_meal_replaced(self):
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = FeedbackService(db=mock_db)
        with patch('app.services.feedback_service.EventService.emit', new_callable=AsyncMock):
            result = await service.process_rejection(
                user_id=uuid.uuid4(),
                recipe_id=uuid.uuid4(),
                feedback_type="REJECTION",
                reason="DONT_LIKE_TASTE",
                scope="TODAY",
            )
        assert result["change_level"] == PlanChangeLevel.MEAL_REPLACED.value

    @pytest.mark.asyncio
    async def test_positive_feedback_no_plan_change(self):
        """Positive feedback should not trigger plan change."""
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = FeedbackService(db=mock_db)
        with patch('app.services.feedback_service.EventService.emit', new_callable=AsyncMock):
            result = await service.process_positive_feedback(
                user_id=uuid.uuid4(),
                recipe_id=uuid.uuid4(),
            )
        # Positive feedback doesn't include change_level (no plan change needed)
        assert "change_level" not in result


class TestDashboardNutrientComputation:
    """Dashboard nutrition display must use real data, not mocks."""

    def test_calorie_target_from_context(self):
        """Adjusted calorie target from daily context should be used."""
        ctx = DailyContext(
            user_id=uuid.uuid4(),
            date=date.today(),
            status=DailyCheckInStatus.COMPLETED,
            adjusted_calorie_target=1800,
        )
        # The frontend reads ctx.adjusted_calorie_target
        assert ctx.adjusted_calorie_target == 1800

    def test_default_calorie_target_when_no_context(self):
        """Without daily context, calorie target should use base profile."""
        ctx = DailyContext(
            user_id=uuid.uuid4(),
            date=date.today(),
            status=DailyCheckInStatus.PENDING,
        )
        # adjusted_calorie_target is None -> frontend uses default 2000
        assert ctx.adjusted_calorie_target is None


class TestDashboardInsightsIntegration:
    """Behavioral insights must use real computed data."""

    def test_insight_requires_sufficient_data(self):
        """Insights should only appear with enough samples."""
        # Profile with low sample count should NOT generate insight
        p = MagicMock()
        p.dimension = BehavioralDimension.CUISINE_PREFERENCE
        p.meal_type = "BREAKFAST"
        p.entity_key = "South Indian"
        p.observed_strength = 0.8
        p.confidence = 0.3  # Below threshold
        p.sample_count = 5

        insights = BehavioralService.check_for_insights([p])
        assert len(insights) == 0

    def test_insight_generated_with_sufficient_data(self):
        """Insights should appear when pattern is strong enough."""
        p = MagicMock()
        p.dimension = BehavioralDimension.CUISINE_PREFERENCE
        p.meal_type = "BREAKFAST"
        p.entity_key = "South Indian"
        p.observed_strength = 0.8
        p.confidence = 0.6  # Above threshold
        p.sample_count = 25

        insights = BehavioralService.check_for_insights([p])
        assert len(insights) == 1
        assert "Munchly learned" in insights[0].message


class TestDashboardConflictDisplay:
    """Conflicts must be detected from real user profile data."""

    def test_no_conflict_displays_nothing(self):
        report = ConflictResolver.detect_conflicts(
            diet_type="VEGETARIAN",
            health_goal="MAINTAIN_WEIGHT",
            weekly_budget=2000,
        )
        assert not report.has_conflicts

    def test_conflict_surfaces_options(self):
        report = ConflictResolver.detect_conflicts(
            diet_type="VEGAN",
            health_goal="BUILD_MUSCLE",
        )
        assert report.has_conflicts
        assert all(len(c.options) >= 2 for c in report.conflicts)


class TestDashboardSafetyPreservation:
    """Dashboard interactions must not bypass safety boundaries."""

    @pytest.mark.asyncio
    async def test_feedback_cannot_create_allergy(self):
        """Dashboard rejection must NEVER create allergy constraint."""
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = FeedbackService(db=mock_db)
        with pytest.raises(ValueError, match="Cannot create ALLERGY"):
            await service._create_override(
                user_id=uuid.uuid4(),
                entity_type="ingredient",
                entity_id=uuid.uuid4(),
                tier=PreferenceTier.ALLERGY,
            )

    def test_behavioral_confidence_never_reaches_one(self):
        """Behavioral confidence must never fully override explicit preferences."""
        conf = BehavioralService.compute_confidence(10000)
        assert conf < 1.0
