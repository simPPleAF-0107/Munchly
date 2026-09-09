from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.feature_gate import TIER_LIMITS
from app.core.dependencies import User

class TierLimitTracker:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_usage(self, user_id: str, feature: str) -> int:
        return 0

    async def increment_usage(self, user_id: str, feature: str, amount: int = 1) -> None:
        pass
        
    async def can_use_feature(self, user: User, feature: str) -> bool:
        tier = getattr(user, "tier", "FREE")
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["FREE"])
        limit = limits.get(feature)
        
        if limit is None:
            return True
            
        current_usage = await self.get_usage(user.id, feature)
        return current_usage < limit
