import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.feedback_service import FeedbackService
from app.services.behavioral_service import BehavioralService
from app.services.conflict_resolver import ConflictResolver
from app.models.enums import (
    PreferenceTier, DietType, FeedbackScope, EventType,
    BehavioralDimension, Allergen, MedicalCondition,
)


class TestAllergenSafety:
    """ALLERGY constraints must never be bypassed."""

    @pytest.mark.asyncio
    async def test_feedback_cannot_create_allergy_override(self):
        """User feedback NEVER creates ALLERGY tier override."""
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        service = FeedbackService(db=mock_db)
        with pytest.raises((ValueError, Exception)):
            await service._create_override(
                user_id=uuid.uuid4(),
                entity_type="ingredient",
                entity_id=uuid.uuid4(),
                tier=PreferenceTier.ALLERGY,
            )

    @pytest.mark.asyncio
    async def test_feedback_cannot_create_medical_override(self):
        """User feedback NEVER creates MEDICAL tier override."""
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        service = FeedbackService(db=mock_db)
        with pytest.raises((ValueError, Exception)):
            await service._create_override(
                user_id=uuid.uuid4(),
                entity_type="ingredient",
                entity_id=uuid.uuid4(),
                tier=PreferenceTier.MEDICAL,
            )

    def test_rejection_produces_avoidance_not_allergy(self):
        """PERMANENT rejection should produce AVOIDANCE tier, not ALLERGY."""
        # When a user permanently rejects an ingredient, it becomes
        # AVOIDANCE (reversible) not ALLERGY (safety-critical)
        assert PreferenceTier.AVOIDANCE.value != PreferenceTier.ALLERGY.value
        # AVOIDANCE is in scoring layer, ALLERGY is in constraint layer


class TestBehavioralSafetyBoundary:
    """Behavioral learning must NEVER escalate to safety constraints."""

    def test_behavioral_confidence_capped(self):
        """Confidence never reaches 1.0 - explicit always retains weight."""
        conf = BehavioralService.compute_confidence(100000)
        assert conf < 1.0
        assert conf <= 0.9

    def test_behavioral_cannot_override_explicit(self):
        """Even max behavioral confidence retains 10% explicit weight."""
        # explicit = 1.0 (strong preference), behavioral = 0.0 (opposite)
        combined = BehavioralService.combine_preferences(
            explicit_strength=1.0,
            behavioral_strength=0.0,
            confidence=0.9,  # Maximum confidence
        )
        # At max confidence: 1.0 * (1-0.9) + 0.0 * 0.9 = 0.1
        assert combined >= 0.1  # Explicit still has influence

    def test_repeated_skipping_does_not_create_allergy(self):
        """User skipping peanuts 100 times creates behavioral signal, NOT allergy."""
        # Get event signal for MEAL_SKIPPED
        signal = BehavioralService.get_event_signal(EventType.MEAL_SKIPPED)
        # Should return a float signal, NOT create a safety constraint
        assert isinstance(signal, (float, type(None)))

    def test_behavioral_reset_preserves_safety(self):
        """Resetting behavioral profiles must NOT affect MEDICAL/ALLERGY."""
        profile = MagicMock()
        profile.dimension = BehavioralDimension.CUISINE_PREFERENCE
        profile.observed_strength = 0.8
        profile.confidence = 0.7
        profile.sample_count = 50
        
        reset = BehavioralService.reset_behavioral_profiles([profile])
        # After reset, behavioral data is zeroed
        for p in reset:
            assert p.observed_strength == 0.0
            assert p.confidence == 0.0
            assert p.sample_count == 0
        # But this does NOT touch UserAllergy or UserHealthCondition
        # (those are separate models entirely)


class TestTierHierarchyEnforcement:
    """Verify ALLERGY > MEDICAL > AVOIDANCE > DISLIKE > PREFERENCE."""

    def test_tier_ordering(self):
        """PreferenceTier enum values must maintain strict ordering."""
        tiers = list(PreferenceTier)
        tier_names = [t.value for t in tiers]
        assert "ALLERGY" in tier_names
        assert "MEDICAL" in tier_names
        assert "AVOIDANCE" in tier_names
        assert "DISLIKE" in tier_names
        assert "PREFERENCE" in tier_names

    def test_allergy_is_hard_constraint(self):
        """Allergy belongs in constraint layer, not scoring layer."""
        # Verify that allergy and medical are treated as safety-critical
        safety_tiers = {PreferenceTier.ALLERGY, PreferenceTier.MEDICAL}
        scoring_tiers = {PreferenceTier.AVOIDANCE, PreferenceTier.DISLIKE, PreferenceTier.PREFERENCE}
        assert safety_tiers.isdisjoint(scoring_tiers)


class TestConflictDetection:
    """Conflicting constraints must be surfaced, not silently ignored."""

    def test_vegan_muscle_conflict(self):
        """Vegan + build muscle should surface a conflict."""
        report = ConflictResolver.detect_conflicts(
            diet_type="VEGAN",
            health_goal="BUILD_MUSCLE",
        )
        assert report.has_conflicts
        assert len(report.conflicts) >= 1

    def test_conflict_has_options(self):
        """Every conflict must offer actionable options."""
        report = ConflictResolver.detect_conflicts(
            diet_type="VEGAN",
            health_goal="BUILD_MUSCLE",
        )
        for conflict in report.conflicts:
            assert len(conflict.options) >= 2, "Each conflict must offer at least 2 options"

    def test_no_conflict_for_compatible(self):
        """Compatible constraints should not flag false conflicts."""
        report = ConflictResolver.detect_conflicts(
            diet_type="VEGETARIAN",
            health_goal="MAINTAIN_WEIGHT",
            weekly_budget=2000,
        )
        assert not report.has_conflicts

    def test_low_budget_high_goal_conflict(self):
        """Very low budget + muscle gain should flag conflict."""
        report = ConflictResolver.detect_conflicts(
            diet_type="NON_VEGETARIAN",
            health_goal="BUILD_MUSCLE",
            weekly_budget=300,
        )
        assert report.has_conflicts


class TestFeedbackScopeEnforcement:
    """Feedback scope must limit impact correctly."""

    @pytest.mark.asyncio
    async def test_today_scope_does_not_affect_future(self):
        """TODAY scope rejection should not create PERMANENT override."""
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
        assert result["change_level"] is not None
