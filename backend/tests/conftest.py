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


# ============================================================
# MOCK LLM PROVIDER
# ============================================================

from app.core.llm.base import LLMBase
from typing import Dict, Any, List, Optional, AsyncIterator


class MockLLM(LLMBase):
    """Mock LLM provider for testing"""
    
    def __init__(self, api_key: str = "mock-key", model: Optional[str] = None):
        super().__init__(api_key, model)
        self.call_count = 0
        self.last_messages = None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Return a mock response"""
        self.call_count += 1
        self.last_messages = messages
        
        return {
            "content": "This is a mock response from the AI assistant. How can I help you reset your password?",
            "role": "assistant",
            "usage": {
                "input_tokens": 50,
                "output_tokens": 20
            }
        }
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Return a mock streaming response"""
        self.call_count += 1
        chunks = [
            "This ", "is ", "a ", "mock ", "streaming ",
            "response ", "from ", "the ", "AI ", "assistant."
        ]
        for chunk in chunks:
            yield chunk
    
    async def embed_text(self, text: str, **kwargs) -> List[float]:
        """Return a mock embedding vector"""
        # Return a consistent embedding for testing
        return [0.1] * 384
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text (simplified)"""
        return len(text.split())


@pytest.fixture
def mock_llm() -> MockLLM:
    """Provide a mock LLM for testing"""
    return MockLLM()


# ============================================================
# CHAT SESSION FIXTURES
# ============================================================

from app.models.chat import ChatSession, ChatMessage, MessageRole


@pytest.fixture
async def test_chat_session(test_db: AsyncSession, test_user: User) -> ChatSession:
    """Create a test chat session"""
    session = ChatSession(
        user_id=test_user.id,
        title="Test Password Reset"
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    return session


@pytest.fixture
async def test_chat_message(test_db: AsyncSession, test_chat_session: ChatSession) -> ChatMessage:
    """Create a test chat message"""
    message = ChatMessage(
        session_id=test_chat_session.id,
        role=MessageRole.USER,
        content="How do I reset my password?"
    )
    test_db.add(message)
    await test_db.commit()
    await test_db.refresh(message)
    return message


# ============================================================
# KB DOCUMENT FIXTURES
# ============================================================

from app.models.kb_document import KBDocument


@pytest.fixture
async def test_kb_document(test_db: AsyncSession, admin_user: User) -> KBDocument:
    """Create a test KB document"""
    doc = KBDocument(
        title="Password Reset Guide",
        file_name="password_reset.txt",
        file_type="txt",
        content="""
        How to Reset Your Password
        
        If you have forgotten your password, follow these steps:
        1. Go to the login page
        2. Click on "Forgot Password"
        3. Enter your email address
        4. Click the reset link in your email
        5. Enter your new password
        6. Login with your new password
        """,
        created_by_id=admin_user.id
    )
    test_db.add(doc)
    await test_db.commit()
    await test_db.refresh(doc)
    return doc
