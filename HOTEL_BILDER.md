# Hotel-Bildbearbeitung (Web-Oberfläche)

Webbasiertes Tool zur Aufbereitung von Hotelbildern für Trainingslager-Präsentationen.

> **Umgebung:** Dieses Setup (`127.0.0.1:8000`) ist die **Entwicklungs-/Testumgebung**. Produktivbetrieb und Deployment: [UMGEBUNGEN.md](UMGEBUNGEN.md).

## Funktionen

- **Hotelname** (Freitext)
- **Brand** per Radiobutton (Pflicht): SOCCATOURS, SOCCACUP, SWIMTOURS, ATHLETICSTOURS, TENNISTOURS
- **Drag & Drop** für beliebig viele Bilder
- Bearbeitung: 3:2, Querformat, 1800×1200 px, JPG, Präsentations-Optimierung
- Dateinamen: `Hotelname_Brand_001.jpg`, `…_002.jpg`, …
- Download als ZIP: `Hotelname_Brand.zip`

## Start (einfach – ohne Activate.ps1)

**Doppelklick** auf `start-hotel.bat` im Projektordner  
oder im Terminal:

```powershell
cd "C:\Users\JustusWenzel\OneDrive - SOCCA GROUP\Process\KI\Cursor"
.\start-hotel.bat
```

**Manuell** (wenn PowerShell `Activate.ps1` blockiert):

```powershell
cd "C:\Users\JustusWenzel\OneDrive - SOCCA GROUP\Process\KI\Cursor"
.\.venv\Scripts\python.exe -m pip install jinja2 python-multipart pillow fastapi "uvicorn[standard]"
.\.venv\Scripts\python.exe -m uvicorn app.hotel_app:app --reload
```

> Nicht `python` und `uvicorn` allein verwenden – das trifft oft das falsche Python. Immer `.\.venv\Scripts\python.exe` nutzen.

Im Browser: [http://127.0.0.1:8000](http://127.0.0.1:8000)

> Das Rechnungs-Export-Tool bleibt unter `uvicorn app.main:app --reload` erreichbar (anderer Prozess/Port bei parallelem Betrieb, z. B. Port 8001).

## Technik

- Backend: FastAPI + Pillow
- Zuschnitt auf 3:2 (mittig), Hochformat wird gedreht
- Keine grafische Nachbearbeitung (nur Zuschnitt, Drehung, Größe, JPG-Export)
