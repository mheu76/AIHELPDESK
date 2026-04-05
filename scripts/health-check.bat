@echo off
REM Health check script for IT AI Helpdesk (Windows)

set BACKEND_URL=http://localhost:8080
set FRONTEND_URL=http://localhost:3000

echo.
echo Health Check - IT AI Helpdesk
echo ================================
echo.

echo Checking Backend (%BACKEND_URL%)...
curl -f -s --max-time 5 %BACKEND_URL%/health >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Backend: OK
) else (
    echo [FAILED] Backend: FAILED
    set BACKEND_FAILED=1
)

echo.

echo Checking Frontend (%FRONTEND_URL%)...
curl -f -s --max-time 5 %FRONTEND_URL% >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Frontend: OK
) else (
    echo [FAILED] Frontend: FAILED
    set FRONTEND_FAILED=1
)

echo.

echo Checking Docker Containers...
docker compose ps

echo.

echo Checking Database Connection...
docker exec aihelpdesk-db pg_isready -U helpdesk >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Database: OK
) else (
    echo [FAILED] Database: FAILED
    set DB_FAILED=1
)

echo.
echo ================================

if defined BACKEND_FAILED goto failed
if defined FRONTEND_FAILED goto failed
if defined DB_FAILED goto failed

echo [OK] All systems operational
exit /b 0

:failed
echo [FAILED] Health check FAILED
exit /b 1
