#!/bin/bash
cd "$(dirname "$0")"

# Start backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload &
BACKEND_PID=$!

# Start frontend
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "App running at http://localhost:5173"
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
