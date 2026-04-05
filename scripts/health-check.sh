#!/bin/bash
# Health check script for IT AI Helpdesk

set -e

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8080}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
TIMEOUT="${TIMEOUT:-5}"

echo "🏥 IT AI Helpdesk Health Check"
echo "================================"
echo ""

# Check backend health
echo "Checking Backend ($BACKEND_URL)..."
if curl -f -s --max-time "$TIMEOUT" "$BACKEND_URL/health" > /dev/null 2>&1; then
    BACKEND_RESPONSE=$(curl -s "$BACKEND_URL/health")
    echo "✅ Backend: OK"
    echo "   Response: $BACKEND_RESPONSE"
else
    echo "❌ Backend: FAILED"
    BACKEND_FAILED=1
fi

echo ""

# Check frontend
echo "Checking Frontend ($FRONTEND_URL)..."
if curl -f -s --max-time "$TIMEOUT" "$FRONTEND_URL" > /dev/null 2>&1; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: FAILED"
    FRONTEND_FAILED=1
fi

echo ""

# Check Docker containers
echo "Checking Docker Containers..."
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""

# Check database connection
echo "Checking Database Connection..."
if docker exec aihelpdesk-db pg_isready -U helpdesk > /dev/null 2>&1; then
    echo "✅ Database: OK"
else
    echo "❌ Database: FAILED"
    DB_FAILED=1
fi

echo ""
echo "================================"

# Exit with error if any check failed
if [ -n "$BACKEND_FAILED" ] || [ -n "$FRONTEND_FAILED" ] || [ -n "$DB_FAILED" ]; then
    echo "❌ Health check FAILED"
    exit 1
else
    echo "✅ All systems operational"
    exit 0
fi
