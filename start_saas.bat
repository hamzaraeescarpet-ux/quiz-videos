@echo off
echo Starting QuizViral AI Backend...
start cmd /k "uvicorn main:app --reload --port 8000"

echo Starting QuizViral AI Frontend...
start cmd /k "cd frontend && npm run dev"

echo Both services are starting up!
