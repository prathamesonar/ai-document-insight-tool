#!/bin/bash

# Start script for AI Document Insights Application

echo "Starting AI Document Insights Application..."

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Install backend dependencies if not already installed
echo "Checking backend dependencies..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file for configuration..."
    echo "# Sarvam AI API Key (optional - get from https://sarvam.ai)" > .env
    echo "SARVAM_API_KEY=your_api_key_here" >> .env
    echo "Note: Edit .env file with your actual API key for AI features"
fi

# Start backend server
echo "Starting backend server on http://localhost:8000"
uvicorn main:app --host localhost --port 8000 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo "Starting frontend server on http://localhost:5000"
cd ../frontend
python -m http.server 5000 &
FRONTEND_PID=$!

echo ""
echo "Application started successfully!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for interrupt signal
wait $BACKEND_PID $FRONTEND_PID
