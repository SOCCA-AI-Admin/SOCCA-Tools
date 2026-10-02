#!/usr/bin/env python3
"""Frage-Server für das SOCCA Sales Cockpit.

Nimmt Freitext-Fragen entgegen, lässt Claude über die Anthropic-API
antworten und gibt Claude dafür Werkzeuge, die direkt auf web/data.json
rechnen (cockpit_query.py). Claude sieht nur die Frage und die Ergebnisse
dieser Abfragen — nie die Excel-Dateien, nie Namen oder Mail-Adressen.

    python3 ask_server.py            startet auf Port 8080 (ASK_PORT)

Konfiguration in anthropic.env (Vorlage: deploy/anthropic.env.vorlage).
Nur Standardbibliothek.

Endpunkte (nginx leitet /api/ hierher weiter):
    GET  /api/status   {enabled, remaining, limit, model}
    POST /api/ask      {question, lang}  →  {answer, steps, remaining}
"""
import datetime
import json
import os
import pathlib
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cockpit_query as cq

ROOT = pathlib.Path(__file__).resolve().parent
ENV_FILE = pathlib.Path(os.environ.get('ASK_ENV', ROOT / 'anthropic.env'))
STATE = ROOT / '.state'
USAGE_FILE = STATE / 'ask_usage.json'
LOG_FILE = STATE / 'ask.log'
DATA_FILE = ROOT / 'web' / 'data.json'

API_URL = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com') + '/v1/messages'
MAX_ROUNDS = 8                 # Werkzeugrunden je Frage
MAX_QUESTION = 600             # Zeichen

LANG_NAMES = {'de': 'Deutsch', 'nl': 'Niederländisch', 'es': 'Spanisch', 'it': 'Italienisch',
              'hr': 'Kroatisch', 'cs': 'Tschechisch', 'nb': 'Norwegisch (Bokmål)',
              'tr': 'Türkisch', 'hu': 'Ungarisch'}


def load_env():
    cfg = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in '"\'':
                v = v[1:-1]
            cfg[k.strip()] = v
    return {
        'key': cfg.get('ANTHROPIC_API_KEY', os.environ.get('ANTHROPIC_API_KEY', '')).strip(),
        'model': cfg.get('ASK_MODEL', 'claude-sonnet-5-5').strip() or 'claude-sonnet-5-5',
        'limit': int(cfg.get('ASK_DAILY_LIMIT', '200') or 200),
        'max_tokens': int(cfg.get('ASK_MAX_TOKENS', '1500') or 1500),
        'log_questions': cfg.get('ASK_LOG_QUESTIONS', 'ja').strip().lower() in ('ja', 'yes', '1', 'true'),
    }


# ------------------------------------------------------------- Tageslimit
# Der Zähler liegt in .state/ask_usage.json und gilt für alle Nutzer
# gemeinsam. Kann die Datei nicht geschrieben werden (z. B. falsche Rechte
# auf .state), zählt der Server im Speicher weiter und meldet das im Log —
# so springt die Anzeige beim Neuladen nie wieder auf das volle Limit.
_usage_lock = threading.Lock()
_usage_mem = {}
_usage_warned = False


def _today():
    return datetime.date.today().isoformat()


def _usage_read():
    try:
        u = json.loads(USAGE_FILE.read_text())
        return u if isinstance(u, dict) else {}
    except Exception:
        return {}


def usage_used():
    today = _today()
    return max(int(_usage_read().get(today, 0) or 0), _usage_mem.get(today, 0))


def usage_remaining(limit):
    return max(0, limit - usage_used())


