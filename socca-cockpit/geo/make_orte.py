#!/usr/bin/env python3
"""Ortsverzeichnis fuer die Reiseregionen -> geo/orte.tsv.gz

etl.py braucht es nur in zwei Faellen:
  1. Hotel ohne Region in Locations Spalte AO: der Ort am Anfang des
     Hotelnamens wird gesucht und die Region der naechstgelegenen Hotels
     mit gepflegter Region uebernommen.
  2. Kreise auf der Karte: Mittelpunkt einer Reiseregion = Median der
     Orte ihrer Hotels.

Quellen (GeoNames, CC BY 4.0):
  cities_all.json   Orte ab 1.000 Einwohnern mit Einwohnerzahl, aus dem
                    npm-Paket all-the-cities, Felder [Land, Name, Altnamen,
                    Einwohner, Laenge, Breite]
  allCountries.txt  GeoNames-Postleitzahlen (github.com/Aareon/GeoNamesMirror)
                    fuer kleinere Orte

    python3 geo/make_orte.py QUELLEN > /dev/null   (schreibt geo/orte.tsv.gz)
"""
import csv, gzip, json, os, re, sys

SRC = sys.argv[1]
# Laender mit SOCCA-Hotels bzw. SOCCA-Reiseregionen (Locations, Liste der Regionen)
LANDS = {'DE', 'AT', 'IT', 'ES', 'CZ', 'HR', 'TR', 'HU', 'SI', 'NL', 'PT', 'GR', 'DK', 'CY', 'CH',
         'SK', 'PL', 'MT', 'TN', 'EG', 'LI', 'AE', 'SE'}
# erstes Wort mehrteiliger Ortsnamen zusaetzlich (Desenzano del Garda -> desenzano),
# aber nicht fuer Allerweltswoerter
NOFIRST = {'bad', 'san', 'sankt', 'santa', 'santo', 'saint', 'st', 'le', 'la', 'il', 'lo', 'el', 'los',
           'las', 'de', 'den', 'der', 'die', 'das', 'nova', 'novo', 'stara', 'stari', 'gross', 'klein',
           'alt', 'neu', 'ober', 'unter', 'nieder', 'hohen', 'markt', 'mont', 'monte', 'porto', 'puerto',
           'villa', 'castel', 'castello', 'cala', 'playa', 'costa', 'lido', 'marina', 'ses', 'sa', 'es'}


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from reiseregion import norm        # dieselbe Schreibweise wie beim Nachschlagen


best = {}            # (Land, Name) -> (Rang, Laenge, Breite)


def put(land, name, lon, lat, rank):
    k = norm(name)
    if not k:
        return
    cur = best.get((land, k))
    if cur is None or rank > cur[0]:
        best[(land, k)] = (rank, lon, lat)
    w = k.split()
    if len(w) > 1 and w[0] not in NOFIRST and len(w[0]) > 3 and rank >= 1e6:
        cur = best.get((land, w[0]))
        r2 = rank - 1e6                       # Einwohnerzahl: staerker als ein Dorf gleichen Namens,
                                              # schwaecher als jede Stadt mit genau diesem Namen
        if cur is None or r2 > cur[0]:
            best[(land, w[0])] = (r2, lon, lat)


for land, name, alt, pop, lon, lat in json.load(open(os.path.join(SRC, 'cities_all.json'), encoding='utf-8')):
    if land not in LANDS:
        continue
    put(land, name, lon, lat, 1e6 + (pop or 0))
    for a in [x for x in (alt or '').split(',') if x][:6]:
        put(land, a, lon, lat, 1e6 + (pop or 0) - 1)
with open(os.path.join(SRC, 'allCountries.txt'), encoding='utf-8') as f:
    for row in csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
        if row[0] in LANDS and row[9] and row[10]:
            ort = re.split(r'\s*(?:[,(/]| b\. | bei | a\. d\. )', row[2])[0]
            put(row[0], ort, round(float(row[10]), 3), round(float(row[9]), 3), 0)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'orte.tsv.gz')
with gzip.open(out, 'wt', encoding='utf-8', compresslevel=9) as f:
    f.write('# Land\tOrt (normiert)\tLaenge\tBreite - GeoNames, CC BY 4.0, erzeugt mit geo/make_orte.py\n')
    for (land, k), (_, lon, lat) in sorted(best.items()):
        f.write(f'{land}\t{k}\t{lon:.3f}\t{lat:.3f}\n')
print(len(best), 'Orte ->', out, os.path.getsize(out), 'Bytes', file=sys.stderr)
