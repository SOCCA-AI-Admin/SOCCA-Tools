# Umgebungen

## Entwicklung & Test (lokal)

| | |
|---|---|
| **Zweck** | Entwickeln, testen, Fehler beheben |
| **Ort** | Dieser Projektordner auf deinem Rechner |
| **URL** | [http://127.0.0.1:8000](http://127.0.0.1:8000) |
| **Start** | `start-hotel.bat` (Doppelklick) oder `uvicorn app.hotel_app:app --reload` |
| **Python** | `.\.venv\Scripts\python.exe` / `.\.venv\Scripts\uvicorn.exe` |

## Produktion (Team-Betrieb)

| | |
|---|---|
| **Zweck** | Zentraler Zugriff für Kolleginnen und Kollegen |
| **Ort** | Interner Server/Host (nicht der lokale Laptop) |
| **Start** | `docker compose up -d --build` |
| **Anleitung** | [README_DEPLOY_CLAUDE.md](README_DEPLOY_CLAUDE.md) |

## Versionskontrolle (GitHub)

| | |
|---|---|
| **Zweck** | Code-Stand sichern und versionieren |
| **Organisation** | SOCCA-GROUP |
| **Hinweis** | GitHub ist kein Laufzeit-Server für die Anwendung |

## Ablauf bei Änderungen

1. **Lokal** entwickeln und testen (`127.0.0.1:8000`)
2. **GitHub** – Änderungen committen und pushen (bei Bedarf)
3. **Produktion** – separat auf dem Server deployen
