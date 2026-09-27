#!/usr/bin/env bash
# Läuft im Container "worker": prüft alle $INTERVAL Sekunden, ob sich die
# Mappen geändert haben, und rechnet nur dann neu (update.sh entscheidet).
set -u
cd /app
INTERVAL="${INTERVAL:-900}"
mkdir -p web .state data

# Platzhalter, bis der erste Lauf fertig ist
if [ ! -f web/index.html ]; then
  cat > web/index.html <<'HTML'
<!doctype html><html lang="de"><meta charset="utf-8"><meta http-equiv="refresh" content="30">
<title>SOCCA Sales Cockpit</title>
<body style="font:16px system-ui,sans-serif;margin:15vh auto;max-width:560px;color:#414141">
<h1 style="font-size:22px">SOCCA Sales Cockpit wird aufgebaut …</h1>
<p>Der erste Lauf dauert zwei bis drei Minuten. Die Seite lädt sich von selbst neu.</p>
<p style="color:#6f6f6f;font-size:14px">Bleibt es dabei: <code>docker compose logs worker</code> auf dem Server ansehen.</p>
</body></html>
HTML
fi

if [ -f sharepoint.env ]; then SRC="SharePoint (sharepoint.env)"; else SRC="Ordner data/"; fi
echo "SOCCA Cockpit: Quelle $SRC, Prüfung alle ${INTERVAL}s"

while true; do
  bash /app/update.sh || echo "$(date -Is)  update.sh meldet einen Fehler — Details in .state/update.log"
  sleep "$INTERVAL"
done
