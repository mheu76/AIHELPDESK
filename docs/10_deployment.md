# 10. Deployment Manual

## Overview

IT AI Helpdesk는 Docker Compose 기반 개발 환경과 Production 배포를 지원합니다.

**Tech Stack:**
- Backend: FastAPI + SQLAlchemy (async) + Alembic
- Frontend: Next.js 14 (App Router) + TypeScript
- Database: PostgreSQL 15
- Optional: ChromaDB for vector search

---

## 1. Development Deployment (Docker Compose)

### 1.1 Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git

### 1.2 Quick Start

```bash
# Clone repository
git clone <repository-url>
cd AIhelpdesk

# Start all services
docker compose up --build
```

**Services:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080
- API Docs (Swagger): http://localhost:8080/docs
- PostgreSQL: localhost:5432

### 1.3 Environment Configuration

**Backend**: `backend/.env.docker`

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>

# Optional
OPENAI_API_KEY=sk-your-openai-key
LLM_PROVIDER=claude  # or openai
```

⚠️ **Security Note**: `.env.docker`에는 개발용 dummy key가 포함되어 있습니다. 실제 API 키로 변경 필요.

### 1.4 Service Architecture

```yaml
services:
  db:           # PostgreSQL 15
    - Port: 5432
    - Volume: postgres_data (persistent)
    - Healthcheck enabled
  
  backend:      # FastAPI
    - Port: 8080
    - Auto-migration on startup
    - Hot reload enabled
  
  frontend:     # Next.js
    - Port: 3000
    - Hot reload enabled
```

### 1.5 Common Commands

```bash
# Start services
docker compose up

# Start in background
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart a service
docker compose restart backend

# Stop all services
docker compose down

# Stop and remove volumes (⚠️ deletes data)
docker compose down -v

# Rebuild after code changes
docker compose up --build
```

### 1.6 Database Operations

```bash
# Access PostgreSQL
docker exec -it aihelpdesk-db psql -U helpdesk -d helpdesk

# Run migrations manually
docker exec -it aihelpdesk-backend alembic upgrade head

# Create new migration
docker exec -it aihelpdesk-backend alembic revision --autogenerate -m "description"

# Rollback migration
docker exec -it aihelpdesk-backend alembic downgrade -1
```

---

## 2. Production Deployment

### 2.1 Prerequisites

- Linux server (Ubuntu 22.04 LTS recommended)
- Docker 20.10+ and Docker Compose 2.0+
- Domain name with DNS configured
- SSL certificate (Let's Encrypt recommended)
- PostgreSQL 15+ (managed or self-hosted)

### 2.2 Architecture Overview

```text
Internet
  -> Nginx (reverse proxy, SSL termination)
  -> Docker Network
      -> Frontend (Next.js, port 3000)
      -> Backend (FastAPI, port 8080)
  -> PostgreSQL (external or containerized)
  -> ChromaDB (optional, port 8000)
```

### 2.3 Environment Setup

#### Backend Production Environment

Create `backend/.env.production`:

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# LLM Configuration
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=<your-production-anthropic-key>
OPENAI_API_KEY=<your-production-openai-key>
GEMINI_API_KEY=<your-production-gemini-key>
LLM_MODEL=claude-sonnet-4-20250514
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7

# Database (use external managed PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/helpdesk_prod
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_ECHO=false

# ChromaDB (optional)
CHROMA_HOST=chroma-host
CHROMA_PORT=8000
CHROMA_COLLECTION=it_knowledge_base_prod

# Authentication
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
FRONTEND_URL=https://your-domain.com
ALLOWED_ORIGINS=["https://your-domain.com"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Application
APP_NAME=IT Helpdesk API
APP_VERSION=1.0.0
MAX_CONVERSATION_TURNS=10
RAG_TOP_K=3
```

#### Frontend Production Environment

Create `frontend/.env.production`:

```bash
NEXT_PUBLIC_API_URL=https://api.your-domain.com/api/v1
```

### 2.4 Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: helpdesk-backend-prod
    restart: unless-stopped
    env_file:
      - ./backend/.env.production
    command: >
      sh -c "alembic upgrade head &&
      gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker 
      --bind 0.0.0.0:8080 
      --access-logfile - 
      --error-logfile -"
    ports:
      - "8080:8080"
    networks:
      - helpdesk-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: helpdesk-frontend-prod
    restart: unless-stopped
    environment:
      NEXT_PUBLIC_API_URL: https://api.your-domain.com/api/v1
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - helpdesk-network

networks:
  helpdesk-network:
    driver: bridge
```

### 2.5 Production Dockerfiles

#### Backend: `backend/Dockerfile.prod`

```dockerfile
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libpq5 \
       curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]
```

#### Frontend: `frontend/Dockerfile.prod`

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM node:20-alpine

WORKDIR /app

RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public

USER nextjs

EXPOSE 3000

ENV NODE_ENV=production

CMD ["npm", "start"]
```

### 2.6 Nginx Configuration

Create `/etc/nginx/sites-available/helpdesk`:

```nginx
# Backend API
upstream backend {
    server localhost:8080;
}

# Frontend
upstream frontend {
    server localhost:3000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com api.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# Frontend
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend API
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 50M;

    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/helpdesk /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2.7 SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# Auto-renewal is configured by default
# Test renewal
sudo certbot renew --dry-run
```

