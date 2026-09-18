import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RejectionRequest(BaseModel):
    """Structured meal rejection."""
    recipe_id: uuid.UUID
    meal_plan_meal_id: Optional[uuid.UUID] = None
    feedback_type: str = "REJECTION"  # FeedbackType value
    reason: Optional[str] = None
    ingredient_ids: Optional[List[str]] = None
    scope: str = "TODAY"  # FeedbackScope value: TODAY | FUTURE | PERMANENT
    notes: Optional[str] = Field(None, max_length=500)


class PositiveFeedbackRequest(BaseModel):
    """User liked a meal."""
    recipe_id: uuid.UUID
    meal_plan_meal_id: Optional[uuid.UUID] = None
    notes: Optional[str] = Field(None, max_length=500)


class FeedbackResponse(BaseModel):
    """Response after processing feedback."""
    feedback_id: str
    change_level: Optional[str] = None  # PlanChangeLevel value
    applied_tier: str
    affected_entities: List[Dict[str, str]] = []


class ConflictOption(BaseModel):
    label: str
    action: str


class ConflictResponse(BaseModel):
    conflict_type: str
    severity: str
    description: str
    constraint_a: str
    constraint_b: str
    options: List[ConflictOption]
    recommendation: Optional[str] = None


class ConflictReportResponse(BaseModel):
    has_conflicts: bool
    conflicts: List[ConflictResponse] = []
    warnings: List[str] = []


class PreferenceOverrideResponse(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    tier: str
    is_active: bool
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
