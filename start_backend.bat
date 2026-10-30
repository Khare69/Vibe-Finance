@echo off
echo Starting Vibe Finance Backend (FastAPI on http://localhost:8000)...
set PYTHONPATH=%CD%
python -m uvicorn backend.main:app --port 8000 --reload
pause
