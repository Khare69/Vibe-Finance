@echo off
echo Starting Vibe Finance Backend (FastAPI on http://localhost:8000)...
cd backend
python -m uvicorn main:app --port 8000 --reload
pause
