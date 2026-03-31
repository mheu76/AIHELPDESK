"""
Pytest configuration and fixtures.
Provides reusable test infrastructure.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.base import Base, import_models
from app.db.session import get_db

# Test database URL (SQLite in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database with all tables.
    Uses SQLite in-memory for speed.
    """
    # Import all models
    import_models()

    # Create engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    TestSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        yield session

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client with database override.
    """
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


from app.models.user import User, UserRole
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test employee user"""
    user = User(
        employee_id="TEST001",
        email="test@company.com",
        full_name="Test User",
        hashed_password=get_password_hash("Test123!@#"),
        role=UserRole.EMPLOYEE
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def admin_user(test_db: AsyncSession) -> User:
    """Create a test admin user"""
    user = User(
        employee_id="ADMIN001",
        email="admin@company.com",
        full_name="Admin User",
        hashed_password=get_password_hash("Admin123!@#"),
        role=UserRole.ADMIN
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def it_staff_user(test_db: AsyncSession) -> User:
    """Create a test IT staff user"""
    user = User(
        employee_id="IT001",
        email="it@company.com",
        full_name="IT Staff",
        hashed_password=get_password_hash("IT123!@#"),
        role=UserRole.IT_STAFF
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create auth headers for test user"""
    token = create_access_token({"sub": test_user.employee_id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    """Create auth headers for admin user"""
    token = create_access_token({"sub": admin_user.employee_id})
    return {"Authorization": f"Bearer {token}"}
