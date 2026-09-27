#!/usr/bin/env bash
# SOCCA Sales Cockpit — Neuberechnung
#
# Prüft, ob sich die Sales-Mappe oder der Combit-Export (C_AP) seit dem letzten Lauf geändert
# haben, und baut nur dann neu. Gedacht für einen stündlichen Cronlauf.
#
#   ./update.sh          nur bei Änderung neu bauen
#   ./update.sh --force  in jedem Fall neu bauen
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

DATA="$ROOT/data"
WEB="$ROOT/web"
STATE="$ROOT/.state"
LOG="$STATE/update.log"
PYTHON="${PYTHON:-python3}"
MIN_AGE=60        # Sekunden, die eine Datei unverändert sein muss

mkdir -p "$STATE" "$WEB"
exec 9>"$STATE/lock"
if ! flock -n 9; then
  echo "$(date -Is)  Lauf übersprungen, es läuft bereits einer" >>"$LOG"
  exit 0
fi

log(){ echo "$(date -Is)  $*" | tee -a "$LOG"; }

# Eingabedateien finden. Gesucht wird in data/ nach
#   Sales:  *Sales*.xlsx | .xlsm | .xlsb      z. B. Sales.xlsx, 20260930_Sales.xlsb
#   Combit: *C_AP*.xlsx  | .csv               z. B. C_AP.xlsx, 20260930_C_AP.csv
# Liegen mehrere passende Dateien dort, gewinnt die zuletzt geänderte.
# Excel-Sperrdateien (~$...) werden übergangen.
# newest DATEIEN… → gibt die jüngste gültige Datei aus, setzt COUNT
newest(){
  local best="" f; COUNT=0
  for f in "$@"; do
    [ -f "$f" ] || continue
    case "$(basename "$f")" in '~$'*|.*) continue;; esac
    COUNT=$((COUNT+1))
    if [ -z "$best" ] || [ "$f" -nt "$best" ]; then best="$f"; fi
  done
  PICK="$best"
}
shopt -s nullglob nocaseglob
newest "$DATA"/*Sales*.xlsx "$DATA"/*Sales*.xlsm "$DATA"/*Sales*.xlsb; XLS="$PICK"; NXLS=$COUNT
newest "$DATA"/*C_AP*.xlsx "$DATA"/*C_AP*.csv;                         CAP="$PICK"; NCAP=$COUNT
shopt -u nullglob nocaseglob
[ -n "$XLS" ] || { log "FEHLER: keine Sales-Mappe in $DATA"; exit 1; }
[ -n "$CAP" ] || { log "FEHLER: kein Combit-Export (C_AP) in $DATA"; exit 1; }
[ "$NXLS" -gt 1 ] && log "Hinweis: $NXLS Sales-Dateien in data/, verwendet wird die neueste: $(basename "$XLS")"
[ "$NCAP" -gt 1 ] && log "Hinweis: $NCAP C_AP-Dateien in data/, verwendet wird die neueste: $(basename "$CAP")"

# Frisch hochgeladene Dateien kurz liegen lassen, damit kein halb
# übertragener Stand gelesen wird.
now=$(date +%s)
for f in "$XLS" "$CAP"; do
  age=$(( now - $(stat -c %Y "$f") ))
  if [ "$age" -lt "$MIN_AGE" ]; then
    log "übersprungen: $(basename "$f") ist erst ${age}s alt"; exit 0
  fi
done

APL="$DATA/AP_Leads.csv"
[ -f "$APL" ] || APL=""
SUM=$(sha256sum "$XLS" "$CAP" $APL | sha256sum | cut -d' ' -f1)
PREV=$(cat "$STATE/last.sha" 2>/dev/null || echo "")

if [ "${1:-}" != "--force" ] && [ "$SUM" = "$PREV" ]; then
  exit 0
fi

log "Neuberechnung: $(basename "$XLS") ($(date -r "$XLS" "+%d.%m.%Y %H:%M")) + $(basename "$CAP") ($(date -r "$CAP" "+%d.%m.%Y %H:%M"))"
START=$(date +%s)

TMP="$STATE/data.json"
"$PYTHON" etl.py "$XLS" "$CAP" "$TMP" $APL   >>"$LOG" 2>&1
"$PYTHON" build.py "$TMP" "$WEB"             >>"$LOG" 2>&1

echo "$SUM" > "$STATE/last.sha"
date -Is  > "$WEB/.built"
log "fertig in $(( $(date +%s) - START ))s — $(du -h "$WEB/data.json" | cut -f1)"
