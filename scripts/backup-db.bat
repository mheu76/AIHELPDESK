@echo off
REM Database backup script for IT AI Helpdesk (Windows)

setlocal enabledelayedexpansion

set BACKUP_DIR=backups
set CONTAINER_NAME=aihelpdesk-db
set DB_NAME=helpdesk
set DB_USER=helpdesk

REM Get timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%

set BACKUP_FILE=%BACKUP_DIR%\helpdesk_backup_%TIMESTAMP%.sql

REM Create backup directory
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo.
echo Starting database backup...
echo Container: %CONTAINER_NAME%
echo Database: %DB_NAME%
echo Backup file: %BACKUP_FILE%
echo.

REM Create backup
docker exec %CONTAINER_NAME% pg_dump -U %DB_USER% %DB_NAME% > "%BACKUP_FILE%"

if %errorlevel% == 0 (
    echo [OK] Backup completed successfully!
    echo File: %BACKUP_FILE%

    REM Show file size
    for %%A in ("%BACKUP_FILE%") do echo Size: %%~zA bytes
) else (
    echo [FAILED] Backup failed!
    exit /b 1
)

echo.
echo Tip: You can compress the backup file manually using 7-Zip or WinRAR
