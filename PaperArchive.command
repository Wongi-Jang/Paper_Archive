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

# Wait for frontend to be ready then open browser
sleep 4
open http://localhost:5173

echo "Paper Archive is running."
echo "Close this window to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
