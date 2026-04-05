<div align="center">

# 🤖 IT AI Helpdesk

**AI-Powered Internal IT Support System**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Deployment](#-deployment)

</div>

---

## 📖 About

IT AI Helpdesk는 **AI를 활용한 내부 IT 지원 시스템**입니다. 직원들의 IT 관련 문의를 AI가 1차로 처리하고, 필요시 IT 담당자에게 티켓을 생성하여 효율적인 지원 체계를 구축합니다.

### Why IT AI Helpdesk?

- 🚀 **즉각적인 응답**: AI가 24/7 실시간으로 IT 문의에 답변
- 📚 **지식 기반 검색**: RAG(Retrieval-Augmented Generation)를 통한 정확한 답변
- 🎫 **자동 티켓 생성**: AI가 해결하지 못한 문제는 자동으로 티켓 생성
- 👥 **역할 기반 접근**: 직원/IT 담당자/관리자별 권한 관리
- 🔄 **런타임 설정**: 재시작 없이 AI 모델 및 설정 변경 가능
- 🌐 **다국어 지원**: 한국어/영어 UI 제공

---

## ✨ Features

### 🤖 AI Chat Interface
- Claude/OpenAI 기반 대화형 IT 지원
- RAG를 통한 지식 베이스 검색 (ChromaDB 또는 DB fallback)
- 대화 이력 관리 및 세션 기반 컨텍스트 유지
- 런타임 LLM 제공자/모델 전환 (재시작 불필요)

### 📚 Knowledge Base Management
- IT 문서/매뉴얼 업로드 및 관리
- 벡터 검색을 통한 관련 문서 자동 검색
- 문서 메타데이터 관리 (카테고리, 태그)

### 🎫 Ticket System
- 채팅 세션에서 원클릭 티켓 생성
- AI 기반 자동 분류 및 요약
- 우선순위/상태/담당자 관리
- 댓글 및 이력 추적
- 통계 대시보드

### 👤 User Management
- JWT 기반 인증 (Access/Refresh Token)
- 역할 기반 권한 제어 (Employee/IT Staff/Admin)
- 관리자 보호 (마지막 관리자 삭제 방지)
- 사용자 프로필 관리

### ⚙️ Admin Dashboard
- 실시간 통계 (티켓, 사용자, 세션)
- 시스템 설정 관리 (DB 영속화)
- 사용자 관리 및 권한 변경
- LLM 설정 (제공자, 모델, 파라미터)

---

## 🎨 Screenshots

<div align="center">

### Chat Interface
<img src="docs/images/chat-screenshot.png" alt="Chat Interface" width="700">
*AI 기반 대화형 IT 지원 인터페이스*

### Ticket Management
<img src="docs/images/ticket-screenshot.png" alt="Ticket Management" width="700">
*티켓 관리 및 추적 시스템*

### Admin Dashboard
<img src="docs/images/admin-screenshot.png" alt="Admin Dashboard" width="700">
*통계 및 시스템 관리 대시보드*

</div>

> **Note**: 스크린샷은 실제 구현된 UI를 기반으로 추후 추가 예정

---

## 🛠 Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast Python web framework
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) (Async) - Database ORM
- **Migration**: [Alembic](https://alembic.sqlalchemy.org/) - Database migrations
- **Database**: [PostgreSQL 15](https://www.postgresql.org/) - Primary database
- **Vector DB**: [ChromaDB](https://www.trychroma.com/) (Optional) - RAG vector search
- **LLM**: [Anthropic Claude](https://www.anthropic.com/) / [OpenAI](https://openai.com/) - AI models
- **Testing**: [pytest](https://pytest.org/) - Testing framework

### Frontend
- **Framework**: [Next.js 14](https://nextjs.org/) - React App Router
- **Language**: [TypeScript](https://www.typescriptlang.org/) - Type-safe JavaScript
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS
- **UI Components**: Custom React components
- **API Client**: Fetch API with custom hooks

### Infrastructure
- **Containerization**: [Docker](https://www.docker.com/) + Docker Compose
- **Reverse Proxy**: [Nginx](https://nginx.org/) - Production deployment
- **Process Manager**: [Gunicorn](https://gunicorn.org/) + [Uvicorn](https://www.uvicorn.org/) - ASGI server

---

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ & Docker Compose 2.0+
- (Optional) Python 3.11+ and Node.js 20+ for local development

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/AIhelpdesk.git
cd AIhelpdesk
```

### 2. Configure Environment

```bash
# Backend environment
cp backend/.env.example backend/.env.docker

# Edit backend/.env.docker and set:
# - ANTHROPIC_API_KEY or OPENAI_API_KEY
# - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
```

### 3. Start Services

```bash
docker compose up --build
```

### 4. Access Application

- 🌐 **Frontend**: http://localhost:3000
- 🔌 **Backend API**: http://localhost:8080
- 📚 **API Docs**: http://localhost:8080/docs
- 🗄️ **PostgreSQL**: localhost:5432

### 5. Create Admin User

```bash
# Access backend container
docker exec -it aihelpdesk-backend bash

# Create admin (interactive)
python -m app.scripts.create_admin
```

That's it! 🎉

---

## 📁 Project Structure

```text
AIhelpdesk/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # API endpoints (routers)
│   │   ├── core/              # Core utilities (config, security, LLM)
│   │   ├── db/                # Database session and base
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/          # Business logic layer
│   │   ├── middleware/        # Custom middleware
│   │   └── utils/             # Utility functions
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Test suite (141 tests ✅)
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Backend container
│
├── frontend/                   # Next.js Frontend
│   ├── app/                   # Next.js App Router pages
│   │   ├── auth/              # Authentication pages
│   │   ├── chat/              # Chat interface
│   │   ├── tickets/           # Ticket management
│   │   ├── kb/                # Knowledge base
│   │   └── admin/             # Admin dashboard
│   ├── components/            # React components
│   ├── hooks/                 # Custom React hooks
│   ├── lib/                   # Utility libraries
│   ├── public/                # Static assets
│   └── Dockerfile             # Frontend container
│
├── docs/                       # Documentation
│   ├── 01_architecture.md     # System architecture
│   ├── 02_features.md         # Feature specifications
│   ├── 03_db_schema.md        # Database schema
│   ├── 04_api_spec.md         # API specifications
│   ├── 05_ui_spec.md          # UI specifications
│   ├── 09_admin_manual.md     # Admin guide
│   └── 10_deployment.md       # Deployment guide
│
├── scripts/                    # Deployment scripts
│   ├── backup-db.sh           # Database backup
│   ├── restore-db.sh          # Database restore
│   ├── health-check.sh        # Health check
│   └── deploy-prod.sh         # Production deployment
│
├── docker-compose.yml          # Development stack
└── README.md                   # This file
```

---

## ⚙️ Configuration

### Backend Environment Variables

Create `backend/.env.docker` for development or `backend/.env.production` for production:

```bash
# Environment
ENVIRONMENT=development
DEBUG=true

# LLM Configuration (Required)
LLM_PROVIDER=claude              # or openai or gemini
ANTHROPIC_API_KEY=sk-ant-xxx     # Required if using Claude
OPENAI_API_KEY=sk-xxx            # Required if using OpenAI
GEMINI_API_KEY=xxx               # Required if using Gemini
LLM_MODEL=claude-sonnet-4-20250514
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7

# Database (Required)
DATABASE_URL=postgresql+asyncpg://helpdesk:password@localhost:5432/helpdesk
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Authentication (Required)
JWT_SECRET_KEY=your-super-secret-key-min-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=["http://localhost:3000"]

# ChromaDB (Optional)
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION=it_knowledge_base

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=human               # or json for production

# Application
APP_NAME=IT Helpdesk API
MAX_CONVERSATION_TURNS=10
RAG_TOP_K=3
```

See [`backend/.env.example`](backend/.env.example) for all available options.

### Frontend Environment Variables

```bash
NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1
```

---

## 💻 Development

### Backend Development

```bash
# Setup virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

**API Documentation**: http://localhost:8080/docs (Swagger UI)

### Frontend Development

```bash
# Setup
cd frontend
npm install

# Start development server
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint
```

**Frontend**: http://localhost:3000

### Database Operations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current revision
alembic current

# View migration history
alembic history
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_api_auth.py

# Run integration tests only
pytest -m integration

# Run with verbose output
pytest -v -s
```

**Test Status**: ✅ 141 tests passing (as of 2026-04-06)

### Frontend Tests

```bash
cd frontend

# Type checking
npm run type-check

# Linting
npm run lint

# Build verification
npm run build
```

---

## 🚢 Deployment

### Development Deployment (Docker Compose)

```bash
docker compose up --build
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend: http://localhost:8080
- PostgreSQL: localhost:5432

### Production Deployment

See **[📘 Deployment Guide](docs/10_deployment.md)** for comprehensive production deployment instructions.

**Quick Production Deployment:**

```bash
# 1. Configure environment
cp backend/.env.example backend/.env.production
# Edit .env.production with production values

# 2. Deploy
./scripts/deploy-prod.sh

# 3. Setup Nginx reverse proxy (see deployment guide)
# 4. Configure SSL certificates (Let's Encrypt)
```

**Deployment Scripts:**

```bash
# Database backup
./scripts/backup-db.sh

# Database restore
./scripts/restore-db.sh backups/helpdesk_backup_20260406.sql.gz

# Health check
./scripts/health-check.sh

# Production deployment automation
./scripts/deploy-prod.sh
```

### Production Checklist

Before deploying to production:

- [ ] Replace SHA-256 password hashing with bcrypt/argon2
- [ ] Generate secure `JWT_SECRET_KEY` (32+ characters)
- [ ] Set `DEBUG=false` and `ENVIRONMENT=production`
- [ ] Configure production database (managed PostgreSQL recommended)
- [ ] Set up Nginx reverse proxy with SSL
- [ ] Configure firewall (allow only 80, 443, SSH)
- [ ] Set up automated database backups
- [ ] Configure log rotation
- [ ] Set up monitoring (health checks, metrics)
- [ ] Review CORS settings

---

## 📚 Documentation

### Core Documentation

- [📐 Architecture](docs/01_architecture.md) - System design and architecture
- [✨ Features](docs/02_features.md) - Feature specifications
- [🗄️ Database Schema](docs/03_db_schema.md) - Database design and schema
- [🔌 API Specification](docs/04_api_spec.md) - REST API endpoints
- [🎨 UI Specification](docs/05_ui_spec.md) - Frontend design specs

### Operations

- [⚙️ Operating Principles](docs/06_operating_principles.md) - System principles
- [🔍 RAG Configuration](docs/07.HYBRID%20RAG%20SETTING.MD) - Hybrid RAG setup
- [📊 Embedding Design](docs/08_harrier_embedding_design.md) - Harrier embedding
- [👑 Admin Manual](docs/09_admin_manual.md) - Admin operations guide
- [🚀 Deployment Guide](docs/10_deployment.md) - Production deployment

### Additional Resources

- [📋 CLAUDE.md](CLAUDE.md) - Claude Code integration guide
- [🐳 DOCKER_DEV.md](DOCKER_DEV.md) - Docker development notes
- [📝 NEXT_STEPS.md](NEXT_STEPS.md) - Roadmap and future work
- [🛠️ Scripts README](scripts/README.md) - Deployment scripts guide

---

## 🗺️ Roadmap

### ✅ Completed (v1.0)

- [x] JWT authentication with role-based access control
- [x] AI chat with Claude/OpenAI integration
- [x] RAG-based knowledge base search
- [x] Ticket management system
- [x] Admin dashboard and settings
- [x] Runtime LLM provider switching
- [x] Database migrations with Alembic
- [x] Docker containerization
- [x] Comprehensive test suite (141 tests)
- [x] API documentation (Swagger)
- [x] Korean/English UI localization
- [x] Deployment automation scripts

### 🚧 In Progress

- [ ] **Security**: Replace SHA-256 password hashing with bcrypt/argon2
- [ ] **Performance**: Implement SSE streaming for chat responses
- [ ] **CI/CD**: GitHub Actions pipeline
- [ ] **Monitoring**: Prometheus + Grafana integration

### 🔮 Future Enhancements

- [ ] Multi-tenant support
- [ ] Advanced analytics dashboard
- [ ] Email notifications for tickets
- [ ] Slack integration
- [ ] Mobile app (React Native)
- [ ] Voice input for chat
- [ ] Knowledge base auto-sync from external sources
- [ ] Advanced ticket routing and SLA management
- [ ] Chat history export

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Development Workflow

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/yourusername/AIhelpdesk.git`
3. **Create a branch**: `git checkout -b feature/amazing-feature`
4. **Make changes** and commit: `git commit -m 'Add amazing feature'`
5. **Push** to your fork: `git push origin feature/amazing-feature`
6. **Create a Pull Request**

### Coding Standards

**Backend (Python):**
- Follow PEP 8 style guide
- Use type hints for all functions
- Write tests for new features
- Use async/await patterns
- Document complex logic

**Frontend (TypeScript):**
- Use TypeScript strict mode
- Follow React best practices
- Use functional components and hooks
- Ensure type safety
- Write meaningful component names

**Git Commits:**
- Use conventional commits format
- Examples:
  - `feat: add ticket export feature`
  - `fix: resolve chat session bug`
  - `docs: update deployment guide`
  - `test: add integration tests for auth`

### Running Tests

Before submitting a PR, ensure:

```bash
# Backend tests pass
cd backend && pytest

# Frontend type-check passes
cd frontend && npm run type-check

# No linting errors
npm run lint
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Next.js](https://nextjs.org/) - React framework
- [Anthropic Claude](https://www.anthropic.com/) - AI language model
- [OpenAI](https://openai.com/) - AI language model
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework

---

## 📞 Support

### Issues

If you encounter any issues, please [create an issue](https://github.com/yourusername/AIhelpdesk/issues) on GitHub.

### Questions

For questions and discussions, please use [GitHub Discussions](https://github.com/yourusername/AIhelpdesk/discussions).

### Contact

- **Project Maintainer**: [Your Name](mailto:your.email@example.com)
- **Project Homepage**: [https://github.com/yourusername/AIhelpdesk](https://github.com/yourusername/AIhelpdesk)

---

<div align="center">

**Built with ❤️ using FastAPI and Next.js**

[⬆ Back to Top](#-it-ai-helpdesk)

</div>
