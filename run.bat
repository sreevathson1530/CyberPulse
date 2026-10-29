@echo off
title CyberPulse
echo.
echo  ====================================================
echo   CyberPulse - Early-Warning Cyber Incident Linker
echo  ====================================================
echo.

REM Check if venv exists
if not exist ".venv\Scripts\streamlit.exe" (
    echo [!] Virtual environment not found or packages not installed.
    echo [*] Setting up environment...
    echo.
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
    echo.
    echo [OK] Environment ready.
    echo.
)

echo [*] Launching CyberPulse...
echo [*] Open http://localhost:8501 in your browser.
echo.

.venv\Scripts\streamlit run app.py --server.port 8501
