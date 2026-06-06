# Deployment fuer Claude-Umgebung (Docker)

Diese Anleitung stellt das Hotel-Bildtool zentral bereit, damit Kolleginnen und Kollegen es im Browser nutzen koennen.

## 1) Voraussetzungen

- Docker Desktop (Windows/Mac) oder Docker Engine (Linux)
- Zugriff auf dieses Projektverzeichnis

## 2) Starten

Im Projektordner:

```powershell
docker compose up -d --build
```

Danach ist das Tool lokal erreichbar unter:

- [http://localhost:8000](http://localhost:8000)

## 3) Fuer Kollegen im Netzwerk bereitstellen

- App auf einem internen Server/Host starten (nicht nur auf dem eigenen Laptop)
- Port `8000` intern freigeben
- Kollegen nutzen dann:
  - `http://<SERVERNAME>:8000` oder
  - `http://<SERVER-IP>:8000`

## 4) Stoppen / Neustarten

```powershell
docker compose down
docker compose up -d
```

## 5) Logs ansehen

```powershell
docker compose logs -f
```

## Hinweise

- Die Verarbeitung ist serverseitig, daher fuer Teamnutzung zentral geeignet.
- Upload unterstuetzt Einzelbilder und ZIP-Dateien mit Bildern.
- Ergebnis ist weiterhin eine ZIP-Datei mit bearbeiteten JPGs.
