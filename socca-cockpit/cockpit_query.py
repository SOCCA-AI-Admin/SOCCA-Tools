"""Abfrage-Engine über data.json — dieselben Definitionen wie im Cockpit.

Wird vom Frage-Server (ask_server.py) als Werkzeug für Claude genutzt.
Rechnet ausschließlich aus web/data.json; es gibt keine zweite Datenquelle.
"""
import datetime
import json
import os
import threading
from collections import defaultdict

DAY0 = datetime.date(2019, 1, 1)
LEAD_CUT_M = (2024 - 2019) * 12          # ab hier tagesgenaue Anfragen aus Combit

TEAM_GROUPS = {
    'futl': ('Fußball Trainingslager (FU…, ohne FUTU)', lambda c: c.startswith('FU') and c != 'FUTU'),
    'futu': ('Fußballturniere (FUTU)', lambda c: c == 'FUTU'),
    'teca': ('Tennis (TECA)', lambda c: c == 'TECA'),
    'swim': ('Schwimmen (SWIM)', lambda c: c == 'SWIM'),
    'latr': ('Leichtathletik (LATR)', lambda c: c == 'LATR'),
    'haba': ('Handball (HABA)', lambda c: c == 'HABA'),
}

# id: (Name, Formel über die Rohsummen b, Art)  Art: n=Anzahl, eur, pct, fac
METRICS = {
    'leads':   ('Unique Anfragen (je Kunde, Team, AP-Jahr; je Hotel: je angefragtem Hotel)', lambda b: b['leads'], 'n'),
    'web':     ('Unique Web-Anfragen', lambda b: b['web'], 'n'),
    'props':   ('Angebote', lambda b: b['props'], 'n'),
    'teams':   ('Teams (Summe der Spalte Teams)', lambda b: b['teams'], 'n'),
    'book':    ('Buchungen', lambda b: b['book'], 'n'),
    'vk':      ('Umsatz (VK)', lambda b: b['vk'], 'eur'),
    'ek':      ('Einkauf (EK)', lambda b: b['ek'], 'eur'),
    'db':      ('Deckungsbeitrag (MargIn = VK − EK)', lambda b: b['db'], 'eur'),
    'ros':     ('ROS = DB / Umsatz', lambda b: b['db'] / b['vk'] if b['vk'] else None, 'pct'),
    'pax':     ('Pax', lambda b: b['pax'], 'n'),
    'nights':  ('Übernachtungen = Σ Pax × Nächte', lambda b: b['paxn'], 'n'),
    'anights': ('Ø Nächte je Buchung', lambda b: b['nights'] / b['book'] if b['book'] else None, 'n'),
    'apax':    ('Ø Pax je Buchung', lambda b: b['pax'] / b['book'] if b['book'] else None, 'n'),
    'leads_all': ('Anfragen gesamt (jede Anfrage-Zeile in C_AP, ohne Unique-Regel; erst ab 01/2024)', lambda b: b['leads_all'], 'n'),
    'quote1':  ('Angebote je Unique Anfrage = Angebote / Unique Anfragen', lambda b: b['props'] / b['leads'] if b['leads'] else None, 'fac'),
    'quote2':  ('Buchungsquote = Buchungen / Unique Anfragen', lambda b: b['book'] / b['leads'] if b['leads'] else None, 'pct'),
    'quote3':  ('Abschlussquote = Buchungen / Angebote', lambda b: b['book'] / b['props'] if b['props'] else None, 'pct'),
    'webq':    ('Web-Anteil der Unique Anfragen', lambda b: b['web'] / b['leads'] if b['leads'] else None, 'pct'),
    'uteam':   ('Umsatz je Team', lambda b: b['vk'] / b['teams'] if b['teams'] else None, 'eur'),
    'dbteam':  ('DB je Team', lambda b: b['db'] / b['teams'] if b['teams'] else None, 'eur'),
    'ubook':   ('Umsatz je Buchung', lambda b: b['vk'] / b['book'] if b['book'] else None, 'eur'),
    'dbbook':  ('DB je Buchung', lambda b: b['db'] / b['book'] if b['book'] else None, 'eur'),
    'mpn':     ('Marge/Pax/Nacht = DB / (ØPax × ØNächte × Teams)',
                lambda b: (b['db'] / ((b['pax'] / b['book']) * (b['nights'] / b['book']) * b['teams'])
                           if b['book'] and b['teams'] and b['pax'] and b['nights'] else None), 'eur'),
    'fte':     ('FTE (Mittel der Monate)', lambda b: b['fte'], 'n'),
    'leadfte': ('Unique Anfragen je FTE', lambda b: b['leads'] / b['fte'] if b['fte'] and b['leads'] is not None else None, 'n'),
    'bookfte': ('Buchungen je FTE', lambda b: b['book'] / b['fte'] if b['fte'] else None, 'n'),
    'teamfte': ('Teams je FTE', lambda b: b['teams'] / b['fte'] if b['fte'] else None, 'n'),
    'vkfte':   ('Umsatz je FTE', lambda b: b['vk'] / b['fte'] if b['fte'] else None, 'eur'),
    'dbfte':   ('DB je FTE', lambda b: b['db'] / b['fte'] if b['fte'] else None, 'eur'),
    'ap_teams': ('Annual Planning: geplante Teams', lambda b: b['ap'], 'n'),
    'ap_delta': ('Teams minus Plan', lambda b: b['teams'] - b['ap'] if b['ap'] is not None else None, 'n'),
    'ap_pct':  ('Zielerreichung Teams = Teams / Plan', lambda b: b['teams'] / b['ap'] if b['ap'] else None, 'pct'),
    'ap_leads': ('Annual Planning: geplante Unique Anfragen (AP-Teams des Folgemonats / Vorjahresquote Teams÷Anfragen bzw. feste BuQ aus Blatt AP)',
                 lambda b: b['apl'], 'n'),
    'ap_leads_delta': ('Unique Anfragen minus AP-Anfragen', lambda b: b['leads'] - b['apl'] if b['apl'] is not None and b['leads'] is not None else None, 'n'),
    'ap_leads_pct': ('Zielerreichung Anfragen = Unique Anfragen / AP-Anfragen', lambda b: b['leads'] / b['apl'] if b['apl'] and b['leads'] is not None else None, 'pct'),
}
LEAD_METRICS = {'leads', 'web', 'props', 'quote1', 'quote2', 'quote3', 'webq', 'leadfte'}
ALL_LEAD_METRICS = {'leads_all'}
FTE_METRICS = {'fte', 'leadfte', 'bookfte', 'teamfte', 'vkfte', 'dbfte'}
AP_METRICS = {'ap_teams', 'ap_delta', 'ap_pct'}
APL_METRICS = {'ap_leads', 'ap_leads_delta', 'ap_leads_pct'}

