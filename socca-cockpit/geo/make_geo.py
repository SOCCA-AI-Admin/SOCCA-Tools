#!/usr/bin/env python3
"""Erzeugt aus Natural-Earth-Daten (gemeinfrei) die SVG-Geometrie fuer das
Sales Cockpit: eine Europakarte auf Laenderebene und eine DACH-Karte auf
Ebene der Bundeslaender und Kantone.

Projektion: ETRS89-LAEA (EPSG:3035), Lambert azimutal flaechentreu,
Bezugspunkt 52 Grad Nord / 10 Grad Ost - die Standardprojektion fuer
Europakarten.

    python3 make_geo.py > geo.js
"""
import json, math, sys

R = 6378137.0
LAT0, LON0 = math.radians(52.0), math.radians(10.0)


def laea(lon, lat):
    la, lo = math.radians(lat), math.radians(lon)
    d = 1 + math.sin(LAT0) * math.sin(la) + math.cos(LAT0) * math.cos(la) * math.cos(lo - LON0)
    if d <= 1e-12:
        return None
    k = math.sqrt(2.0 / d)
    x = R * k * math.cos(la) * math.sin(lo - LON0)
    y = R * k * (math.cos(LAT0) * math.sin(la) - math.sin(LAT0) * math.cos(la) * math.cos(lo - LON0))
    return x, -y                      # SVG zaehlt y nach unten


