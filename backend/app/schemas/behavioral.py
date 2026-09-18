import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class BehavioralProfileResponse(BaseModel):
    id: uuid.UUID
    dimension: str
    meal_type: Optional[str] = None
    entity_key: str
    observed_strength: float
    sample_count: int
    confidence: float
    last_updated: datetime

    class Config:
        from_attributes = True


class InsightResponse(BaseModel):
    id: uuid.UUID
    dimension: str
    meal_type: Optional[str] = None
    entity_key: str
    message: str
    observed_strength: float
    confidence: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class InsightActionRequest(BaseModel):
    """Accept or dismiss an insight."""
    action: str  # "ACCEPT" | "DISMISS"


class ResetResponse(BaseModel):
    profiles_reset: int
    insights_dismissed: int
    message: str = "Behavioral profiles reset. Explicit preferences and safety constraints are preserved."
