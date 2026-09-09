from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends
from app.core.dependencies import get_current_active_user, User

TIER_LIMITS: Dict[str, Dict[str, Optional[int]]] = {
    "FREE": {
        "meal_replacements_per_day": 3,
        "plan_regenerations_per_week": 1,
        "ai_messages_per_day": 5,
    },
    "PLUS": {
        "meal_replacements_per_day": None,
        "plan_regenerations_per_week": None,
        "ai_messages_per_day": None,
    },
}

def check_feature_limit(feature: str):
    async def _check_feature_limit(user: User = Depends(get_current_active_user)):
        tier = getattr(user, "tier", "FREE")
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["FREE"])
        limit = limits.get(feature)
        
        if limit is None:
            return True
            
        current_usage = 0 # Placeholder for actual usage check
        if current_usage >= limit:
            raise HTTPException(status_code=403, detail=f"Feature limit exceeded for {feature}. Upgrade to access more.")
        return True
    return _check_feature_limit
