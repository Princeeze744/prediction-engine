@echo off
cd /d "%~dp0"
echo Starting QuantSport v10.8 Core API...
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
pause
