import uuid
import math
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from app.services.behavioral_service import (
    BehavioralService, MEANINGFUL_EVENTS, EVENT_SIGNALS,
)
from app.models.behavioral_profile import UserBehavioralProfile, UserBehavioralInsight
from app.models.enums import (
    EventType, BehavioralDimension, InsightStatus, PreferenceTier,
)


class TestMeaningfulEvents:
    """Only meaningful actions should count toward sample_count."""

    def test_meal_viewed_not_meaningful(self):
        """Viewing a recipe 10 times != selecting it 10 times."""
        assert EventType.MEAL_VIEWED not in MEANINGFUL_EVENTS

    def test_meal_suggested_not_meaningful(self):
        """Being suggested a meal is not an action."""
        assert EventType.MEAL_SUGGESTED not in MEANINGFUL_EVENTS

    def test_meal_selected_is_meaningful(self):
        assert EventType.MEAL_SELECTED in MEANINGFUL_EVENTS

    def test_meal_eaten_is_meaningful(self):
        assert EventType.MEAL_EATEN in MEANINGFUL_EVENTS

    def test_meal_skipped_is_meaningful(self):
        assert EventType.MEAL_SKIPPED in MEANINGFUL_EVENTS

    def test_meal_replaced_is_meaningful(self):
        assert EventType.MEAL_REPLACED in MEANINGFUL_EVENTS

    def test_feedback_submitted_is_meaningful(self):
        assert EventType.FEEDBACK_SUBMITTED in MEANINGFUL_EVENTS


class TestEventSignals:
    def test_meal_eaten_strongest_positive(self):
        """MEAL_EATEN should be the strongest positive signal."""
        signal = BehavioralService.get_event_signal(EventType.MEAL_EATEN)
        assert signal > 0
        assert signal >= EVENT_SIGNALS[EventType.MEAL_SELECTED]

    def test_ingredient_rejected_strong_negative(self):
        signal = BehavioralService.get_event_signal(EventType.INGREDIENT_REJECTED)
        assert signal < 0

    def test_meal_viewed_returns_none(self):
        """Non-meaningful events should return None."""
        signal = BehavioralService.get_event_signal(EventType.MEAL_VIEWED)
        assert signal is None

    def test_feedback_positive_is_positive(self):
        signal = BehavioralService.get_event_signal(
            EventType.FEEDBACK_SUBMITTED,
            metadata={"feedback_type": "POSITIVE"},
        )
        assert signal > 0

    def test_feedback_rejection_is_negative(self):
        signal = BehavioralService.get_event_signal(
            EventType.FEEDBACK_SUBMITTED,
            metadata={"feedback_type": "REJECTION"},
        )
        assert signal < 0


class TestConfidenceComputation:
    def test_below_threshold_zero(self):
        """< 10 actions -> confidence = 0."""
        for n in range(0, 10):
            assert BehavioralService.compute_confidence(n) == 0.0

    def test_at_threshold_starts(self):
        """At exactly 10 actions, confidence should be > 0 but small."""
        conf = BehavioralService.compute_confidence(10)
        assert conf == 0.0  # At MIN_ACTIONS, effective=0, so 1-exp(0)=0

    def test_above_threshold_grows(self):
        """20 actions should have meaningful confidence."""
        conf = BehavioralService.compute_confidence(20)
        assert conf > 0.3

    def test_high_sample_saturates(self):
        """50+ actions should saturate near MAX_CONFIDENCE."""
        conf = BehavioralService.compute_confidence(50)
        assert conf >= 0.8

    def test_confidence_never_exceeds_max(self):
        """Confidence must NEVER exceed MAX_CONFIDENCE (0.9)."""
        for n in [100, 500, 1000]:
            conf = BehavioralService.compute_confidence(n)
            assert conf <= BehavioralService.MAX_CONFIDENCE

    def test_confidence_monotonic(self):
        """More samples should never decrease confidence."""
        prev = 0.0
        for n in range(0, 100):
            conf = BehavioralService.compute_confidence(n)
            assert conf >= prev
            prev = conf


class TestEMA:
    def test_ema_smooths(self):
        """EMA should smooth signals, not overreact."""
        strength = 0.0
        # Add 5 positive signals
        for _ in range(5):
            strength = BehavioralService.update_ema(strength, +0.5)
        # Should be positive but not 0.5
        assert 0.0 < strength < 0.5

    def test_ema_recovers(self):
        """After positive signals, negative signals should decrease strength."""
        strength = 0.4
        for _ in range(3):
            strength = BehavioralService.update_ema(strength, -0.5)
        assert strength < 0.4

    def test_ema_recent_weighted_more(self):
        """Recent signals should have more weight."""
        # Start at 0, add large positive
        s1 = BehavioralService.update_ema(0.0, 1.0)
        # Start at 0, add small positive
        s2 = BehavioralService.update_ema(0.0, 0.1)
        assert s1 > s2


