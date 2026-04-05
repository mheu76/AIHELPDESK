# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🚧 In Progress

- Security enhancement: bcrypt/argon2 password hashing
- Performance: SSE streaming for chat responses
- CI/CD: GitHub Actions pipeline
- Monitoring: Prometheus + Grafana integration

## [1.0.0] - 2026-04-06

### 🎉 Initial Release

First production-ready release of IT AI Helpdesk.

### ✨ Features

#### Authentication & Authorization
- JWT-based authentication with access and refresh tokens
- Role-based access control (Employee, IT Staff, Admin)
- User registration and login
- Profile management
- Admin account protection (prevent deletion of last admin)

#### AI Chat System
- AI-powered IT support conversations (Claude/OpenAI)
- RAG-based knowledge base integration
- Session-based conversation history
- Runtime LLM provider switching (no restart required)
- Multi-turn conversation support
- Knowledge base search integration

#### Knowledge Base Management
- Document upload and storage
- Vector-based semantic search (ChromaDB)
- Database fallback for search when ChromaDB unavailable
- Document categorization and tagging
- Metadata management
- Document deletion with cleanup

#### Ticket Management
- Create tickets from chat sessions
- AI-powered ticket summarization and categorization
- Priority and status management
- Ticket assignment to IT staff
- Comment system for ticket updates
- Ticket statistics and reporting
- Atomic ticket numbering (PostgreSQL SEQUENCE)
- One-ticket-per-session constraint

#### Admin Dashboard
- Real-time statistics (tickets, users, sessions)
- User management (view, update, role changes)
- System settings management (DB-persisted)
- LLM configuration (provider, model, parameters)
- Runtime settings updates

#### Internationalization
- Korean UI translation (complete)
- English UI (default)
- Bilingual support throughout application

### 🛠 Technical

#### Backend
- FastAPI framework
- SQLAlchemy async ORM
- Alembic database migrations
- PostgreSQL 15 database
- Pydantic v2 for data validation
- Structured logging with request IDs
- Comprehensive error handling
- CORS middleware
- Health check endpoint

#### Frontend
- Next.js 14 App Router
- TypeScript with strict mode
- Tailwind CSS styling
- Custom React hooks (useAuth)
- Protected routes with AuthGuard
- Responsive design
- Korean/English locale support

#### Infrastructure
- Docker containerization
- Docker Compose for development
- Production Dockerfiles (multi-stage builds)
- Nginx reverse proxy configuration
- SSL/TLS support (Let's Encrypt)
- Database backup scripts
- Health check scripts
- Deployment automation scripts

### 🧪 Testing
- 141 backend unit and integration tests
- pytest test framework
- Test fixtures and factories
- Frontend type checking
- Linting configured

### 📚 Documentation
- Comprehensive README
- Architecture documentation
- API specification (Swagger/OpenAPI)
- Database schema documentation
- Deployment guide
- Admin manual
- Contributing guidelines
- Issue templates
- Pull request template

### 🔒 Security Notes

⚠️ **Important**: Current password hashing uses SHA-256 (temporary implementation).
**Must replace with bcrypt or argon2 before production deployment.**

### 🐛 Known Issues

- SSE chat streaming not implemented (API exists, not wired to frontend)
- Several deprecation warnings (`datetime.utcnow`, `HTTP_422` constant)
- No automated frontend tests yet

### 📦 Dependencies

**Backend:**
- fastapi==0.109.0
- sqlalchemy==2.0.25
- alembic==1.13.1
- anthropic==0.18.1
- openai==1.12.0
- chromadb==0.4.22
- pydantic==2.6.0
- pytest==8.0.0

**Frontend:**
- next==14.1.0
- react==18.2.0
- typescript==5.3.3
- tailwindcss==3.4.1

---

## Version History

### Semantic Versioning Guide

- **MAJOR** (X.0.0): Incompatible API changes
- **MINOR** (x.X.0): Backwards-compatible new features
- **PATCH** (x.x.X): Backwards-compatible bug fixes

### Release Tags

- `[Unreleased]`: Changes in development
- `[1.0.0]`: First stable release

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to this project.

## Links

- [GitHub Repository](https://github.com/yourusername/AIhelpdesk)
- [Issue Tracker](https://github.com/yourusername/AIhelpdesk/issues)
- [Documentation](docs/)
