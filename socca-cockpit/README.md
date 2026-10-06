# SOCCA Sales Cockpit

Interaktives Vertriebs-Dashboard der SOCCA GROUP. Liest die Sales-Arbeitsmappe
und den Combit-Export, rechnet daraus einen kompakten Datensatz und baut eine
statische HTML-Seite.

Kein Server-Framework, keine Datenbank, kein Kartendienst. Die fertige Seite
besteht aus zwei Dateien — `index.html` und `data.json` — und läuft auf jedem
Webserver, der statische Dateien ausliefert.

---

## Der Ablauf in einem Satz

Der Server holt sich `Sales.xlsb` und `C_AP.xlsx` stündlich selbst aus
SharePoint (Site SOCCASales), rechnet bei einer Änderung neu und tauscht die
Seite aus. Du arbeitest nur in Excel. Ohne SharePoint-Zugang geht es auch
über Dateien, die du per SFTP nach `data/` legst.

---

## Zuerst: mit den aktuellen Dateien starten

Das Paket enthält **keine Daten**. Das Cockpit, das du bisher gesehen hast
(Artefakt auf claude.ai, `SOCCA_Sales_Cockpit.html`, Beispiel-PDFs), wurde aus
`20260831_Sales.xlsb` und einem Combit-Export als CSV gerechnet — Stand
31.08.2026.

**Mit SharePoint-Anbindung** (empfohlen, siehe *Dateien direkt aus
SharePoint holen*) entfällt Schritt 1: Der Server lädt die aktuellen Dateien
selbst. Die Schritte 2, 3 und 5 gelten trotzdem.

**Ohne SharePoint-Anbindung** gehst du so vor:

**1. Dateien nach `data/` legen.**

| Datei | Erlaubte Formate | Beispiele für Namen |
|---|---|---|
| Sales-Arbeitsmappe | `.xlsx`, `.xlsm`, `.xlsb` | `Sales.xlsx`, `20260930_Sales.xlsb` |
| Combit-Export | `.xlsx`, `.csv` | `C_AP.xlsx`, `20260930_C_AP.csv` |

Der Name muss `Sales` bzw. `C_AP` enthalten; Groß-/Kleinschreibung und ein
Datum davor sind egal. Liegen mehrere passende Dateien dort, nimmt
`update.sh` die **zuletzt geänderte** und schreibt einen Hinweis ins Log.
Empfehlung trotzdem: je Quelle genau eine Datei mit festem Namen
(`Sales.xlsx`, `C_AP.xlsx`), die du jedes Mal überschreibst. Alte Stände
löschen — sonst gewinnt womöglich eine alte Datei, die zuletzt kopiert wurde.
Excel-Sperrdateien (`~$Sales.xlsx`) werden übergangen.

**2. Sales-Mappe in Excel speichern.** Das ETL liest die in der Datei
gespeicherten Ergebnisse der Formeln, rechnet sie aber nicht selbst nach. Die
Mappe also einmal in Excel öffnen, rechnen lassen und speichern, bevor sie
hochgeladen wird. Benötigte Blätter: `Sales`, `FTE`, `Leads`, `Props`,
`Goals`, `Locations`.

**3. Combit-Export mit dem gleichen Aufbau wie bisher.** Erste Zeile
Spaltenköpfe, bei `.xlsx` das erste Tabellenblatt. Gelesen werden
`Belegart`, `Team`, `Anfragedatum`, `AngebotVersandtDatum`,
`AnsprechpartnerMail`, `AP`, `Quelle`, `ErfassungsBenutzer`, `Destination`,
`KundenHerkunft` und `WebID`; alle anderen Spalten stören nicht. Der Export
sollte **ab 01.01.2024 lückenlos** sein — ab da kommen Anfragen und Angebote
aus Combit, und die Dublettenregel (je Mail × Team × AP-Jahr zählt die erste
Anfrage) braucht das ganze AP-Jahr. CSV darf UTF-8 oder Windows-1252 sein,
Trennzeichen `;` oder `,`.

**4. Neu rechnen.**

Auf dem Server:

```bash
cd /srv/socca-cockpit
PYTHON=.venv/bin/python ./update.sh --force
```

Lokal unter Windows (Cursor-Terminal, PowerShell) — ohne `update.sh`:

```powershell
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt          # nur beim ersten Mal
.venv\Scripts\python etl.py data\Sales.xlsx data\C_AP.xlsx web\data.json
.venv\Scripts\python build.py web\data.json web
cd web; ..\.venv\Scripts\python -m http.server 8000     # http://localhost:8000
```

Dateinamen im `etl.py`-Aufruf an deine anpassen. Mit Lead-Plan hängst du
`data\AP_Leads.csv` als vierten Parameter an. Unter macOS/Linux oder in Git
Bash geht alternativ `./update.sh --force`.

**5. Prüfen, ob der neue Stand angekommen ist.**

- Kopfzeile des Cockpits: *„… Buchungen nach Buchungsdatum, TT.MM.JJJJ bis
  **TT.MM.JJJJ**“* — das Enddatum ist die letzte Buchung in der Mappe. *Stand*
  dahinter ist der Zeitpunkt des Builds.
