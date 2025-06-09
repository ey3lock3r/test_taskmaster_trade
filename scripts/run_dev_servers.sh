#!/bin/bash

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