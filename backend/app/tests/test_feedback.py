import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date, timezone

from app.services.feedback_service import FeedbackService
from app.services.conflict_resolver import ConflictResolver
from app.models.feedback import UserFeedback, UserPreferenceOverride
from app.models.enums import (
    FeedbackType, FeedbackScope, PreferenceTier,
    PlanChangeLevel, ConflictType,
)


class TestFiveTierHierarchy:
    """The 5-tier hierarchy must be architecturally enforced."""

    def test_today_scope_maps_to_dislike(self):
        """TODAY scope -> DISLIKE tier."""
        assert FeedbackService.SCOPE_TO_TIER[FeedbackScope.TODAY] == PreferenceTier.DISLIKE

    def test_future_scope_maps_to_dislike(self):
        """FUTURE scope -> DISLIKE tier."""
        assert FeedbackService.SCOPE_TO_TIER[FeedbackScope.FUTURE] == PreferenceTier.DISLIKE

    def test_permanent_scope_maps_to_avoidance(self):
        """PERMANENT scope -> AVOIDANCE tier."""
        assert FeedbackService.SCOPE_TO_TIER[FeedbackScope.PERMANENT] == PreferenceTier.AVOIDANCE

    @pytest.mark.asyncio
    async def test_cannot_create_medical_override_from_feedback(self):
        """Critical safety: feedback NEVER creates MEDICAL overrides."""
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        service = FeedbackService(db=mock_db)
        
        with pytest.raises(ValueError, match="Cannot create MEDICAL"):
            await service._create_override(
                user_id=uuid.uuid4(),
                entity_type="ingredient",
                entity_id=uuid.uuid4(),
                tier=PreferenceTier.MEDICAL,
            )

    @pytest.mark.asyncio
    async def test_cannot_create_allergy_override_from_feedback(self):
        """Critical safety: feedback NEVER creates ALLERGY overrides."""
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

    def test_preference_tiers_exist(self):
        """All 5 tiers must exist."""
        assert len(PreferenceTier) == 5
        expected = {"PREFERENCE", "DISLIKE", "AVOIDANCE", "MEDICAL", "ALLERGY"}
        actual = {t.value for t in PreferenceTier}
        assert actual == expected


class TestFeedbackPersistence:
    @pytest.mark.asyncio
    async def test_rejection_creates_feedback_record(self):
        """Rejection should create a UserFeedback record."""
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()
        
        # Mock execute for _create_override
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        service = FeedbackService(db=mock_db)
        recipe_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        with patch('app.services.feedback_service.EventService.emit', new_callable=AsyncMock):
            result = await service.process_rejection(
                user_id=user_id,
                recipe_id=recipe_id,
                feedback_type="REJECTION",
                reason="DONT_LIKE_TASTE",
                scope="FUTURE",
            )
        
        assert result["applied_tier"] == "DISLIKE"
        assert result["change_level"] == "MEAL_REPLACED"
        assert len(result["affected_entities"]) >= 1

    @pytest.mark.asyncio
    async def test_rejection_emits_event(self):
        """Rejection should emit FEEDBACK_SUBMITTED event."""
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        service = FeedbackService(db=mock_db)
        
        with patch('app.services.feedback_service.EventService.emit', new_callable=AsyncMock) as mock_emit:
            await service.process_rejection(
                user_id=uuid.uuid4(),
                recipe_id=uuid.uuid4(),
                scope="TODAY",
            )
            mock_emit.assert_called()
            # First call should be FEEDBACK_SUBMITTED
            first_call = mock_emit.call_args_list[0]
            assert first_call.kwargs["event_type"].value == "FEEDBACK_SUBMITTED"


class TestScopeApplication:
    @pytest.mark.asyncio
    async def test_today_scope_has_expiry(self):
        """TODAY scope should set an expiry date."""
        expiry = FeedbackService._calculate_expiry(FeedbackScope.TODAY)
        assert expiry is not None
        assert expiry > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_future_scope_no_expiry(self):
        """FUTURE scope should not expire."""
        expiry = FeedbackService._calculate_expiry(FeedbackScope.FUTURE)
        assert expiry is None

    @pytest.mark.asyncio
    async def test_permanent_scope_no_expiry(self):
        """PERMANENT scope should not expire."""
        expiry = FeedbackService._calculate_expiry(FeedbackScope.PERMANENT)
        assert expiry is None


