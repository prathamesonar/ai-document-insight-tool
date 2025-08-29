@echo off
echo Starting AI Document Insights Application...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.11 or higher.
    pause
    exit /b 1
)

REM Install backend dependencies if not already installed
echo Checking backend dependencies...
cd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file for configuration...
    echo # Sarvam AI API Key (optional - get from https://sarvam.ai) > .env
    echo SARVAM_API_KEY=your_api_key_here >> .env
    echo Note: Edit .env file with your actual API key for AI features
)

REM Start backend server
echo Starting backend server on http://localhost:8000
start "Backend Server" cmd /k "uvicorn main:app --host localhost --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server
echo Starting frontend server on http://localhost:5000
cd ..\frontend
start "Frontend Server" cmd /k "python -m http.server 5000"

echo.
echo Application started successfully!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5000
echo.
echo Both servers are running in separate windows.
echo Close the windows to stop the servers.
pause