def usage_take(limit):
    """Eine Frage vom Tageskontingent abbuchen. False, wenn aufgebraucht."""
    global _usage_warned
    with _usage_lock:
        today = _today()
        n = usage_used()
        if n >= limit:
            return False
        _usage_mem.clear()
        _usage_mem[today] = n + 1
        u = _usage_read()
        cutoff = (datetime.date.today() - datetime.timedelta(days=60)).isoformat()
        u = {k: v for k, v in u.items() if k >= cutoff}
        u[today] = n + 1
        try:
            STATE.mkdir(exist_ok=True)
            tmp = USAGE_FILE.with_suffix('.tmp')
            tmp.write_text(json.dumps(u))
            os.replace(tmp, USAGE_FILE)
        except OSError as e:
            if not _usage_warned:
                print(f'WARNUNG: Fragezähler kann nicht gespeichert werden ({e}). '
                      f'Rechte von {STATE} prüfen — gezählt wird bis zum Neustart im Speicher.', flush=True)
                _usage_warned = True
        return True


def usage_check():
    """Beim Start prüfen, ob .state beschreibbar ist."""
    try:
        STATE.mkdir(exist_ok=True)
        probe = STATE / '.ask_probe'
        probe.write_text('ok')
        probe.unlink()
        return True
    except OSError as e:
        print(f'WARNUNG: {STATE} ist für den Frage-Server nicht beschreibbar ({e}). '
              f'Der Fragezähler überlebt dann keinen Neustart.', flush=True)
        return False


def log(line):
    STATE.mkdir(exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.datetime.now().isoformat(timespec="seconds")}  {line}\n')


# ----------------------------------------------------------- Werkzeuge
FILTER_SCHEMA = {
    'type': 'object',
    'description': 'Optionale Filter. Mehrere Werte in einer Liste sind ODER, verschiedene Filter sind UND.',
    'properties': {
        'teams': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Team-Codes, z. B. ["FUNO","FUSU"]'},
        'team_groups': {'type': 'array', 'items': {'type': 'string', 'enum': list(cq.TEAM_GROUPS)}},
        'destinations': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Reiseländer als Code (I, HR, ES, D, A, …)'},
        'origin_countries': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Herkunftsländer der Kunden als Code (D, A, CH, …)'},
        'regions': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Bundesland/Kanton der Kunden, Code oder Name, z. B. "BY" oder "Bayern"'},
        'hotels': {'type': 'array', 'items': {'type': 'integer'}, 'description': 'WebIDs (mit find_hotels ermitteln)'},
        'sports': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Sportart-Codes laut get_overview'},
    },
}

TOOLS = [
    {
        'name': 'get_overview',
        'description': 'Datenstand, Rechenregeln, gültige Teams, Länder, Sportarten und alle Kennzahlen. Zuerst aufrufen, wenn Codes oder Definitionen unklar sind.',
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'find_hotels',
        'description': 'Hotels nach Namensteil oder WebID suchen. Liefert WebID, Name und Land.',
        'input_schema': {'type': 'object', 'properties': {
            'text': {'type': 'string', 'description': 'Namensteil (z. B. "Castelnuovo") oder WebID'}},
            'required': ['text']},
    },
    {
        'name': 'query',
        'description': ('Kennzahlen des Cockpits für einen Zeitraum berechnen, optional gruppiert, gefiltert und mit '
                        'Vorjahresvergleich. Rechnet exakt wie das Cockpit. Datumsangaben beziehen sich auf das '
                        'Buchungsdatum (bzw. Anfrage-/Angebotsdatum). Werte: Beträge in Euro, Quoten als Anteil (0.25 = 25 %).'),
        'input_schema': {
            'type': 'object',
            'properties': {
                'metrics': {'type': 'array', 'items': {'type': 'string', 'enum': list(cq.METRICS)},
                            'description': 'Kennzahlen, siehe get_overview'},
                'date_from': {'type': 'string', 'description': 'YYYY-MM-DD, einschließlich'},
                'date_to': {'type': 'string', 'description': 'YYYY-MM-DD, einschließlich'},
                'group_by': {'type': 'string', 'enum': cq.GROUP_BY, 'default': 'none'},
                'filters': FILTER_SCHEMA,
                'sort_by': {'type': 'string', 'description': 'Kennzahl zum Sortieren (Standard: erste Kennzahl)'},
                'sort_desc': {'type': 'boolean', 'default': True},
                'limit': {'type': 'integer', 'default': 25, 'description': 'max. Zeilen (1–100)'},
                'compare_previous_year': {'type': 'boolean', 'default': False,
                                          'description': 'zusätzlich Vorjahreswerte (_vj) und Veränderung in % (_delta_pct)'},
            },
            'required': ['metrics', 'date_from', 'date_to'],
        },
    },
]