class TestIngredientRejection:
    @pytest.mark.asyncio
    async def test_ingredient_rejection_creates_ingredient_overrides(self):
        """Ingredient rejection should create overrides for each ingredient."""
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        service = FeedbackService(db=mock_db)
        ing1 = str(uuid.uuid4())
        ing2 = str(uuid.uuid4())
        
        with patch('app.services.feedback_service.EventService.emit', new_callable=AsyncMock) as mock_emit:
            result = await service.process_rejection(
                user_id=uuid.uuid4(),
                recipe_id=uuid.uuid4(),
                feedback_type="INGREDIENT_REJECTION",
                ingredient_ids=[ing1, ing2],
                scope="PERMANENT",
            )
        
        # Should have recipe + 2 ingredient entities
        assert len(result["affected_entities"]) == 3
        types = [e["type"] for e in result["affected_entities"]]
        assert types.count("ingredient") == 2
        assert types.count("recipe") == 1

    @pytest.mark.asyncio
    async def test_ingredient_rejection_emits_ingredient_events(self):
        """Each rejected ingredient should emit its own event."""
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        service = FeedbackService(db=mock_db)
        ing1 = str(uuid.uuid4())
        
        with patch('app.services.feedback_service.EventService.emit', new_callable=AsyncMock) as mock_emit:
            await service.process_rejection(
                user_id=uuid.uuid4(),
                recipe_id=uuid.uuid4(),
                feedback_type="INGREDIENT_REJECTION",
                ingredient_ids=[ing1],
                scope="FUTURE",
            )
        
        # Should have FEEDBACK_SUBMITTED + INGREDIENT_REJECTED events
        event_types = [call.kwargs["event_type"].value for call in mock_emit.call_args_list]
        assert "FEEDBACK_SUBMITTED" in event_types
        assert "INGREDIENT_REJECTED" in event_types


class TestPlanStabilityFromFeedback:
    @pytest.mark.asyncio
    async def test_rejection_uses_meal_replaced_not_full_regen(self):
        """Rejection should use MEAL_REPLACED, not FULL_REGENERATION."""
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
                scope="TODAY",
            )
        
        assert result["change_level"] == PlanChangeLevel.MEAL_REPLACED.value
        assert result["change_level"] != PlanChangeLevel.FULL_REGENERATION.value


class TestPositiveFeedback:
    @pytest.mark.asyncio
    async def test_positive_creates_preference_tier(self):
        """Positive feedback should create PREFERENCE tier override."""
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
        
        assert result["applied_tier"] == PreferenceTier.PREFERENCE.value


class TestConflictResolver:
    def test_vegan_muscle_conflict_detected(self):
        """Vegan + build muscle should detect protein conflict."""
        report = ConflictResolver.detect_conflicts(
            diet_type="VEGAN",
            health_goal="BUILD_MUSCLE",
        )
        assert report.has_conflicts
        types = [c.conflict_type for c in report.conflicts]
        assert ConflictType.DIET_VS_PROTEIN in types

    def test_low_budget_gain_weight_conflict(self):
        """Very low budget + gain weight should detect conflict."""
        report = ConflictResolver.detect_conflicts(
            health_goal="GAIN_WEIGHT",
            weekly_budget=500,
        )
        assert report.has_conflicts
        types = [c.conflict_type for c in report.conflicts]
        assert ConflictType.BUDGET_VS_NUTRITION in types

    def test_no_conflict_normal_profile(self):
        """Normal profile should have no conflicts."""
        report = ConflictResolver.detect_conflicts(
            diet_type="NON_VEGETARIAN",
            health_goal="MAINTAIN_WEIGHT",
            weekly_budget=2000,
            max_prep_time_min=30,
        )
        assert not report.has_conflicts

    def test_conflicts_have_options(self):
        """Each conflict must have resolution options for user to choose."""
        report = ConflictResolver.detect_conflicts(
            diet_type="VEGAN",
            health_goal="BUILD_MUSCLE",
        )
        for conflict in report.conflicts:
            assert len(conflict.options) >= 2

    def test_short_cook_time_conflict(self):
        """Very short prep time should detect time vs nutrition conflict."""
        report = ConflictResolver.detect_conflicts(
            max_prep_time_min=5,
            health_goal="BUILD_MUSCLE",
        )
        assert report.has_conflicts
        types = [c.conflict_type for c in report.conflicts]
        assert ConflictType.TIME_VS_NUTRITION in types

    def test_many_avoidances_warning(self):
        """5+ avoidances should generate a warning."""
        report = ConflictResolver.detect_conflicts(
            avoidance_count=7,
        )
        assert len(report.warnings) > 0

    def test_keto_low_carb_redundancy(self):
        """Keto + low-carb should detect redundancy."""
        report = ConflictResolver.detect_conflicts(
            dietary_restrictions=["KETO", "LOW_CARB"],
        )
        assert report.has_conflicts
        types = [c.conflict_type for c in report.conflicts]
        assert ConflictType.MULTIPLE_RESTRICTIONS in types
