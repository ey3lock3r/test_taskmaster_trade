#!/bin/bash

# Kill any existing processes on ports 8000 and 3000
echo "Attempting to kill processes on ports 8000 and 3000..."
fuser -k 8000/tcp || true
fuser -k 3000/tcp || true
sleep 2 # Give processes a moment to terminate

# Clean up the database directly
echo "Cleaning up database..."
python3 scripts/reset_db.py

# Start Redis in background
echo "Starting Redis server..."
(cd frontend && npm run redis &)
REDIS_PID=$!
echo "Redis PID: $REDIS_PID"

# Start backend in background
echo "Starting backend server..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Start frontend in background
echo "Starting frontend server..."
(cd frontend && npm run dev -- -p 3000 &)
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Wait for backend to be ready
echo "Waiting for backend to be ready (port 8000)..."
for i in $(seq 1 30); do # Wait up to 30 seconds
  if curl -s -X POST http://localhost:8000/test/reset-db > /dev/null; then
    echo "Backend is ready."
    break
  fi
  sleep 1
done

# Wait for frontend to be ready
echo "Waiting for frontend to be ready (port 3000)..."
for i in $(seq 1 30); do # Wait up to 30 seconds
  if curl -s http://localhost:3000 > /dev/null; then
    echo "Frontend is ready."
    break
  fi
  sleep 1
done


# Run Playwright tests
echo "Running Playwright tests..."
pwd # Debug: Before running Playwright tests
    (cd frontend && npm run e2e_headless)

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