def run_tool(cockpit, name, args):
    if name == 'get_overview':
        return cockpit.overview()
    if name == 'find_hotels':
        return cockpit.find_hotels(args.get('text'))
    if name == 'query':
        return cockpit.query(
            metrics=args.get('metrics'), date_from=args.get('date_from'), date_to=args.get('date_to'),
            group_by=args.get('group_by') or 'none', filters=args.get('filters') or {},
            sort_by=args.get('sort_by'), sort_desc=args.get('sort_desc', True),
            limit=args.get('limit', 25), compare_previous_year=bool(args.get('compare_previous_year')))
    raise ValueError(f'Unbekanntes Werkzeug {name}')


def describe_step(name, args):
    """Kurze, lesbare Beschreibung eines Werkzeugaufrufs für den Rechenweg."""
    if name == 'get_overview':
        return 'Datenstand und Definitionen gelesen'
    if name == 'find_hotels':
        return f'Hotel gesucht: „{args.get("text", "")}“'
    if name == 'query':
        parts = [', '.join(args.get('metrics') or []),
                 f'{args.get("date_from")} bis {args.get("date_to")}']
        g = args.get('group_by')
        if g and g != 'none':
            parts.append(f'je {g}')
        for k, v in (args.get('filters') or {}).items():
            if v:
                parts.append(f'{k}={",".join(map(str, v))}')
        if args.get('compare_previous_year'):
            parts.append('mit Vorjahr')
        return 'Abfrage: ' + ' · '.join(parts)
    return name


def system_prompt(cockpit, lang):
    ov = cockpit.overview()['datenstand']
    today = datetime.date.today()
    fy = today.year if today.month >= 7 else today.year - 1
    return f"""Du beantwortest Fragen zum SOCCA Sales Cockpit der SOCCA GROUP (Sportreisen: Trainingslager, Turniere; Marken SOCCATOURS, SOCCACUP, SWIMTOURS, TENNISTOURS).

Heute ist {today.isoformat()}. Laufendes Geschäftsjahr: GJ {fy}/{str(fy+1)[2:]} (01.07.{fy}–30.06.{fy+1}).
Datenstand: Buchungen {ov['erste_buchung']} bis {ov['letzte_buchung']}, Anfragen bis {ov['letzte_anfrage']}.

Regeln:
- Jede Zahl in deiner Antwort muss aus einem Werkzeugergebnis stammen. Rechne nicht aus dem Gedächtnis, schätze nicht.
- Nutze die Werkzeuge: get_overview für Codes und Definitionen, find_hotels für Hotels, query für Kennzahlen. Mehrere Abfragen sind erlaubt.
- Ohne Zeitangabe in der Frage: nimm das laufende Geschäftsjahr bis heute und sag das dazu. „Letztes Jahr“ ohne Zusatz = voriges Geschäftsjahr.
- Nenne immer den Zeitraum und die Filter, auf denen die Antwort beruht.
- Beachte die Hinweise (hinweise) im Ergebnis und gib wichtige Einschränkungen kurz weiter.
- Lässt sich die Frage mit den Daten nicht beantworten (z. B. Reisedatum, Kundennamen, Gründe), sag das klar und schlag vor, was stattdessen geht.
- Antworte auf {LANG_NAMES.get(lang, 'Deutsch')}, außer die Frage ist offensichtlich in einer anderen Sprache gestellt — dann in dieser.
- Kurz und sachlich: zuerst die Antwort in ein, zwei Sätzen, dann bei Bedarf eine kleine Markdown-Tabelle (höchstens 12 Zeilen). Keine Überschriften, keine Emojis.
- Zahlen im Format der Antwortsprache; Euro gerundet (ab 10.000 € in Tsd €), Quoten in Prozent mit einer Nachkommastelle.
- Team-Codes (FUNO, FUSU, TECA …) nicht übersetzen. Teams (Zählgröße) ≠ Buchungen.
- Begriffe wie im Cockpit: „Unique Anfragen“ (leads) und „Anfragen gesamt“ (leads_all); „Buchungsquote“ = Buchungen ÷ Unique Anfragen (quote2), „Abschlussquote“ = Buchungen ÷ Angebote. Nur „Anfragen“ in der Frage = Unique Anfragen. „Laufender Monat“ = vom 1. des aktuellen Kalendermonats bis heute.
- „Unique“ und „Anfragen“ nur auf Deutsch; in anderen Sprachen die Begriffe der Oberfläche: nl unieke aanvragen / aanvragen totaal, es solicitudes únicas / solicitudes totales, it richieste uniche / richieste totali, hr jedinstveni upiti / upiti ukupno, cs unikátní poptávky / poptávky celkem, nb unike forespørsler / forespørsler totalt, tr tekil talepler / toplam talepler, hu egyedi érdeklődések / összes érdeklődés.
"""


