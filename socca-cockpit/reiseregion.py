"""Reiseregionen der Hotels (Locations Spalte AO) fuer etl.py.

Regeln
  1. Steht in Spalte AO eine Region aus der SOCCA-Liste (geo/reiseregionen.json)
     fuer das Land des Hotels, gilt sie. Schreibweisen wie "Kaernten" und
     "Kärnten" sind gleichwertig; angezeigt wird der Name aus der Liste.
  2. Ist AO leer oder passt die Region nicht zum Land, wird sie aus dem Ort
     erschlossen. Der Ort steht am Anfang des Hotelnamens (Spalte Destination),
     bei SOCCACUPs irgendwo im Namen.
       a) Andere Hotels im selben Ort mit gepflegter Region -> deren Region.
       b) Sonst die Region der naechstgelegenen gepflegten Hotels im selben
          Land (bis 150 km), Ortslage aus geo/orte.tsv.gz (GeoNames).
  3. Mittelpunkt einer Region fuer die Kreise auf der Karte = Median der
     Ortslagen ihrer Hotels, ersatzweise die Lage eines gleichnamigen Ortes.
"""
import gzip, json, math, os, re, unicodedata
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
ISO = {'D': 'DE', 'A': 'AT', 'I': 'IT'}              # Kuerzel im Blatt Sales -> ISO
ALIAS = {'voralberg': 'vorarlberg'}
STOP = {'hotel', 'sporthotel', 'jugendherberge', 'turnier', 'camping', 'resort', 'gasthof',
        'landgasthof', 'pension', 'residence', 'residenz', 'villa', 'park', 'soccacup', 'cup',
        'girls', 'boys', 'insel', 'jufa', 'hostel'}
MAX_KM = 150


def norm(s):
    """Ortsnamen vergleichbar machen: ohne Akzente, klein, St. = Sankt."""
    s = str(s or '').replace('ß', 'ss').replace("'", '').replace('’', '')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    s = re.sub(r'\bst\b', 'sankt', s)
    return re.sub(r'\s+', ' ', s).strip()


def rkey(s):
    """Vergleichsschluessel fuer Regionsnamen: Umlaut und ae/oe/ue gleich."""
    k = norm(str(s).replace('ä', 'a').replace('ö', 'o').replace('ü', 'u')
             .replace('Ä', 'A').replace('Ö', 'O').replace('Ü', 'U'))
    k = k.replace('ae', 'a').replace('oe', 'o').replace('ue', 'u').replace(' ', '')
    return ALIAS.get(k, k)


_ORTE = None


def orte():
    global _ORTE
    if _ORTE is None:
        _ORTE = defaultdict(dict)
        path = os.path.join(BASE, 'geo', 'orte.tsv.gz')
        try:
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('#'):
                        continue
                    land, k, lon, lat = line.rstrip('\n').split('\t')
                    _ORTE[land][k] = (float(lon), float(lat))
        except OSError:
            pass
    return _ORTE


def town(land, name):
    """(Ortsschluessel, (Laenge, Breite)) aus dem Hotelnamen oder (None, None)."""
    gz = orte().get(ISO.get(land, land), {})
    toks = norm(name).split()
    if not toks or not gz:
        return None, None
    cup = 'soccacup' in toks or 'cup' in toks
    starts = range(len(toks)) if cup else [0]
    for s in starts:
        if toks[s] in STOP:
            continue
        for n in range(min(5, len(toks) - s), 0, -1):
            k = ' '.join(toks[s:s + n])
            if k in STOP:
                continue
            if k in gz:
                return k, gz[k]
    return None, None


def km(a, b):
    return math.hypot((a[0] - b[0]) * math.cos(math.radians((a[1] + b[1]) / 2)), a[1] - b[1]) * 111.2


