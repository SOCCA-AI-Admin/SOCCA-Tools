# SOCCA-Tools – Kontext für Claude

Dieses Repository (`SOCCA-AI-Admin/SOCCA-Tools`, Branch `main`) enthält mehrere voneinander
getrennte Tools. Jedes Tool hat eigenen Code, eigene Umgebung und eigenen Start.
Lokaler Arbeitsordner: `OneDrive - SOCCA GROUP\Process\KI\SOCCA PiXX`.

| Tool | Ort | Lokale Umgebung | Produktion |
|---|---|---|---|
| Hotelbilder (Oberfläche: „Bilder Destinationen“) | `app/hotel_app.py` | `.venv` in der Wurzel | Docker, Port 8000 |
| Rechnungs-Upload | `app/main.py` | `.venv` in der Wurzel | nicht produktiv |
| SOCCA Sales Cockpit | `socca-cockpit/` | eigene `.venv` in `socca-cockpit/` | Docker, eigener Port, siehe `socca-cockpit/README.md` |

Änderungen am Hotelbilder-Tool dürfen das Sales Cockpit und den Rechnungs-Upload nicht berühren.

## Hotelbilder-Tool

Aufbereitung von Hotelbildern für Trainingslager-Präsentationen. Ablauf, Kategorien und
Nummernkreise: siehe `HOTEL_BILDER.md`.

Kurz: Brand im schwarzen Kopf per Logo wählen, Hotelname angeben (beides danach fest), Bilder oder ZIPs hochladen, jedes Bild wird
einzeln bearbeitet und erscheint unter „Nicht zugeordnet“. Bilder werden sieben Kategorien mit
festen Nummernkreisen (010–019 bis 070–079, je max. 10 Bilder) zugeordnet und sortiert.
Dateiname `Hotelname_Brand_XXX.jpg`, Nummer aus Kategorie und Position. Export als ZIP erst,
wenn alle Bilder zugeordnet sind. Entfernen mit ✕ (6 Sekunden rückgängig machbar).

### Dateien

- `app/hotel_app.py` – FastAPI-Einstieg, bindet Router und `/static` ein
- `app/hotel_routes.py` – `GET /` (Oberfläche) und `POST /api/process` (eine Datei je Anfrage, Antwort JSON mit Bildern als Base64, Vorschau, übersprungenen und fehlgeschlagenen Dateien, Dateinamen-Präfix)
- `app/image_processor.py` – Bildpipeline, Konstanten (Zielgröße, Mindestpixel, Brands, Dateiendungen)
- `app/templates/hotel.html` – Oberfläche; Dateiendungen und Mindestpixel kommen per `data-*` aus Python
- `app/static/hotel.js` – Upload-Warteschlange, Kategorien (`CATS`), Drag & Drop, Dateinamen, Export
- `app/static/zip.js` – eigener ZIP-Schreiber (Methode „stored“), keine Fremdbibliothek
- `app/static/logos/` – Negativ-Logos (weiße Schrift) für den schwarzen Kopf: `<brand>.png` für die Brand-Auswahl, `socca-group.png` für die Kopfzeile; fehlt ein Brand-Logo, steht der Name als Text
- `app/static/hotel.css` – Gestaltung nach SOCCA GROUP Design System, Tokens wie im Sales Cockpit
- `Dockerfile`, `docker-compose.yml` – Produktion
- `start-hotel.bat`, `start-hotel.ps1` – lokaler Start unter Windows

### Architektur

- Der Server speichert nichts. Er bearbeitet je Anfrage eine Datei und gibt die Bilder zurück.
- Zuordnung, Reihenfolge, Dateinamen und ZIP entstehen im Browser. Seite neu laden verwirft alles,
  der Browser warnt vorher.
- Der Endpunkt ist bewusst synchron (`def`), damit die rechenintensive Bearbeitung im Threadpool läuft.
- Kategorien und Nummernkreise stehen nur in `hotel.js` (`CATS`, `MAX_PER_CAT`).

### Bildpipeline (`app/image_processor.py`)

1. Öffnen, EXIF-Drehung übernehmen, nach RGB wandeln, auf höchstens 3000 px Kante verkleinern
2. **LightCraft** (Open-Source-Nachbau von Lightroom, `lightcraft-cli run`): Preset
   `app/presets/SOCCA.xmp` importieren und anwenden, `crop.autoStraighten` (Gerade ausrichten: Auto),
   Export als TIFF. Preset-ID = `user.xmp.<crs:UUID klein>`. Höchstens zwei Läufe gleichzeitig.
3. Mittig auf 3:2 Querformat zuschneiden; Hochformat wird dabei oben und unten beschnitten (nicht gedreht)
4. Auf 1800 × 1200 skalieren, JPG ab Qualität 90 absteigend, bis höchstens 1 MB

LightCraft steckt im Docker-Image (`Dockerfile`, feste Version mit SHA-256-Prüfsumme, derzeit 0.13.0).
Pfad zum Programm über Umgebungsvariable `LIGHTCRAFT_CLI` (Standard: `lightcraft-cli` im PATH).
Fehlt LightCraft, scheitert jedes Bild mit klarer Meldung; es gibt bewusst keinen stillen Ersatz.
Filter ändern: neues `SOCCA.xmp` aus LightCraft exportieren und `app/presets/SOCCA.xmp` ersetzen.

## Arbeitsweise

- Weiterentwicklung im Claude-Chat. Claude liefert eine ZIP mit dem vollständigen Stand des
  Hotelbilder-Tools; Justus entpackt sie in die Wurzel des Arbeitsordners, committet und pusht in
  Cursor, dann `git pull` und `docker compose up -d --build` auf dem Server.
- Beim Entpacken werden Dateien nur überschrieben, nie gelöscht. Entfernte Dateien nennt Claude ausdrücklich.
- GitHub ist die Quelle für den Code. Keine Bilder, `.env`, Schlüssel oder Excel-Dateien committen.
- Antworten und Oberflächentexte auf Deutsch.
- Keine Annahmen treffen, die nicht bestätigt sind. Bei Unklarheit nachfragen.

### Lokal starten (Windows, im Projektordner)

Für die Bildbearbeitung braucht es lokal LightCraft: `lightcraft-0.13.0-windows-x64-portable.zip` von
https://github.com/storytold/lightcraft/releases/tag/v0.13.0 entpacken und den Pfad setzen, z. B.
`$env:LIGHTCRAFT_CLI = "C:\Tools\lightcraft\lightcraft-cli.exe"` (genaue Lage der exe im Archiv prüfen).

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

- Bisher begannen Dateinamen bei 001, jetzt je Kategorie bei 010, 020 usw. Prüfen, ob Website,
  CMS oder Präsentationsvorlagen von den alten Nummern abhängen.
- `requirements.txt` enthält auch Pakete des Rechnungs-Uploads (`pypdf`, `openpyxl`, `pymupdf`, `pytesseract`).
  OpenCV und numpy braucht das Bildtool seit LightCraft nicht mehr; ob der Rechnungs-Upload sie nutzt, ist ungeprüft.
- LightCraft ist jung und erscheint alle paar Tage neu. Updates nur bewusst: Version und Prüfsumme
  im Dockerfile ändern, vorher mit echten Hotelbildern vergleichen.