# --------------------------------------------------------- Anthropic
def call_claude(cfg, system, messages):
    body = {
        'model': cfg['model'],
        'max_tokens': cfg['max_tokens'],
        'system': [{'type': 'text', 'text': system, 'cache_control': {'type': 'ephemeral'}}],
        'tools': TOOLS[:-1] + [dict(TOOLS[-1], cache_control={'type': 'ephemeral'})],
        'messages': messages,
    }
    req = urllib.request.Request(API_URL, data=json.dumps(body).encode(), method='POST', headers={
        'x-api-key': cfg['key'], 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            txt = e.read().decode('utf-8', 'replace')[:500]
            if e.code in (429, 500, 502, 503, 529) and attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError(f'API {e.code}: {txt}')
        except urllib.error.URLError as e:
            if attempt < 2:
                time.sleep(3)
                continue
            raise RuntimeError(f'Keine Verbindung zur Anthropic-API: {e.reason}')


def context_note(ctx):
    """Aktuelle Auswahl im Cockpit als Zusatz zur Frage."""
    if not isinstance(ctx, dict):
        return ''
    labels = {'von': 'von', 'bis': 'bis', 'bereich': 'Teamgruppe', 'team': 'Team', 'reiseland': 'Reiseland',
              'herkunft': 'Herkunft', 'region': 'Region'}
    parts = [f'{labels[k]} {str(v)[:40]}' for k, v in ctx.items()
             if k in labels and v not in (None, '', 'all')]
    if not parts:
        return ''
    return ('\n\n[Aktuelle Auswahl im Cockpit: ' + ', '.join(parts) +
            '. Nur verwenden, wenn sich die Frage darauf bezieht (z. B. „hier“, „ausgewählt“, „dieser Zeitraum“).]')


def answer(cockpit, cfg, question, lang, ctx=None):
    cockpit.maybe_reload()
    system = system_prompt(cockpit, lang)
    messages = [{'role': 'user', 'content': question + context_note(ctx)}]
    steps, usage = [], {'input': 0, 'output': 0, 'cache_read': 0, 'cache_write': 0}
    for _ in range(MAX_ROUNDS):
        resp = call_claude(cfg, system, messages)
        u = resp.get('usage', {})
        usage['input'] += u.get('input_tokens', 0)
        usage['output'] += u.get('output_tokens', 0)
        usage['cache_read'] += u.get('cache_read_input_tokens', 0) or 0
        usage['cache_write'] += u.get('cache_creation_input_tokens', 0) or 0
        content = resp.get('content', [])
        if resp.get('stop_reason') != 'tool_use':
            text = '\n'.join(b.get('text', '') for b in content if b.get('type') == 'text').strip()
            return text, steps, usage
        messages.append({'role': 'assistant', 'content': content})
        results = []
        for b in content:
            if b.get('type') != 'tool_use':
                continue
            args = b.get('input') or {}
            steps.append(describe_step(b['name'], args))
            try:
                out = run_tool(cockpit, b['name'], args)
                results.append({'type': 'tool_result', 'tool_use_id': b['id'],
                                'content': json.dumps(out, ensure_ascii=False)})
            except Exception as e:                       # Fehler an Claude zurückgeben
                results.append({'type': 'tool_result', 'tool_use_id': b['id'],
                                'content': f'Fehler: {e}', 'is_error': True})
        messages.append({'role': 'user', 'content': results})
    return ('Die Frage war zu umfangreich — bitte enger fassen, z. B. mit Zeitraum oder Team.', steps, usage)


# ------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = 'SOCCA-Ask/1'

    def log_message(self, *a):
        pass

    def send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split('?')[0].rstrip('/').endswith('/api/status'):
            cfg = load_env()
            ok = bool(cfg['key']) and DATA_FILE.exists()
            return self.send_json(200, {'enabled': ok, 'model': cfg['model'] if ok else None,
                                        'limit': cfg['limit'], 'remaining': usage_remaining(cfg['limit']),
                                        'used': usage_used(), 'day': _today()})
        self.send_json(404, {'error': 'not found'})

    def do_POST(self):
        if not self.path.split('?')[0].rstrip('/').endswith('/api/ask'):
            return self.send_json(404, {'error': 'not found'})
        cfg = load_env()
        if not cfg['key']:
            return self.send_json(503, {'error': 'not_configured'})
        try:
            n = int(self.headers.get('Content-Length') or 0)
            req = json.loads(self.rfile.read(min(n, 20000)) or b'{}')
        except Exception:
            return self.send_json(400, {'error': 'bad_request'})
        q = str(req.get('question') or '').strip()[:MAX_QUESTION]
        lang = str(req.get('lang') or 'de')[:5]
        if len(q) < 3:
            return self.send_json(400, {'error': 'empty'})
        if not usage_take(cfg['limit']):
            return self.send_json(429, {'error': 'limit', 'remaining': 0, 'limit': cfg['limit']})
        t0 = time.time()
        try:
            text, steps, usage = answer(self.server.cockpit, cfg, q, lang, req.get('context'))
        except Exception as e:
            log(f'FEHLER {type(e).__name__}: {e}')
            traceback.print_exc()
            return self.send_json(502, {'error': 'upstream', 'detail': str(e)[:300],
                                        'remaining': usage_remaining(cfg['limit'])})
        dur = time.time() - t0
        log(f'{lang} {dur:.1f}s in={usage["input"]} out={usage["output"]} cache={usage["cache_read"]}'
            f' schritte={len(steps)}' + (f'  „{q}“' if cfg['log_questions'] else ''))
        self.send_json(200, {'answer': text, 'steps': steps, 'seconds': round(dur, 1),
                             'remaining': usage_remaining(cfg['limit']), 'limit': cfg['limit']})


def main():
    port = int(os.environ.get('ASK_PORT', '8080'))
    while not DATA_FILE.exists():            # erster Lauf des Workers noch nicht fertig
        print('warte auf web/data.json …', flush=True)
        time.sleep(15)
    srv = ThreadingHTTPServer(('0.0.0.0', port), Handler)
    srv.cockpit = cq.Cockpit(str(DATA_FILE))
    cfg = load_env()
    usage_check()
    print(f'SOCCA Frage-Server auf Port {port} · Modell {cfg["model"]} · '
          f'{"API-Schlüssel gefunden" if cfg["key"] else "KEIN API-Schlüssel (anthropic.env) — Fragefeld bleibt aus"}'
          f' · Tageslimit {cfg["limit"]}, heute schon {usage_used()} gestellt', flush=True)
    srv.serve_forever()


if __name__ == '__main__':
    main()
