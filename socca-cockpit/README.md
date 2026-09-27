# SOCCA Sales Cockpit

Eigenständiges Tool im Repository **SOCCA-Tools**, Ordner `socca-cockpit/`. Eigene Python-Umgebung, eigener Webserver, eigener Cron. Nicht Teil von Rechnungs-Upload oder Hotel-Bildbearbeitung.

Interaktives Vertriebs-Dashboard der SOCCA GROUP. Liest die Sales-Arbeitsmappe
und den Combit-Export, rechnet daraus einen kompakten Datensatz und baut eine
statische HTML-Seite.

Kein Server-Framework, keine Datenbank, kein Kartendienst. Die fertige Seite
besteht aus zwei Dateien — `index.html` und `data.json` — und läuft auf jedem
Webserver, der statische Dateien ausliefert.

---

## Der Ablauf in einem Satz

Du legst `Sales.xlsx` und `C_AP.xlsx` in `data/`, ein stündlicher Cronlauf
merkt die Änderung und baut die Seite neu.

---

## Zuerst: mit den aktuellen Dateien starten

Das Paket enthält **keine Daten**. Das Cockpit, das du bisher gesehen hast
(Artefakt auf claude.ai, `SOCCA_Sales_Cockpit.html`, Beispiel-PDFs), wurde aus
`20260831_Sales.xlsb` und einem Combit-Export als CSV gerechnet — Stand
31.08.2026. Mit deinen aktuellen Dateien gehst du so vor:

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
cd /srv/socca-tools/socca-cockpit
PYTHON=.venv/bin/python ./update.sh --force
```

Lokal unter Windows im Ordner `socca-cockpit` (PowerShell) — ohne `update.sh`:

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

## Einmalige Einrichtung auf dem Server

```bash
# 1. SOCCA-Tools ablegen, dann in dieses Tool wechseln
sudo mkdir -p /srv/socca-tools
sudo chown $USER /srv/socca-tools
git clone git@github.com:SOCCA-AI-Admin/SOCCA-Tools.git /srv/socca-tools
cd /srv/socca-tools/socca-cockpit

# 2. Python-Umgebung
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Erster Lauf von Hand (dauert ein bis zwei Minuten)
PYTHON=.venv/bin/python ./update.sh --force

# 4. nginx
sudo cp deploy/nginx-socca-cockpit.conf /etc/nginx/sites-available/socca-cockpit
sudo nano /etc/nginx/sites-available/socca-cockpit     # Domain und Pfade anpassen
sudo ln -s ../sites-available/socca-cockpit /etc/nginx/sites-enabled/
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd-cockpit justus   # weitere ohne -c anlegen
sudo nginx -t && sudo systemctl reload nginx

# 5. Zertifikat
sudo certbot --nginx -d cockpit.socca.example

# 6. Cron
crontab -e        # Zeile aus deploy/socca-cockpit.cron übernehmen
```

Wenn `update.sh` aus dem Cron läuft, muss `PYTHON` gesetzt sein, damit die
virtuelle Umgebung genutzt wird:

```cron
7 * * * * PYTHON=/srv/socca-tools/socca-cockpit/.venv/bin/python /srv/socca-tools/socca-cockpit/update.sh >/dev/null 2>&1
```

---

## Die Dateien aktuell halten

Welche Namen und Formate `update.sh` findet, steht oben unter *Zuerst: mit
den aktuellen Dateien starten*. Kurz: Name enthält `Sales` bzw. `C_AP`, die
jüngste Datei gewinnt.

Drei Wege, die Dateien dorthin zu bekommen:

**WinSCP mit Ordnerüberwachung.** Der bequemste Weg unter Windows. In WinSCP
eine Sitzung zum Server öffnen, dann *Befehle → Verzeichnisse laufend
abgleichen*, lokal den Ordner wählen, in dem du die beiden Mappen speicherst,
als Ziel `/srv/socca-tools/socca-cockpit/data`. Ab dann lädt WinSCP jede Speicherung
automatisch hoch. Du arbeitest wie bisher in Excel, der Rest passiert von
selbst.

**scp von Hand.** Wenn du lieber bewusst auslöst:

```bash
scp Sales.xlsx C_AP.xlsx user@server:/srv/socca-tools/socca-cockpit/data/
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

