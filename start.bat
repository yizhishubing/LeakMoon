@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   LeakMoon Startup
echo ============================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: python not found
    pause
    exit /b 1
)

echo [1] Scanning free port 8000-9000...
python "%~dp0find_port.py" > "%TEMP%\lm_port.txt" 2>&1
set /p BACKEND_PORT=<"%TEMP%\lm_port.txt"
if not defined BACKEND_PORT set BACKEND_PORT=8000
echo   Port: %BACKEND_PORT%
echo.

echo [2] MySQL...
sc query MySQL84 | findstr /C:"RUNNING" >nul 2>&1
if errorlevel 1 (
    echo   MySQL not running, starting...
    net start MySQL84 >nul 2>&1
    if errorlevel 1 (
        echo   ERROR: MySQL not running
        echo   Please start MySQL and try again:
        echo     net start MySQL84
        pause
        exit /b 1
    )
)
echo   MySQL: Running
echo.

echo [3] Redis...
redis-cli -p 6379 ping >nul 2>&1
if %errorlevel% neq 0 (
    echo   WARNING: Redis not running
) else (
    echo   Redis: Running
)
echo.

echo [4] Initializing database...
cd /d "%~dp0backend"
call venv\Scripts\activate.bat
python init_db.py
if %errorlevel% neq 0 (
    echo   ERROR: Database initialization failed
    pause
    exit /b 1
)
echo.

echo [5] Starting backend on port %BACKEND_PORT%...
start "LeakMoon-Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port %BACKEND_PORT%"
timeout /t 5 /nobreak >nul
echo.

echo [6] Starting frontend...
start "LeakMoon-Frontend" cmd /k "cd /d %~dp0frontend && set VITE_API_PORT=%BACKEND_PORT% && npm run dev"
timeout /t 5 /nobreak >nul
echo.

echo ============================================
echo   Started!
echo ============================================
echo.
echo   Frontend:   http://localhost:5173
echo   Backend:    http://localhost:%BACKEND_PORT%/api/health
echo   Docs:       http://localhost:%BACKEND_PORT%/docs
echo.
echo   Two new windows show logs.
echo   Closing this window will NOT stop services.
echo.
pause