GROUP_BY = ['none', 'team', 'team_group', 'month', 'quarter', 'calendar_year', 'fiscal_year',
            'destination', 'origin_country', 'region', 'hotel', 'sport']
TIME_GROUPS = {'month', 'quarter', 'calendar_year', 'fiscal_year'}

ALIASES = {'DE': 'D', 'AT': 'A', 'IT': 'I', 'GER': 'D', 'AUT': 'A', 'ITA': 'I'}


def d2i(d):
    return (d - DAY0).days


def i2d(i):
    return DAY0 + datetime.timedelta(days=i)


def m2d(m):
    return datetime.date(2019 + m // 12, m % 12 + 1, 1)


def midx(d):
    return (d.year - 2019) * 12 + d.month - 1


def shift_year(d, n):
    try:
        return d.replace(year=d.year + n)
    except ValueError:                       # 29. Februar
        return d.replace(year=d.year + n, day=28)


def bucket_of(d, kind):
    if kind == 'month':
        return f'{d.year}-{d.month:02d}'
    if kind == 'quarter':
        return f'{d.year}-Q{(d.month - 1) // 3 + 1}'
    if kind == 'calendar_year':
        return str(d.year)
    if kind == 'fiscal_year':
        y = d.year if d.month >= 7 else d.year - 1
        return f'GJ {y}/{str(y + 1)[2:]}'
    return 'Gesamt'


def empty():
    return dict(book=0, teams=0.0, pax=0.0, nights=0.0, paxn=0.0, vk=0.0, ek=0.0, db=0.0,
                leads=0, web=0, props=0, leads_all=0, fte=None, ap=None, apl=None)


class Cockpit:
    def __init__(self, path):
        self.path = path
        self._mtime = None
        self._lock = threading.Lock()
        self.reload()

    # ------------------------------------------------------------ Laden
    def reload(self):
        with self._lock:
            mt = os.path.getmtime(self.path)
            if mt == self._mtime:
                return
            D = json.load(open(self.path, encoding='utf-8'))
            self.D = D
            self._mtime = mt
            self.hotel_by_idx = D['hotels']
            self.hidx_by_webid = {h[0]: i for i, h in enumerate(D['hotels'])}
            self.first_day = min(r[0] for r in D['bookings'])
            self.last_day = max(r[0] for r in D['bookings'])
            self.last_lead_day = max((r[0] for r in D['leadDaily']), default=None)

    def maybe_reload(self):
        try:
            if os.path.getmtime(self.path) != self._mtime:
                self.reload()
        except OSError:
            pass

    # ------------------------------------------------------ Übersicht
    def overview(self):
        D = self.D
        return {
            'datenstand': {
                'erste_buchung': i2d(self.first_day).isoformat(),
                'letzte_buchung': i2d(self.last_day).isoformat(),
                'letzte_anfrage': i2d(self.last_lead_day).isoformat() if self.last_lead_day is not None else None,
                'erzeugt': D['meta'].get('generated'),
                'quellen': D['meta'].get('sources'),
            },
            'regeln': [
                'Stichtag aller Buchungs-, Umsatz- und DB-Kennzahlen ist das Buchungsdatum, nicht das Reisedatum.',
                'Geschäftsjahr (GJ, Annual Planning AP) läuft von 1. Juli bis 30. Juni; GJ 2025/26 = AP2025/26 = 01.07.2025–30.06.2026.',
                'Unique Anfragen, Web-Anfragen und Angebote tagesgenau ab 01.01.2024 (Combit); davor nur monatlich je Team, ohne Länder/Hotel.',
                'Begriffe: „Unique Anfragen“ (Kennzahl leads) = eine Mail-Adresse zählt einmal je Sales-Team und AP-Jahr; „Anfragen gesamt“ (leads_all) = jede Anfrage-Zeile. Sagt jemand nur „Anfragen“, sind die Unique Anfragen gemeint. Auf Hotelebene zählt eine Anfrage bei jedem Hotel, das der Kunde angefragt hat — Summe der Hotels > Gesamtzahl.',
                'Angebote werden je Angebotszeile gezählt, datiert auf das Versanddatum.',
                'Buchungsquote (quote2) = Buchungen / Unique Anfragen; Abschlussquote (quote3) = Buchungen / Angebote. Den Begriff „Buchungsrate“ gibt es nicht mehr.',
                'Für Regionen (Bundesländer/Kantone) und Sportarten gibt es keine Anfragen/Angebote, nur Buchungsdaten.',
                'Anfragen und Angebote je Hotel gibt es je Team und je Reiseland (= Land des Hotels), aber nicht je Herkunftsland, Region oder Sportart.',
                'FTE und Annual Planning (Teams und Anfragen) gibt es nur je Team bzw. gesamt, nicht je Land, Region, Hotel oder Sportart. AP-Anfragen je Monat = AP-Teams des Folgemonats / Quote des Folgemonats im Vorjahr (Teams ÷ Unique Anfragen des Vormonats); ist im Blatt AP eine BuQ von Hand eingetragen, gilt diese.',
            ],
            'teams': D['teams'],
            'team_groups': {k: v[0] for k, v in TEAM_GROUPS.items()},
            'destinations': {c: D['countries'].get(c, c) for c in D['dests']},
            'origin_countries': {c: D['countries'].get(c, c) for c in D['regs']},
            'sports': D['sports'],
            'metrics': {k: v[0] for k, v in METRICS.items()},
            'group_by': GROUP_BY,
        }

    def find_hotels(self, text, limit=15):
        text = str(text or '').strip().lower()
        out = []
        for h in self.D['hotels']:
            if text.isdigit() and str(h[0]).startswith(text) or (text and text in (h[1] or '').lower()):
                out.append({'webid': h[0], 'name': h[1], 'land': h[2]})
            if len(out) >= limit:
                break
        return {'treffer': out, 'anzahl': len(out)}

    # ------------------------------------------------------- Filter
    def _norm_countries(self, vals, allowed):
        if not vals:
            return None
        names = {v.lower(): k for k, v in self.D['countries'].items()}
        out = set()
        for v in vals:
            s = str(v).strip()
            c = ALIASES.get(s.upper(), s.upper())
            if c in allowed:
                out.add(c)
            elif s.lower() in names:
                out.add(names[s.lower()])
            else:
                raise ValueError(f'Unbekanntes Land: {v}. Erlaubt: {", ".join(sorted(allowed))}')
        return out

    def _team_set(self, teams, groups):
        allt = self.D['teams']
        sel = set(allt)
        if groups:
            g = set()
            for gid in groups:
                if gid not in TEAM_GROUPS:
                    raise ValueError(f'Unbekannte Teamgruppe: {gid}. Erlaubt: {", ".join(TEAM_GROUPS)}')
                g |= {t for t in allt if TEAM_GROUPS[gid][1](t)}
            sel &= g
        if teams:
            want = {str(t).strip().upper() for t in teams}
            bad = want - set(allt)
            if bad:
                raise ValueError(f'Unbekannte Teams: {", ".join(sorted(bad))}. Erlaubt: {", ".join(allt)}')
            sel &= want
        return sel

    def _regions(self, vals):
        if not vals:
            return None
        out = set()
        for v in vals:
            s = str(v).strip().lower()
            hit = {i for i, r in enumerate(self.D['regions'])
                   if s == r[1].lower() or s == r[2].lower() or s in r[2].lower()}
            if not hit:
                raise ValueError(f'Unbekannte Region: {v}')
            out |= hit
        return out

    def _hotels(self, vals):
        if not vals:
            return None
        out = set()
        for v in vals:
            try:
                w = int(str(v).strip())
            except ValueError:
                raise ValueError(f'Hotels bitte als WebID angeben (find_hotels nutzen): {v}')
            if w not in self.hidx_by_webid:
                raise ValueError(f'Unbekannte WebID: {w}')
            out.add(self.hidx_by_webid[w])
        return out

    # ------------------------------------------------------- Abfrage
    def query(self, metrics, date_from, date_to, group_by='none', filters=None,
              sort_by=None, sort_desc=True, limit=25, compare_previous_year=False):
        self.maybe_reload()
        filters = filters or {}
        metrics = [m for m in (metrics or []) if m]
        if not metrics:
            raise ValueError('Mindestens eine Kennzahl angeben.')
        bad = [m for m in metrics if m not in METRICS]
        if bad:
            raise ValueError(f'Unbekannte Kennzahl(en): {", ".join(bad)}. Erlaubt: {", ".join(METRICS)}')
        if group_by not in GROUP_BY:
            raise ValueError(f'group_by muss eines von {GROUP_BY} sein.')
        f = datetime.date.fromisoformat(str(date_from)[:10])
        t = datetime.date.fromisoformat(str(date_to)[:10])
        if t < f:
            f, t = t, f
        limit = max(1, min(int(limit or 25), 100))

        spec = dict(
            teams=self._team_set(filters.get('teams'), filters.get('team_groups')),
            dest=self._norm_countries(filters.get('destinations'), set(self.D['dests'])),
            herk=self._norm_countries(filters.get('origin_countries'), set(self.D['regs'])),
            region=self._regions(filters.get('regions')),
            hotel=self._hotels(filters.get('hotels')),
            sport=({str(s).upper() for s in filters['sports']} if filters.get('sports') else None),
        )
        notes = []
        cur = self._agg(f, t, group_by, spec, notes, 0)
        vj = self._agg(shift_year(f, -1), shift_year(t, -1), group_by, spec, [], 1) if compare_previous_year else None

        rows = []
        for key, b in cur.items():
            row = {'gruppe': self._label(group_by, key)}
            for m in metrics:
                row[m] = self._val(m, b, spec, group_by)
                if vj is not None:
                    bv = vj.get(key)
                    v0 = self._val(m, bv, spec, group_by) if bv else None
                    row[m + '_vj'] = v0
                    v1 = row[m]
                    row[m + '_delta_pct'] = (round((v1 - v0) / abs(v0) * 100, 1)
                                             if v0 not in (None, 0) and v1 is not None else None)
            rows.append(row)

        # Summe = dieselbe Abfrage ohne Gruppierung (wie die Kacheln im Cockpit)
        total_b = self._agg(f, t, 'none', spec, [], 0).get('Gesamt')
        total = {'gruppe': 'Summe'}
        for m in metrics:
            total[m] = self._val(m, total_b, spec, 'none')
        if vj is not None:
            tv = self._agg(shift_year(f, -1), shift_year(t, -1), 'none', spec, [], 1).get('Gesamt')
            for m in metrics:
                v0 = self._val(m, tv, spec, 'none')
                total[m + '_vj'] = v0
                total[m + '_delta_pct'] = (round((total[m] - v0) / abs(v0) * 100, 1)
                                           if v0 not in (None, 0) and total[m] is not None else None)

        if group_by in TIME_GROUPS:
            rows.sort(key=lambda r: r['gruppe'])
        else:
            sk = sort_by if sort_by in metrics else metrics[0]
            rows.sort(key=lambda r: (r[sk] is None, -(r[sk] or 0) if sort_desc else (r[sk] or 0)))
        n_all = len(rows)
        rows = rows[:limit]

        if group_by == 'hotel' and 'leads' in metrics:
            notes.append('Anfragen je Hotel: jede Anfrage zählt bei jedem angefragten Hotel; die Summe über Hotels ist größer als die unique Anfragen.')
        for m in metrics:
            if m in FTE_METRICS | AP_METRICS | APL_METRICS and (spec['dest'] or spec['herk'] or spec['region']
                                                   or spec['hotel'] or spec['sport']
                                                   or group_by in ('destination', 'origin_country', 'region', 'hotel', 'sport')):
                notes.append(f'{m}: FTE/Plan gibt es nur je Team oder gesamt — hier leer.')
                break
        return {
            'zeitraum': {'von': f.isoformat(), 'bis': t.isoformat(),
                         'vorjahr': ({'von': shift_year(f, -1).isoformat(), 'bis': shift_year(t, -1).isoformat()}
                                     if compare_previous_year else None)},
            'gruppierung': group_by,
            'filter': {k: (sorted(v) if isinstance(v, set) else v) for k, v in filters.items() if v},
            'zeilen': rows, 'zeilen_gesamt': n_all, 'summe': total,
            'hinweise': sorted(set(notes)),
            'einheiten': {m: METRICS[m][2] for m in metrics},
        }

    # ---------------------------------------------------------- intern
    def _label(self, g, key):
        if g == 'hotel':
            h = self.hotel_by_idx[key]
            return f'{h[1]} (WebID {h[0]}, {h[2] or "?"})'
        if g in ('destination', 'origin_country'):
            return f'{self.D["countries"].get(key, key)} ({key})' if key else 'unbekannt'
        if g == 'region':
            r = self.D['regions'][key] if isinstance(key, int) and key >= 0 else None
            return f'{r[2]} ({r[0]})' if r else 'ohne Region'
        if g == 'team_group':
            return TEAM_GROUPS[key][0] if key in TEAM_GROUPS else 'andere Teams'
        return key if key is not None else 'unbekannt'

    def _key_booking(self, g, r, d):
        D = self.D
        if g == 'none':
            return 'Gesamt'
        if g in TIME_GROUPS:
            return bucket_of(d, g)
        if g == 'team':
            return self._at(D['teams'], r[1])
        if g == 'team_group':
            return self._group_of(self._at(D['teams'], r[1]))
        if g == 'destination':
            return self._at(D['dests'], r[12])
        if g == 'origin_country':
            return self._at(D['regs'], r[3])
        if g == 'region':
            return r[11]
        if g == 'hotel':
            return r[4]
        if g == 'sport':
            return self._at(D['sports'], r[2])

    @staticmethod
    def _at(lst, i):
        """Listenzugriff ohne Pythons negative Indizes (-1 = unbekannt)."""
        return lst[i] if i is not None and 0 <= i < len(lst) else None

    @staticmethod
    def _group_of(team):
        for k, (_, test) in TEAM_GROUPS.items():
            if test(team):
                return k
        return 'other'

    def _agg(self, f, t, g, spec, notes, shift):
        """Rohsummen je Gruppe. shift=1: Vorjahresdaten, Zeitschlüssel um ein Jahr nach vorn."""
        D = self.D
        fi, ti = d2i(f), d2i(t)
        out = defaultdict(empty)
        kd = (lambda d: shift_year(d, shift)) if shift else (lambda d: d)

        for r in D['bookings']:
            if r[0] < fi or r[0] > ti:
                continue
            if self._at(D['teams'], r[1]) not in spec['teams']:
                continue
            if spec['dest'] and self._at(D['dests'], r[12]) not in spec['dest']:
                continue
            if spec['herk'] and self._at(D['regs'], r[3]) not in spec['herk']:
                continue
            if spec['region'] and r[11] not in spec['region']:
                continue
            if spec['hotel'] and r[4] not in spec['hotel']:
                continue
            if spec['sport'] and self._at(D['sports'], r[2]) not in spec['sport']:
                continue
            if g == 'hotel' and r[4] < 0:
                continue
            b = out[self._key_booking(g, r, kd(i2d(r[0])))]
            b['book'] += 1; b['vk'] += r[5]; b['ek'] += r[6]; b['db'] += r[7]
            b['teams'] += r[8]; b['pax'] += r[9]; b['nights'] += r[10]; b['paxn'] += r[9] * r[10]

        # ---- Anfragen / Angebote
        # Je Hotel liegen sie je Team vor; Reiseland = Land des Hotels.
        # Für Herkunft, Region und Sportart gibt es keine Anfragen.
        lead_na = bool(spec['region'] or spec['sport'] or g in ('region', 'sport'))
        hotel_mode = bool(spec['hotel'] or g == 'hotel')
        if hotel_mode and (spec['herk'] or g == 'origin_country'):
            lead_na = True
        if lead_na:
            notes.append('Anfragen/Angebote sind für diese Kombination aus Filter und Gruppierung nicht verfügbar.')
            for b in out.values():
                b['leads'] = b['web'] = b['props'] = b['leads_all'] = None
        elif hotel_mode:
            all_teams = spec['teams'] == set(D['teams'])
            for r in D['leadHotel']:
                if r[0] < fi or r[0] > ti:
                    continue
                if spec['hotel'] and r[1] not in spec['hotel']:
                    continue
                land = self.hotel_by_idx[r[1]][2]
                if spec['dest'] and land not in spec['dest']:
                    continue
                team = self._at(D['teams'], r[2])
                if not all_teams and team not in spec['teams']:
                    continue
                d = kd(i2d(r[0]))
                if g == 'hotel':
                    key = r[1]
                elif g == 'team':
                    key = team
                elif g == 'team_group':
                    key = self._group_of(team) if team else 'other'
                elif g == 'destination':
                    key = land
                elif g in TIME_GROUPS:
                    key = bucket_of(d, g)
                else:
                    key = 'Gesamt'
                b = out[key]
                b['leads'] += r[3]; b['web'] += r[4]; b['props'] += r[5]
                b['leads_all'] += r[6] if len(r) > 6 else 0
            if f < datetime.date(2024, 1, 1):
                notes.append('Anfragen je Hotel gibt es erst ab 01.01.2024.')
            if spec['dest']:
                notes.append('Anfragen/Angebote je Hotel: Reiseland = Land des Hotels.')
        else:
            for r in D['leadDaily']:
                if r[0] < fi or r[0] > ti:
                    continue
                team = self._at(D['teams'], r[1])
                if team not in spec['teams']:
                    continue
                if spec['dest'] and self._at(D['dests'], r[3]) not in spec['dest']:
                    continue
                if spec['herk'] and self._at(D['regs'], r[2]) not in spec['herk']:
                    continue
                d = kd(i2d(r[0]))
                if g == 'team':
                    key = team
                elif g == 'team_group':
                    key = self._group_of(team)
                elif g == 'destination':
                    key = self._at(D['dests'], r[3])
                elif g == 'origin_country':
                    key = self._at(D['regs'], r[2])
                elif g in TIME_GROUPS:
                    key = bucket_of(d, g)
                else:
                    key = 'Gesamt'
                b = out[key]
                b['leads'] += r[4]; b['web'] += r[5]; b['props'] += r[6]
                b['leads_all'] += r[7] if len(r) > 7 else 0
            # vor 2024: nur ganze Monate, nur je Team, ohne Länder
            mf, mt = midx(f), midx(t)
            if mf < LEAD_CUT_M:
                if spec['dest'] or spec['herk'] or g in ('destination', 'origin_country'):
                    notes.append('Anfragen vor 2024 gibt es nur je Team, nicht je Land — für diesen Teil fehlen sie.')
                else:
                    full_from = mf if f.day == 1 else mf + 1
                    nxt = (t + datetime.timedelta(days=1))
                    full_to = mt if nxt.day == 1 else mt - 1
                    partial = False
                    for src, fld in ((D['leadMonthly'], 'leads'), (D['propMonthly'], 'props')):
                        for r in src:
                            m = r[0]
                            if m >= LEAD_CUT_M or m < mf or m > mt:
                                continue
                            team = self._at(D['teams'], r[1])
                            if team not in spec['teams']:
                                continue
                            if m < full_from or m > full_to:
                                partial = True
                                continue
                            d = kd(m2d(m))
                            key = (team if g == 'team' else self._group_of(team) if g == 'team_group'
                                   else bucket_of(d, g) if g in TIME_GROUPS else 'Gesamt')
                            out[key][fld] += r[2]
                    notes.append('Anfragen vor 2024 stammen aus dem Blatt Leads (monatlich, ohne Web-Anteil).')
                    if partial:
                        notes.append('Angebrochene Monate vor 2024 sind bei Anfragen/Angeboten nicht enthalten.')

        if f < datetime.date(2024, 1, 1) and not lead_na:
            for b in out.values():
                b['leads_all'] = None
            notes.append('Anfragen gesamt gibt es erst ab 01.01.2024.')

        # ---- FTE und Annual Planning (nur je Team, Teamgruppe, Zeit, gesamt)
        dim = spec['dest'] or spec['herk'] or spec['region'] or spec['hotel'] or spec['sport']
        if not dim and g in {'none', 'team', 'team_group'} | TIME_GROUPS:
            mf, mt = midx(f), midx(t)
            per = defaultdict(lambda: defaultdict(float))
            for r in D['fte']:
                if r[0] < mf or r[0] > mt:
                    continue
                team = self._at(D['teams'], r[1])
                if team not in spec['teams']:
                    continue
                key = (team if g == 'team' else self._group_of(team) if g == 'team_group'
                       else bucket_of(kd(m2d(r[0])), g) if g in TIME_GROUPS else 'Gesamt')
                per[key][r[0]] += r[2]
            for key, months in per.items():
                out[key]['fte'] = sum(months.values()) / len(months)
            for r in D['ap']:
                if r[0] < mf or r[0] > mt:
                    continue
                team = self._at(D['teams'], r[1])
                if team not in spec['teams']:
                    continue
                key = (team if g == 'team' else self._group_of(team) if g == 'team_group'
                       else bucket_of(kd(m2d(r[0])), g) if g in TIME_GROUPS else 'Gesamt')
                out[key]['ap'] = (out[key]['ap'] or 0) + r[2]
            for r in D.get('apLeads') or []:
                if r[0] < mf or r[0] > mt:
                    continue
                team = self._at(D['teams'], r[1])
                if team not in spec['teams']:
                    continue
                key = (team if g == 'team' else self._group_of(team) if g == 'team_group'
                       else bucket_of(kd(m2d(r[0])), g) if g in TIME_GROUPS else 'Gesamt')
                out[key]['apl'] = (out[key]['apl'] or 0) + r[2]
            if f.day != 1 or (t + datetime.timedelta(days=1)).day != 1:
                notes.append('FTE und Plan werden für jeden berührten Monat voll gezählt.')
        return out

    def _val(self, m, b, spec, g):
        if b is None:
            return None
        if m in LEAD_METRICS and b.get('leads') is None:
            return None
        if m in ALL_LEAD_METRICS and (b.get('leads_all') is None or b.get('leads') is None):
            return None
        if m in FTE_METRICS and not b.get('fte'):
            return None
        if m in AP_METRICS and b.get('ap') is None:
            return None
        if m in APL_METRICS and b.get('apl') is None:
            return None
        if m in ('ap_leads_delta', 'ap_leads_pct') and b.get('leads') is None:
            return None
        try:
            v = METRICS[m][1](b)
        except (TypeError, ZeroDivisionError):
            return None
        if v is None:
            return None
        kind = METRICS[m][2]
        return round(v, 4) if kind in ('pct', 'fac') else round(v, 2)

