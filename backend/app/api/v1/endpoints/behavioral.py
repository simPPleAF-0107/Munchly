import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.behavioral_profile import UserBehavioralProfile, UserBehavioralInsight
from app.models.enums import InsightStatus
from app.schemas.behavioral import (
    BehavioralProfileResponse, InsightResponse,
    InsightActionRequest, ResetResponse,
)
from app.services.behavioral_service import BehavioralService

router = APIRouter(prefix="/behavioral", tags=["behavioral"])


@router.get("/profiles", response_model=list[BehavioralProfileResponse])
async def get_profiles(
    meal_type: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's behavioral profiles."""
    stmt = select(UserBehavioralProfile).where(
        UserBehavioralProfile.user_id == current_user.id,
    )
    if meal_type:
        stmt = stmt.where(UserBehavioralProfile.meal_type == meal_type)
    result = await db.execute(stmt)
    return [BehavioralProfileResponse.model_validate(p) for p in result.scalars().all()]


@router.get("/insights", response_model=list[InsightResponse])
async def get_insights(
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get behavioral insights ('Munchly Learned...')."""
    stmt = select(UserBehavioralInsight).where(
        UserBehavioralInsight.user_id == current_user.id,
    )
    if status:
        stmt = stmt.where(UserBehavioralInsight.status == InsightStatus(status))
    result = await db.execute(stmt)
    return [InsightResponse.model_validate(i) for i in result.scalars().all()]


@router.post("/insights/{insight_id}/action", response_model=InsightResponse)
async def action_insight(
    insight_id: uuid.UUID,
    payload: InsightActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept or dismiss a behavioral insight."""
    stmt = select(UserBehavioralInsight).where(
        UserBehavioralInsight.id == insight_id,
        UserBehavioralInsight.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    if payload.action == "ACCEPT":
        insight.status = InsightStatus.ACCEPTED
    elif payload.action == "DISMISS":
        insight.status = InsightStatus.DISMISSED
    else:
        raise HTTPException(status_code=400, detail="Action must be ACCEPT or DISMISS")
    
    await db.commit()
    return InsightResponse.model_validate(insight)


@router.post("/reset", response_model=ResetResponse)
async def reset_behavioral(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reset all behavioral profiles.
    
    PRESERVES: explicit preferences, medical constraints, allergy constraints.
    CLEARS: all behavioral learning (observed_strength, sample_count, confidence).
    """
    # Reset profiles
    stmt = select(UserBehavioralProfile).where(
        UserBehavioralProfile.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    profiles = list(result.scalars().all())
    BehavioralService.reset_behavioral_profiles(profiles)
    
    # Dismiss all pending/shown insights
    dismiss_stmt = (
        update(UserBehavioralInsight)
        .where(
            UserBehavioralInsight.user_id == current_user.id,
            UserBehavioralInsight.status.in_([
                InsightStatus.PENDING, InsightStatus.SHOWN,
            ]),
        )
        .values(status=InsightStatus.DISMISSED)
    )
    dismiss_result = await db.execute(dismiss_stmt)
    
    await db.commit()
    
    return ResetResponse(
        profiles_reset=len(profiles),
        insights_dismissed=dismiss_result.rowcount,
    )
