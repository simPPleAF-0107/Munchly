import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.db.base import Base
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.enums import SubscriptionTier
import uuid

# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(SQLALCHEMY_TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    # We use ASGITransport with AsyncClient for FastAPI testing
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
        
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        password_hash="hashedpassword",
        subscription_tier=SubscriptionTier.FREE,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient, test_user: User):
    async def override_get_current_user():
        return test_user
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.clear()
