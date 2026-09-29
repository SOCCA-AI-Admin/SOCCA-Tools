#!/usr/bin/env python3
"""Holt Sales-Mappe und Combit-Export aus SharePoint nach data/.

    python3 fetch_sharepoint.py            laden, falls sich etwas geändert hat
    python3 fetch_sharepoint.py --check    nur prüfen und anzeigen, nichts laden
    python3 fetch_sharepoint.py --force    in jedem Fall neu laden

Zugang über Microsoft Graph mit einer eigenen App-Registrierung
(Client-Credentials). Konfiguration in sharepoint.env neben diesem Skript,
Vorlage: deploy/sharepoint.env.vorlage. Nur Standardbibliothek, keine
zusätzlichen Pakete.

Auf stdout stehen am Ende Zeilen der Form  SALES=/pfad  CAP=/pfad
[APLEADS=/pfad] — update.sh liest sie ein. Alles andere geht auf stderr.

Exit-Code 0: Dateien aktuell (neu geladen oder unverändert)
          1: Fehler; bereits vorhandene Dateien in data/ bleiben unberührt
"""
import base64
import http.client as httpclient
import datetime
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
ENV_FILE = pathlib.Path(os.environ.get('SP_ENV', ROOT / 'sharepoint.env'))
DATA = ROOT / 'data'
STATE_FILE = ROOT / '.state' / 'sharepoint.json'

# Nur für Tests überschreibbar
LOGIN = os.environ.get('SP_LOGIN_BASE', 'https://login.microsoftonline.com')
GRAPH = os.environ.get('SP_GRAPH_BASE', 'https://graph.microsoft.com/v1.0')

FILES = [('SALES', 'SP_SALES', True), ('CAP', 'SP_CAP', True), ('APLEADS', 'SP_APLEADS', False)]


class Fail(Exception):
    pass


def err(msg):
    print(msg, file=sys.stderr)


