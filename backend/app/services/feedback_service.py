import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import UserFeedback, UserPreferenceOverride
from app.models.enums import (
    FeedbackType, FeedbackScope, PreferenceTier, EventType,
    PlanChangeLevel,
)
from app.services.event_service import EventService


class FeedbackService:
    """Processes structured feedback and applies appropriate preference changes.
    
    Architecture:
    1. Record feedback + emit immutable event
    2. Map scope to preference tier:
       - TODAY -> daily exclusion (expires end of day)
       - FUTURE -> DISLIKE tier (persistent penalty in scoring)
       - PERMANENT -> AVOIDANCE tier (persistent, reversible penalty)
    3. Determine minimum Plan Stability change (MEAL_REPLACED, not FULL_REGENERATION)
    4. Return change level so caller can regenerate ONLY the affected meal
    
    Critical safety rule:
    - Feedback NEVER creates MEDICAL or ALLERGY overrides
    - Only explicit user onboarding/settings can set those tiers
    - Behavioral learning (Phase 5) can NEVER escalate to safety tiers
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # Scope -> Preference tier mapping
    SCOPE_TO_TIER = {
        FeedbackScope.TODAY: PreferenceTier.DISLIKE,      # Temporary exclusion
        FeedbackScope.FUTURE: PreferenceTier.DISLIKE,     # Persistent penalty
        FeedbackScope.PERMANENT: PreferenceTier.AVOIDANCE, # Strong persistent penalty
    }

    async def process_rejection(
        self,
        user_id: uuid.UUID,
        recipe_id: uuid.UUID,
        meal_plan_meal_id: Optional[uuid.UUID] = None,
        feedback_type: str = "REJECTION",
        reason: Optional[str] = None,
        ingredient_ids: Optional[List[str]] = None,
        scope: str = "TODAY",
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a meal rejection.
        
        Steps:
        1. Record feedback + emit event
        2. Apply scope (PERMANENT->AVOIDANCE, FUTURE->DISLIKE, TODAY->daily exclusion)
        3. Determine change level (MEAL_REPLACED, not FULL_REGENERATION)
        4. Create preference overrides for affected entities
        
        Returns:
            Dict with feedback_id, change_level, applied_tier, affected_entities
        """
        scope_enum = FeedbackScope(scope)
        type_enum = FeedbackType(feedback_type)
        tier = self.SCOPE_TO_TIER[scope_enum]
        
        # 1. Record feedback
        feedback = UserFeedback(
            user_id=user_id,
            recipe_id=recipe_id,
            meal_plan_meal_id=meal_plan_meal_id,
            feedback_type=type_enum,
            scope=scope_enum,
            reason=reason,
            ingredient_ids=ingredient_ids,
            notes=notes,
            applied_tier=tier,
        )
        self.db.add(feedback)
        await self.db.flush()
        
        # 2. Emit event
        await EventService.emit(
            db=self.db,
            user_id=user_id,
            event_type=EventType.FEEDBACK_SUBMITTED,
            entity_type="recipe",
            entity_id=recipe_id,
            metadata={
                "feedback_type": feedback_type,
                "scope": scope,
                "reason": reason,
                "ingredient_ids": ingredient_ids,
                "applied_tier": tier.value,
            },
        )
        
        # 3. Create preference overrides
        affected_entities = []
        
        # Recipe-level override
        expires = self._calculate_expiry(scope_enum)
        await self._create_override(
            user_id=user_id,
            entity_type="recipe",
            entity_id=recipe_id,
            tier=tier,
            feedback_id=feedback.id,
            expires_at=expires,
        )
        affected_entities.append({"type": "recipe", "id": str(recipe_id)})
        
        # Ingredient-level overrides (affects multiple recipes)
        if ingredient_ids and type_enum == FeedbackType.INGREDIENT_REJECTION:
            for ing_id_str in ingredient_ids:
                try:
                    ing_id = uuid.UUID(ing_id_str)
                except ValueError:
                    continue
                
                await self._create_override(
                    user_id=user_id,
                    entity_type="ingredient",
                    entity_id=ing_id,
                    tier=tier,
                    feedback_id=feedback.id,
                    expires_at=expires,
                )
                affected_entities.append({"type": "ingredient", "id": ing_id_str})
                
                # Emit ingredient rejection event
                await EventService.emit(
                    db=self.db,
                    user_id=user_id,
                    event_type=EventType.INGREDIENT_REJECTED,
                    entity_type="ingredient",
                    entity_id=ing_id,
                    metadata={"scope": scope, "reason": reason},
                )
        
        # 4. Determine change level
        change_level = PlanChangeLevel.MEAL_REPLACED
        
        await self.db.flush()
        
        return {
            "feedback_id": str(feedback.id),
            "change_level": change_level.value,
            "applied_tier": tier.value,
            "affected_entities": affected_entities,
        }

    async def process_positive_feedback(
        self,
        user_id: uuid.UUID,
        recipe_id: uuid.UUID,
        meal_plan_meal_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record positive feedback (user liked the meal)."""
        feedback = UserFeedback(
            user_id=user_id,
            recipe_id=recipe_id,
            meal_plan_meal_id=meal_plan_meal_id,
            feedback_type=FeedbackType.POSITIVE,
            scope=FeedbackScope.FUTURE,
            notes=notes,
            applied_tier=PreferenceTier.PREFERENCE,
        )
        self.db.add(feedback)
        await self.db.flush()
        
        # Emit event
        await EventService.emit(
            db=self.db,
            user_id=user_id,
            event_type=EventType.FEEDBACK_SUBMITTED,
            entity_type="recipe",
            entity_id=recipe_id,
            metadata={"feedback_type": "POSITIVE"},
        )
        
        # Create/update PREFERENCE override
        await self._create_override(
            user_id=user_id,
            entity_type="recipe",
            entity_id=recipe_id,
            tier=PreferenceTier.PREFERENCE,
            feedback_id=feedback.id,
        )
        
        return {
            "feedback_id": str(feedback.id),
            "applied_tier": PreferenceTier.PREFERENCE.value,
        }

    async def get_active_overrides(
        self,
        user_id: uuid.UUID,
        entity_type: Optional[str] = None,
        tier: Optional[PreferenceTier] = None,
    ) -> List[UserPreferenceOverride]:
        """Get active preference overrides for a user.
        
        Used by RecommendationService (PREFERENCE/DISLIKE/AVOIDANCE)
        and ConstraintService (MEDICAL/ALLERGY).
        """
        stmt = select(UserPreferenceOverride).where(
            UserPreferenceOverride.user_id == user_id,
            UserPreferenceOverride.is_active == True,
        )
        if entity_type:
            stmt = stmt.where(UserPreferenceOverride.entity_type == entity_type)
        if tier:
            stmt = stmt.where(UserPreferenceOverride.tier == tier)
        
        # Filter expired
        now = datetime.now(timezone.utc)
        stmt = stmt.where(
            (UserPreferenceOverride.expires_at == None) |
            (UserPreferenceOverride.expires_at > now)
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def revoke_override(
        self,
        user_id: uuid.UUID,
        override_id: uuid.UUID,
    ) -> bool:
        """Revoke (deactivate) a preference override. Used for user reset.
        
        MEDICAL and ALLERGY overrides can only be revoked through
        explicit user action (settings/onboarding), never through
        behavioral inference.
        """
        stmt = (
            update(UserPreferenceOverride)
            .where(
                UserPreferenceOverride.id == override_id,
                UserPreferenceOverride.user_id == user_id,
            )
            .values(is_active=False)
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def _create_override(
        self,
        user_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        tier: PreferenceTier,
        feedback_id: Optional[uuid.UUID] = None,
        expires_at: Optional[datetime] = None,
    ) -> UserPreferenceOverride:
        """Create or update a preference override.
        
        Critical: This method REFUSES to create MEDICAL or ALLERGY overrides
        from feedback. Those can only come from onboarding/settings.
        """
        if tier in (PreferenceTier.MEDICAL, PreferenceTier.ALLERGY):
            raise ValueError(
                f"Cannot create {tier.value} override from feedback. "
                "Safety-tier overrides can only be set through onboarding or settings."
            )
        
        # Check for existing active override
        stmt = select(UserPreferenceOverride).where(
            UserPreferenceOverride.user_id == user_id,
            UserPreferenceOverride.entity_type == entity_type,
            UserPreferenceOverride.entity_id == entity_id,
            UserPreferenceOverride.is_active == True,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Escalate tier if stronger feedback received
            # But NEVER escalate to MEDICAL/ALLERGY
            tier_order = {
                PreferenceTier.PREFERENCE: 0,
                PreferenceTier.DISLIKE: 1,
                PreferenceTier.AVOIDANCE: 2,
            }
            if tier_order.get(tier, 0) > tier_order.get(existing.tier, 0):
                existing.tier = tier
                existing.source_feedback_id = feedback_id
                existing.expires_at = expires_at
            return existing
        
        override = UserPreferenceOverride(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            tier=tier,
            source_feedback_id=feedback_id,
            expires_at=expires_at,
        )
        self.db.add(override)
        await self.db.flush()
        return override

    @staticmethod
    def _calculate_expiry(scope: FeedbackScope) -> Optional[datetime]:
        """Calculate expiry time for a feedback scope."""
        if scope == FeedbackScope.TODAY:
            # Expires at end of today (midnight UTC)
            today = date.today()
            tomorrow = today + timedelta(days=1)
            return datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=timezone.utc)
        # FUTURE and PERMANENT don't expire
        return None
