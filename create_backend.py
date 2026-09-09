import os
from pathlib import Path

base_dir = Path(r"d:\Projects\Munchly\backend")

files = {
    "pyproject.toml": """[tool.poetry]
name = "munchly-backend"
version = "0.1.0"
description = "Munchly backend"
authors = ["Author <author@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "*"
uvicorn = {extras = ["standard"], version = "*"}
sqlalchemy = {extras = ["asyncio"], version = ">=2.0"}
asyncpg = "*"
alembic = "*"
pydantic = ">=2.0"
pydantic-settings = "*"
python-jose = {extras = ["cryptography"], version = "*"}
passlib = {extras = ["bcrypt"], version = "*"}
httpx = "*"
google-generativeai = "*"
slowapi = "*"

[tool.poetry.group.dev.dependencies]
pytest = "*"
pytest-asyncio = "*"
httpx = "*"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""",

    "docker-compose.yml": """version: '3.8'

services:
  db:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_USER: munchly
      POSTGRES_PASSWORD: munchly_dev
      POSTGRES_DB: munchly
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
""",

    "app/__init__.py": "",
    "app/core/__init__.py": "",
    
    "app/core/config.py": """from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Munchly"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://munchly:munchly_dev@localhost:5432/munchly"
    JWT_SECRET: str = "supersecretkey_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GEMINI_API_KEY: str | None = None
    GOOGLE_CLIENT_ID: str | None = None
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    AI_PROVIDER: str = "gemini"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
""",

    "app/core/security.py": """from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
""",

    "app/core/dependencies.py": """from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from app.db.session import async_session_maker
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

# Minimal User model representation to pass the requirement
class User:
    id: str
    is_active: bool = True
    tier: str = "FREE"

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # In a real app, query db for User
    user = User()
    user.id = user_id
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
""",

    "app/core/rate_limiter.py": """from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])

RATE_LIMITS = {
    "meal_plan_generate": "5/hour",
    "meal_replace": "30/hour",
    "ai_chat": "30/hour",
    "auth_register": "5/hour",
    "auth_login": "10/hour",
    "default": "100/hour"
}
""",

    "app/core/scoring_config.py": """from dataclasses import dataclass, field
from typing import Dict

@dataclass
class ScoringWeights:
    weights: Dict[str, float] = field(default_factory=lambda: {
        "nutrition_fit": 0.20,
        "budget_efficiency": 0.15,
        "food_preference": 0.12,
        "cuisine_preference": 0.10,
        "regional_relevance": 0.08,
        "local_availability": 0.05,
        "ingredient_reuse": 0.05,
        "prep_time_fit": 0.05,
        "pantry_overlap": 0.05,
        "variety": 0.05,
        "medical_fit": 0.05,
        "protein_source_rotation": 0.05,
    })

DEFAULT_SCORING_WEIGHTS = ScoringWeights().weights
""",

    "app/core/feature_gate.py": """from typing import Dict, Any, Optional
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
        
        # If limit is None, it means unlimited
        if limit is None:
            return True
            
        # Here we would normally check the current usage against the limit
        # This acts as the dependency gate
        current_usage = 0 # Placeholder for actual usage check
        if current_usage >= limit:
            raise HTTPException(status_code=403, detail=f"Feature limit exceeded for {feature}. Upgrade to access more.")
        return True
    return _check_feature_limit
""",

    "app/core/tier_limits.py": """from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.feature_gate import TIER_LIMITS
from app.core.dependencies import User

class TierLimitTracker:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_usage(self, user_id: str, feature: str) -> int:
        # Placeholder for DB query to get current usage
        return 0

    async def increment_usage(self, user_id: str, feature: str, amount: int = 1) -> None:
        # Placeholder for DB query to increment usage
        pass
        
    async def can_use_feature(self, user: User, feature: str) -> bool:
        tier = getattr(user, "tier", "FREE")
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["FREE"])
        limit = limits.get(feature)
        
        if limit is None:
            return True
            
        current_usage = await self.get_usage(user.id, feature)
        return current_usage < limit
""",

    "app/db/__init__.py": "",
    
    "app/db/base.py": """import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

class Base(DeclarativeBase):
    pass

class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
""",

    "app/db/session.py": """from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
""",

    "app/main.py": """from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.core.config import settings
from app.core.rate_limiter import limiter
from app.api.v1.router import api_router
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    yield
    # Shutdown actions
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    debug=settings.DEBUG
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
""",

    "app/api/__init__.py": "",
    "app/api/v1/__init__.py": "",
    
    "app/api/v1/router.py": """from fastapi import APIRouter

api_router = APIRouter()
# Endpoint routers will be added here as they are built
""",

    "app/api/v1/endpoints/__init__.py": "",
    "app/models/__init__.py": "",
    "app/schemas/__init__.py": "",
    "app/services/__init__.py": "",
    "app/services/ai/__init__.py": "",
    "app/data/.gitkeep": "",
    
    "alembic.ini": """# A generic, single database configuration.
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[post_write_hooks]
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""",

    "alembic/env.py": """import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.db.base import Base
from app.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""",

    "alembic/script.py.mako": '\"\"\"${message}\n\nRevision ID: ${up_revision}\nRevises: ${down_revision | comma,n}\nCreate Date: ${create_date}\n\n\"\"\"\nfrom typing import Sequence, Union\n\nfrom alembic import op\nimport sqlalchemy as sa\n${imports if imports else ""}\n\n# revision identifiers, used by Alembic.\nrevision: str = ${repr(up_revision)}\ndown_revision: Union[str, None] = ${repr(down_revision)}\nbranch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}\ndepends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}\n\n\ndef upgrade() -> None:\n    ${upgrades if upgrades else "pass"}\n\n\ndef downgrade() -> None:\n    ${downgrades if downgrades else "pass"}\n',

    ".env.example": """DATABASE_URL=postgresql+asyncpg://munchly:munchly_dev@localhost:5432/munchly
JWT_SECRET=supersecretkey_change_me_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
GEMINI_API_KEY=
GOOGLE_CLIENT_ID=
CORS_ORIGINS=["http://localhost:3000"]
AI_PROVIDER=gemini
APP_NAME=Munchly
DEBUG=True
"""
}

for filepath, content in files.items():
    full_path = base_dir / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Scaffolding completed successfully.")
