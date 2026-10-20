@echo off
cd /d "%~dp0"
py -3.11 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo CourtLab AI se abrira en http://127.0.0.1:8000
python -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
