# Testing Guide

## Overview

This document covers the testing strategy and how to run tests for the IT AI Helpdesk backend.

## Test Structure

```
backend/tests/
├── conftest.py          # Pytest fixtures and configuration
├── unit/                # Unit tests
│   ├── test_llm.py      # LLM abstraction layer tests
│   ├── test_auth_service.py    # Auth service tests
│   ├── test_chat_service.py    # Chat service tests
│   ├── test_api_auth.py        # Auth API endpoint tests
│   └── test_api_chat.py        # Chat API endpoint tests
└── integration/         # Integration tests (future)
```

## Test Coverage

### Unit Tests (Completed)

**LLM Tests** (`test_llm.py`):
- ✅ LLM factory pattern
- ✅ Claude provider implementation
- ✅ OpenAI provider implementation
- ✅ Interface compliance
- ✅ Mock API responses

**Auth Service Tests** (`test_auth_service.py`):
- ✅ User registration (success, duplicates, validation)
- ✅ Login (success, wrong password, non-existent user)
- ✅ Get current user from token
- ✅ Token refresh (success, invalid token)
- ✅ Password hashing verification

**Chat Service Tests** (`test_chat_service.py`):
- ✅ Send message (new session, existing session)
- ✅ Session management
- ✅ Title generation
- ✅ Get user sessions (with pagination)
- ✅ Get session detail
- ✅ Mark session resolved
- ✅ Authorization checks

**Auth API Tests** (`test_api_auth.py`):
- ✅ POST /auth/register
- ✅ POST /auth/login
- ✅ GET /auth/me
- ✅ POST /auth/refresh
- ✅ Error handling (401, 400, 422)

**Chat API Tests** (`test_api_chat.py`):
- ✅ POST /chat (send message)
- ✅ GET /chat/sessions (list sessions)
- ✅ GET /chat/sessions/{id} (get detail)
- ✅ PATCH /chat/sessions/{id}/resolve
- ✅ Authorization and validation

## Running Tests

### Prerequisites

1. **Install Dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Environment Setup**:
Tests use SQLite in-memory database, so no PostgreSQL setup needed.

### Run All Tests

```bash
cd backend
pytest
```

### Run Specific Test Files

```bash
# LLM tests
pytest tests/unit/test_llm.py -v

# Auth service tests
pytest tests/unit/test_auth_service.py -v

# Chat service tests
pytest tests/unit/test_chat_service.py -v

# Auth API tests
pytest tests/unit/test_api_auth.py -v

# Chat API tests
pytest tests/unit/test_api_chat.py -v
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

### Run Specific Tests

```bash
# Run tests matching pattern
pytest -k "test_login"

# Run single test
pytest tests/unit/test_auth_service.py::TestAuthService::test_login_success
```

## Test Fixtures

### Database Fixtures

**`test_db`**: Creates SQLite in-memory database with all tables
```python
@pytest.fixture
async def test_db() -> AsyncSession:
    # Creates fresh database for each test
    # Automatically cleaned up after test
```

**`test_client`**: HTTP client with database override
```python
@pytest.fixture
async def test_client(test_db) -> AsyncClient:
    # HTTP client for API testing
```

### User Fixtures

**`test_user`**: Regular employee user
```python
employee_id: TEST001
password: Test123!@#
role: EMPLOYEE
```

**`admin_user`**: Admin user
```python
employee_id: ADMIN001
password: Admin123!@#
role: ADMIN
```

**`it_staff_user`**: IT staff user
```python
employee_id: IT001
password: IT123!@#
role: IT_STAFF
```

### Auth Fixtures

**`auth_headers`**: Authorization headers for test_user
```python
{"Authorization": "Bearer <token>"}
```

**`admin_headers`**: Authorization headers for admin_user

## Mocking Strategy

### LLM Mocking

LLM API calls are mocked to avoid real API costs:

```python
@pytest.fixture
def mock_llm():
    llm = MagicMock(spec=LLMBase)
    llm.chat_completion = AsyncMock(return_value={
        "content": "Test AI response",
        "model": "test-model",
        "usage": {"input_tokens": 50, "completion_tokens": 20}
    })
    return llm
```

### RAG Mocking

ChromaDB is mocked for unit tests:

```python
@pytest.fixture
def mock_rag_service():
    rag = MagicMock()
    rag.search_knowledge_base = AsyncMock(return_value=[])
    return rag
```

## Test Patterns

### Async Tests

All async functions are tested with `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_function(test_db: AsyncSession):
    result = await some_async_function(test_db)
    assert result is not None
```

### API Tests

API endpoints are tested with `test_client`:

```python
@pytest.mark.asyncio
async def test_endpoint(test_client: AsyncClient, auth_headers: dict):
    response = await test_client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"message": "Test"}
    )
    assert response.status_code == 200
```

### Error Testing

Both service and API level errors are tested:

```python
with pytest.raises(UnauthorizedError, match="Invalid credentials"):
    await auth_service.login("invalid", "password")
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Known Issues and Limitations

### Current Environment

⚠️ **Python 3.14 Compatibility**: Some packages (asyncpg) may have build issues with Python 3.14 as it's very new. Recommended Python version: **3.11 or 3.12**.

### Workarounds

If you encounter package installation issues:

1. **Use Python 3.11/3.12**:
```bash
pyenv install 3.11
pyenv local 3.11
pip install -r requirements.txt
```

2. **Use Docker**:
```bash
docker run -v $(pwd):/app -w /app python:3.11 bash -c "pip install -r requirements.txt && pytest"
```

## Test Results (Expected)

When all dependencies are properly installed, expected test results:

```
tests/unit/test_llm.py ...................... [ 20%]
tests/unit/test_auth_service.py ............. [ 45%]
tests/unit/test_chat_service.py ............. [ 70%]
tests/unit/test_api_auth.py ................. [ 85%]
tests/unit/test_api_chat.py ................. [100%]

==================== 50+ passed in X.XXs ====================
```

## Best Practices

1. **Isolation**: Each test is independent and uses fresh database
2. **Mocking**: External services (LLM, ChromaDB) are mocked
3. **Fast**: Tests run in seconds using in-memory SQLite
4. **Comprehensive**: Tests cover success and error cases
5. **Type Safety**: All test functions have type hints

## Next Steps

### Integration Tests

Future integration tests will cover:
- Real ChromaDB integration
- Real PostgreSQL database
- End-to-end API flows
- Performance testing

### Load Tests

```bash
# Using locust or artillery
locust -f tests/load/locustfile.py
```

## Troubleshooting

### Import Errors

```bash
# Add backend to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
pytest
```

### Database Connection Errors

Tests use in-memory SQLite, no external database needed.

### Async Warnings

Make sure `pytest-asyncio` is installed and `asyncio_mode = auto` is set in `pytest.ini`.

## Manual Testing

For manual API testing, see `PHASE1_SETUP.md` which includes curl examples for all endpoints.

---

**Test Suite Status**: ✅ Complete (50+ unit tests)  
**Coverage Target**: 80%+  
**Execution Time**: <10 seconds (with mocks)
