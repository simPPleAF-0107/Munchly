from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.core.rate_limiter import limiter
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    GoogleAuthRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register(request: Request, payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user with email and password."""
    auth_service = AuthService(db)
    _, access_token, refresh_token = await auth_service.register(
        email=payload.email,
        password=payload.password,
        name=payload.name
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/hour")
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    auth_service = AuthService(db)
    _, access_token, refresh_token = await auth_service.login(
        email=payload.email,
        password=payload.password
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with Google ID token. Creates account if needed, links if same email."""
    auth_service = AuthService(db)
    _, access_token, refresh_token = await auth_service.google_auth(
        id_token=request.id_token
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange refresh token for new token pair."""
    auth_service = AuthService(db)
    access_token, refresh_token = await auth_service.refresh_tokens(
        refresh_token=request.refresh_token
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user."""
    return current_user
