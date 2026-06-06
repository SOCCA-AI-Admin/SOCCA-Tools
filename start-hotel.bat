@echo off
cd /d "%~dp0"

echo Installiere Pakete in .venv ...
".venv\Scripts\python.exe" -m pip install jinja2 python-multipart pillow fastapi "uvicorn[standard]" -q

echo.
echo Server startet - Browser oeffnen:
echo   http://127.0.0.1:8000
echo.
echo Fenster NICHT schliessen. Beenden mit Strg+C
echo.

".venv\Scripts\python.exe" -m uvicorn app.hotel_app:app --host 127.0.0.1 --port 8000 --reload
pause
