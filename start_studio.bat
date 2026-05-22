@echo off
echo ==========================================
echo   NASUTA EVO 8 // JULES STUDIO LAUNCHER
echo ==========================================
echo.
echo [1/2] Starting Backend Server...
start /b python src/jules_studio_server.py
echo [2/2] Opening Web Dashboard...
timeout /t 3 /nobreak > nul
start http://localhost:8000
echo.
echo Studio is running. Press Ctrl+C in this window to stop (or just close it).
pause
