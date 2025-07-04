#!/bin/bash

# Kill any existing processes on ports 8000 and 3000 and 6379
echo "Attempting to kill processes on ports 8000 and 3000..."
fuser -k 8000/tcp || true
fuser -k 3000/tcp || true
fuser -k 6379/tcp || true
sleep 2 # Give processes a moment to terminate

# Clean up the database directly
echo "Cleaning up database..."
python3 scripts/reset_db.py

echo "Starting Redis server..."
cd frontend && npm run redis &
REDIS_PID=$!
echo "Redis server started with PID: $REDIS_PID"

echo "Starting backend server..."
uvicorn src.main:app --reload &
BACKEND_PID=$!
echo "Backend server started with PID: $BACKEND_PID"

echo "Waiting for backend server to start..."
sleep 5 # Give the backend server some time to initialize

# Add test user after backend is up
echo "Adding test user..."
./scripts/add_test_data.sh

echo "Starting frontend server..."
cd frontend && npm run dev &
FRONTEND_PID=$!
echo "Frontend server started with PID: $FRONTEND_PID"

echo "Development servers are running. Press Ctrl+C to stop both."

# Function to kill background processes
cleanup() {
  echo "Stopping servers..."
  kill $REDIS_PID
  kill $BACKEND_PID
  kill $FRONTEND_PID
  wait $REDIS_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null
  echo "Servers stopped."
}

# Trap Ctrl+C to call the cleanup function
trap cleanup SIGINT

wait $REDIS_PID
wait $BACKEND_PID
wait $FRONTEND_PID