Das Cockpit ist kein eigenes Repository. Es liegt als Ordner `socca-cockpit/`
in **SOCCA-Tools** (`git@github.com:SOCCA-AI-Admin/SOCCA-Tools.git`).
Gearbeitet wird in diesem Ordner; Commit und Push kommen aus der
Repository-Wurzel.

Ins Repository gehört der Code, **nicht die Daten**. Die `.gitignore` in
diesem Ordner sorgt dafür: `data/`, `web/` und `.state/` bleiben draußen.
Die Mappe enthält Umsätze, Margen und Personalstände — die haben auf GitHub
nichts verloren, auch nicht in einem privaten Repository.

```bash
# in der Wurzel von SOCCA-Tools
git status            # prüfen: nichts aus socca-cockpit/data/ oder socca-cockpit/web/
git add socca-cockpit
git commit -m "SOCCA Sales Cockpit als eigenes Tool"
git push
```

Der Kreislauf:

```
Cursor (lokal, Ordner socca-cockpit)  →  git push  →  Server: git pull  →  ./update.sh --force
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
| Country Status Report | Ein Zielland, gleiche Zeitfenster — Standard sind ES, I, HR, CZ, A, HU, TR | 2 Seiten je Land |

**Präsentieren** öffnet den Bericht bildschirmfüllend. Die Pfeiltasten blättern
durch alle Teams, alle Länder oder beim Monatsvergleich durch die Monate, *Esc*
beendet. **Drucken / PDF** druckt den aktuellen Bericht, **Alle drucken** das
komplette Meeting-Paket — 16 TSR oder 7 CSR in einem Durchgang, A4 quer. Im
Druckdialog als Ziel *Als PDF speichern* wählen, dann entsteht das PDF.

Läuft das Cockpit in einer abgeschotteten Vorschau (Artefakt auf claude.ai,
Dateivorschau in Chat oder Mail-Programm), sperrt der Browser den
Druckdialog. Das Cockpit merkt das und gibt den Bericht stattdessen als
druckfertige HTML-Datei aus — als Download bzw. in einem neuen Tab. Beim
Öffnen startet der Druckdialog von selbst. Auf dem Server und in der
heruntergeladenen `SOCCA_Sales_Cockpit.html` öffnet sich der Dialog direkt.

Mit ★ markierte Kennzahlen und Abschnitte sind neu gegenüber dem Excel-Report.

### AP für Leads

Die Mappe führt Annual Planning nur für Teams. Die Spalten *LeadsAP* im Blatt
*AP* sind leer, deshalb fehlt im Monatsvergleich die AP-Zeile bei den Leads.
Sie erscheint, sobald `data/AP_Leads.csv` existiert — Aufbau siehe
`deploy/AP_Leads.vorlage.csv`, einmal im Jahr für das neue Geschäftsjahr pflegen.

## Sprachen

Das Cockpit spricht Deutsch, Niederländisch, Spanisch, Italienisch, Kroatisch,
Tschechisch, Norwegisch, Türkisch und Ungarisch. Die Auswahl sitzt oben rechts
und wird im Browser gemerkt; beim ersten Aufruf richtet sie sich nach der
Spracheinstellung des Browsers.

Zahlen, Datumsangaben, Monatskürzel und Ländernamen kommen aus der
Intl-Schnittstelle des Browsers und passen sich automatisch an. Regionsnamen
bleiben als Eigennamen stehen — Bayern heißt auch auf Kroatisch Bayern.
Unübersetzt bleiben außerdem Team, Pax, FTE, ROS, WebID, Annual Planning und
die Blattnamen der Arbeitsmappe.

Übersetzungen werden in `i18n/make_i18n.py` geändert, nicht in `i18n.js`:

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
| `i18n.js` | Oberflächentexte in neun Sprachen, fertig gebaut |
| `i18n/make_i18n.py` | Erzeugt `i18n.js` neu — hier werden Übersetzungen geändert |
| `geo/make_geo.py` | Erzeugt `geo.js` neu, falls der Kartenausschnitt geändert wird |
| `update.sh` | Der Wächter: prüft auf Änderung, baut, protokolliert |
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
- **Anfragen und Angebote** kommen ab 2024 aus Combit, davor aus den Blättern
  `Leads` und `Props` der Mappe und dort nur monatsgenau.
- **FTE und Annual Planning** liegen nur je Team vor. Bei gesetztem Länder-
  oder Regionsfilter bleiben sie und alles daraus Abgeleitete leer.
- Die **Region** aus Spalte H gibt es nur für Buchungen; Combit führt kein
  Bundesland.

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
