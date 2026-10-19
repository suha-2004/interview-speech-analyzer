@echo off
echo ========================================================
echo   Starting AI Interview Speech Quality Analyzer...
echo ========================================================
if exist "venv\Scripts\python.exe" (
    echo Running inside project virtual environment (venv)...
    venv\Scripts\python.exe run.py
) else (
    python run.py
)
pause