### 2.8 Production Deployment Steps

```bash
# 1. Clone repository
git clone <repository-url>
cd AIhelpdesk

# 2. Configure environment files
cp backend/.env.example backend/.env.production
# Edit backend/.env.production with production values

# 3. Create production Dockerfiles
# Create backend/Dockerfile.prod and frontend/Dockerfile.prod as shown above

# 4. Create production docker-compose
# Create docker-compose.prod.yml as shown above

# 5. Build and start services
docker compose -f docker-compose.prod.yml up --build -d

# 6. Check logs
docker compose -f docker-compose.prod.yml logs -f

# 7. Verify health
curl http://localhost:8080/health
curl http://localhost:3000

# 8. Configure Nginx (see section 2.6)

# 9. Setup SSL (see section 2.7)

# 10. Create initial admin user
docker exec -it helpdesk-backend-prod python -m app.scripts.create_admin
```

### 2.9 Database Migration

```bash
# Run migrations
docker exec -it helpdesk-backend-prod alembic upgrade head

# Check current revision
docker exec -it helpdesk-backend-prod alembic current

# Backup database before migration
pg_dump -h db-host -U user -d helpdesk_prod > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 3. Security Checklist

### ⚠️ CRITICAL Before Production

- [ ] Replace `backend/app/core/security.py` SHA-256 password hashing with bcrypt or argon2
- [ ] Generate secure `JWT_SECRET_KEY` (min 32 characters): `openssl rand -hex 32`
- [ ] Use strong database passwords
- [ ] Configure firewall (allow only 80, 443, SSH)
- [ ] Enable PostgreSQL SSL connections
- [ ] Set `DEBUG=false` in production
- [ ] Configure log rotation
- [ ] Setup monitoring (disk, memory, CPU)
- [ ] Configure automated backups
- [ ] Review CORS settings (`ALLOWED_ORIGINS`)
- [ ] Enable rate limiting (consider adding nginx rate limiting)

### Production Environment Variables

Never commit these to git:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `JWT_SECRET_KEY`
- `DATABASE_URL` (production)

Use environment files (`.env.production`) and add to `.gitignore`.

---

## 4. Monitoring & Maintenance

### 4.1 Health Checks

```bash
# Backend health
curl https://api.your-domain.com/health

# Docker container status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### 4.2 Database Backup

```bash
# Manual backup
docker exec aihelpdesk-db pg_dump -U helpdesk helpdesk > backup_$(date +%Y%m%d).sql

# Automated backup (cron)
# Add to crontab: 0 2 * * * /path/to/backup_script.sh
```

### 4.3 Log Rotation

Configure logrotate for Docker logs:

```bash
# /etc/logrotate.d/docker-helpdesk
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

### 4.4 Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml up --build -d

# Run migrations
docker exec -it helpdesk-backend-prod alembic upgrade head
```

---

## 5. Troubleshooting

### Backend won't start

```bash
# Check logs
docker compose logs backend

# Common issues:
# - Database not ready: wait for db healthcheck
# - Migration failed: check alembic logs
# - Missing env vars: verify .env.docker or .env.production
```

### Frontend can't connect to backend

```bash
# Verify NEXT_PUBLIC_API_URL
docker compose exec frontend env | grep NEXT_PUBLIC_API_URL

# Should be: http://localhost:8080/api/v1 (dev)
# Or: https://api.your-domain.com/api/v1 (prod)
```

### Database connection issues

```bash
# Test connection
docker exec -it aihelpdesk-db psql -U helpdesk -d helpdesk

# Check DATABASE_URL format:
# postgresql+asyncpg://user:password@host:port/database
```

### Port conflicts

```bash
# Check ports
netstat -tulpn | grep -E '3000|8080|5432'

# Change ports in docker-compose.yml if needed
```

---

## 6. Rollback Procedure

```bash
# 1. Stop current deployment
docker compose -f docker-compose.prod.yml down

# 2. Checkout previous version
git checkout <previous-commit-hash>

# 3. Restore database backup (if migration was involved)
psql -U helpdesk -d helpdesk_prod < backup_YYYYMMDD.sql

# 4. Rebuild and start
docker compose -f docker-compose.prod.yml up --build -d

# 5. Verify health
curl https://api.your-domain.com/health
```

---

## 7. Performance Tuning

### Database

```bash
# PostgreSQL settings for production
# /etc/postgresql/15/main/postgresql.conf
shared_buffers = 256MB          # 25% of RAM
effective_cache_size = 1GB      # 50-75% of RAM
work_mem = 16MB
maintenance_work_mem = 128MB
max_connections = 100
```

### Backend

```bash
# Gunicorn workers: (2 x CPU cores) + 1
# In docker-compose.prod.yml:
command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Connection pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

### Frontend

```bash
# Next.js production build
npm run build

# Verify build output
ls -la .next/
```

---

## 8. Additional Resources

- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- Next.js Production: https://nextjs.org/docs/deployment
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/
- PostgreSQL Performance: https://wiki.postgresql.org/wiki/Performance_Optimization

---

## Version History

- 2026-04-06: Initial deployment manual created
