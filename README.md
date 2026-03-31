# IT AI Helpdesk System

An intelligent IT helpdesk system that uses AI to handle employee IT inquiries, with automatic ticket escalation for unresolved issues.

## 🏗️ Project Status

**Current Phase:** Harness Implementation ✅ Complete

The core infrastructure (harness) for both backend and frontend is now fully implemented, providing:

- ✅ Configuration management with type-safe settings
- ✅ Human-readable logging with request context tracking
- ✅ Comprehensive error handling with custom exceptions
- ✅ Database session management (async SQLAlchemy)
- ✅ Request ID tracking throughout request lifecycle
- ✅ Middleware stack (CORS, error context, request ID)
- ✅ Test infrastructure with pytest fixtures
- ✅ API client with automatic auth token injection
- ✅ Frontend error boundary for React errors

## 📁 Project Structure

```
it-helpdesk/
├── CLAUDE.md              # Project instructions for Claude Code
├── docs/                  # Documentation (placeholder, actual docs at root)
│   ├── 01_architecture.md # System architecture
│   ├── 02_features.md     # Feature specifications
│   ├── 03_db_schema.md    # Database schema
│   ├── 04_api_spec.md     # API specification
│   └── 05_ui_spec.md      # UI design
├── backend/               # FastAPI backend ✅ Harness Complete
│   ├── app/
│   │   ├── core/         # Core infrastructure (config, logging, errors)
│   │   ├── middleware/   # Request middleware
│   │   ├── db/           # Database session management
│   │   ├── api/v1/       # API endpoints (to be added)
│   │   └── main.py       # Application entry point
│   ├── tests/            # Test suite with fixtures
│   ├── requirements.txt
│   └── README.md
├── frontend/              # Next.js 14 frontend ✅ Harness Complete
│   ├── lib/              # Core utilities (API client, auth helpers)
│   ├── components/       # React components
│   ├── app/              # App Router pages (to be added)
│   ├── package.json
│   └── README.md
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Anthropic API Key (for Claude)

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set:
#   - ANTHROPIC_API_KEY
#   - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
#   - DATABASE_URL

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Backend will be available at http://localhost:8080

- API Docs: http://localhost:8080/docs
- Health Check: http://localhost:8080/health

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1" > .env.local

# Run development server
npm run dev
```

Frontend will be available at http://localhost:3000

### 3. Run Tests

```bash
cd backend
pytest
```

## 🏛️ Architecture

### System Components

```
┌─────────────────────────────────────────────┐
│              사내 네트워크                    │
│                                              │
│  [임직원 브라우저]                            │
│       │ HTTPS                                │
│       ▼                                      │
│  ┌─────────────┐                            │
│  │  Next.js    │  Frontend (Port 3000)      │
│  │  Web App    │  ✅ Harness Ready          │
│  └──────┬──────┘                            │
│         │ REST API (HTTPS)                   │
│         ▼                                    │
│  ┌─────────────┐     ┌──────────────┐       │
│  │  FastAPI    │────▶│  ChromaDB    │       │
│  │  Backend    │     │  (Port 8000) │       │
│  │  (Port 8080)│     └──────────────┘       │
│  │ ✅ Harness  │     ┌──────────────┐       │
│  │    Ready    │────▶│  PostgreSQL  │       │
│  └──────┬──────┘     │  (Port 5432) │       │
│         │            └──────────────┘       │
│         │ HTTPS (외부)                       │
│         ▼                                    │
│  ┌─────────────┐                            │
│  │  Claude API │                            │
│  └─────────────┘                            │
└─────────────────────────────────────────────┘
```

### Harness Layer

The harness provides foundational infrastructure that all application code builds upon:

**Backend Harness:**
- Configuration management (Pydantic Settings)
- Logging system with context injection
- Error handling framework
- Database session management
- Middleware stack (Request ID, Error context, CORS)
- Test infrastructure

