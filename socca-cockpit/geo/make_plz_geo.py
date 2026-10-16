#!/usr/bin/env python3
"""Erzeugt die Karte der PLZ-Gebiete (Leitregionen, erste zwei Ziffern) fuer
Deutschland, Oesterreich, die Schweiz und die Niederlande -> geo/geo_plz.js

Die Datei wird nur neu gebaut, wenn sich die Geometrie aendern soll; der
taegliche Datenlauf braucht dieses Skript nicht.

Quellen (alle im Ordner QUELLEN, Pfad als erstes Argument):
  DE  postleitzahlen.geojson.br  github.com/yetzt/postleitzahlen (Release)
      PLZ-Gebiete aus OpenStreetMap, (c) OpenStreetMap-Mitwirkende, ODbL
  AT  gemeinden_995_geo.json     github.com/ginseng666/GeoJSON-TopoJSON-Austria
      Gemeindegrenzen 2021, CC BY 4.0 Statistik Austria / Flooh Perlot
  CH  municipalities.shp, lakes.shp (Ordner package/2026, npm-Paket swiss-maps)
      Gemeindegrenzen und Seen, (c) swisstopo
  NL  -                         Gebiete aus den PC4-Mittelpunkten (Voronoi),
      begrenzt durch den Landesumriss aus Natural Earth (gemeinfrei)
  alle allCountries.txt          GeoNames-Postleitzahlen, CC BY 4.0
      (github.com/Aareon/GeoNamesMirror) - ordnet AT/CH-Gemeinden und
      NL-Mittelpunkte einer Leitregion zu und liefert die Ortsnamen
  ne_10m_admin_0_countries_lakes.geojson  Natural Earth, gemeinfrei
  cities.json                   Orte mit Einwohnerzahl (GeoNames, CC BY 4.0) aus dem
      npm-Paket all-the-cities, Felder [Land, Name, Einwohner, Laenge, Breite, Typ]:
      node -e "const c=require('all-the-cities');require('fs').writeFileSync('cities.json',
        JSON.stringify(c.filter(x=>['DE','AT','CH','NL'].includes(x.country)).map(x=>
        [x.country,x.name,x.population,...x.loc.coordinates,x.featureCode])))"
      Name eines Gebiets = einwohnerstaerkster Ort darin.

Gemeinden in AT und CH bekommen die Leitregion, in der die meisten
GeoNames-Orte der Gemeinde liegen. Das trifft die Postleitzahlengebiete auf
Ebene der zwei Ziffern sehr gut; einzelne Grenzgemeinden koennen abweichen.

Benoetigt: shapely, pyshp, pyproj, brotli und mapshaper (npm).

    python3 geo/make_plz_geo.py QUELLEN MAPSHAPER > geo/geo_plz.js

Nebenbei entsteht geo/plz_bundesland.json: volle PLZ -> Bundesland/Kanton/
Provinz (Kuerzel wie im Blatt Sales, Spalte H). Damit ordnet etl.py auch
Anfragen und Angebote einem Bundesland zu; die Datei bleibt auf dem Server,
im Cockpit landet nur das Kuerzel.
"""
import csv, json, math, os, re, subprocess, sys, tempfile
from collections import Counter, defaultdict

import shapefile
from pyproj import Transformer
from shapely import STRtree, voronoi_polygons
from shapely.geometry import MultiPoint, Point, mapping, shape
from shapely.ops import transform, unary_union  # noqa

SRC, MAPSHAPER = sys.argv[1], sys.argv[2]
P = lambda *a: os.path.join(SRC, *a)
TMP = tempfile.mkdtemp(prefix='plzgeo')
LAND = {'D': 'DE', 'A': 'AT', 'CH': 'CH', 'NL': 'NL'}        # Cockpit-Kuerzel -> ISO


def log(*a):
    print(*a, file=sys.stderr)


def ms(*args):
    subprocess.run([MAPSHAPER, '-quiet', *args], check=True)