def simplify(pts, tol):
    """Douglas-Peucker."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        ax, ay = pts[a]
        bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy)
        best, bi = -1.0, None
        for i in range(a + 1, b):
            px, py = pts[i]
            d = (abs(dy * px - dx * py + bx * ay - by * ax) / n) if n else math.hypot(px - ax, py - ay)
            if d > best:
                best, bi = d, i
        if best > tol:
            keep[bi] = True
            stack.append((a, bi))
            stack.append((bi, b))
    return [p for p, k in zip(pts, keep) if k]


def rings(geom, box=None):
    t = geom['type']
    if t == 'Polygon':
        rs = [geom['coordinates'][0]]
    elif t == 'MultiPolygon':
        rs = [poly[0] for poly in geom['coordinates']]
    else:
        return []
    if box is None:
        return rs
    # Ringe ausserhalb des Kartenausschnitts verwerfen - sonst ziehen
    # Ueberseegebiete und Inselgruppen die Karte auseinander.
    lo0, la0, lo1, la1 = box
    keep = []
    for r in rs:
        cx = sum(c[0] for c in r) / len(r)
        cy = sum(c[1] for c in r) / len(r)
        if lo0 <= cx <= lo1 and la0 <= cy <= la1:
            keep.append(r)
    return keep


def path(geom, tol, min_area, box=None):
    out = []
    for ring in rings(geom, box):
        pts = []
        for lon, lat in ring:
            p = laea(lon, lat)
            if p:
                pts.append(p)
        if len(pts) < 4:
            continue
        a = abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1]
                    for i in range(len(pts)))) / 2
        out.append((a, pts))
    if not out:
        return ''
    # Die groesste Flaeche bleibt immer - sonst verschwinden Kleinstaaten
    # wie Malta. Alle weiteren Ringe muessen die Mindestflaeche erreichen.
    out.sort(key=lambda t: -t[0])
    keep = [out[0]] + [r for r in out[1:] if r[0] >= min_area]
    ds = []
    for _, pts in keep:
        pts = simplify(pts, tol)
        if len(pts) < 4:
            continue
        ds.append('M' + 'L'.join(f'{x:.0f} {y:.0f}' for x, y in pts) + 'Z')
    return ''.join(ds)


def bbox(paths):
    import re
    xs, ys = [], []
    for d in paths:
        for m in re.finditer(r'(-?\d+) (-?\d+)', d):
            xs.append(int(m.group(1)))
            ys.append(int(m.group(2)))
    return min(xs), min(ys), max(xs), max(ys)


def scaled(entries, pad_frac=0.02, size=1000):
    """Pfade auf ein Koordinatensystem 0..size normieren."""
    x0, y0, x1, y1 = bbox([e[-1] for e in entries])
    w, h = x1 - x0, y1 - y0
    pad = max(w, h) * pad_frac
    x0 -= pad; y0 -= pad; w += 2 * pad; h += 2 * pad
    s = size / max(w, h)
    import re

    def tr(d):
        return re.sub(r'(-?\d+) (-?\d+)',
                      lambda m: f'{(int(m.group(1))-x0)*s:.1f} {(int(m.group(2))-y0)*s:.1f}', d)
    return [e[:-1] + [tr(e[-1])] for e in entries], [round(w * s, 1), round(h * s, 1)]


# ------------------------------------------------------------------ Laender
ISO_TO_SALES = {'DE': 'D', 'AT': 'A', 'IT': 'I'}
# Ausschnitt Europa plus die Reiselaender am Mittelmeerrand
EU_BOX = (-13, 30, 45, 71)      # lon min, lat min, lon max, lat max
EXTRA = {'TR', 'CY'}
# Der Ausschnitt greift ueber Kleinasien hinaus - diese Laender gehoeren
# nicht auf eine Europakarte und wuerden sie nur nach Osten ziehen.
DROP = {'IQ', 'JO', 'SY', 'LB', 'PS', 'IL', 'GE', 'AM', 'AZ', 'SA', 'KW',
        'IR', 'EG', 'LY', 'DZ', 'MA', 'TN', 'EH', 'KZ', 'TM', 'UZ'}


# Natural Earth laesst ISO_A2 fuer Frankreich und Norwegen leer.
A3_TO_A2 = {'FRA': 'FR', 'NOR': 'NO', 'KOS': 'XK', 'CYN': 'CY',
            'SOL': 'SO', 'SDS': 'SS'}


def country_code(p):
    for k in ('ISO_A2_EH', 'ISO_A2', 'iso_a2'):
        v = p.get(k)
        if v and v not in ('-99', '-999'):
            return v
    a3 = p.get('ADM0_A3') or p.get('adm0_a3')
    return A3_TO_A2.get(a3)


def build_countries(src):
    d = json.load(open(src))
    out = []
    for f in d['features']:
        p = f['properties']
        code = country_code(p)
        if not code or code == 'AQ' or code in DROP:
            continue
        dd = path(f['geometry'], tol=4000, min_area=6e8, box=EU_BOX)
        if not dd:
            continue
        name = p.get('NAME') or p.get('name')
        out.append([ISO_TO_SALES.get(code, code), name, dd])
    # Gleicher Code mehrfach (etwa Nordzypern) -> zu einer Flaeche vereinen
    merged = {}
    for code, name, dd in out:
        if code in merged:
            merged[code][2] += dd
        else:
            merged[code] = [code, name, dd]
    return list(merged.values())


# ------------------------------------------------------------------ Regionen
AT_NAME_TO_CODE = {
    'Burgenland': 'BGLD', 'Kärnten': 'KTN', 'Niederösterreich': 'NOE',
    'Oberösterreich': 'OOE', 'Salzburg': 'SBG', 'Steiermark': 'STMK',
    'Tirol': 'T', 'Vorarlberg': 'VBG', 'Wien': 'W',
}


def build_regions(src):
    d = json.load(open(src))
    out = []
    for f in d['features']:
        p = f['properties']
        iso2 = p.get('iso_a2')
        if iso2 not in ('DE', 'AT', 'CH'):
            continue
        land = ISO_TO_SALES.get(iso2, iso2)
        name = p.get('name')
        sub = (p.get('iso_3166_2') or '').split('-')[-1]
        if iso2 == 'AT':
            code = AT_NAME_TO_CODE.get(name, sub)
        else:
            code = sub
        dd = path(f['geometry'], tol=900, min_area=2e7)
        if not dd:
            continue
        out.append([land, code, name, dd])
    return out


if __name__ == '__main__':
    eu = build_countries('ne_50m_admin_0_countries.json')
    eu, eu_vb = scaled(eu, size=1000)
    rg = build_regions('ne10_admin1.json')
    rg, rg_vb = scaled(rg, size=1000)
    geo = {'eu': {'vb': eu_vb, 'f': eu}, 'dach': {'vb': rg_vb, 'f': rg}}
    js = json.dumps(geo, separators=(',', ':'), ensure_ascii=False)
    sys.stdout.write('/* Geometrie: Natural Earth, gemeinfrei. '
                     'Projektion ETRS89-LAEA (EPSG:3035). */\nconst GEO=' + js + ';\n')
    print(f'Laender {len(eu)}  Regionen {len(rg)}  {len(js)/1000:.0f} kB',
          file=sys.stderr)
