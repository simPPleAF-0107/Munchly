import pytest
from app.services.behavioral_service import BehavioralService
from app.models.enums import BehavioralDimension

class TestConfidenceCurve:
    """Verify confidence evolution at 1/5/9/10/20/50/100 samples."""
    
    def test_below_threshold_zero_influence(self):
        """1, 5, 9 actions -> confidence effectively 0 (no behavioral influence)."""
        for count in [1, 5, 9]:
            conf = BehavioralService.compute_confidence(count)
            assert conf == 0.0, f"count={count} should have 0 confidence"
    
    def test_at_threshold(self):
        """10 actions -> just at threshold, minimal confidence."""
        conf = BehavioralService.compute_confidence(10)
        assert conf >= 0.0
    
    def test_moderate_confidence(self):
        """20 actions -> moderate."""
        conf = BehavioralService.compute_confidence(20)
        assert 0.1 < conf < 0.6
    
    def test_high_confidence(self):
        """50 actions -> strong."""
        conf = BehavioralService.compute_confidence(50)
        assert conf > 0.5
    
    def test_cap_at_90_percent(self):
        """100+ actions -> capped at 0.9."""
        conf = BehavioralService.compute_confidence(100)
        assert conf <= 0.9
        conf = BehavioralService.compute_confidence(100000)
        assert conf <= 0.9
    
    def test_monotonically_increasing(self):
        """More samples -> higher confidence (never decreases)."""
        prev = 0.0
        for count in [1, 5, 10, 20, 50, 100, 500]:
            conf = BehavioralService.compute_confidence(count)
            assert conf >= prev, f"Confidence decreased from {prev} at count={count}"
            prev = conf


class TestPreferenceCombination:
    """Verify combined = explicit * (1-conf) + behavioral * conf."""
    
    def test_zero_confidence_uses_explicit(self):
        combined = BehavioralService.combine_preferences(0.8, 0.2, confidence=0.0)
        assert combined == 0.8  # 100% explicit
    
    def test_max_confidence_retains_explicit(self):
        combined = BehavioralService.combine_preferences(1.0, 0.0, confidence=0.9)
        assert combined >= 0.1  # At least 10% explicit
    
    def test_half_confidence_blends(self):
        combined = BehavioralService.combine_preferences(0.8, 0.4, confidence=0.5)
        expected = 0.8 * 0.5 + 0.4 * 0.5  # = 0.6
        assert abs(combined - expected) < 0.01
    
    def test_explicit_love_behavioral_reject(self):
        """User explicitly loves X but behaviorally avoids it."""
        combined = BehavioralService.combine_preferences(
            explicit_strength=1.0, behavioral_strength=0.0, confidence=0.9
        )
        # Explicit should still retain 10% influence
        assert combined >= 0.1
    
    def test_explicit_dislike_behavioral_select(self):
        """User explicitly dislikes X but behaviorally selects it."""
        combined = BehavioralService.combine_preferences(
            explicit_strength=0.0, behavioral_strength=1.0, confidence=0.9
        )
        # Should be influenced by behavior but NOT fully override
        assert combined <= 0.9


class TestBehavioralDimensions:
    """Verify behavioral dimensions exist and are tracked."""
    
    def test_expected_dimensions_exist(self):
        # Adapted from user request to match actual enums in enums.py
        expected = {'CUISINE_PREFERENCE', 'TIME_OF_DAY_PATTERN', 'INGREDIENT_PREFERENCE', 'COMPLEXITY_PREFERENCE'}
        actual = {d.value for d in BehavioralDimension}
        assert expected.issubset(actual)
