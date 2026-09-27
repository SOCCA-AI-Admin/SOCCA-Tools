# SOCCA-Tools

Jedes Tool hat einen eigenen Bereich, eine eigene Python-Umgebung und einen eigenen Start. Das Sales Cockpit gehört nicht zum Rechnungs-Upload und nicht zur Hotel-Bildbearbeitung.

| Tool | Ort | Umgebung |
|---|---|---|
| Rechnungs-Upload | `app/main.py` in diesem Ordner | `.venv` in der Repository-Wurzel |
| Hotel-Bildbearbeitung | `app/hotel_app.py` | dieselbe Wurzel-Umgebung, Start mit `start-hotel.bat` |
| SOCCA Sales Cockpit | `socca-cockpit/` | eigene `.venv` in `socca-cockpit/`, Anleitung in `socca-cockpit/README.md` |

---

# Invoice Upload MVP

Ein minimales Grundgerüst für:
- PDF-Rechnungen per Drag & Drop hochladen
- Kontoinhaber, IBAN, BIC, Betrag extrahieren
- Excel mit den Spalten `Kontoinhaber`, `IBAN`, `BIC`, `Betrag` erzeugen

## Start

1. Python-Umgebung erstellen (optional, empfohlen):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Abhängigkeiten installieren:

```powershell
python -m pip install -r requirements.txt
```

3. Server starten:

```powershell
uvicorn app.main:app --reload
```

4. Im Browser öffnen:

`http://127.0.0.1:8000`

## Hinweise

- Das Parsing ist im MVP regelbasiert (Regex + Heuristiken).
- Für Scan-PDFs ist ein OCR-Fallback integriert (Tesseract + PyMuPDF).
- Auf Windows muss Tesseract OCR lokal installiert sein:
  - Download: [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
  - Optionaler Pfad im Terminal setzen:

```powershell
$env:TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"
```

- Optional OCR-Sprachen setzen (Standard: `eng+deu+ita+fra+spa`):

```powershell
$env:OCR_LANGS="eng+deu+ita+fra+spa"
```

- Für schnelleres Upload-Verhalten (empfohlen im MVP):

```powershell
$env:OCR_MAX_PAGES="2"
$env:OCR_DPI="170"
```

- OCR bei Bedarf komplett deaktivieren:

```powershell
$env:OCR_ENABLED="0"
```

- Für produktiven Einsatz sind Validierung, Logging und Rechte-/Datenschutzkonzept zu ergänzen.