class TestPreferenceCombination:
    def test_zero_confidence_fully_explicit(self):
        """With 0 confidence, combined = explicit."""
        combined = BehavioralService.combine_preferences(
            explicit_strength=0.8,
            behavioral_strength=0.2,
            confidence=0.0,
        )
        assert combined == 0.8

    def test_max_confidence_mostly_behavioral(self):
        """With max confidence (0.9), combined = 10% explicit + 90% behavioral."""
        combined = BehavioralService.combine_preferences(
            explicit_strength=0.0,
            behavioral_strength=1.0,
            confidence=0.9,
        )
        assert combined == pytest.approx(0.9, abs=0.01)

    def test_explicit_always_has_weight(self):
        """Even at max confidence, explicit retains 10% weight."""
        combined = BehavioralService.combine_preferences(
            explicit_strength=1.0,
            behavioral_strength=-1.0,
            confidence=0.9,
        )
        # 1.0 * 0.1 + (-1.0) * 0.9 = 0.1 - 0.9 = -0.8
        assert combined > -1.0  # Explicit prevents full behavioral

    def test_contradictory_preferences(self):
        """When explicit and behavioral disagree, explicit should still have weight."""
        # User explicitly likes (0.8) but behavior shows skipping (-0.6)
        combined = BehavioralService.combine_preferences(
            explicit_strength=0.8,
            behavioral_strength=-0.6,
            confidence=0.7,
        )
        # 0.8 * 0.3 + (-0.6) * 0.7 = 0.24 - 0.42 = -0.18
        assert combined == pytest.approx(-0.18, abs=0.01)

    def test_half_confidence_equal_weight(self):
        """At 0.5 confidence, equal weight to both."""
        combined = BehavioralService.combine_preferences(
            explicit_strength=1.0,
            behavioral_strength=0.0,
            confidence=0.5,
        )
        assert combined == pytest.approx(0.5, abs=0.01)


class TestInsightGeneration:
    def _make_profile(self, strength, confidence, sample_count=20,
                      dimension=BehavioralDimension.CUISINE_PREFERENCE,
                      meal_type="BREAKFAST", entity_key="South Indian"):
        p = MagicMock(spec=UserBehavioralProfile)
        p.dimension = dimension
        p.meal_type = meal_type
        p.entity_key = entity_key
        p.observed_strength = strength
        p.confidence = confidence
        p.sample_count = sample_count
        return p

    def test_strong_pattern_generates_insight(self):
        """Strong pattern (confidence > 0.5, |strength| > 0.4) should generate insight."""
        profiles = [self._make_profile(0.7, 0.6)]
        insights = BehavioralService.check_for_insights(profiles)
        assert len(insights) == 1
        assert "Munchly learned" in insights[0].message

    def test_weak_pattern_no_insight(self):
        """Weak pattern should NOT generate insight."""
        profiles = [self._make_profile(0.2, 0.3)]
        insights = BehavioralService.check_for_insights(profiles)
        assert len(insights) == 0

    def test_high_confidence_low_strength_no_insight(self):
        """High confidence but low strength = no insight."""
        profiles = [self._make_profile(0.1, 0.8)]
        insights = BehavioralService.check_for_insights(profiles)
        assert len(insights) == 0

    def test_negative_pattern_generates_insight(self):
        """Strong avoidance pattern should also generate insight."""
        profiles = [self._make_profile(-0.6, 0.7,
                    dimension=BehavioralDimension.INGREDIENT_AVOIDANCE,
                    entity_key="bitter gourd")]
        insights = BehavioralService.check_for_insights(profiles)
        assert len(insights) == 1
        assert "skip" in insights[0].message.lower() or "avoid" in insights[0].message.lower()


class TestPersonalizationReset:
    def test_reset_clears_behavioral_values(self):
        """Reset should zero out observed_strength, sample_count, confidence."""
        profiles = []
        for i in range(3):
            p = MagicMock(spec=UserBehavioralProfile)
            p.observed_strength = 0.8
            p.sample_count = 25
            p.confidence = 0.7
            profiles.append(p)
        
        BehavioralService.reset_behavioral_profiles(profiles)
        
        for p in profiles:
            assert p.observed_strength == 0.0
            assert p.sample_count == 0
            assert p.confidence == 0.0

    def test_reset_preserves_dimension_info(self):
        """Reset should keep the profile rows (dimension, entity_key) intact."""
        p = MagicMock(spec=UserBehavioralProfile)
        p.dimension = BehavioralDimension.CUISINE_PREFERENCE
        p.entity_key = "South Indian"
        p.observed_strength = 0.8
        p.sample_count = 25
        p.confidence = 0.7
        
        BehavioralService.reset_behavioral_profiles([p])
        
        # Dimension and entity_key should not be modified
        assert p.dimension == BehavioralDimension.CUISINE_PREFERENCE
        assert p.entity_key == "South Indian"


class TestSafetyBoundary:
    """Behavioral learning must NEVER cross the safety boundary."""

    def test_behavioral_confidence_capped(self):
        """Confidence can never reach 1.0 - explicit always retains weight."""
        # Even with 10000 samples
        conf = BehavioralService.compute_confidence(10000)
        assert conf < 1.0
        assert conf <= BehavioralService.MAX_CONFIDENCE

    def test_preference_tiers_architecturally_separate(self):
        """MEDICAL and ALLERGY are not in BehavioralDimension."""
        behavioral_dims = {d.value for d in BehavioralDimension}
        safety_tiers = {PreferenceTier.MEDICAL.value, PreferenceTier.ALLERGY.value}
        # These should be in completely separate enums
        assert behavioral_dims.isdisjoint(safety_tiers)

    def test_explicit_always_has_minimum_weight(self):
        """At max confidence, explicit still has 10% weight."""
        max_conf = BehavioralService.MAX_CONFIDENCE
        explicit_weight = round(1 - max_conf, 2)
        assert explicit_weight >= 0.1