# ---------------------------------------------------------------- GeoNames
gn = defaultdict(list)          # ISO -> [(plz, ort, lon, lat)]
# Bundesland je PLZ: GeoNames fuehrt admin1 teils als Name, teils als Code -
# beides wird auf die Kuerzel des Blattes Sales gebracht.
STATE = {
    'DE': {'Baden-Württemberg': 'BW', 'Bayern': 'BY', 'Bavaria': 'BY', 'Berlin': 'BE', 'Land Berlin': 'BE',
           'Brandenburg': 'BB', 'Bremen': 'HB', 'Hamburg': 'HH', 'Hessen': 'HE',
           'Mecklenburg-Vorpommern': 'MV', 'Mecklenburg-Western Pomerania': 'MV',
           'Niedersachsen': 'NI', 'Lower Saxony': 'NI', 'Nordrhein-Westfalen': 'NW',
           'Rheinland-Pfalz': 'RP', 'Saarland': 'SL', 'Sachsen': 'SN', 'Saxony': 'SN',
           'Sachsen-Anhalt': 'ST', 'Saxony-Anhalt': 'ST', 'Schleswig-Holstein': 'SH',
           'Thüringen': 'TH', 'Thuringia': 'TH'},
    'AT': {'Wien': 'W', 'Niederösterreich': 'NOE', 'Oberösterreich': 'OOE', 'Salzburg': 'SBG',
           'Tirol': 'T', 'Vorarlberg': 'VBG', 'Kärnten': 'KTN', 'Steiermark': 'STMK', 'Burgenland': 'BGLD'},
    'NL': {'North Holland': 'NH', 'South Holland': 'ZH', 'Utrecht': 'UT', 'North Brabant': 'NB',
           'Guelders': 'GE', 'Overijssel': 'OV', 'Flevoland': 'FL', 'Friesland': 'FR',
           'Groningen': 'GR', 'Drenthe': 'DR', 'Zeeland': 'ZE', 'Limburg': 'LI'},
}
state_votes = defaultdict(Counter)   # (Land, PLZ) -> Kuerzel
with open(P('allCountries.txt'), encoding='utf-8') as f:
    for row in csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
        if row[0] in ('DE', 'AT', 'CH', 'NL') and row[9] and row[10]:
            gn[row[0]].append((row[1].strip(), row[2].strip(), float(row[10]), float(row[9])))
        if row[0] in ('DE', 'AT', 'CH', 'NL'):
            # CH: admin1-Code ist das Kantonskuerzel; Bern heisst im Blatt Sales BN
            code = (row[4].strip() if row[0] == 'CH' else STATE[row[0]].get(row[3].strip()))
            if row[0] == 'CH' and code == 'BE':
                code = 'BN'
            if code:
                state_votes[(row[0], row[1].strip())][code] += 1