- Fußzeile: nennt die beiden tatsächlich gelesenen Dateinamen.
- Reports: *Datenstand* oben rechts ist ebenfalls die letzte Buchung.
- Server: `.state/update.log` zeigt je Lauf, welche Dateien mit welchem
  Änderungsdatum verarbeitet wurden, samt Zeilenzahlen und Dauer.

Das Artefakt auf claude.ai aktualisiert sich **nicht** von selbst — es ist
eine Momentaufnahme. Die aktuelle Fassung zum Weitergeben ist
`SOCCA_Sales_Cockpit.html`, die `build.py` bei jedem Lauf im Projektordner neu
schreibt.

---

## Betrieb mit Docker (Server 10.10.20.60)

So läuft das Cockpit neben der bestehenden App: gleiche IP, eigener Port.

| | Adresse |
|---|---|
| Bestehende App | `http://10.10.20.60:8000` |
| SOCCA Sales Cockpit | `http://10.10.20.60:8001` |
| Projektordner | `/opt/socca-tools/socca-cockpit` |

Drei Container, beschrieben in `docker-compose.yml`:

- **worker** prüft alle 15 Minuten, ob sich die Mappen geändert haben, und
  rechnet nur dann neu (`update.sh`). Quelle ist SharePoint, sobald
  `sharepoint.env` existiert, sonst der Ordner `data/`. Der Projektordner ist
  eingebunden — ein `git pull` wirkt ohne Neubau.
- **ask** beantwortet Fragen aus dem Feld *Frag das Cockpit* (siehe unten).
  Ohne `anthropic.env` läuft er still mit, das Feld bleibt ausgeblendet.
- **web** liefert die fertige Seite auf Port 8001 aus — ohne Passwort, für
  alle im internen Netz.

Kein Cron, keine Domain, kein Zertifikat nötig. Die Abschnitte zu nginx,
certbot und Cron weiter unten gelten nur für den Betrieb ohne Docker.

### Einrichten

```bash
cd /opt/socca-tools
git clone <URL-des-Repositorys> socca-cockpit
cd socca-cockpit

# 1. Eigene Benutzer-ID eintragen, damit die Dateien dir gehören
printf 'COCKPIT_UID=%s\nCOCKPIT_GID=%s\n' "$(id -u)" "$(id -g)" > .env

# 2. Starten
docker compose up -d --build
docker compose logs -f worker        # Strg+C beendet nur die Anzeige
```

Solange der erste Lauf rechnet (drei bis vier Minuten), zeigt
`http://10.10.20.60:8001` eine Seite „wird aufgebaut“, die sich selbst neu
lädt.

### Im Alltag

| Aufgabe | Befehl (im Projektordner) |
|---|---|
| Sofort neu rechnen | `docker compose exec worker bash update.sh --force` |
| Protokoll ansehen | `tail -30 .state/update.log` oder `docker compose logs --tail 50 worker` |
| Neue Version aus GitHub | `git pull && docker compose up -d --build` |
| SharePoint-Zugang testen | `docker compose exec worker python3 fetch_sharepoint.py --check` |
| Anhalten / wieder starten | `docker compose stop` / `docker compose start` |
| Anderer Port | in `.env` `COCKPIT_PORT=8002` ergänzen, dann `docker compose up -d` |
| Häufiger prüfen | in `.env` `COCKPIT_INTERVAL=300` (Sekunden), dann `docker compose up -d` |

Die Container starten nach einem Neustart des Servers von selbst.

### Gut zu wissen

- **Ohne Passwort, nur im internen Netz.** Jeder, der `10.10.20.60`
  erreicht, sieht Umsätze, Margen und FTE — auch über VPN oder ein
  Gäste-WLAN im selben Netz. Port 8001 darf deshalb nicht ins Internet
  freigegeben werden.
- **Zugriff auf bestimmte Netze begrenzen:** In `deploy/docker/nginx.conf`
  die Zeilen `allow …` / `deny all` aktivieren und die Netze eintragen, dann
  `docker compose restart web`.
- **Passwortschutz wieder einschalten:** In `deploy/docker/nginx.conf` die
  beiden `auth_basic`-Zeilen und in `docker-compose.yml` die Zeile mit
  `.htpasswd` aktivieren. Zugang anlegen mit
  `printf 'justus:%s\n' "$(openssl passwd -apr1)" > .htpasswd`, dann
  `docker compose up -d`.
- **Nicht zusätzlich einen Cron** für `update.sh` einrichten — der Container
  erledigt das.
- **Ohne SharePoint** legst du die Mappen per SFTP/WinSCP nach
  `/opt/socca-tools/socca-cockpit/data/` — der Container findet sie dort.
- **Internet für SharePoint:** Der Container *worker* braucht ausgehend HTTPS
  zu Microsoft. Geht der Server über einen Proxy, in `docker-compose.yml`
  die Zeile `HTTPS_PROXY` aktivieren.
- **Seite nicht erreichbar?** `docker compose ps` — beide Container müssen
  *running* sein. Ist eine Firewall aktiv (`sudo ufw status`), Port freigeben:
  `sudo ufw allow 8001/tcp`.

---

## Frag das Cockpit (Freitext-Fragen mit Claude)