# ------------------------------------------------------------ Konfiguration
def load_env(path):
    if not path.exists():
        raise Fail(f'{path.name} fehlt. Vorlage: deploy/sharepoint.env.vorlage')
    cfg = {}
    for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise Fail(f'{path.name}, Zeile {n}: erwartet SCHLUESSEL=Wert')
        k, v = line.split('=', 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in '"\'':
            v = v[1:-1]
        cfg[k.strip()] = v
    for k in ('SP_TENANT_ID', 'SP_CLIENT_ID', 'SP_CLIENT_SECRET', 'SP_SITE', 'SP_SALES', 'SP_CAP'):
        if not cfg.get(k):
            raise Fail(f'{path.name}: {k} ist leer')
    return cfg


def site_ref(site):
    """'https://socca.sharepoint.com/sites/X' oder 'socca.sharepoint.com:/sites/X' → Graph-Form."""
    if site.startswith('http'):
        u = urllib.parse.urlparse(site)
        return f'{u.hostname}:{u.path.rstrip("/")}'
    return site


# ------------------------------------------------------------------- HTTP
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def http(method, url, token=None, data=None, headers=None, stream_to=None):
    """Einfacher Aufruf mit Wiederholung bei 429/503. Liefert (status, headers, body|None)."""
    h = dict(headers or {})
    if token:
        h['Authorization'] = 'Bearer ' + token
    for attempt in range(4):
        req = urllib.request.Request(url, data=data, method=method, headers=h)
        try:
            with _opener.open(req, timeout=120) as r:
                if stream_to:
                    with open(stream_to, 'wb') as f:
                        while True:
                            chunk = r.read(1 << 20)
                            if not chunk:
                                break
                            f.write(chunk)
                    return r.status, r.headers, None
                return r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                return e.code, e.headers, None
            body = e.read()
            if e.code in (429, 503, 504) and attempt < 3:
                wait = int(e.headers.get('Retry-After') or 5 * (attempt + 1))
                err(f'  Graph drosselt ({e.code}), neuer Versuch in {wait}s')
                time.sleep(min(wait, 60))
                continue
            return e.code, e.headers, body
        except (urllib.error.URLError, httpclient.HTTPException, OSError) as e:
            if stream_to:
                pathlib.Path(stream_to).unlink(missing_ok=True)
            if attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            reason = getattr(e, 'reason', None) or e
            raise Fail(f'Keine Verbindung zu {urllib.parse.urlparse(url).hostname}: {reason}')
    raise Fail('Zu viele Wiederholungen')


def graph_error(body):
    try:
        e = json.loads(body)['error']
        return e.get('code', ''), e.get('message', '')
    except Exception:
        return '', (body or b'')[:300].decode('utf-8', 'replace')


def gget(token, path):
    st, _, body = http('GET', GRAPH + path, token)
    if st == 200:
        return json.loads(body)
    code, msg = graph_error(body)
    raise GraphError(st, code, msg, path)


class GraphError(Fail):
    def __init__(self, status, code, msg, path):
        super().__init__(f'Graph {status} {code}: {msg}  [{path}]')
        self.status, self.code = status, code


# -------------------------------------------------------------------- Auth
AADSTS_HINTS = {
    'AADSTS7000215': 'Client-Secret ist falsch. Den WERT des Secrets eintragen, nicht die Secret-ID.',
    'AADSTS7000222': 'Client-Secret ist abgelaufen. In Entra ein neues anlegen und in sharepoint.env eintragen.',
    'AADSTS700016': 'App (SP_CLIENT_ID) in diesem Tenant nicht gefunden. Client-ID und Tenant-ID prüfen.',
    'AADSTS90002': 'Tenant (SP_TENANT_ID) nicht gefunden.',
    'AADSTS900023': 'SP_TENANT_ID hat ein ungültiges Format.',
}


def get_token(cfg):
    data = urllib.parse.urlencode({
        'client_id': cfg['SP_CLIENT_ID'],
        'client_secret': cfg['SP_CLIENT_SECRET'],
        'scope': 'https://graph.microsoft.com/.default',
        'grant_type': 'client_credentials',
    }).encode()
    st, _, body = http('POST', f'{LOGIN}/{cfg["SP_TENANT_ID"]}/oauth2/v2.0/token', data=data,
                       headers={'Content-Type': 'application/x-www-form-urlencoded'})
    j = json.loads(body or b'{}')
    if st == 200 and 'access_token' in j:
        return j['access_token']
    desc = j.get('error_description', '') or str(body)[:300]
    for code, hint in AADSTS_HINTS.items():
        if code in desc:
            raise Fail(f'Anmeldung fehlgeschlagen: {hint}\n  ({desc.splitlines()[0]})')
    raise Fail(f'Anmeldung fehlgeschlagen ({st}): {desc.splitlines()[0] if desc else ""}')


# ----------------------------------------------------------- Dateien finden
SELECT = '$select=id,name,size,cTag,eTag,lastModifiedDateTime,lastModifiedBy,webUrl,parentReference,file'


def share_token(url):
    return 'u!' + base64.urlsafe_b64encode(url.encode()).decode().rstrip('=')


def resolve_drive(token, cfg):
    try:
        site = gget(token, f'/sites/{site_ref(cfg["SP_SITE"])}?$select=id,displayName,webUrl')
    except GraphError as e:
        if e.status in (401, 403):
            raise Fail('Kein Zugriff auf die Site. Bei „Sites.Selected“ muss der App die Site '
                       'SOCCASales zusätzlich freigegeben werden (README, Schritt 4). '
                       f'Außerdem prüfen, ob die Administratorzustimmung erteilt ist.\n  ({e})')
        if e.status == 404:
            raise Fail(f'Site {cfg["SP_SITE"]} nicht gefunden. Schreibweise prüfen, z. B. '
                       'socca.sharepoint.com:/sites/SOCCASales')
        raise
    lib = cfg.get('SP_LIBRARY', '').strip()
    if lib:
        drives = gget(token, f'/sites/{site["id"]}/drives?$select=id,name,webUrl')['value']
        hit = [d for d in drives if d['name'].lower() == lib.lower()
               or d['webUrl'].rstrip('/').split('/')[-1].lower() == urllib.parse.quote(lib).lower()]
        if not hit:
            raise Fail(f'Bibliothek „{lib}“ nicht gefunden. Vorhanden: ' + ', '.join(d['name'] for d in drives))
        drive = hit[0]
    else:
        drive = gget(token, f'/sites/{site["id"]}/drive?$select=id,name,webUrl')
    return site, drive


def resolve_item(token, drive, ref):
    """ref = Pfad in der Bibliothek ('Sales.xlsb', 'Ordner/C_AP.xlsx') oder ein Freigabelink."""
    if ref.startswith('http'):
        try:
            return gget(token, f'/shares/{share_token(ref)}/driveItem?{SELECT}')
        except GraphError as e:
            if e.status in (401, 403):
                raise Fail('Freigabelinks brauchen die Berechtigung Sites.Read.All oder Files.Read.All. '
                           'Mit Sites.Selected stattdessen den Pfad in der Bibliothek eintragen, '
                           f'z. B. SP_SALES=Sales.xlsb\n  ({e})')
            raise
    path = '/'.join(urllib.parse.quote(p) for p in ref.strip('/').split('/'))
    try:
        return gget(token, f'/drives/{drive["id"]}/root:/{path}?{SELECT}')
    except GraphError as e:
        if e.status != 404:
            raise
        parent = '/'.join(ref.strip('/').split('/')[:-1])
        where = f'root:/{urllib.parse.quote(parent)}:' if parent else 'root'
        try:
            kids = gget(token, f'/drives/{drive["id"]}/{where}/children?$select=name,file&$top=200')['value']
            names = sorted(k['name'] for k in kids if 'file' in k)
            hint = ('Dateien dort: ' + ', '.join(names[:30])) if names else 'Der Ordner ist leer.'
        except GraphError:
            hint = 'Auch der Ordner ist nicht erreichbar.'
        raise Fail(f'„{ref}“ nicht gefunden in „{drive["name"]}“. {hint}')


# ---------------------------------------------------------------- Download
def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding='utf-8')
    os.replace(tmp, STATE_FILE)