def assign(hotels, log=print):
    """hotels: {webid: dict(name, land, region_raw)} -> (regions, hreg, inferred, problems)

    regions   Liste [Land, Name, Laenge, Breite] (Lage None, wenn unbekannt)
    hreg      {webid: Index in regions}
    inferred  {webid: Ortsschluessel} fuer erschlossene Regionen
    """
    try:
        js = json.load(open(os.path.join(BASE, 'geo', 'reiseregionen.json'), encoding='utf-8'))
    except OSError:
        js = {}
    master, fixpos = js.get('regionen', {}), js.get('lage', {})
    known = {land: {rkey(r): r for r in rs} for land, rs in master.items()}
    anyland = defaultdict(set)
    for land, m in known.items():
        for k in m:
            anyland[k].add(land)

    label, pos, tkey, problems = {}, {}, {}, []
    for w, h in hotels.items():
        k, p = town(h['land'], h['name'])
        if p:
            pos[w], tkey[w] = p, k
        raw = str(h.get('region_raw') or '').strip()
        if not raw:
            continue
        rk = rkey(raw)
        if rk in known.get(h['land'], {}):
            label[w] = known[h['land']][rk]
        elif not h['land'] and len(anyland.get(rk, ())) == 1:
            h['land'] = next(iter(anyland[rk]))          # Hotel ohne Land: Land der Region
            label[w] = known[h['land']][rk]
        elif anyland.get(rk):
            problems.append(f'{w} {h["name"]}: Region „{raw}“ gehört zu {"/".join(sorted(anyland[rk]))}, '
                            f'Hotel liegt in {h["land"]} — Region wird erschlossen')
        elif re.fullmatch(r"[^\W\d_][\w '.,/&()-]{1,40}", raw) and h['land']:
            label[w] = raw                     # neue Region, noch nicht in der Liste
            problems.append(f'{w} {h["name"]}: Region „{raw}“ steht nicht in geo/reiseregionen.json '
                            f'— übernommen, bitte Liste ergänzen')
        else:
            problems.append(f'{w} {h["name"]}: „{raw[:40]}“ in Spalte AO ist keine Region — Region wird erschlossen')

    # Erschliessen
    by_town = defaultdict(Counter)
    for w, r in label.items():
        if w in tkey:
            by_town[(hotels[w]['land'], tkey[w])][r] += 1
    inferred = {}
    for w, h in hotels.items():
        if w in label:
            continue
        r = None
        # a) Ort oder Namensanfang ist selbst eine Region (Berlin, Wien, Prag, Rom ...)
        toks = norm(h['name']).split()
        for n in range(min(4, len(toks)), 0, -1):
            hit = known.get(h['land'], {}).get(rkey(' '.join(toks[:n])))
            if hit:
                r = hit
                break
        if r:
            pass
        elif w in tkey and by_town.get((h['land'], tkey[w])):
            r = by_town[(h['land'], tkey[w])].most_common(1)[0][0]
        elif w in pos:
            near = sorted((km(pos[w], pos[v]), label[v]) for v in label
                          if v in pos and hotels[v]['land'] == h['land'])[:5]
            near = [x for x in near if x[0] <= MAX_KM]
            if near:
                votes = Counter()
                for d, lab in near:
                    votes[lab] += 1 / (1 + d)
                r = votes.most_common(1)[0][0]
        if r:
            label[w] = r
            inferred[w] = tkey.get(w)

    # Regionen und Mittelpunkte
    pts = defaultdict(list)
    for w, r in label.items():
        if w in pos:
            pts[(hotels[w]['land'], r)].append(pos[w])
    keys = sorted({(hotels[w]['land'], r) for w, r in label.items()}, key=lambda k: (k[0], rkey(k[1])))
    regions, rix = [], {}
    for land, r in keys:
        p = pts.get((land, r))
        if p:
            lon = sorted(x for x, _ in p)[len(p) // 2]
            lat = sorted(y for _, y in p)[len(p) // 2]
        else:
            q = fixpos.get(f'{land}|{r}') or orte().get(ISO.get(land, land), {}).get(norm(r))
            lon, lat = q if q else (None, None)
        rix[(land, r)] = len(regions)
        regions.append([land, r, None if lon is None else round(lon, 3), None if lat is None else round(lat, 3)])
    hreg = {w: rix[(hotels[w]['land'], r)] for w, r in label.items()}
    return regions, hreg, inferred, problems
