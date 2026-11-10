# SOCCA-Tools – Kontext für Claude

Dieses Repository (`SOCCA-AI-Admin/SOCCA-Tools`, Branch `main`) enthält mehrere voneinander
getrennte Tools. Jedes Tool hat eigenen Code, eigene Umgebung und eigenen Start.

| Tool | Ort | Lokale Umgebung | Produktion |
|---|---|---|---|
| Hotelbilder („Trainingslager – Hotelbilder“) | `app/hotel_app.py` | `.venv` in der Wurzel | Docker, Port 8000 |
| Rechnungs-Upload | `app/main.py` | `.venv` in der Wurzel | nicht produktiv |
| SOCCA Sales Cockpit | `socca-cockpit/` | eigene `.venv` in `socca-cockpit/` | Docker, eigener Port, siehe `socca-cockpit/README.md` |

Änderungen am Hotelbilder-Tool dürfen das Sales Cockpit und den Rechnungs-Upload nicht berühren.

## Hotelbilder-Tool

Aufbereitung von Hotelbildern für Trainingslager-Präsentationen.

Eingabe: Hotelname (Freitext), Brand (Pflicht: SOCCATOURS, SOCCACUP, SWIMTOURS,
ATHLETICSTOURS, TENNISTOURS), beliebig viele Bilder oder ZIP-Dateien mit Bildern
(JPG, PNG, WebP, BMP, TIFF, GIF, HEIC/HEIF, AVIF).

Ausgabe: JPG 1800 × 1200 px (3:2, Querformat), höchstens 1 MB je Bild,
Dateinamen `Hotelname_Brand_001.jpg` fortlaufend, Download als `Hotelname_Brand.zip`.
Bilder unter 480.000 Pixel werden übersprungen und in der Oberfläche gemeldet
(Prüfung im Browser und im Backend).

### Dateien

- `app/hotel_app.py` – FastAPI-Einstieg, bindet Router und `/static` ein
- `app/hotel_routes.py` – `GET /` (Oberfläche) und `POST /api/process` (Verarbeitung, ZIP-Antwort, Header `X-Skipped-Files` / `X-Skipped-Count`)
- `app/image_processor.py` – Bildpipeline, Konstanten (Zielgröße, Mindestpixel, Brands, Dateiendungen)
- `app/templates/hotel.html`, `app/static/hotel.css`, `app/static/hotel.js` – Oberfläche
- `Dockerfile`, `docker-compose.yml` – Produktion
- `start-hotel.bat`, `start-hotel.ps1` – lokaler Start unter Windows

### Bildpipeline (Stand Code)

1. EXIF-Drehung übernehmen, nach RGB wandeln
2. Horizont automatisch begradigen (OpenCV, nur bei klarem Signal, max. ±5°)
3. Hochformat um 90° drehen
4. Mittig auf 3:2 zuschneiden, auf 1800 × 1200 skalieren
5. Adaptive Korrektur: Schatten, Helligkeit, Kontrast, Sättigung, Weißabgleich, Schärfe
6. JPG-Export, Qualität ab 90 absteigend, bis die Datei höchstens 1 MB groß ist

Konstanten wie Mindestpixel und Dateiendungen stehen doppelt in `image_processor.py`
und `hotel.js`. Bei Änderungen beide anpassen.

## Arbeitsweise

- Lokal entwickeln und testen, dann committen und nach GitHub pushen, dann auf dem Server deployen.
- GitHub ist die Quelle für den Code. Keine Bilder, `.env`, Schlüssel oder Excel-Dateien committen.
- Antworten und Oberflächentexte auf Deutsch.
- Keine Annahmen treffen, die nicht bestätigt sind. Bei Unklarheit nachfragen.

### Lokal starten (Windows, im Projektordner)

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.hotel_app:app --host 127.0.0.1 --port 8000 --reload
```

Browser: http://127.0.0.1:8000. Immer `.\.venv\Scripts\python.exe` verwenden, nicht `python` allein.

### Produktion

Linux-Server im internen Netz, `10.10.20.60`. Im geklonten Repository auf dem Server:

```bash
git pull
docker compose up -d --build
```

Erreichbar unter http://10.10.20.60:8000. Das Sales Cockpit liegt auf demselben Server
unter `/opt/socca-tools/socca-cockpit` und läuft auf einem anderen Port.

## Offene Punkte

- Oberfläche und `HOTEL_BILDER.md` sagen „Originalfarben“ bzw. „keine Farb- oder
  Kontrastbearbeitung“, der Code korrigiert aber Helligkeit, Kontrast, Sättigung,
  Weißabgleich und Schärfe und begradigt den Horizont. Welches Verhalten gewollt ist, ist zu klären.
- Hochformatbilder werden um 90° gedreht und liegen danach auf der Seite.
- `start-hotel.bat` und `start-hotel.ps1` installieren nur einen Teil der Pakete
  (ohne `numpy`, `opencv-python-headless`, `pillow-heif`).
- `requirements.txt` enthält auch Pakete des Rechnungs-Uploads (`pypdf`, `openpyxl`, `pymupdf`, `pytesseract`).
- Gestaltung entspricht noch nicht dem SOCCA GROUP CI (Lato, max. 8 px Radius).
