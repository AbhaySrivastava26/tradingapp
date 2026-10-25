@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
 echo Install Python 3.11+ from https://www.python.org/downloads/ and select "Add Python to PATH".
 pause
 exit /b 1
)
if not exist .venv\Scripts\python.exe py -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
