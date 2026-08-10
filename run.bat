@echo off
setlocal

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 exit /b %errorlevel%
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 exit /b %errorlevel%
python -m pip install -r requirements.txt
if errorlevel 1 exit /b %errorlevel%
python main.py