Am rechten Bildschirmrand sitzt die Lasche *Frag das Cockpit*. Ein Klick
schiebt das Fragefeld von rechts herein; ✕, Esc oder ein Klick daneben
schließen es wieder. Man stellt eine Frage in eigenen
Worten, in jeder der zehn Sprachen, und bekommt eine kurze Antwort mit
Tabelle. Beispiele: *„Welche drei Hotels in Kroatien hatten im GJ 2025/26 die
meisten Anfragen?“*, *„Wie steht FUNO gegenüber dem Vorjahr?“*

**So funktioniert es.** Der Container *ask* nimmt die Frage entgegen und
reicht sie an die Claude API weiter. Claude rechnet nicht selbst, sondern
ruft Abfragen auf dem Server auf (`cockpit_query.py`), die exakt wie das
Cockpit rechnen — geprüft gegen die Kacheln des Cockpits. An Anthropic gehen
nur die Frage und die Ergebnisse dieser Abfragen, keine Excel-Dateien,
keine Kundennamen, keine Mail-Adressen. Unter jeder Antwort zeigt
*So wurde gerechnet*, welche Abfragen gelaufen sind.

### Einrichten

1. In der Claude Console (platform.claude.com) einen API-Schlüssel im
   Workspace *SOCCA Cockpit* anlegen.
2. Auf dem Server:

   ```bash
   cd /opt/socca-tools/socca-cockpit
   cp deploy/anthropic.env.vorlage anthropic.env
   chmod 600 anthropic.env
   nano anthropic.env              # ANTHROPIC_API_KEY=sk-ant-… eintragen
   # Läuft der Container nicht als root (siehe .env, COCKPIT_UID):
   # chown <UID>:<GID> anthropic.env
   docker compose up -d --build
   ```

3. Seite neu laden (Strg+F5). Das Fragefeld erscheint, sobald der Container
   *ask* läuft und einen Schlüssel findet. Ohne `anthropic.env` bleibt es
   ausgeblendet; das übrige Cockpit ist davon nicht betroffen.

### Einstellungen in `anthropic.env`

| Zeile | Bedeutung |
|---|---|
| `ASK_MODEL` | `claude-sonnet-5-5` (Standard) oder günstiger `claude-haiku-4-5-20251001` |
| `ASK_DAILY_LIMIT` | Höchstzahl Fragen pro Tag für alle zusammen, Standard 200 |
| `ASK_MAX_TOKENS` | Länge der Antwort, Standard 1500 |
| `ASK_LOG_QUESTIONS` | `ja` schreibt die Fragen ins Protokoll `.state/ask.log` |

Änderungen wirken bei der nächsten Frage, ohne Neustart.

### Kosten und Kontrolle

- Pro Frage meist 2–4 Cent mit Sonnet, etwa die Hälfte mit Haiku.
- `.state/ask.log` zeigt je Frage Dauer, Tokens und — wenn eingeschaltet —
  den Wortlaut. Der Verbrauch in Dollar steht in der Claude Console.
- Das Tageslimit schützt das Budget, auch wenn alle im Netz fragen können.
  Zusätzlich greift das Limit des Workspace in der Console.
- Der Zähler „heute noch … von …“ gilt für alle Kollegen gemeinsam und steht
  in `.state/ask_usage.json`. Die Anzeige holt ihn beim Laden, beim Zurück-
  kehren ins Fenster und alle 2 Minuten vom Server.

### Wenn etwas klemmt

| Beobachtung | Ursache |
|---|---|
| Lasche „Frag das Cockpit“ erscheint nicht | `docker compose ps` — läuft *ask*? `docker compose logs ask` sagt, ob ein Schlüssel gefunden wurde. Rechte: `anthropic.env` muss für den Container-Benutzer lesbar sein |
| „konnte nicht beantwortet werden“ | `tail .state/ask.log` — häufig: Guthaben leer, Schlüssel falsch, Workspace-Limit erreicht, kein Internet (dann `HTTPS_PROXY` in `docker-compose.yml`) |
| „Tageslimit erreicht“ | `ASK_DAILY_LIMIT` erhöhen oder bis morgen warten |
| Zähler springt nach Neustart von *ask* auf das volle Limit | `docker compose logs ask` zeigt eine WARNUNG, wenn `.state` nicht beschreibbar ist — dann `chown -R` auf den Container-Benutzer (`COCKPIT_UID` in `.env`) |

---

## Einrichtung ohne Docker (direkt auf dem Server)

```bash
# 1. Repository ablegen
sudo mkdir -p /srv/socca-cockpit
sudo chown $USER /srv/socca-cockpit
git clone <euer-repo> /srv/socca-cockpit
cd /srv/socca-cockpit

# 2. Python-Umgebung
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Datenquelle: SharePoint-Zugang einrichten (Abschnitt „Dateien direkt
#    aus SharePoint holen“) — oder die Mappen per SFTP nach data/ legen

# 4. Erster Lauf von Hand (dauert ein bis zwei Minuten)
PYTHON=.venv/bin/python ./update.sh --force

# 5. nginx
sudo cp deploy/nginx-socca-cockpit.conf /etc/nginx/sites-available/socca-cockpit
sudo nano /etc/nginx/sites-available/socca-cockpit     # Domain und Pfade anpassen
sudo ln -s ../sites-available/socca-cockpit /etc/nginx/sites-enabled/
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd-cockpit justus   # weitere ohne -c anlegen
sudo nginx -t && sudo systemctl reload nginx

# 6. Zertifikat
sudo certbot --nginx -d cockpit.socca.example

# 7. Cron
crontab -e        # Zeile aus deploy/socca-cockpit.cron übernehmen
```

