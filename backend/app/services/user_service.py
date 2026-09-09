import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.profile import UserProfile

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()
    
    async def get_profile(self, user_id: uuid.UUID) -> Optional[UserProfile]:
        result = await self.db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        return result.scalar_one_or_none()
    
    async def update_profile(self, user_id: uuid.UUID, data: dict) -> UserProfile:
        profile = await self.get_profile(user_id)
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
        
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
