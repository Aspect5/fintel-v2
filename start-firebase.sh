#!/bin/bash

# Kill any existing processes
pkill -f "python.*app|vite" || true
sleep 2

# Start backend in background
echo "Starting backend..."
cd backend
source venv/bin/activate
BACKEND_PORT=5001 python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend with Firebase Studio port
echo "Starting frontend on port $PORT..."
cd ..
npx vite --host 0.0.0.0 --port ${PORT:-5173}

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null || true" EXIT