Wenn `update.sh` aus dem Cron läuft, muss `PYTHON` gesetzt sein, damit die
virtuelle Umgebung genutzt wird:

```cron
7 * * * * PYTHON=/srv/socca-cockpit/.venv/bin/python /srv/socca-cockpit/update.sh >/dev/null 2>&1
```

---

## Dateien direkt aus SharePoint holen (empfohlen)

Der Server meldet sich mit einer **eigenen App-Registrierung** bei Microsoft
365 an — nicht mit deinem Konto — und darf ausschließlich die Site
**SOCCASales lesen**. Vor jedem Lauf fragt `fetch_sharepoint.py` die
Änderungskennung beider Dateien ab (ein kurzer Aufruf). Nur wenn sich eine
Datei geändert hat, wird sie geladen, zuerst in eine Zwischendatei, geprüft
und erst dann in `data/` getauscht. Fällt SharePoint aus, bleibt das Cockpit
auf dem letzten Stand.

Abgeholt werden aus der Bibliothek *Freigegebene Dokumente* der Site
SOCCASales, Hauptordner:

- `Sales.xlsb`
- `C_AP.xlsx`

Achtung: Im Unterordner `Sales_19082025/` liegt eine ältere `Sales.xlsb`.
Deshalb wird der genaue Pfad eingetragen, nicht nach dem Namen gesucht.

Einmalig brauchst du dafür rund 20 Minuten und ein Admin-Konto für
Microsoft 365.

### Schritt 1 — App registrieren