def parse_ts(s):
    return datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))


def download(token, drive, item, target):
    st, hdr, body = http('GET', f'{GRAPH}/drives/{drive["id"]}/items/{item["id"]}/content', token)
    part = target.with_name('.' + target.name + '.part')
    if st in (301, 302, 303, 307, 308):
        # Die Weiterleitung zeigt auf eine vorab signierte Adresse — ohne Token abrufen
        st2, _, _ = http('GET', hdr['Location'], stream_to=part)
        if st2 != 200:
            part.unlink(missing_ok=True)
            raise Fail(f'Download von {item["name"]} fehlgeschlagen ({st2})')
    elif st == 200:
        part.write_bytes(body)
    else:
        code, msg = graph_error(body)
        raise Fail(f'Download von {item["name"]} fehlgeschlagen ({st} {code}: {msg})')
    size = part.stat().st_size
    if item.get('size') and size != item['size']:
        part.unlink(missing_ok=True)
        raise Fail(f'{item["name"]}: {size} Bytes geladen, erwartet {item["size"]} — abgebrochen')
    ts = parse_ts(item['lastModifiedDateTime']).timestamp()
    os.utime(part, (ts, ts))
    os.replace(part, target)          # erst jetzt sieht update.sh die neue Datei
    return size


def fmt_ts(s):
    return parse_ts(s).astimezone().strftime('%d.%m.%Y %H:%M')


def who(item):
    u = (item.get('lastModifiedBy') or {}).get('user') or {}
    return u.get('displayName') or u.get('email') or '?'


# ------------------------------------------------------------------- Ablauf
def main(argv):
    check = '--check' in argv
    force = '--force' in argv
    cfg = load_env(ENV_FILE)
    token = get_token(cfg)
    site, drive = resolve_drive(token, cfg)
    err(f'Site: {site.get("displayName")} · Bibliothek: {drive.get("name")}')

    state = load_state()
    DATA.mkdir(exist_ok=True)
    out = []
    for key, cfgkey, required in FILES:
        ref = cfg.get(cfgkey, '').strip()
        if not ref:
            if required:
                raise Fail(f'{cfgkey} ist leer')
            continue
        if ref in ('_', '-'):
            continue
        try:
            item = resolve_item(token, drive, ref)
        except Fail as e:
            if required:
                raise
            err(f'Hinweis: optionale Datei {cfgkey} übersprungen — {e}')
            continue
        if 'file' not in item:
            raise Fail(f'„{ref}“ ist ein Ordner, keine Datei')
        target = DATA / item['name']
        prev = state.get(key, {})
        same = (prev.get('cTag') == item.get('cTag') and prev.get('id') == item['id']
                and prev.get('local') == str(target) and target.exists())
        line = (f'{key:7s} {item["name"]}  {item.get("size", 0)/1e6:.1f} MB  '
                f'geändert {fmt_ts(item["lastModifiedDateTime"])} von {who(item)}')
        if check:
            err(line + ('  · lokal aktuell' if same else '  · würde geladen'))
        elif same and not force:
            err(line + '  · unverändert')
        else:
            t0 = time.time()
            download(token, drive, item, target)
            err(line + f'  · geladen in {time.time()-t0:.0f}s')
            state[key] = dict(id=item['id'], cTag=item.get('cTag'), local=str(target),
                              modified=item['lastModifiedDateTime'], webUrl=item.get('webUrl'))
            save_state(state)
        out.append((key, target))
    if not check:
        for key, target in out:
            print(f'{key}={target}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Fail as e:
        err(f'SharePoint: {e}')
        sys.exit(1)
    except Exception as e:                      # unerwartet: knapp melden, nicht abstürzen
        err(f'SharePoint: unerwarteter Fehler {type(e).__name__}: {e}')
        sys.exit(1)
