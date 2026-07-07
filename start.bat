@echo off
echo ============================================
echo   LeakMoon - Campus Website Leak Inspection Platform
echo ============================================
echo.

REM Check and start MySQL
echo [1/4] Checking MySQL...
net start | find "MySQL84" >nul
if %errorlevel% equ 0 (
    echo   MySQL: Running
) else (
    echo   MySQL: Not running, starting...
    net start MySQL84
    if %errorlevel% equ 0 (
        echo   MySQL: Started successfully
    ) else (
        echo   MySQL: Start failed. Please start it manually:
        echo     net start MySQL84
    )
)

REM Check and start Redis
echo.
echo [2/4] Checking Redis...
redis-cli -p 6379 ping >nul 2>&1
if %errorlevel% equ 0 (
    echo   Redis: Running
) else (
    echo   Redis: Not running, starting...
    redis-server --service-start
    timeout /t 2 /nobreak >nul
    echo   Redis: Started
)

REM Start backend
echo.
echo [3/4] Starting backend service...
start "Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python -m uvicorn app.main:app --host 0.0.0.0"
timeout /t 3 /nobreak >nul

REM Start frontend
echo.
echo [4/4] Starting frontend service...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 3 /nobreak >nul

echo.
echo ============================================
echo   All services started!
echo ============================================
echo.
echo Frontend:   http://localhost:5173
echo Backend:    http://localhost:8000/api/health
echo API Docs:   http://localhost:8000/docs
echo.
echo Note: If port 8000 is occupied, backend will auto-find next available port.
echo.
pause
