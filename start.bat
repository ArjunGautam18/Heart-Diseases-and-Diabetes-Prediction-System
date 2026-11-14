@echo off
echo Starting Smart Healthcare System...

if not exist "%~dp0venv\Scripts\python.exe" (
	echo Python virtual environment was not found at %~dp0venv
	pause
	exit /b 1
)

netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul
if errorlevel 1 (
	start "Backend - FastAPI" cmd /k "cd /d "%~dp0" && "%~dp0venv\Scripts\python.exe" -m uvicorn src.app:app --reload"
) else (
	echo Backend is already running on port 8000.
)

timeout /t 3 /nobreak >nul

netstat -ano | findstr /R /C:":3000 .*LISTENING" >nul
if errorlevel 1 (
	start "Frontend - React" cmd /k "cd /d "%~dp0new frontend" && npm run dev"
) else (
	echo Frontend is already running on port 3000.
)

timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:3000

echo Both servers launching in separate windows...