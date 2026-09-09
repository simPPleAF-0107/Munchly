import uuid
import httpx
from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.user import User
from app.models.profile import UserProfile
from app.services.user_service import UserService
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.config import settings

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
    
    async def register(self, email: str, password: str, name: str) -> Tuple[User, str, str]:
        """Register with email/password. Returns (user, access_token, refresh_token)."""
        existing_user = await self.user_service.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        hashed_password = hash_password(password)
        new_user = User(
            email=email,
            password_hash=hashed_password,
            auth_provider="email"
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        # Create profile with just the name
        profile = UserProfile(user_id=new_user.id, name=name)
        self.db.add(profile)
        
        # Generate tokens
        access_token, refresh_token = await self._generate_tokens(new_user)
        
        # Store hashed refresh token
        new_user.refresh_token_hash = hash_password(refresh_token)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        return new_user, access_token, refresh_token

    async def login(self, email: str, password: str) -> Tuple[User, str, str]:
        """Login with email/password. Returns (user, access_token, refresh_token)."""
        user = await self.user_service.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account was created with Google. Please use Google login."
            )
        
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        access_token, refresh_token = await self._generate_tokens(user)
        
        user.refresh_token_hash = hash_password(refresh_token)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user, access_token, refresh_token

    async def google_auth(self, id_token: str) -> Tuple[User, str, str]:
        """Authenticate with Google ID token. Find or create user. Handle account linking."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token}
            )
            
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google token"
            )
            
        payload = response.json()
        
        # Verify audience if client ID is configured
        if settings.GOOGLE_CLIENT_ID and payload.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google client ID"
            )
            
        email = payload.get("email")
        google_id = payload.get("sub")
        name = payload.get("name")
        
        if not email or not google_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incomplete token info"
            )
            
        user = await self.user_service.get_by_google_id(google_id)
        
        if not user:
            user = await self.user_service.get_by_email(email)
            if user:
                # Link account
                user.google_id = google_id
                user.auth_provider = "email+google"
            else:
                # Create new user
                user = User(
                    email=email,
                    auth_provider="google",
                    google_id=google_id
                )
                self.db.add(user)
                await self.db.commit()
                await self.db.refresh(user)
                
                profile = UserProfile(user_id=user.id, name=name)
                self.db.add(profile)
        
        access_token, refresh_token = await self._generate_tokens(user)
        
        user.refresh_token_hash = hash_password(refresh_token)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user, access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> Tuple[str, str]:
        """Exchange refresh token for new tokens."""
        try:
            payload = decode_token(refresh_token)
            user_id_str = payload.get("sub")
            token_type = payload.get("type")
            
            if not user_id_str or token_type != "refresh":
                raise ValueError("Invalid token")
                
            user_id = uuid.UUID(user_id_str)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
            
        user = await self.user_service.get_by_id(user_id)
        if not user or not user.refresh_token_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
            
        if not verify_password(refresh_token, user.refresh_token_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
            
        access_token, new_refresh_token = await self._generate_tokens(user)
        
        user.refresh_token_hash = hash_password(new_refresh_token)
        await self.db.commit()
        
        return access_token, new_refresh_token

    async def _generate_tokens(self, user: User) -> Tuple[str, str]:
        """Generate access + refresh token pair for a user."""
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "type": "refresh"}
        )
        return access_token, refresh_token
