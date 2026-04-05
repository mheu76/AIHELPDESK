# Contributing to IT AI Helpdesk

Thank you for considering contributing to IT AI Helpdesk! 🎉

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)

---

## Code of Conduct

This project follows a Code of Conduct that all contributors are expected to adhere to. Please be respectful and constructive in all interactions.

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating a bug report, please:

1. **Search existing issues** to see if the problem has already been reported
2. **Use the latest version** to ensure the bug hasn't been fixed
3. **Collect information** about your environment

**Good Bug Report Includes:**

```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
What you expected to happen

## Actual Behavior
What actually happened

## Environment
- OS: [e.g., Windows 11]
- Browser: [e.g., Chrome 120]
- Backend version: [e.g., 1.0.0]
- Frontend version: [e.g., 1.0.0]

## Screenshots
If applicable, add screenshots

## Additional Context
Any other relevant information
```

### 💡 Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear title** that describes the enhancement
- **Provide detailed description** of the proposed feature
- **Explain why this enhancement would be useful**
- **Include mockups or examples** if applicable

### 📝 Contributing Code

1. **Fork** the repository
2. **Create a branch** from `main`
3. **Make your changes**
4. **Write/update tests**
5. **Update documentation**
6. **Submit a pull request**

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Backend Setup

```bash
# Clone repository
git clone https://github.com/yourusername/AIhelpdesk.git
cd AIhelpdesk/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Docker Setup

```bash
# Start all services
docker compose up --build
```

---

## Coding Standards

### Backend (Python)

#### Style Guide

- Follow **PEP 8** style guide
- Use **type hints** for all function parameters and return values
- Maximum line length: **88 characters** (Black formatter default)
- Use **docstrings** for classes and public methods

#### Example

```python
from typing import List, Optional
from pydantic import BaseModel

async def get_user_by_email(
    session: AsyncSession,
    email: str,
    *,
    include_inactive: bool = False
) -> Optional[User]:
    """
    Retrieve a user by email address.
    
    Args:
        session: Database session
        email: User's email address
        include_inactive: Whether to include inactive users
        
    Returns:
        User object if found, None otherwise
    """
    # Implementation
    pass
```

#### Import Order

1. Standard library imports
2. Third-party library imports
3. Local application imports

```python
# Standard library
import os
from datetime import datetime
from typing import List, Optional

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Local
from app.models import User
from app.schemas import UserResponse
from app.core.dependencies import get_session
```

### Frontend (TypeScript)

#### Style Guide

- Use **TypeScript strict mode**
- Prefer **functional components** over class components
- Use **custom hooks** for reusable logic
- Follow **React best practices**

#### Example

```typescript
import { useState, useEffect } from 'react';

interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Effect logic
  }, []);

  return (
    <div className="chat-container">
      {/* Component JSX */}
    </div>
  );
}
```

#### Component Structure

```
Component.tsx
├── Imports
├── Type definitions
├── Component definition
├── Hooks
├── Event handlers
├── Render logic
└── Export
```

---

## Commit Guidelines

We follow **Conventional Commits** specification.

### Commit Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no code change)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **perf**: Performance improvements

### Scopes

- **backend**: Backend changes
- **frontend**: Frontend changes
- **api**: API changes
- **db**: Database changes
- **auth**: Authentication changes
- **chat**: Chat feature
- **ticket**: Ticket feature
- **kb**: Knowledge base feature
- **admin**: Admin feature
- **deploy**: Deployment changes

### Examples

```bash
# Good commits
feat(chat): add streaming response support
fix(auth): resolve JWT token expiration bug
docs(readme): update installation instructions
test(api): add integration tests for ticket endpoints
refactor(backend): extract LLM abstraction layer

# Bad commits
update stuff
fix bug
changes
WIP
```

---

## Pull Request Process

### Before Submitting

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Run all tests** and ensure they pass
4. **Check code style** (linting)
5. **Update CHANGELOG** if applicable

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran

## Checklist
- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)
Add screenshots to help explain your changes
```

### Review Process

1. **Automated checks** must pass (tests, linting)
2. At least **one maintainer review** required
3. **All comments** must be resolved
4. **Squash and merge** preferred for clean history

---

## Testing Guidelines

### Backend Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_api_auth.py

# Run with verbose output
pytest -v -s

# Run integration tests only
pytest -m integration
```

#### Test Structure

```python
import pytest
from fastapi.testclient import TestClient

def test_user_registration(client: TestClient):
    """Test user registration endpoint."""
    # Arrange
    payload = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    }
    
    # Act
    response = client.post("/api/v1/auth/register", json=payload)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == payload["email"]
    assert "password" not in data
```

### Frontend Testing

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build verification
npm run build
```

---

## Documentation

### When to Update Documentation

- Adding new features
- Changing API endpoints
- Modifying configuration options
- Changing deployment process
- Fixing bugs that affect user behavior

### Documentation Files

- **README.md**: Project overview and quick start
- **docs/**: Detailed documentation
- **CLAUDE.md**: Claude Code integration guide
- **API docs**: Auto-generated from code (Swagger)

---

## Project Structure

Before contributing, familiarize yourself with:

```
AIhelpdesk/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── docs/             # Documentation
├── scripts/          # Deployment scripts
└── tests/            # Test files
```

See [README.md](README.md) for detailed structure.

---

## Getting Help

- **Documentation**: Check [docs/](docs/) directory
- **Issues**: Search [existing issues](https://github.com/yourusername/AIhelpdesk/issues)
- **Discussions**: Join [GitHub Discussions](https://github.com/yourusername/AIhelpdesk/discussions)

---

## Recognition

Contributors will be recognized in:

- GitHub contributors page
- Release notes
- Project documentation (if significant contribution)

---

Thank you for contributing! 🚀

**Questions?** Feel free to ask in [GitHub Discussions](https://github.com/yourusername/AIhelpdesk/discussions).
