@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo The project virtual environment was not found.
    echo Open a terminal in this folder and create it, then install requirements.txt.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m streamlit run app.py
pause
