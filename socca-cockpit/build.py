#!/usr/bin/env python3
"""Baut das Sales Cockpit aus dashboard.tpl.html und data.json.

    python3 build.py [data.json] [ausgabeordner]

Erzeugt
  <ordner>/index.html              laedt data.json nach - fuer den Webserver
  <ordner>/data.json               Kopie der Datendatei
  SOCCA_Sales_Cockpit.html         Daten eingebettet - zum Weitergeben
  artifact_body.html               Daten eingebettet, ohne Dokumentrahmen
"""
import sys, os, json, shutil, pathlib

base = pathlib.Path(__file__).parent
data_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else base / 'web' / 'data.json'
outdir = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else base / 'web'
outdir.mkdir(parents=True, exist_ok=True)

tpl = (base / 'dashboard.tpl.html').read_text(encoding='utf-8')
tpl = tpl.replace('/*__GEO__*/', (base / 'geo' / 'geo.js').read_text(encoding='utf-8'))
tpl = tpl.replace('/*__I18N__*/', (base / 'i18n.js').read_text(encoding='utf-8'))
tpl = tpl.replace('/*__REPORTS__*/', (base / 'reports.js').read_text(encoding='utf-8'))
data = data_path.read_text(encoding='utf-8')

HEAD = ('<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n')

def document(body):
    style, rest = body.split('</style>', 1)
    return HEAD + style + '</style>\n</head>\n<body>\n' + rest + '\n</body>\n</html>\n'

inline = tpl.replace('/*__BOOT__*/', 'start(' + data + ');')
(base / 'artifact_body.html').write_text(inline, encoding='utf-8')
(base / 'SOCCA_Sales_Cockpit.html').write_text(document(inline), encoding='utf-8')

remote = tpl.replace('/*__BOOT__*/', """
fetch('data.json?v=' + Date.now())
  .then(r => { if(!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
  .then(start)
  .catch(e => {
    document.querySelector('.wrap').innerHTML =
      '<div class="card"><h2>Daten nicht erreichbar</h2><p style="margin-top:12px">' +
      'data.json konnte nicht geladen werden (' + e.message + '). Liegt die Datei neben index.html ' +
      'und laeuft die Seite ueber einen Webserver statt per Doppelklick?</p></div>';
  });
""".strip())
(outdir / 'index.html').write_text(document(remote), encoding='utf-8')
if data_path.resolve() != (outdir / 'data.json').resolve():
    shutil.copyfile(data_path, outdir / 'data.json')

for f in (base / 'SOCCA_Sales_Cockpit.html', base / 'artifact_body.html',
          outdir / 'index.html', outdir / 'data.json'):
    try:
        name = str(f.resolve().relative_to(base.resolve()))
    except ValueError:
        name = str(f)
    print(f'{name:32s} {f.stat().st_size/1e6:.2f} MB')
