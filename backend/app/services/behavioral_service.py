import uuid
import math
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

from app.models.enums import (
    EventType, BehavioralDimension, InsightStatus, PreferenceTier,
)
from app.models.behavioral_profile import UserBehavioralProfile, UserBehavioralInsight


# Events that count as meaningful behavioral signals
# MEAL_VIEWED and MEAL_SUGGESTED do NOT count
MEANINGFUL_EVENTS = {
    EventType.MEAL_SELECTED,
    EventType.MEAL_EATEN,
    EventType.MEAL_SKIPPED,
    EventType.MEAL_REPLACED,
    EventType.MEAL_FAVORITED,
    EventType.FEEDBACK_SUBMITTED,
    EventType.INGREDIENT_REJECTED,
}

# Event signal weights: positive events boost, negative events penalize
EVENT_SIGNALS = {
    EventType.MEAL_SELECTED: +0.3,    # Selected from options
    EventType.MEAL_EATEN: +0.5,       # Actually ate it (strongest positive)
    EventType.MEAL_FAVORITED: +0.7,   # Explicitly favorited
    EventType.MEAL_SKIPPED: -0.3,     # Skipped this meal
    EventType.MEAL_REPLACED: -0.5,    # Replaced (rejected)
    EventType.FEEDBACK_SUBMITTED: 0,  # Depends on feedback_type in metadata
    EventType.INGREDIENT_REJECTED: -0.7,  # Rejected an ingredient
}


@dataclass
class PreferenceAdjustment:
    """Combined explicit + behavioral preference for a dimension."""
    dimension: str
    entity_key: str
    explicit_strength: float      # From user's declared preferences
    behavioral_strength: float    # From observed behavior (EMA)
    combined_strength: float      # explicit * (1 - confidence) + behavioral * confidence
    confidence: float             # 0.0-0.9
    sample_count: int
    source: str                   # "EXPLICIT_ONLY" | "BEHAVIORAL_ONLY" | "COMBINED"


@dataclass
class InsightCandidate:
    """A potential 'Munchly Learned...' insight."""
    dimension: BehavioralDimension
    meal_type: Optional[str]
    entity_key: str
    message: str
    observed_strength: float
    confidence: float