1. [entra.microsoft.com](https://entra.microsoft.com) öffnen, oben in der
   Suche *App-Registrierungen* eingeben, dort *Neue Registrierung*.
2. Name: `SOCCA Cockpit Server`. Unterstützte Kontotypen: *Nur Konten in
   diesem Organisationsverzeichnis*. Umleitungs-URI leer lassen.
   *Registrieren*.
3. Auf der Übersichtsseite notieren:
   - **Anwendungs-ID (Client)** → `SP_CLIENT_ID`
   - **Verzeichnis-ID (Mandant)** → `SP_TENANT_ID`

### Schritt 2 — Geheimen Schlüssel anlegen

1. In der App: *Zertifikate & Geheimnisse → Geheime Clientschlüssel → Neuer
   geheimer Clientschlüssel*.
2. Beschreibung `Linux-Server`, Ablauf **24 Monate**.
3. Die Spalte **Wert** sofort kopieren → `SP_CLIENT_SECRET`. Der Wert wird
   nur dieses eine Mal angezeigt. Nicht die *Geheimnis-ID* nehmen.
4. Ablaufdatum in den Kalender eintragen, mit zwei Wochen Vorlauf. Läuft der
   Schlüssel ab, meldet das Log *„Client-Secret ist abgelaufen“*; dann hier
   einen neuen anlegen und in `sharepoint.env` tauschen.

### Schritt 3 — Berechtigung vergeben

1. In der App: *API-Berechtigungen → Berechtigung hinzufügen → Microsoft
   Graph → Anwendungsberechtigungen*.
2. **Sites.Selected** suchen, anhaken, *Berechtigungen hinzufügen*.
3. *Administratorzustimmung für SOCCA GROUP erteilen* → Ja. Der Status muss
   auf grün *Gewährt* stehen.
4. Die voreingestellte delegierte Berechtigung `User.Read` wird nicht
   gebraucht und kann entfernt werden.

`Sites.Selected` allein erlaubt noch **gar nichts**. Welche Site die App
lesen darf, legt erst Schritt 4 fest.

### Schritt 4 — Die Site SOCCASales für die App freigeben

Das geht im Graph Explorer, angemeldet mit deinem Admin-Konto:

1. [developer.microsoft.com/graph/graph-explorer](https://developer.microsoft.com/graph/graph-explorer)
   öffnen, oben rechts anmelden.
2. Einmalig die Berechtigung erteilen: *Berechtigungen ändern* (bzw. das
   Zahnrad → *Select permissions*), `Sites.FullControl.All` suchen,
   *Zustimmen*.
3. Site-ID abfragen — Methode **GET**, Adresse:

   ```
   https://graph.microsoft.com/v1.0/sites/socca.sharepoint.com:/sites/SOCCASales
   ```

   *Abfrage ausführen*. Aus der Antwort den Wert von `"id"` kopieren
   (Form `socca.sharepoint.com,xxxxxxxx-…,yyyyyyyy-…`).
4. Freigabe setzen — Methode **POST**, Adresse (ID einsetzen):

   ```
   https://graph.microsoft.com/v1.0/sites/<SITE-ID>/permissions
   ```

   Anforderungstext (Client-ID aus Schritt 1 einsetzen):

   ```json
   {
     "roles": ["read"],
     "grantedToIdentities": [
       { "application": { "id": "<SP_CLIENT_ID>", "displayName": "SOCCA Cockpit Server" } }
     ]
   }
   ```

   *Abfrage ausführen*. Antwort **201 Created** heißt: fertig.
5. Zur Kontrolle dieselbe Adresse mit **GET** — die App muss mit Rolle
   `read` in der Liste stehen.
6. Die Zustimmung für den Graph Explorer (`Sites.FullControl.All`) kannst du
   danach unter *Enterprise-Anwendungen → Graph Explorer → Berechtigungen*
   wieder entziehen.

**Einfachere, aber breitere Alternative:** In Schritt 3 statt
`Sites.Selected` die Berechtigung `Sites.Read.All` nehmen und Schritt 4
auslassen. Dann darf die App **alle** SharePoint-Sites der SOCCA GROUP lesen —
funktioniert sofort, gibt aber mehr frei als nötig. Nur mit dieser
Berechtigung lassen sich statt der Pfade auch Freigabelinks in
`sharepoint.env` eintragen.

### Schritt 5 — Server einrichten

```bash
cd /srv/socca-cockpit
cp deploy/sharepoint.env.vorlage sharepoint.env
chmod 600 sharepoint.env
nano sharepoint.env        # SP_TENANT_ID, SP_CLIENT_ID, SP_CLIENT_SECRET eintragen
```

Site, Bibliothek und Dateipfade sind in der Vorlage schon richtig gesetzt.
`sharepoint.env` enthält den geheimen Schlüssel und ist über `.gitignore` vom
Repository ausgeschlossen.

Verbindung testen, ohne etwas zu laden:

```bash
.venv/bin/python fetch_sharepoint.py --check
```

Erwartete Ausgabe:

```
Site: SOCCA Sales · Bibliothek: Freigegebene Dokumente
SALES   Sales.xlsb  27.7 MB  geändert 25.09.2026 16:41 von Justus Wenzel  · würde geladen
CAP     C_AP.xlsx  …   MB  geändert …                von …              · würde geladen
```

Dann der erste echte Lauf:

```bash
PYTHON=.venv/bin/python ./update.sh --force
tail -20 .state/update.log
```

Mit Docker lauten die beiden Befehle:

```bash
docker compose exec worker python3 fetch_sharepoint.py --check
docker compose exec worker bash update.sh --force
```

Ab jetzt erledigt der Cron alles. Sobald `sharepoint.env` existiert, holt
`update.sh` die Dateien aus SharePoint und ignoriert, was sonst in `data/`
liegt. Umbenennen oder Löschen von `sharepoint.env` schaltet zurück auf den
Weg über `data/`.

Der Server braucht ausgehend HTTPS zu `login.microsoftonline.com`,
`graph.microsoft.com` und `*.sharepoint.com`. Steht er hinter einem Proxy,
genügt die Umgebungsvariable `HTTPS_PROXY` in der Cron-Zeile.

### Wie aktuell ist das Cockpit?

Excel speichert auf SharePoint automatisch. Der Cron schaut stündlich nach,
also ist das Cockpit höchstens eine Stunde plus zwei Minuten Rechenzeit
hinter der Mappe. Wer es schneller will, stellt die Cron-Zeile auf
`*/15 * * * *` — die Nachfrage kostet nur Millisekunden, gerechnet wird nur
bei Änderung.

### Wenn der Abruf klemmt

`fetch_sharepoint.py` übersetzt die häufigen Fehler in Klartext, im Log und
bei `--check`:

| Meldung | Ursache |
|---|---|
| *Client-Secret ist falsch* | Die Secret-ID statt des Werts eingetragen, oder Tippfehler |
| *Client-Secret ist abgelaufen* | Schritt 2 wiederholen |
| *App … nicht gefunden* | Client-ID oder Tenant-ID vertauscht |
| *Kein Zugriff auf die Site* | Schritt 4 fehlt, oder die Administratorzustimmung aus Schritt 3 |
| *„Sales.xlsb“ nicht gefunden …* | Datei umbenannt oder verschoben; die Meldung listet, was im Ordner liegt |
| *… Bytes geladen, erwartet …* | Download abgebrochen; die alte Datei bleibt, der nächste Lauf versucht es neu |

---

## Ohne SharePoint: Dateien per SFTP ablegen

Welche Namen und Formate `update.sh` findet, steht oben unter *Zuerst: mit
den aktuellen Dateien starten*. Kurz: Name enthält `Sales` bzw. `C_AP`, die
jüngste Datei gewinnt.

Drei Wege, die Dateien dorthin zu bekommen:

**WinSCP mit Ordnerüberwachung.** Der bequemste Weg unter Windows. In WinSCP
eine Sitzung zum Server öffnen, dann *Befehle → Verzeichnisse laufend
abgleichen*, lokal den Ordner wählen, in dem du die beiden Mappen speicherst,
als Ziel `/srv/socca-cockpit/data`. Ab dann lädt WinSCP jede Speicherung
automatisch hoch. Du arbeitest wie bisher in Excel, der Rest passiert von
selbst.

**scp von Hand.** Wenn du lieber bewusst auslöst:

```bash
scp Sales.xlsx C_AP.xlsx user@server:/srv/socca-cockpit/data/
```

**rsync über eine Aufgabe.** Wenn die Mappen ohnehin auf einem Netzlaufwerk
liegen, das der Server erreicht.

`update.sh` wartet, bis eine Datei mindestens 60 Sekunden unverändert ist.
Damit wird kein halb übertragener Stand gelesen.

---

## Was wann passiert

| Auslöser | Wirkung |
|---|---|
| Datei unverändert | Lauf endet nach Millisekunden, nichts wird gebaut |
| Datei neu | ETL und Build laufen, rund zwei Minuten, dann ist die Seite aktuell |
| Zwei Läufe gleichzeitig | Der zweite bricht ab, eine Sperrdatei verhindert Überschneidungen |
| ETL bricht ab | Die alte Seite bleibt stehen, der Fehler steht in `.state/update.log` |

Die Seite wird erst am Ende ausgetauscht. Ein fehlgeschlagener Lauf hinterlässt
nie eine halb fertige Seite.

---

## Arbeiten mit Cursor und GitHub

Ins Repository gehört der Code, **nicht die Daten**. Die `.gitignore` sorgt
dafür: `data/`, `web/` und `.state/` bleiben draußen. Die Mappe enthält
Umsätze, Margen und Personalstände — die haben auf GitHub nichts verloren,
auch nicht in einem privaten Repository.

Erstmals ins Repository bringen (lokal, im entpackten Ordner):

```bash
git init -b main
git add .
git status            # prüfen: nichts aus data/ oder web/ dabei
git update-index --chmod=+x update.sh fetch_sharepoint.py   # unter Windows nötig
git commit -m "SOCCA Sales Cockpit"
git remote add origin git@github.com:<organisation>/socca-cockpit.git   # privates Repo
git push -u origin main
```

Der Kreislauf:

```
Cursor (lokal)  →  git push  →  Server: git pull  →  ./update.sh --force
```

Zum lokalen Ausprobieren brauchst du nur eine Kopie der beiden Mappen in
`data/`:

```bash
./update.sh --force
cd web && python3 -m http.server 8000
# http://localhost:8000
```

Wichtig: Die Seite muss über einen Webserver laufen, nicht per Doppelklick.
Sonst blockiert der Browser das Nachladen von `data.json`. Für den Versand
per Mail oder die Ablage auf SharePoint erzeugt `build.py` zusätzlich
`SOCCA_Sales_Cockpit.html` mit eingebetteten Daten — eine einzige Datei, die
auch per Doppelklick funktioniert.

---

## Reports für die Status-Meetings

Oben rechts schaltet *Reports* vom Cockpit in die Berichtsansicht. Drei Berichte,
jeweils für einen frei wählbaren Monat:

| Bericht | Inhalt | Umfang im Druck |
|---|---|---|
| Monatsvergleich | Alle Teams nebeneinander, Monat gegen Vorjahresmonat, AP und Δ — wie die bisherige Excel-Übersicht | 1 Seite |
| Team Status Report | Ein Team, Monat / 3 Monate / 12 Monate gegen Vorjahr mit Trend — wie Blatt *Report* | 2 Seiten je Team |
| Country Status Report | Ein Zielland, gleiche Zeitfenster — Standard sind ES, I, HR, CZ, A, HU, TR, CH, NL | 2 Seiten je Land |

**Präsentieren** öffnet den Bericht bildschirmfüllend. Die Pfeiltasten blättern
durch alle Teams, alle Länder oder beim Monatsvergleich durch die Monate, *Esc*
beendet. **Drucken / PDF** druckt den aktuellen Bericht, **Alle drucken** das
komplette Meeting-Paket — 16 TSR oder 9 CSR in einem Durchgang, A4 quer. Im
Druckdialog als Ziel *Als PDF speichern* wählen, dann entsteht das PDF.

Läuft das Cockpit in einer abgeschotteten Vorschau (Artefakt auf claude.ai,
Dateivorschau in Chat oder Mail-Programm), sperrt der Browser den
Druckdialog. Das Cockpit merkt das und gibt den Bericht stattdessen als
druckfertige HTML-Datei aus — als Download bzw. in einem neuen Tab. Beim
Öffnen startet der Druckdialog von selbst. Auf dem Server und in der
heruntergeladenen `SOCCA_Sales_Cockpit.html` öffnet sich der Dialog direkt.

Mit ★ markierte Kennzahlen und Abschnitte sind neu gegenüber dem Excel-Report.

### AP für Anfragen

Das Cockpit berechnet die geplanten Unique Anfragen je Team und Monat selbst,
nach derselben Regel wie das Blatt *AP* der Mappe:

> AP-Anfragen im Monat = AP-Teams des **Folgemonats** (Blatt *Goals*) ÷ Quote
> des Folgemonats im **Vorjahr**
> Quote (im Blatt *AP* „BuQ“) = Teams im Monat ÷ Unique Anfragen („einfach“)
> im Vormonat

**Fest eingetragene Quoten.** Steht in der Tabelle *BuQ (Bu/Leads) JJJJ/JJ*
im Blatt *AP* statt einer Formel ein von Hand eingetragener Wert (heute bei
FUNL, für Teams mit wenig oder ohne Vorjahr), nimmt das Cockpit für diesen
Team-Monat genau diesen Wert — für den AP-Zeitraum, auf den die Tabelle
zielt (Quote 2025/26 → AP 2026/27). Alle Zellen mit Formel rechnet das
Cockpit selbst. Die geplanten Teams kommen immer aus *Goals*, nicht aus
Spalte C des Blattes *AP*.

Anfragen kommen rund einen Monat vor der Buchung. Für Juni gilt der Juli
desselben AP-Zeitraums. Ohne geplante oder stattgefundene Buchungen gibt es
keine AP-Anfragen. Gegen das Blatt *AP* geprüft: FUSU 2026/27, alle zwölf
Monate identisch (Summe 891).

Die AP-Anfragen erscheinen in der Kachel *Unique Anfragen*, in den Vergleichs-
panels, im Verlauf, im Monatsvergleich, im Team Status Report und im
Fragefeld — je Team und Zeitraum. Bei Länder- oder Regionsfiltern bleiben
sie leer, weil es den Plan nur je Team gibt.

**Ganze Monate.** Das Cockpit zählt die Anfragen immer über alle Tage des
Monats. Die Formeln im Blatt *AP* vergleichen das Anfragedatum (mit Uhrzeit)
mit „<=31.MM.JJJJ“ bzw. „<=30.“ und verlieren dadurch die Anfragen vom
letzten Tag des Monats — korrigiert wird das mit „<“ und dem Ersten des
Folgemonats. Nur zum Abgleich mit einer noch nicht korrigierten Mappe lässt
sich das alte Verhalten mit `AP_LEADS_WIE_EXCEL: "1"` beim *worker* in
`docker-compose.yml` nachbilden.

Eine Datei `data/AP_Leads.csv` (Team;Monat;Leads, Vorlage in `deploy/`)
überschreibt einzelne berechnete Werte, etwa für manuell gesetzte Ziele.

## Sprachen

Das Cockpit spricht Deutsch, Englisch, Niederländisch, Spanisch, Italienisch,
Kroatisch, Tschechisch, Norwegisch, Türkisch und Ungarisch. Die Auswahl sitzt oben rechts
und wird im Browser gemerkt; beim ersten Aufruf richtet sie sich nach der
Spracheinstellung des Browsers.

Zahlen, Datumsangaben, Monatskürzel und Ländernamen kommen aus der
Intl-Schnittstelle des Browsers und passen sich automatisch an. Regionsnamen
bleiben als Eigennamen stehen — Bayern heißt auch auf Kroatisch Bayern.
Unübersetzt bleiben außerdem Team, Pax, FTE, ROS, WebID, Annual Planning und
die Blattnamen der Arbeitsmappe.

Übersetzungen werden in `i18n/make_i18n.py` geändert, Englisch in
`i18n/en.py` — nicht in `i18n.js`:

```bash
python3 i18n/make_i18n.py > i18n.js
./update.sh --force
```

Die Datei meldet beim Lauf, wenn für einen Schlüssel eine Sprache fehlt; dort
greift dann Deutsch.

## Die Teile

| Datei | Aufgabe |
|---|---|
| `etl.py` | Liest Mappe und Combit-Export, schreibt `data.json` |
| `build.py` | Setzt Vorlage, Kartengeometrie und Daten zur fertigen Seite zusammen |
| `dashboard.tpl.html` | Die Oberfläche — Struktur, Stil und die gesamte Auswertungslogik |
| `geo/geo.js` | Kartengeometrie als SVG-Pfade, fertig gebaut |
| `i18n.js` | Oberflächentexte in zehn Sprachen, fertig gebaut |
| `i18n/en.py` | Englische Texte, werden von `make_i18n.py` eingelesen |
| `i18n/make_i18n.py` | Erzeugt `i18n.js` neu — hier werden Übersetzungen geändert |
| `geo/make_geo.py` | Erzeugt `geo.js` neu, falls der Kartenausschnitt geändert wird |
| `update.sh` | Der Wächter: prüft auf Änderung, baut, protokolliert |
| `fetch_sharepoint.py` | Holt die Mappen aus SharePoint, nur bei Änderung |
| `deploy/sharepoint.env.vorlage` | Vorlage für den SharePoint-Zugang (`sharepoint.env`) |
| `docker-compose.yml` | Betrieb mit Docker: Container *worker*, *ask* und *web* |
| `ask_server.py` | Frage-Server für „Frag das Cockpit“, spricht mit der Claude API |
| `cockpit_query.py` | Rechnet die Kennzahlen für Claude — gleiche Definitionen wie das Cockpit |
| `deploy/anthropic.env.vorlage` | Vorlage für den API-Schlüssel (`anthropic.env`) |
| `deploy/docker/` | Dockerfile, Startskript des Workers, nginx-Konfiguration |
| `reports.js` | Monatsvergleich, Team und Country Status Report |
| `deploy/AP_Leads.vorlage.csv` | Vorlage für die optionale Plandatei der Leads |

---

## Was aus welcher Quelle kommt

Die vollständigen Definitionen stehen im Dashboard selbst unter
*Definitionen und Datenherkunft*. Das Wichtigste:

- Stichtag aller Umsatz- und DB-Kennzahlen ist das **Buchungsdatum**, nicht
  das Reisedatum.
- **DB** ist die Spalte `MargIn`, also VK minus EK.
- **Teams** ist eine eigene Zählgröße neben Buchungen — eine Buchung kann
  mehrere Teams enthalten.
- **Unique Anfragen** zählen eine Mail-Adresse einmal je Sales-Team und
  AP-Jahr. **Anfragen gesamt** zählen jede Anfrage-Zeile in C_AP, ohne
  Unique-Regel — erst ab 01/2024.
- **Unique Anfragen und Angebote** kommen ab 2024 aus Combit, davor aus den Blättern
  `Leads` und `Props` der Mappe und dort nur monatsgenau.
- **FTE und Annual Planning** liegen nur je Team vor. Bei gesetztem Länder-
  oder Regionsfilter bleiben sie und alles daraus Abgeleitete leer.
- Die **Region** aus Spalte H gibt es nur für Buchungen; Combit führt kein
  Bundesland.
- **Buchungsquote** = Buchungen ÷ Unique Anfragen, je Team und je Hotel,
  mit Vorjahr. **Abschlussquote** = Buchungen ÷ Angebote.
- **Buchungs- / Erfassungszeitraum** (oben, durchgehender Rahmen): Buchungen
  nach Buchungsdatum (Sales Spalte C), Anfragen nach Anfragedatum, Angebote
  nach Versanddatum (C_AP). Er endet höchstens heute.
- **Reisezeitraum (Anreise)** (gestrichelter Rahmen, aktiv farbig): optionaler
  zweiter Filter auf die Anreise über Von/Bis — Sales Spalte B, C_AP
  Startdatum. „Alle Anreisen“ hebt ihn auf. Ohne Auswahl zählen alle Anreisen; gesetzt zählt nur, was im Buchungs-/
  Erfassungszeitraum gebucht bzw. erfasst wurde UND im Reisezeitraum anreist.
  Annual Planning und FTE werden dann ausgeblendet (sie gelten je
  Buchungsmonat), Anfragen vor 2024 haben kein Anreisedatum.
- Die **Schnellauswahl** (nur Buchungs-/Erfassungszeitraum) rechnet ab heute:
  *Laufender Monat* (Standard beim Start), *3 Monate* und *12 Monate*
  taggenau zurück (am 02.10.2026: 03.07.–02.10. bzw. 03.10.2025–02.10.2026),
  *Geschäftsjahr*, *Kalenderjahr*.
- **Annual Planning** zählt angebrochene Monate tagesanteilig und höchstens
  bis heute (Teams und AP-Anfragen). Das Vorjahr endet entsprechend heute vor
  einem Jahr.
- Im **Team und Country Status Report** zeigen die Detailtabellen
  (Reiseländer, Sportarten, Teams, Kundenherkunft, Hotels) standardmäßig den
  Berichtsmonat; *Zeitraum der Tabellen* schaltet
  auf die letzten 3 oder 12 Monate bis einschließlich Berichtsmonat um.
- Der **Hotelblick** folgt den Filtern für Bereich, Team und Reiseland.
- **Unique Anfragen und Angebote je Hotel** gibt es je Team und je Reiseland (Land
  des Hotels), nicht je Kundenherkunft oder Region. Eine Anfrage zählt bei
  jedem Hotel, das der Kunde angefragt hat.

Neun von zehn Kennzahlen wurden gegen das Blatt `Report` der Mappe
nachgerechnet und stimmen auf den Cent. Einzige Ausnahme ist
*Marge/Pax/Nacht*, dessen Berechnung im Report noch ungeklärt ist.

---

## Wenn etwas klemmt

**Seite zeigt „Daten nicht erreichbar".** `data.json` liegt nicht neben
`index.html`, oder die Seite wurde per Doppelklick geöffnet statt über den
Webserver.

**Kennzahlen sind leer, obwohl Daten da sind.** Die Mappe wurde zuletzt von
einem Werkzeug ohne Wert-Cache gespeichert. Einmal in Excel öffnen, speichern,
neu hochladen.

**Cockpit zeigt noch den alten Stand.** Im Log nachsehen, welche Datei
verarbeitet wurde (`Neuberechnung: …`). Häufigste Ursachen: eine ältere
Datei in `data/` ist jünger datiert als die neue; die neue Datei ist noch
keine 60 Sekunden alt (`übersprungen: …`); der Browser zeigt eine
zwischengespeicherte Seite (Strg+F5).

**Drucken / PDF tut nichts.** Pop-up- oder Download-Sperre des Browsers für
die Seite aufheben — das Cockpit braucht sie nur in abgeschotteten Vorschauen.

**Blatt fehlt.** Das ETL nennt die tatsächlich vorhandenen Blattnamen. Es
braucht `Sales`, `FTE`, `Leads`, `Props`, `Goals` und `Locations`.

**Lauf dauert ewig.** Als `.xlsb` braucht das Einlesen rund zwei Minuten. Als
`.xlsx` geht es meist schneller. Der Cron stört das nicht, weil bei
unveränderten Dateien gar nichts passiert.

**Protokoll.** `.state/update.log` enthält jeden Lauf mit Zeitstempel,
Zeilenzahlen und Dauer.
