#!/bin/bash
# Production deployment script for IT AI Helpdesk

set -e

echo "🚀 IT AI Helpdesk Production Deployment"
echo "========================================"
echo ""

# Check if production environment file exists
if [ ! -f "backend/.env.production" ]; then
    echo "❌ Error: backend/.env.production not found"
    echo "Please create it from backend/.env.example"
    exit 1
fi

# Backup database before deployment
echo "📦 Creating database backup..."
./scripts/backup-db.sh

# Pull latest code
echo ""
echo "📥 Pulling latest code..."
git pull origin main

# Build and start services
echo ""
echo "🔨 Building and starting services..."
docker compose -f docker-compose.prod.yml up --build -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Run database migrations
echo ""
echo "🗄️  Running database migrations..."
docker exec helpdesk-backend-prod alembic upgrade head

# Health check
echo ""
echo "🏥 Running health check..."
if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker compose -f docker-compose.prod.yml logs backend
    exit 1
fi

# Show status
echo ""
echo "📊 Container status:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "Services:"
echo "  - Backend: http://localhost:8080"
echo "  - Frontend: http://localhost:3000"
echo "  - API Docs: http://localhost:8080/docs"
echo ""
echo "View logs: docker compose -f docker-compose.prod.yml logs -f"