class BehavioralService:
    """Learns from user behavior to personalize recommendations.
    
    CONSUMES the immutable event store from Phase 1.
    PRODUCES behavioral profiles that feed into recommendation scoring.
    
    Architecture:
        User Action -> Immutable Event -> Behavioral Aggregation ->
        Behavioral Profile -> Recommendation (scoring layer ONLY)
    
    Critical safety rules:
    1. Behavioral learning feeds ONLY into recommendation scoring
    2. It NEVER feeds into the constraint/safety layer
    3. It can NEVER create MEDICAL or ALLERGY overrides
    4. Explicit preferences always retain weight (confidence caps at 0.9)
    5. 10 meaningful actions required before any behavioral inference
    """

    MIN_ACTIONS = 10  # Minimum meaningful events before inference
    EMA_ALPHA = 0.15  # Exponential moving average smoothing factor
    MAX_CONFIDENCE = 0.9  # Behavioral confidence cap (explicit always has >=10% weight)
    INSIGHT_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence to generate insight
    INSIGHT_STRENGTH_THRESHOLD = 0.4    # Minimum |observed_strength| for insight

    @classmethod
    def compute_confidence(cls, sample_count: int) -> float:
        """Compute confidence from sample count.
        
        - sample_count < MIN_ACTIONS -> 0.0 (use explicit preferences only)
        - sample_count 10-30 -> grows from 0 to ~0.7
        - sample_count 30+ -> saturates near 0.8-0.9
        - CAPPED at MAX_CONFIDENCE so explicit preferences always have weight
        
        Uses logistic-style growth: confidence = MAX * (1 - e^(-k*(n-MIN)))
        """
        if sample_count < cls.MIN_ACTIONS:
            return 0.0
        
        effective = sample_count - cls.MIN_ACTIONS
        # k controls growth rate; ~0.1 means ~30 samples to reach 0.8
        raw = 1.0 - math.exp(-0.1 * effective)
        return round(min(raw * cls.MAX_CONFIDENCE, cls.MAX_CONFIDENCE), 4)

    @classmethod
    def update_ema(
        cls,
        current_strength: float,
        new_signal: float,
        alpha: float = None,
    ) -> float:
        """Update Exponential Moving Average.
        
        EMA smooths behavioral signals so the system doesn't overreact
        to temporary mood. Recent actions have more weight.
        
        2 selections != 50 selections.
        """
        alpha = alpha or cls.EMA_ALPHA
        return round(current_strength * (1 - alpha) + new_signal * alpha, 6)

    @classmethod
    def get_event_signal(
        cls,
        event_type: EventType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[float]:
        """Get the behavioral signal value for an event.
        
        Returns None if this event type is not meaningful for behavior.
        
        For FEEDBACK_SUBMITTED, the signal depends on the feedback_type
        in the metadata:
        - POSITIVE -> +0.5
        - REJECTION, INGREDIENT_REJECTION -> -0.5
        - Others (TOO_COMPLEX, etc.) -> -0.2
        """
        if event_type not in MEANINGFUL_EVENTS:
            return None
        
        if event_type == EventType.FEEDBACK_SUBMITTED and metadata:
            feedback_type = metadata.get("feedback_type", "")
            if feedback_type == "POSITIVE":
                return +0.5
            elif feedback_type in ("REJECTION", "INGREDIENT_REJECTION"):
                return -0.5
            else:
                return -0.2
        
        return EVENT_SIGNALS.get(event_type)

    @classmethod
    def combine_preferences(
        cls,
        explicit_strength: float,
        behavioral_strength: float,
        confidence: float,
    ) -> float:
        """Combine explicit and behavioral preferences.
        
        combined = explicit * (1 - confidence) + behavioral * confidence
        
        When confidence is 0 (< MIN_ACTIONS): fully explicit
        When confidence is 0.9 (max): 10% explicit + 90% behavioral
        Explicit always retains at least 10% weight.
        """
        return round(
            explicit_strength * (1 - confidence) + behavioral_strength * confidence,
            4,
        )

    @classmethod
    def generate_insight_message(
        cls,
        dimension: BehavioralDimension,
        meal_type: Optional[str],
        entity_key: str,
        observed_strength: float,
    ) -> str:
        """Generate a human-readable 'Munchly Learned...' message."""
        meal_label = f" for {meal_type.lower()}" if meal_type else ""
        
        if dimension == BehavioralDimension.CUISINE_PREFERENCE:
            if observed_strength > 0:
                return f"Munchly learned that you tend to enjoy {entity_key} cuisine{meal_label}."
            else:
                return f"Munchly noticed you often skip {entity_key} cuisine{meal_label}."
        
        elif dimension == BehavioralDimension.MEAL_TYPE_PATTERN:
            return f"Munchly learned that you usually prefer {entity_key} meals{meal_label}."
        
        elif dimension == BehavioralDimension.INGREDIENT_PREFERENCE:
            if observed_strength > 0:
                return f"Munchly noticed you often choose meals with {entity_key}."
            else:
                return f"Munchly noticed you tend to avoid {entity_key}."
        
        elif dimension == BehavioralDimension.INGREDIENT_AVOIDANCE:
            return f"Munchly noticed you consistently skip meals containing {entity_key}."
        
        elif dimension == BehavioralDimension.COMPLEXITY_PREFERENCE:
            return f"Munchly learned that you prefer {entity_key} recipes{meal_label}."
        
        elif dimension == BehavioralDimension.PORTION_PREFERENCE:
            return f"Munchly noticed you tend to prefer {entity_key} portions{meal_label}."
        
        else:
            return f"Munchly noticed a pattern: {entity_key}{meal_label}."

    @classmethod
    def check_for_insights(
        cls,
        profiles: List[UserBehavioralProfile],
    ) -> List[InsightCandidate]:
        """Check behavioral profiles for patterns strong enough to surface.
        
        Only generates insights when:
        1. confidence >= INSIGHT_CONFIDENCE_THRESHOLD (0.5)
        2. |observed_strength| >= INSIGHT_STRENGTH_THRESHOLD (0.4)
        """
        candidates = []
        
        for profile in profiles:
            if (
                profile.confidence >= cls.INSIGHT_CONFIDENCE_THRESHOLD
                and abs(profile.observed_strength) >= cls.INSIGHT_STRENGTH_THRESHOLD
            ):
                message = cls.generate_insight_message(
                    dimension=profile.dimension,
                    meal_type=profile.meal_type,
                    entity_key=profile.entity_key,
                    observed_strength=profile.observed_strength,
                )
                candidates.append(InsightCandidate(
                    dimension=profile.dimension,
                    meal_type=profile.meal_type,
                    entity_key=profile.entity_key,
                    message=message,
                    observed_strength=profile.observed_strength,
                    confidence=profile.confidence,
                ))
        
        return candidates

    @staticmethod
    def reset_behavioral_profiles(
        profiles: List[UserBehavioralProfile],
    ) -> List[UserBehavioralProfile]:
        """Reset all behavioral profiles to zero.
        
        PRESERVES:
        - Explicit preferences (PreferenceTier.PREFERENCE/DISLIKE/AVOIDANCE)
        - Medical constraints (PreferenceTier.MEDICAL)
        - Allergy constraints (PreferenceTier.ALLERGY)
        
        CLEARS:
        - observed_strength -> 0.0
        - sample_count -> 0
        - confidence -> 0.0
        
        The profile rows are kept (not deleted) so the dimensions are preserved,
        but all learned values are zeroed out.
        """
        for profile in profiles:
            profile.observed_strength = 0.0
            profile.sample_count = 0
            profile.confidence = 0.0
            profile.last_updated = datetime.now(timezone.utc)
        return profiles
