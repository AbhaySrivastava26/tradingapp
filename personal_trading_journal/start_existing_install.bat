@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run run_windows.bat first & pause & exit /b 1)
call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