**Frontend Harness:**
- API client with automatic auth
- Error handling (APIError class)
- Auth helpers (token management)
- Error boundary (React errors)
- TypeScript type safety

## 🛠️ Technology Stack

| Component | Technology | Version | Status |
|-----------|------------|---------|--------|
| Frontend | Next.js (App Router) | 14.1+ | ✅ Harness Ready |
| Backend | Python FastAPI | 0.110+ | ✅ Harness Ready |
| LLM | Claude API | Latest | Abstraction Layer Pending |
| Vector DB | ChromaDB | 0.4+ | Pending |
| RDBMS | PostgreSQL | 15+ | Pending |
| ORM | SQLAlchemy (async) | 2.0+ | ✅ Session Manager Ready |
| Auth | JWT | - | Pending |

## 📝 Development Roadmap

### ✅ Phase 0: Harness Implementation (Complete)
- [x] Backend core infrastructure
- [x] Frontend core utilities
- [x] Test infrastructure
- [x] Configuration management
- [x] Logging and error handling
- [x] Documentation

### 🔄 Phase 1: Sprint 1 - Basic Features (Next)
- [ ] User model and authentication
- [ ] JWT security module
- [ ] Login endpoint
- [ ] AI chat basic implementation
- [ ] Chat session management
- [ ] Frontend login page
- [ ] Frontend chat interface

### ⏳ Phase 2: Sprint 2 - RAG System
- [ ] ChromaDB integration
- [ ] KB document upload
- [ ] Text chunking and embedding
- [ ] Vector search implementation
- [ ] Admin KB management UI

### ⏳ Phase 3: Sprint 3 - Ticketing
- [ ] Ticket models and endpoints
- [ ] Auto-ticket creation from chat
- [ ] Ticket management UI
- [ ] Notification system

### ⏳ Phase 4: Sprint 4 - Admin Dashboard
- [ ] Statistics dashboard
- [ ] LLM provider switching
- [ ] User management
- [ ] System settings

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run integration tests only
pytest -m integration
```

### Verification Tests

The harness includes verification tests to ensure everything is working:

```bash
# Test configuration loading
python -c "from app.core.config import settings; print(settings.model_dump())"

# Test logging
python -c "from app.core.logging import setup_logging, get_logger; setup_logging(); get_logger(__name__).info('Test')"

# Test health endpoint
curl http://localhost:8080/health
```

## 📖 Documentation

Detailed documentation is available in the documentation files:

- **01_architecture.md** - System architecture and design
- **02_features.md** - Feature specifications by sprint
- **03_db_schema.md** - Database schema and models
- **04_api_spec.md** - REST API endpoints and contracts
- **05_ui_spec.md** - UI/UX design specifications
- **CLAUDE.md** - Instructions for Claude Code development

Individual component READMEs:
- **backend/README.md** - Backend setup and development
- **frontend/README.md** - Frontend setup and development

## 🔐 Security Considerations

- JWT-based authentication
- API keys stored in environment variables (never in code)
- CORS configured for internal network only
- HTTPS for external API calls (Claude)
- Database connection encryption (PostgreSQL TLS)

## 🐛 Troubleshooting

### Backend won't start

1. Check environment variables in `.env`
2. Ensure ANTHROPIC_API_KEY is set
3. Verify DATABASE_URL is correct
4. Check JWT_SECRET_KEY is 32+ characters

### Frontend can't connect to backend

1. Verify backend is running: `curl http://localhost:8080/health`
2. Check NEXT_PUBLIC_API_URL in frontend `.env.local`
3. Ensure CORS is configured correctly in backend

### Tests failing

1. Check Python version >= 3.11
2. Install all dependencies: `pip install -r requirements.txt`
3. Ensure DATABASE_URL uses SQLite for tests

## 📄 License

Internal project for company use.

## 🤝 Contributing

This project follows the Vibe Coding methodology with Claude Code.

All development should:
1. Read CLAUDE.md first
2. Follow the technical specifications
3. Use the harness infrastructure
4. Include tests
5. Update documentation
