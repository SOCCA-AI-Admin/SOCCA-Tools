# Hotel-Bildbearbeitung starten
Set-Location $PSScriptRoot

Write-Host "Installiere/aktualisiere Pakete ..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m pip install jinja2 python-multipart pillow fastapi "uvicorn[standard]" -q

Write-Host ""
Write-Host "Server startet. Browser oeffnen:" -ForegroundColor Green
Write-Host "  http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Fenster NICHT schliessen. Beenden mit Strg+C" -ForegroundColor Gray
Write-Host ""

.\.venv\Scripts\uvicorn.exe app.hotel_app:app --host 127.0.0.1 --port 8000 --reload
