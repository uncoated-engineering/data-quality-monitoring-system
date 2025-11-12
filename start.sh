#!/bin/bash

echo "Starting Data Quality Monitoring System..."
echo ""

# Check if Docker is installed
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "Starting with Docker Compose..."
    docker-compose up --build
else
    echo "Docker not found. Starting services manually..."
    echo ""

    # Start backend
    echo "Starting backend server..."
    cd backend
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -q -r requirements.txt

    echo "Backend starting on http://localhost:8000"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!

    cd ..

    # Start frontend
    echo "Starting frontend server..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi

    echo "Frontend starting on http://localhost:3000"
    npm run dev &
    FRONTEND_PID=$!

    cd ..

    echo ""
    echo "========================================="
    echo "Data Quality Monitoring System is running!"
    echo "Backend API: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
    echo "Frontend Dashboard: http://localhost:3000"
    echo "========================================="
    echo ""
    echo "Press Ctrl+C to stop all services"

    # Wait for Ctrl+C
    trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
    wait
fi
