# Hotel-Bildbearbeitung (Web-Oberfläche)

Webbasiertes Tool zur Aufbereitung von Hotelbildern für Trainingslager-Präsentationen.

> **Umgebung:** Dieses Setup (`127.0.0.1:8000`) ist die **Entwicklungs-/Testumgebung**. Produktivbetrieb und Deployment: [UMGEBUNGEN.md](UMGEBUNGEN.md).

## Ablauf

1. Brand im Kopf per Logo wählen (SOCCATOURS, SOCCACUP, SWIMTOURS, ATHLETICSTOURS, TENNISTOURS) und Hotelname eingeben.
   Beides ist nach dem ersten Upload fest; „Neu beginnen“ setzt alles zurück.
2. Bilder oder ZIP-Dateien hochladen. Jedes Bild wird einzeln bearbeitet: LightCraft-Filter „SOCCA“, automatisch
   gerade ausgerichtet, auf 3:2 Querformat zugeschnitten (Hochformat oben und unten beschnitten), 1800 × 1200 px, JPG, höchstens 1 MB.
   Bilder unter 480.000 Pixel werden übersprungen. Weitere Bilder lassen sich jederzeit nachladen.
3. Bilder den Kategorien zuordnen, per Drag & Drop oder Auswahlfeld am Bild.
4. Reihenfolge innerhalb der Kategorie festlegen, per Drag & Drop oder mit ◀ ▶.
5. ZIP herunterladen. Erst möglich, wenn kein Bild mehr unter „Nicht zugeordnet“ liegt.

## Kategorien und Nummernkreise

| Nr. | Nummernkreis | Kategorie |
|---|---|---|
| 1 | 010–019 | Außenansicht und Lage |
| 2 | 020–029 | Hotel innen (Restaurant, Buffet, Lobby) |
| 3 | 030–039 | Zimmer |
| 4 | 040–049 | Sportstätte |
| 5 | 050–059 | Meeting, Fitness, Regeneration |
| 6 | 060–069 | Freizeit und Teambuilding |
| 7 | 070–079 | Umgebung und Destination |

Höchstens 10 Bilder je Kategorie. Dateiname `Hotelname_Brand_XXX.jpg`, die Nummer beginnt in jeder
Kategorie bei der ersten Nummer des Kreises und ergibt sich aus der Reihenfolge. Leere Kreise werden
übersprungen. ZIP-Name: `Hotelname_Brand.zip`.

## Start (einfach – ohne Activate.ps1)

**Doppelklick** auf `start-hotel.bat` im Projektordner. Das Skript installiert die Pakete aus
`requirements.txt` und startet den Server.

**Manuell** (wenn PowerShell `Activate.ps1` blockiert):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.hotel_app:app --reload
```

> Nicht `python` und `uvicorn` allein verwenden – das trifft oft das falsche Python. Immer `.\.venv\Scripts\python.exe` nutzen.

Im Browser: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Technik

- Backend: FastAPI, Pillow, LightCraft (`lightcraft-cli`, Filter `app/presets/SOCCA.xmp`, Gerade ausrichten Auto). `POST /api/process` nimmt eine Datei (Bild oder ZIP) und liefert die
  bearbeiteten Bilder als Base64 zurück, dazu eine Vorschau (480 × 320).
- Zuordnung, Dateinamen und ZIP entstehen im Browser (`app/static/hotel.js`, `app/static/zip.js`).
  Auf dem Server wird nichts gespeichert. Neu laden der Seite verwirft die Sortierung (der Browser warnt vorher).
- Gestaltung nach SOCCA GROUP Design System, Aufbau wie das Sales Cockpit, hell und dunkel.