SALES = {'DE': 'D', 'AT': 'A', 'CH': 'CH', 'NL': 'NL'}
lookup = defaultdict(dict)
for (iso, plz), votes in sorted(state_votes.items()):
    lookup[SALES[iso]][plz] = votes.most_common(1)[0][0]
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plz_bundesland.json'), 'w', encoding='utf-8') as f:
    f.write('{\n' + ',\n'.join(f'"{land}":' + json.dumps(m, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
                              for land, m in sorted(lookup.items())) + '\n}\n')
log('PLZ -> Bundesland', {k: len(v) for k, v in lookup.items()})


def clean(iso, maxdeg=0.15):
    """Ausreisser entfernen: Orte ohne Nachbarn derselben Leitregion im Umkreis
    von etwa 12 km (z. B. NL 7146 mit Koordinaten in Deventer statt Groenlo)."""
    by = defaultdict(list)
    for e in gn[iso]:
        by[e[0][:2]].append(e)
    out, dropped = [], 0
    for k, es in by.items():
        if len(es) < 3:
            out += es; continue
        pts = [Point(e[2], e[3]) for e in es]
        tree = STRtree(pts)
        for i, p in enumerate(pts):
            near = [j for j in tree.query(p.buffer(maxdeg)) if j != i]
            if near:
                out.append(es[i])
            else:
                dropped += 1
    gn[iso] = out
    log(iso, dropped, 'GeoNames-Orte als Ausreisser verworfen')


for _iso in ('AT', 'CH', 'NL'):
    clean(_iso)


def names(iso):
    """Leitregion -> Ort mit den meisten Postleitzahlen (bei Gleichstand die kleinste PLZ)."""
    per = defaultdict(lambda: defaultdict(set))
    for plz, ort, _, _ in gn[iso]:
        ort = re.split(r'\s*[,(/]', ort)[0].strip()
        per[plz[:2]][ort].add(plz)
    return {k: min(v.items(), key=lambda kv: (-len(kv[1]), min(kv[1])))[0] for k, v in per.items()}


ne = json.load(open(P('ne_10m_admin_0_countries_lakes.geojson'), encoding='utf-8'))
outline = {f['properties']['ISO_A2_EH']: shape(f['geometry']) for f in ne['features']
           if f['properties'].get('ISO_A2_EH') in ('DE', 'AT', 'CH', 'NL')}
if outline['NL'].geom_type == 'MultiPolygon':                       # ohne Karibik
    outline['NL'] = unary_union([g for g in outline['NL'].geoms if g.bounds[1] > 50])
feats = []                       # (Schluessel, Geometrie WGS84)

# ---------------------------------------------------------------- DE
de_geo = os.path.join(TMP, 'de.geojson')
if not os.path.exists(P('de_plz.geojson')):
    import brotli
    with open(P('de_plz.geojson'), 'wb') as f:
        f.write(brotli.decompress(open(P('postleitzahlen.geojson.br'), 'rb').read()))
attr = os.path.join(TMP, 'de.csv')
ms('-i', P('de_plz.geojson'), '-filter', r"/^\d{5}$/.test(postcode)",
   '-each', 'cx=this.innerX, cy=this.innerY', '-o', attr, 'format=csv')
keep = set()
de_out = outline['DE'].buffer(0.01)
for r in csv.DictReader(open(attr, encoding='utf-8')):
    if r['postcode'] == '78266' or de_out.contains(Point(float(r['cx']), float(r['cy']))):
        keep.add(r['rel'])
ids = os.path.join(TMP, 'keep.csv')
with open(ids, 'w') as f:
    f.write('rel,keep\n' + ''.join(f'{r},1\n' for r in sorted(keep)))
ms('-i', P('de_plz.geojson'), '-join', ids, 'keys=rel,rel', 'field-types=rel:str',
   '-filter', 'keep == 1',
   '-each', "key='D-'+postcode.slice(0,2)", '-dissolve', 'key', '-o', de_geo, 'format=geojson')
for f in json.load(open(de_geo))['features']:
    feats.append((f['properties']['key'], shape(f['geometry'])))
log('DE', sum(1 for k, _ in feats if k.startswith('D-')), 'Leitregionen aus', len(keep), 'PLZ')


def assign(polys, iso, prefix):
    """Gemeinden -> Leitregion nach Mehrheit der GeoNames-Orte, sonst naechster Ort."""
    pts = [Point(lon, lat) for _, _, lon, lat in gn[iso]]
    codes = [plz[:2] for plz, _, _, _ in gn[iso]]
    tree = STRtree(pts)
    out = defaultdict(list)
    for g in polys:
        hit = [codes[i] for i in tree.query(g, predicate='contains')]
        if hit:
            k = Counter(hit).most_common(1)[0][0]
        else:
            k = codes[tree.nearest(g.representative_point())]
        out[prefix + k].append(g)
    return [(k, unary_union(v)) for k, v in out.items()]


# ---------------------------------------------------------------- AT
at = json.load(open(P('gemeinden_995_geo.json'), encoding='utf-8'))
at_polys = [shape(f['geometry']).buffer(0) for f in at['features'] if f['properties']['iso'] != '90001']
n0 = len(feats)
feats += assign(at_polys, 'AT', 'A-')
log('AT', len(feats) - n0, 'Leitregionen aus', len(at_polys), 'Gemeinden')

# ---------------------------------------------------------------- CH
lv95 = Transformer.from_crs('EPSG:2056', 'EPSG:4326', always_xy=True).transform


def shp(path):
    out = []
    for s in shapefile.Reader(path).shapes():
        g = shape(s.__geo_interface__)
        out.append(transform(lv95, g).buffer(0))
    return out


lakes = unary_union(shp(P('package', '2026', 'lakes')))
ch_polys = [g.difference(lakes) for g in shp(P('package', '2026', 'municipalities'))]
ch_polys = [g for g in ch_polys if not g.is_empty]
n0 = len(feats)
feats += assign(ch_polys, 'CH', 'CH-')
log('CH', len(feats) - n0, 'Leitregionen aus', len(ch_polys), 'Gemeinden')

# ---------------------------------------------------------------- NL
seen, pts = set(), []
for plz, _, lon, lat in gn['NL']:
    if plz not in seen:
        seen.add(plz); pts.append((plz, Point(lon, lat)))
nl = outline['NL']
cells = voronoi_polygons(MultiPoint([p for _, p in pts]), extend_to=nl.envelope.buffer(0.5))
ctree = STRtree([p for _, p in pts])
by = defaultdict(list)
for c in cells.geoms:
    i = ctree.query(c, predicate='contains')
    if len(i):
        by['NL-' + pts[i[0]][0][:2]].append(c.intersection(nl))
n0 = len(feats)
feats += [(k, unary_union(v)) for k, v in by.items()]
log('NL', len(feats) - n0, 'Leitregionen aus', len(pts), 'PC4-Mittelpunkten')

# ------------------------------------------- vereinfachen und projizieren
raw = os.path.join(TMP, 'all.geojson')
json.dump({'type': 'FeatureCollection', 'features': [
    {'type': 'Feature', 'properties': {'key': k, 'land': k.split('-')[0]}, 'geometry': mapping(g)}
    for k, g in feats if not g.is_empty]}, open(raw, 'w'))
LAEA = '+proj=laea +lat_0=52 +lon_0=10 +x_0=0 +y_0=0 +R=6378137 +units=m'
prj = os.path.join(TMP, 'prj.geojson'), os.path.join(TMP, 'land.geojson')
ms('-i', raw, '-proj', LAEA, '-clean', '-simplify', 'weighted', '1.2%', 'keep-shapes',
   '-filter-islands', 'min-area=4km2', '-o', prj[0], 'format=geojson')
ms('-i', prj[0], '-dissolve', 'land', '-o', prj[1], 'format=geojson')


def rings(geom):
    t = geom['type']
    polys = [geom['coordinates']] if t == 'Polygon' else geom['coordinates'] if t == 'MultiPolygon' else []
    return [r for poly in polys for r in poly]


fs = json.load(open(prj[0]))['features']
ls = json.load(open(prj[1]))['features']
xs = [c[0] for f in fs for r in rings(f['geometry']) for c in r]
ys = [c[1] for f in fs for r in rings(f['geometry']) for c in r]
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
W = 1000.0
s = W / (x1 - x0)
H = round((y1 - y0) * s, 1)


def d(geom):
    out = []
    for r in rings(geom):
        pts = [((x - x0) * s, (y1 - y) * s) for x, y in r]
        out.append('M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in pts[:-1]) + 'Z')
    return ''.join(out)


# Name je Gebiet: einwohnerstaerkster Ort im Gebiet (ohne Stadtteile), sonst
# der Ort mit den meisten Postleitzahlen laut GeoNames
NM = {p: names(i) for p, i in LAND.items()}
cities = [c for c in json.load(open(P('cities.json'), encoding='utf-8')) if c[5] != 'PPLX']
ctree = STRtree([Point(c[3], c[4]) for c in cities])
LOCAL = {'Vienna': 'Wien', 'Munich': 'München', 'The Hague': 'Den Haag', 'Sitten': 'Sion',
         'Almere Stad': 'Almere', 'Sankt Gallen': 'St. Gallen', 'Genève': 'Genf',
         'Priel': 'Wolfsberg'}           # Priel ist ein Ortsteil von Wolfsberg
per = defaultdict(lambda: defaultdict(set))
for p, i in LAND.items():
    for plz, ort, _, _ in gn[i]:
        per[p + '-' + plz[:2]][re.split(r'\s*[,(/]', ort)[0].strip()].add(plz)
label = {}
for k, g in feats:
    hit = [cities[i] for i in ctree.query(g, predicate='contains')]
    land, code = k.split('-')
    hit = [c for c in hit if c[0] == LAND[land]]
    # Grossstadt mit vielen eigenen PLZ (Berlin, Hamburg, Wien ...) vor dem groessten Ort
    top = max(per[k].items(), key=lambda kv: len(kv[1]), default=(None, ()))
    if len(top[1]) >= 10:
        name = top[0]
    elif hit:
        name = max(hit, key=lambda c: c[2])[1]
    else:
        name = NM[land].get(code, '')
    label[k] = LOCAL.get(name, name)
f_out = []
for f in sorted(fs, key=lambda f: f['properties']['key']):
    k = f['properties']['key']
    f_out.append([k, label.get(k, ''), d(f['geometry'])])
geo = {'vb': [W, H], 'f': f_out,
       'land': [[f['properties']['land'], d(f['geometry'])] for f in ls]}
log('Gesamt', len(f_out), 'Gebiete')
print('/* PLZ-Gebiete (Leitregionen). Geometrie: (c) OpenStreetMap-Mitwirkende (ODbL), '
      'Statistik Austria (CC BY 4.0), swisstopo, GeoNames (CC BY 4.0), Natural Earth. '
      'Projektion ETRS89-LAEA. Erzeugt mit geo/make_plz_geo.py */')
print('GEO.plz=' + json.dumps(geo, separators=(',', ':'), ensure_ascii=False) + ';')
