import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.feedback import (
    RejectionRequest, PositiveFeedbackRequest, FeedbackResponse,
    ConflictReportResponse, PreferenceOverrideResponse,
)
from app.services.feedback_service import FeedbackService
from app.services.conflict_resolver import ConflictResolver

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/reject", response_model=FeedbackResponse, status_code=200)
async def reject_meal(
    payload: RejectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a meal with structured feedback.
    
    Flow: reason -> ingredient(s) if applicable -> scope -> replacement.
    Only the affected meal slot is regenerated.
    """
    service = FeedbackService(db)
    result = await service.process_rejection(
        user_id=current_user.id,
        recipe_id=payload.recipe_id,
        meal_plan_meal_id=payload.meal_plan_meal_id,
        feedback_type=payload.feedback_type,
        reason=payload.reason,
        ingredient_ids=payload.ingredient_ids,
        scope=payload.scope,
        notes=payload.notes,
    )
    await db.commit()
    return FeedbackResponse(**result)


@router.post("/positive", response_model=FeedbackResponse, status_code=200)
async def positive_feedback(
    payload: PositiveFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record positive feedback for a meal."""
    service = FeedbackService(db)
    result = await service.process_positive_feedback(
        user_id=current_user.id,
        recipe_id=payload.recipe_id,
        meal_plan_meal_id=payload.meal_plan_meal_id,
        notes=payload.notes,
    )
    await db.commit()
    return FeedbackResponse(**result)


@router.get("/overrides", response_model=list[PreferenceOverrideResponse])
async def get_overrides(
    entity_type: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get active preference overrides."""
    service = FeedbackService(db)
    overrides = await service.get_active_overrides(
        user_id=current_user.id,
        entity_type=entity_type,
    )
    return [PreferenceOverrideResponse.model_validate(o) for o in overrides]


@router.delete("/overrides/{override_id}", status_code=200)
async def revoke_override(
    override_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke a preference override."""
    service = FeedbackService(db)
    success = await service.revoke_override(
        user_id=current_user.id,
        override_id=override_id,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Override not found")
    await db.commit()
    return {"status": "revoked"}


@router.post("/conflicts", response_model=ConflictReportResponse)
async def check_conflicts(
    diet_type: str = None,
    health_goal: str = None,
    weekly_budget: float = None,
    max_prep_time_min: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check for conflicts in user's requirement combination."""
    report = ConflictResolver.detect_conflicts(
        diet_type=diet_type,
        health_goal=health_goal,
        weekly_budget=weekly_budget,
        max_prep_time_min=max_prep_time_min,
    )
    return ConflictReportResponse(
        has_conflicts=report.has_conflicts,
        conflicts=[
            {
                "conflict_type": c.conflict_type.value,
                "severity": c.severity,
                "description": c.description,
                "constraint_a": c.constraint_a,
                "constraint_b": c.constraint_b,
                "options": c.options,
                "recommendation": c.recommendation,
            }
            for c in report.conflicts
        ],
        warnings=report.warnings,
    )
