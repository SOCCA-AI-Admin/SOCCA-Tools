#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt i18n.js fuer das SOCCA Sales Cockpit.

    python3 make_i18n.py > ../i18n.js

Aufbau: STRINGS[schluessel][sprache]. Fehlt eine Sprache, greift Deutsch.
Laendernamen und Monatsnamen kommen zur Laufzeit aus Intl und stehen
deshalb nicht hier drin. Regionsnamen (Bayern, Zuerich) bleiben in der
Originalform, weil sie Eigennamen sind.

Fachbegriffe, die bewusst unuebersetzt bleiben: Team, Pax, FTE, ROS,
WebID, Annual Planning, Combit, SOCCA GROUP sowie die Blattnamen der
Arbeitsmappe (Sales, Leads, Props, Goals, Locations, Report).
"""
import json, sys

LANGS = [
    ('de', 'Deutsch'), ('nl', 'Nederlands'), ('es', 'Español'),
    ('it', 'Italiano'), ('hr', 'Hrvatski'), ('cs', 'Čeština'),
    ('nb', 'Norsk'), ('tr', 'Türkçe'), ('hu', 'Magyar'),
]

S = {}


def add(key, de, nl, es, it, hr, cs, nb, tr, hu):
    S[key] = dict(de=de, nl=nl, es=es, it=it, hr=hr, cs=cs, nb=nb, tr=tr, hu=hu)


# ---------------------------------------------------------------- Kopf
add('app.sub', 'Sales Reporting', 'Sales Reporting', 'Sales Reporting', 'Sales Reporting',
    'Sales Reporting', 'Sales Reporting', 'Sales Reporting', 'Sales Reporting', 'Sales Reporting')
add('theme.dark', 'Dunkel', 'Donker', 'Oscuro', 'Scuro', 'Tamno', 'Tmavé', 'Mørk', 'Koyu', 'Sötét')
add('theme.light', 'Hell', 'Licht', 'Claro', 'Chiaro', 'Svijetlo', 'Světlé', 'Lys', 'Açık', 'Világos')
add('lang.label', 'Sprache', 'Taal', 'Idioma', 'Lingua', 'Jezik', 'Jazyk', 'Språk', 'Dil', 'Nyelv')

# ---------------------------------------------------------------- Steuerung
add('ctl.from', 'Zeitraum von', 'Periode van', 'Periodo desde', 'Periodo da',
    'Razdoblje od', 'Období od', 'Periode fra', 'Dönem başlangıcı', 'Időszak ettől')
add('ctl.to', 'bis', 'tot', 'hasta', 'a', 'do', 'do', 'til', 'bitiş', 'eddig')
add('ctl.presets', 'Schnellauswahl', 'Snelkeuze', 'Selección rápida', 'Selezione rapida',
    'Brzi odabir', 'Rychlá volba', 'Hurtigvalg', 'Hızlı seçim', 'Gyorsválasztás')
add('ctl.area', 'Bereich', 'Segment', 'Área', 'Settore', 'Područje', 'Oblast', 'Område', 'Alan', 'Terület')
add('ctl.team', 'Team', 'Team', 'Equipo', 'Team', 'Tim', 'Tým', 'Team', 'Takım', 'Csapat')
add('ctl.dest', 'Reiseland', 'Bestemming', 'País de destino', 'Paese di destinazione',
    'Odredišna zemlja', 'Cílová země', 'Reiseland', 'Varış ülkesi', 'Célország')
add('ctl.herk', 'Kundenherkunft', 'Herkomst klant', 'Origen del cliente', 'Provenienza cliente',
    'Podrijetlo klijenta', 'Původ zákazníka', 'Kundens opprinnelse', 'Müşteri kaynağı', 'Ügyfél származása')
add('ctl.region', 'Region', 'Regio', 'Región', 'Regione', 'Regija', 'Region', 'Region', 'Bölge', 'Régió')
add('ctl.compare', 'Vergleich', 'Vergelijking', 'Comparación', 'Confronto',
    'Usporedba', 'Srovnání', 'Sammenligning', 'Karşılaştırma', 'Összehasonlítás')
add('ctl.py', 'Vorjahr', 'Vorig jaar', 'Año anterior', 'Anno precedente',
    'Prethodna godina', 'Předchozí rok', 'Fjorår', 'Geçen yıl', 'Előző év')
add('ctl.ap', 'Annual Planning', 'Annual Planning', 'Annual Planning', 'Annual Planning',
    'Annual Planning', 'Annual Planning', 'Annual Planning', 'Annual Planning', 'Annual Planning')

add('p.1m', 'Laufender Monat', 'Lopende maand', 'Mes actual', 'Mese corrente',
    'Tekući mjesec', 'Aktuální měsíc', 'Inneværende måned', 'İçinde bulunulan ay', 'Aktuális hónap')
add('p.3m', '3 Monate', '3 maanden', '3 meses', '3 mesi', '3 mjeseca', '3 měsíce', '3 måneder', '3 ay', '3 hónap')
add('p.12m', '12 Monate', '12 maanden', '12 meses', '12 mesi', '12 mjeseci', '12 měsíců', '12 måneder', '12 ay', '12 hónap')
add('p.gj', 'Geschäftsjahr', 'Boekjaar', 'Ejercicio', 'Esercizio',
    'Poslovna godina', 'Hospodářský rok', 'Regnskapsår', 'Mali yıl', 'Üzleti év')
add('p.kj', 'Kalenderjahr', 'Kalenderjaar', 'Año natural', 'Anno solare',
    'Kalendarska godina', 'Kalendářní rok', 'Kalenderår', 'Takvim yılı', 'Naptári év')
add('p.all', 'Alles', 'Alles', 'Todo', 'Tutto', 'Sve', 'Vše', 'Alt', 'Tümü', 'Összes')

add('all.areas', 'Alle Bereiche', 'Alle segmenten', 'Todas las áreas', 'Tutti i settori',
    'Sva područja', 'Všechny oblasti', 'Alle områder', 'Tüm alanlar', 'Minden terület')
add('all.teams', 'Alle Teams', 'Alle teams', 'Todos los equipos', 'Tutti i team',
    'Svi timovi', 'Všechny týmy', 'Alle team', 'Tüm takımlar', 'Minden csapat')
add('all.dests', 'Alle Reiseländer', 'Alle bestemmingen', 'Todos los destinos', 'Tutte le destinazioni',
    'Sve odredišne zemlje', 'Všechny cílové země', 'Alle reiseland', 'Tüm varış ülkeleri', 'Minden célország')
add('all.herks', 'Alle Herkunftsländer', 'Alle herkomstlanden', 'Todos los países de origen',
    'Tutti i paesi di provenienza', 'Sve zemlje podrijetla', 'Všechny země původu',
    'Alle opprinnelsesland', 'Tüm kaynak ülkeler', 'Minden származási ország')
add('all.regions', 'Alle Regionen', 'Alle regio’s', 'Todas las regiones', 'Tutte le regioni',
    'Sve regije', 'Všechny regiony', 'Alle regioner', 'Tüm bölgeler', 'Minden régió')

add('grp.futl', 'Fußball Trainingslager', 'Voetbal trainingskamp', 'Fútbol — campos de entrenamiento',
    'Calcio — ritiri', 'Nogomet — pripreme', 'Fotbal — soustředění', 'Fotball treningsleir',
    'Futbol kampı', 'Labdarúgó edzőtábor')
add('grp.futu', 'Fußballturniere', 'Voetbaltoernooien', 'Torneos de fútbol', 'Tornei di calcio',
    'Nogometni turniri', 'Fotbalové turnaje', 'Fotballturneringer', 'Futbol turnuvaları',
    'Labdarúgó tornák')
add('grp.teca', 'Tennis', 'Tennis', 'Tenis', 'Tennis', 'Tenis', 'Tenis', 'Tennis', 'Tenis', 'Tenisz')
add('grp.swim', 'Schwimmen', 'Zwemmen', 'Natación', 'Nuoto', 'Plivanje', 'Plavání', 'Svømming', 'Yüzme', 'Úszás')
add('grp.latr', 'Leichtathletik', 'Atletiek', 'Atletismo', 'Atletica', 'Atletika', 'Atletika',
    'Friidrett', 'Atletizm', 'Atlétika')
add('grp.haba', 'Handball', 'Handbal', 'Balonmano', 'Pallamano', 'Rukomet', 'Házená',
    'Håndball', 'Hentbol', 'Kézilabda')

# ---------------------------------------------------------------- Abschnitte
add('s.funnel', 'Funnel', 'Funnel', 'Embudo', 'Funnel', 'Lijevak', 'Trychtýř', 'Trakt', 'Huni', 'Tölcsér')
add('s.kpi', 'Kennzahlen im Zeitraum', 'Kerncijfers in de periode', 'Indicadores del periodo',
    'Indicatori del periodo', 'Pokazatelji u razdoblju', 'Ukazatele za období',
    'Nøkkeltall i perioden', 'Dönem göstergeleri', 'Mutatók az időszakban')
add('s.map', 'Karte', 'Kaart', 'Mapa', 'Mappa', 'Karta', 'Mapa', 'Kart', 'Harita', 'Térkép')
add('s.cmp', 'Vorjahr · Plan · Ist', 'Vorig jaar · Plan · Werkelijk', 'Año anterior · Plan · Real',
    'Anno prec. · Piano · Effettivo', 'Prethodna godina · Plan · Stvarno',
    'Předchozí rok · Plán · Skutečnost', 'Fjorår · Plan · Faktisk',
    'Geçen yıl · Plan · Gerçekleşen', 'Előző év · Terv · Tény')
add('s.hotel', 'Hotel', 'Hotel', 'Hotel', 'Hotel', 'Hotel', 'Hotel', 'Hotell', 'Otel', 'Szálloda')
add('s.trend', 'Verlauf', 'Verloop', 'Evolución', 'Andamento', 'Kretanje', 'Vývoj',
    'Utvikling', 'Seyir', 'Alakulás')
add('s.teams', 'Teams im Vergleich', 'Teams vergeleken', 'Comparativa de equipos',
    'Confronto tra team', 'Usporedba timova', 'Srovnání týmů', 'Team sammenlignet',
    'Takım karşılaştırması', 'Csapatok összehasonlítása')
add('s.heat', 'Abweichung zum Vorjahr', 'Afwijking t.o.v. vorig jaar', 'Variación frente al año anterior',
    'Scostamento sull’anno precedente', 'Odstupanje od prethodne godine',
    'Odchylka od předchozího roku', 'Avvik mot fjoråret', 'Geçen yıla göre sapma',
    'Eltérés az előző évhez')
add('s.table', 'Alle Werte', 'Alle waarden', 'Todos los valores', 'Tutti i valori',
    'Sve vrijednosti', 'Všechny hodnoty', 'Alle verdier', 'Tüm değerler', 'Minden érték')
add('s.defs', 'Definitionen und Datenherkunft', 'Definities en databronnen',
    'Definiciones y origen de los datos', 'Definizioni e origine dei dati',
    'Definicije i izvori podataka', 'Definice a zdroje dat', 'Definisjoner og datakilder',
    'Tanımlar ve veri kaynakları', 'Definíciók és adatforrások')

# ---------------------------------------------------------------- Hinweise
add('h.kpi', 'Vorjahr = derselbe Zeitraum ein Jahr früher. Annual Planning liegt nur für Teams vor.',
    'Vorig jaar = dezelfde periode een jaar eerder. Annual Planning bestaat alleen per team.',
    'Año anterior = el mismo periodo un año antes. Annual Planning solo existe por equipo.',
    'Anno precedente = lo stesso periodo un anno prima. Annual Planning esiste solo per team.',
    'Prethodna godina = isto razdoblje godinu ranije. Annual Planning postoji samo po timu.',
    'Předchozí rok = stejné období o rok dříve. Annual Planning existuje jen po týmech.',
    'Fjorår = samme periode ett år tidligere. Annual Planning finnes bare per team.',
    'Geçen yıl = bir yıl önceki aynı dönem. Annual Planning yalnızca takım bazında vardır.',
    'Előző év = ugyanaz az időszak egy évvel korábban. Az Annual Planning csak csapatonként létezik.')
add('h.kpiFiltered',
    'FTE und Annual Planning werden nur je Team geführt — bei gesetztem Länder- oder Regionsfilter bleiben sie und alles daraus Abgeleitete leer.',
    'FTE en Annual Planning bestaan alleen per team — met een land- of regiofilter blijven ze en alles wat eruit volgt leeg.',
    'FTE y Annual Planning solo existen por equipo: con un filtro de país o región quedan vacíos, igual que todo lo derivado.',
    'FTE e Annual Planning esistono solo per team: con un filtro per paese o regione restano vuoti, come tutto ciò che ne deriva.',
    'FTE i Annual Planning postoje samo po timu — uz filtar zemlje ili regije ostaju prazni, kao i sve izvedeno iz njih.',
    'FTE a Annual Planning existují jen po týmech — při filtru na zemi nebo region zůstanou prázdné, stejně jako vše odvozené.',
    'FTE og Annual Planning finnes bare per team — med et land- eller regionfilter står de tomme, likeså alt som utledes av dem.',
    'FTE ve Annual Planning yalnızca takım bazında tutulur — ülke veya bölge filtresi seçiliyken bunlar ve bunlardan türeyen her şey boş kalır.',
    'Az FTE és az Annual Planning csak csapatonként létezik — ország- vagy régiószűrő esetén ezek és a belőlük származtatott értékek üresen maradnak.')
add('h.cmp', 'Jede Kennzahl mit eigener Skala — von links nach rechts Vorjahr, Plan, Ist.',
    'Elk kerncijfer met eigen schaal — van links naar rechts vorig jaar, plan, werkelijk.',
    'Cada indicador con su propia escala: de izquierda a derecha año anterior, plan, real.',
    'Ogni indicatore con scala propria: da sinistra a destra anno precedente, piano, effettivo.',
    'Svaki pokazatelj ima vlastitu skalu — slijeva nadesno prethodna godina, plan, stvarno.',
    'Každý ukazatel má vlastní škálu — zleva doprava předchozí rok, plán, skutečnost.',
    'Hvert nøkkeltall med egen skala — fra venstre mot høyre fjorår, plan, faktisk.',
    'Her gösterge kendi ölçeğinde — soldan sağa geçen yıl, plan, gerçekleşen.',
    'Minden mutató saját skálán — balról jobbra előző év, terv, tény.')
add('h.mapDest', 'Klick auf ein Land setzt den Reiselandfilter, erneuter Klick hebt ihn auf.',
    'Klik op een land zet het bestemmingsfilter, nogmaals klikken heft het op.',
    'Al hacer clic en un país se aplica el filtro de destino; otro clic lo quita.',
    'Un clic su un paese imposta il filtro destinazione, un altro clic lo rimuove.',
    'Klik na zemlju postavlja filtar odredišta, ponovni klik ga uklanja.',
    'Kliknutí na zemi nastaví filtr cílové země, další kliknutí jej zruší.',
    'Klikk på et land setter reiselandfilteret, nytt klikk fjerner det.',
    'Bir ülkeye tıklamak varış ülkesi filtresini uygular, tekrar tıklamak kaldırır.',
    'Egy országra kattintva beáll a célország szűrő, újabb kattintásra megszűnik.')
add('h.mapHerk', 'Klick auf ein Land oder eine Region setzt den passenden Filter.',
    'Klik op een land of regio zet het bijbehorende filter.',
    'Al hacer clic en un país o región se aplica el filtro correspondiente.',
    'Un clic su un paese o una regione imposta il filtro corrispondente.',
    'Klik na zemlju ili regiju postavlja odgovarajući filtar.',
    'Kliknutí na zemi nebo region nastaví odpovídající filtr.',
    'Klikk på et land eller en region setter tilsvarende filter.',
    'Bir ülkeye veya bölgeye tıklamak ilgili filtreyi uygular.',
    'Egy országra vagy régióra kattintva a megfelelő szűrő áll be.')
add('h.mapRegionNA',
    'Regionen kennen keine Anfragen und Angebote — für diese Kennzahl bleibt die rechte Karte leer.',
    'Regio’s kennen geen aanvragen en offertes — voor dit kerncijfer blijft de rechterkaart leeg.',
    'Las regiones no tienen solicitudes ni ofertas: para este indicador el mapa derecho queda vacío.',
    'Le regioni non hanno richieste né offerte: per questo indicatore la mappa a destra resta vuota.',
    'Regije nemaju upite ni ponude — za ovaj pokazatelj desna karta ostaje prazna.',
    'Regiony nemají poptávky ani nabídky — pro tento ukazatel zůstane pravá mapa prázdná.',
    'Regioner har ingen forespørsler og tilbud — for dette nøkkeltallet står kartet til høyre tomt.',
    'Bölgelerde talep ve teklif verisi yoktur — bu gösterge için sağdaki harita boş kalır.',
    'A régiókhoz nincs érdeklődés és ajánlat — ennél a mutatónál a jobb oldali térkép üres marad.')
add('h.hotel', 'Nach Name oder WebID suchen. Der Hotelblick nutzt den gewählten Zeitraum und die Filter für Bereich, Team und Reiseland.',
    'Zoek op naam of WebID. Het hotelbeeld gebruikt de gekozen periode en de filters voor gebied, team en bestemming.',
    'Buscar por nombre o WebID. La vista de hotel usa el periodo elegido y los filtros de área, equipo y destino.',
    'Cerca per nome o WebID. La vista hotel usa il periodo scelto e i filtri per area, team e destinazione.',
    'Traži po nazivu ili WebID-u. Prikaz hotela koristi odabrano razdoblje i filtre za područje, tim i odredište.',
    'Hledat podle názvu nebo WebID. Pohled na hotel používá zvolené období a filtry pro oblast, tým a destinaci.',
    'Søk etter navn eller WebID. Hotellvisningen bruker valgt periode og filtrene for område, team og reisemål.',
    'Ada veya WebID’ye göre arayın. Otel görünümü seçilen dönemi ve alan, takım ve varış ülkesi filtrelerini kullanır.',
    'Keresés név vagy WebID alapján. A szállodanézet a kiválasztott időszakot és a terület, csapat és úti cél szűrőit használja.')
add('h.trend', 'Monatswerte im gewählten Zeitraum, darüber das Vorjahr.',
    'Maandwaarden in de gekozen periode, daarboven vorig jaar.',
    'Valores mensuales del periodo elegido, con el año anterior encima.',
    'Valori mensili del periodo scelto, sopra l’anno precedente.',
    'Mjesečne vrijednosti u odabranom razdoblju, iznad prethodna godina.',
    'Měsíční hodnoty ve zvoleném období, nad nimi předchozí rok.',
    'Månedsverdier i valgt periode, over dem fjoråret.',
    'Seçilen dönemdeki aylık değerler, üstünde geçen yıl.',
    'Havi értékek a kiválasztott időszakban, felette az előző év.')
add('h.teams', 'Balken = Ist im Zeitraum, Strich = Vorjahr.',
    'Balk = werkelijk in de periode, streep = vorig jaar.',
    'Barra = real en el periodo, línea = año anterior.',
    'Barra = effettivo nel periodo, trattino = anno precedente.',
    'Stupac = stvarno u razdoblju, crta = prethodna godina.',
    'Sloupec = skutečnost v období, čárka = předchozí rok.',
    'Stolpe = faktisk i perioden, strek = fjorår.',
    'Çubuk = dönemdeki gerçekleşen, çizgi = geçen yıl.',
    'Oszlop = tény az időszakban, vonal = előző év.')
add('h.heat', 'Prozentuale Veränderung je Team und Kennzahl. Grau = keine Vorjahresbasis.',
    'Procentuele verandering per team en kerncijfer. Grijs = geen basis in vorig jaar.',
    'Variación porcentual por equipo e indicador. Gris = sin base del año anterior.',
    'Variazione percentuale per team e indicatore. Grigio = nessuna base dell’anno precedente.',
    'Postotna promjena po timu i pokazatelju. Sivo = nema osnovice prethodne godine.',
    'Procentní změna podle týmu a ukazatele. Šedá = bez základny předchozího roku.',
    'Prosentvis endring per team og nøkkeltall. Grå = ingen fjorårsbasis.',
    'Takım ve göstergeye göre yüzdesel değişim. Gri = geçen yıl verisi yok.',
    'Százalékos változás csapatonként és mutatónként. Szürke = nincs előző évi bázis.')
add('h.table', 'Spaltenkopf klicken sortiert.', 'Klik op een kolomkop om te sorteren.',
    'Haz clic en la cabecera para ordenar.', 'Clic sull’intestazione per ordinare.',
    'Klik na zaglavlje stupca sortira.', 'Kliknutím na záhlaví sloupce se řadí.',
    'Klikk på kolonneoverskriften for å sortere.', 'Sütun başlığına tıklayınca sıralanır.',
    'Az oszlopfejlécre kattintva rendez.')

# ---------------------------------------------------------------- Kennzahlen
add('m.leads', 'Anfragen', 'Aanvragen', 'Solicitudes', 'Richieste', 'Upiti', 'Poptávky',
    'Forespørsler', 'Talepler', 'Érdeklődések')
add('m.props', 'Angebote', 'Offertes', 'Ofertas', 'Offerte', 'Ponude', 'Nabídky',
    'Tilbud', 'Teklifler', 'Ajánlatok')
add('m.teams', 'Teams', 'Teams', 'Equipos', 'Team', 'Timovi', 'Týmy', 'Team', 'Takımlar', 'Csapatok')
add('m.book', 'Buchungen', 'Boekingen', 'Reservas', 'Prenotazioni', 'Rezervacije', 'Rezervace',
    'Bestillinger', 'Rezervasyonlar', 'Foglalások')
add('m.vk', 'Umsatz', 'Omzet', 'Facturación', 'Fatturato', 'Promet', 'Obrat',
    'Omsetning', 'Ciro', 'Árbevétel')
add('m.ek', 'Einkauf', 'Inkoop', 'Compras', 'Acquisto', 'Nabava', 'Nákup',
    'Innkjøp', 'Alım', 'Beszerzés')
add('m.db', 'Deckungsbeitrag', 'Dekkingsbijdrage', 'Margen de contribución',
    'Margine di contribuzione', 'Doprinos pokriću', 'Příspěvek na úhradu',
    'Dekningsbidrag', 'Katkı payı', 'Fedezeti összeg')
add('m.ros', 'ROS', 'ROS', 'ROS', 'ROS', 'ROS', 'ROS', 'ROS', 'ROS', 'ROS')
add('m.pax', 'Pax', 'Pax', 'Pax', 'Pax', 'Pax', 'Pax', 'Pax', 'Pax', 'Pax')
add('m.nights', 'Übernachtungen', 'Overnachtingen', 'Pernoctaciones', 'Pernottamenti',
    'Noćenja', 'Přenocování', 'Overnattinger', 'Geceleme', 'Vendégéjszakák')
add('m.anights', 'Ø Nächte', 'Gem. nachten', 'Noches medias', 'Notti medie',
    'Prosj. noćenja', 'Prům. nocí', 'Gj.sn. netter', 'Ort. gece', 'Átl. éjszaka')
add('m.apax', 'Ø Pax/Buchung', 'Gem. pax/boeking', 'Pax medios/reserva', 'Pax medi/prenotazione',
    'Prosj. pax/rezervacija', 'Prům. pax/rezervace', 'Gj.sn. pax/bestilling',
    'Ort. pax/rezervasyon', 'Átl. pax/foglalás')
add('m.quote1', 'Angebote je Anfrage', 'Offertes per aanvraag', 'Ofertas por solicitud',
    'Offerte per richiesta', 'Ponude po upitu', 'Nabídky na poptávku',
    'Tilbud per forespørsel', 'Talep başına teklif', 'Ajánlat / érdeklődés')
add('m.quote2', 'Buchungsrate', 'Boekingsratio', 'Tasa de reserva', 'Tasso di prenotazione',
    'Stopa rezervacija', 'Míra rezervací', 'Bestillingsrate', 'Rezervasyon oranı',
    'Foglalási arány')
add('m.quote3', 'Abschlussquote', 'Conversieratio', 'Tasa de cierre', 'Tasso di chiusura',
    'Stopa zaključenja', 'Míra uzavření', 'Avslutningsrate', 'Kapanış oranı', 'Zárási arány')
add('m.webq', 'Web-Anteil Anfragen', 'Webaandeel aanvragen', 'Cuota web de solicitudes',
    'Quota web richieste', 'Web udio upita', 'Podíl webu na poptávkách',
    'Webandel forespørsler', 'Taleplerde web payı', 'Web arány az érdeklődésekben')
add('m.web', 'Web-Anfragen', 'Webaanvragen', 'Solicitudes web', 'Richieste web',
    'Web upiti', 'Webové poptávky', 'Webforespørsler', 'Web talepleri', 'Web érdeklődések')
add('m.uteam', 'Umsatz je Team', 'Omzet per team', 'Facturación por equipo', 'Fatturato per team',
    'Promet po timu', 'Obrat na tým', 'Omsetning per team', 'Takım başına ciro',
    'Árbevétel / csapat')
add('m.dbteam', 'DB je Team', 'Dekkingsbijdrage per team', 'Margen por equipo',
    'Margine per team', 'Doprinos po timu', 'Příspěvek na tým', 'Dekningsbidrag per team',
    'Takım başına katkı payı', 'Fedezet / csapat')
add('m.ubook', 'Umsatz je Buchung', 'Omzet per boeking', 'Facturación por reserva',
    'Fatturato per prenotazione', 'Promet po rezervaciji', 'Obrat na rezervaci',
    'Omsetning per bestilling', 'Rezervasyon başına ciro', 'Árbevétel / foglalás')
add('m.dbbook', 'DB je Buchung', 'Dekkingsbijdrage per boeking', 'Margen por reserva',
    'Margine per prenotazione', 'Doprinos po rezervaciji', 'Příspěvek na rezervaci',
    'Dekningsbidrag per bestilling', 'Rezervasyon başına katkı payı', 'Fedezet / foglalás')
add('m.mpn', 'Marge/Pax/Nacht', 'Marge/pax/nacht', 'Margen/pax/noche', 'Margine/pax/notte',
    'Marža/pax/noćenje', 'Marže/pax/noc', 'Margin/pax/natt', 'Marj/pax/gece',
    'Árrés/pax/éjszaka')
add('m.fte', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE')
add('m.leadfte', 'Anfragen je FTE', 'Aanvragen per FTE', 'Solicitudes por FTE',
    'Richieste per FTE', 'Upiti po FTE', 'Poptávky na FTE', 'Forespørsler per FTE',
    'FTE başına talep', 'Érdeklődés / FTE')
add('m.bookfte', 'Buchungen je FTE', 'Boekingen per FTE', 'Reservas por FTE',
    'Prenotazioni per FTE', 'Rezervacije po FTE', 'Rezervace na FTE',
    'Bestillinger per FTE', 'FTE başına rezervasyon', 'Foglalás / FTE')
add('m.teamfte', 'Teams je FTE', 'Teams per FTE', 'Equipos por FTE', 'Team per FTE',
    'Timovi po FTE', 'Týmy na FTE', 'Team per FTE', 'FTE başına takım', 'Csapat / FTE')
add('m.vkfte', 'Umsatz je FTE', 'Omzet per FTE', 'Facturación por FTE', 'Fatturato per FTE',
    'Promet po FTE', 'Obrat na FTE', 'Omsetning per FTE', 'FTE başına ciro', 'Árbevétel / FTE')
add('m.dbfte', 'DB je FTE', 'Dekkingsbijdrage per FTE', 'Margen por FTE', 'Margine per FTE',
    'Doprinos po FTE', 'Příspěvek na FTE', 'Dekningsbidrag per FTE', 'FTE başına katkı payı',
    'Fedezet / FTE')

add('g.funnel', 'Funnel', 'Funnel', 'Embudo', 'Funnel', 'Lijevak', 'Trychtýř', 'Trakt', 'Huni', 'Tölcsér')
add('g.value', 'Wert', 'Waarde', 'Valor', 'Valore', 'Vrijednost', 'Hodnota', 'Verdi', 'Değer', 'Érték')
add('g.volume', 'Volumen', 'Volume', 'Volumen', 'Volume', 'Obujam', 'Objem', 'Volum', 'Hacim', 'Volumen')
add('g.rates', 'Quoten', 'Ratio’s', 'Ratios', 'Tassi', 'Stope', 'Míry', 'Rater', 'Oranlar', 'Arányok')
add('g.unit', 'Je Einheit', 'Per eenheid', 'Por unidad', 'Per unità', 'Po jedinici',
    'Na jednotku', 'Per enhet', 'Birim başına', 'Egységenként')
add('g.fte', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE')

# ---------------------------------------------------------------- Kacheln, Legenden
add('t.py', 'VJ', 'VJ', 'AA', 'AP', 'PG', 'PR', 'FJ', 'GY', 'EÉ')
add('t.ap', 'AP', 'AP', 'AP', 'AP', 'AP', 'AP', 'AP', 'AP', 'AP')
add('pn.plan', 'Plan', 'Plan', 'Plan', 'Piano', 'Plan', 'Plán', 'Plan', 'Plan', 'Terv')
add('pn.ist', 'Ist', 'Werkelijk', 'Real', 'Effettivo', 'Stvarno', 'Skutečnost',
    'Faktisk', 'Gerçekleşen', 'Tény')
add('pn.none', '— kein Wert —', '— geen waarde —', '— sin valor —', '— nessun valore —',
    '— nema vrijednosti —', '— bez hodnoty —', '— ingen verdi —', '— değer yok —',
    '— nincs érték —')
add('lg.pyDashed', 'Vorjahr (gestrichelt)', 'Vorig jaar (gestreept)', 'Año anterior (discontinua)',
    'Anno precedente (tratteggiata)', 'Prethodna godina (iscrtkano)', 'Předchozí rok (čárkovaně)',
    'Fjorår (stiplet)', 'Geçen yıl (kesikli)', 'Előző év (szaggatott)')
add('lg.apDotted', 'Annual Planning (gepunktet)', 'Annual Planning (gestippeld)',
    'Annual Planning (punteada)', 'Annual Planning (punteggiata)', 'Annual Planning (točkasto)',
    'Annual Planning (tečkovaně)', 'Annual Planning (prikket)', 'Annual Planning (noktalı)',
    'Annual Planning (pontozott)')
add('hl.bad', '−30 % und schlechter', '−30 % en slechter', '−30 % o peor', '−30 % o peggio',
    '−30 % i lošije', '−30 % a horší', '−30 % og dårligere', '−30 % ve daha kötü',
    '−30 % vagy rosszabb')
add('hl.flat', 'unverändert', 'ongewijzigd', 'sin cambio', 'invariato', 'nepromijenjeno',
    'beze změny', 'uendret', 'değişmedi', 'változatlan')
add('hl.good', '+30 % und besser', '+30 % en beter', '+30 % o mejor', '+30 % o meglio',
    '+30 % i bolje', '+30 % a lepší', '+30 % og bedre', '+30 % ve daha iyi',
    '+30 % vagy jobb')

# ---------------------------------------------------------------- Karte
add('mp.titleDest', 'Reiseländer', 'Bestemmingen', 'Países de destino', 'Paesi di destinazione',
    'Odredišne zemlje', 'Cílové země', 'Reiseland', 'Varış ülkeleri', 'Célországok')
add('mp.titleHerk', 'Herkunftsländer der Kunden', 'Herkomstlanden van de klanten',
    'Países de origen de los clientes', 'Paesi di provenienza dei clienti',
    'Zemlje podrijetla klijenata', 'Země původu zákazníků', 'Kundenes opprinnelsesland',
    'Müşterilerin kaynak ülkeleri', 'Az ügyfelek származási országai')
add('mp.titleDach', 'Regionen in Deutschland, Österreich und der Schweiz',
    'Regio’s in Duitsland, Oostenrijk en Zwitserland',
    'Regiones de Alemania, Austria y Suiza', 'Regioni di Germania, Austria e Svizzera',
    'Regije u Njemačkoj, Austriji i Švicarskoj', 'Regiony v Německu, Rakousku a Švýcarsku',
    'Regioner i Tyskland, Østerrike og Sveits', 'Almanya, Avusturya ve İsviçre bölgeleri',
    'Régiók Németországban, Ausztriában és Svájcban')
add('mp.none', 'ohne Vorgang', 'zonder verkeer', 'sin actividad', 'nessuna attività',
    'bez prometa', 'bez transakcí', 'ingen aktivitet', 'işlem yok', 'nincs forgalom')
add('mp.noOps', 'keine Vorgänge', 'geen verkeer', 'sin actividad', 'nessuna attività',
    'nema prometa', 'žádné transakce', 'ingen aktivitet', 'işlem yok', 'nincs forgalom')

# ---------------------------------------------------------------- Hotel
add('ho.ph', 'Hotelname oder WebID, z. B. Freudenstadt oder 10431',
    'Hotelnaam of WebID, bijv. Freudenstadt of 10431',
    'Nombre del hotel o WebID, p. ej. Freudenstadt o 10431',
    'Nome hotel o WebID, ad es. Freudenstadt o 10431',
    'Naziv hotela ili WebID, npr. Freudenstadt ili 10431',
    'Název hotelu nebo WebID, např. Freudenstadt nebo 10431',
    'Hotellnavn eller WebID, f.eks. Freudenstadt eller 10431',
    'Otel adı veya WebID, örn. Freudenstadt veya 10431',
    'Szállodanév vagy WebID, pl. Freudenstadt vagy 10431')
add('ho.searchLabel', 'Hotel suchen', 'Hotel zoeken', 'Buscar hotel', 'Cerca hotel',
    'Traži hotel', 'Hledat hotel', 'Søk hotell', 'Otel ara', 'Szálloda keresése')
add('ho.clear', 'Auswahl aufheben', 'Selectie wissen', 'Quitar selección', 'Annulla selezione',
    'Poništi odabir', 'Zrušit výběr', 'Fjern valg', 'Seçimi kaldır', 'Kijelölés törlése')
add('ho.nohit', 'Kein Treffer', 'Geen resultaat', 'Sin resultados', 'Nessun risultato',
    'Nema rezultata', 'Žádný výsledek', 'Ingen treff', 'Sonuç yok', 'Nincs találat')
add('ho.noops', 'ohne Vorgänge', 'zonder verkeer', 'sin actividad', 'nessuna attività',
    'bez prometa', 'bez transakcí', 'ingen aktivitet', 'işlem yok', 'nincs forgalom')
add('ho.since', 'im Verkauf seit', 'in verkoop sinds', 'a la venta desde', 'in vendita da',
    'u prodaji od', 'v prodeji od', 'i salg siden', 'satışta', 'értékesítés óta')
add('ho.excl', 'exklusiv', 'exclusief', 'exclusivo', 'esclusivo', 'ekskluzivno',
    'exkluzivní', 'eksklusiv', 'özel', 'exkluzív')
add('ho.monthly', 'Monatsverlauf', 'Maandverloop', 'Evolución mensual', 'Andamento mensile',
    'Mjesečno kretanje', 'Měsíční vývoj', 'Månedsutvikling', 'Aylık seyir', 'Havi alakulás')
add('ho.whoSells', 'Welche Teams verkaufen dieses Hotel',
    'Welke teams verkopen dit hotel', 'Qué equipos venden este hotel',
    'Quali team vendono questo hotel', 'Koji timovi prodaju ovaj hotel',
    'Které týmy prodávají tento hotel', 'Hvilke team selger dette hotellet',
    'Bu oteli hangi takımlar satıyor', 'Mely csapatok értékesítik ezt a szállodát')
add('ho.empty', 'Noch kein Hotel gewählt — unten steht die Rangliste für den gewählten Zeitraum.',
    'Nog geen hotel gekozen — hieronder staat de ranglijst voor de gekozen periode.',
    'Aún no hay hotel seleccionado: abajo está la clasificación del periodo elegido.',
    'Nessun hotel selezionato: sotto trovi la classifica per il periodo scelto.',
    'Hotel još nije odabran — ispod je poredak za odabrano razdoblje.',
    'Zatím není vybrán hotel — níže je pořadí za zvolené období.',
    'Ingen hotell valgt ennå — nedenfor står rangeringen for valgt periode.',
    'Henüz otel seçilmedi — aşağıda seçilen döneme ait sıralama var.',
    'Még nincs szálloda kiválasztva — alább a kiválasztott időszak rangsora.')
add('ho.noBookings', 'Keine Buchungen im Zeitraum.', 'Geen boekingen in de periode.',
    'Sin reservas en el periodo.', 'Nessuna prenotazione nel periodo.',
    'Nema rezervacija u razdoblju.', 'V období žádné rezervace.',
    'Ingen bestillinger i perioden.', 'Dönemde rezervasyon yok.',
    'Nincs foglalás az időszakban.')
add('ho.rank', 'Rangliste', 'Ranglijst', 'Clasificación', 'Classifica', 'Poredak',
    'Pořadí', 'Rangering', 'Sıralama', 'Rangsor')
add('ho.rankAll', 'Alle Teams und Länder, gewählter Zeitraum. Anfragen je angefragtem Hotel — ein Kunde zählt bei jedem Hotel, das er angefragt hat.',
    'Alle teams en landen, gekozen periode. Aanvragen per aangevraagd hotel — een klant telt bij elk hotel dat hij heeft aangevraagd.',
    'Todos los equipos y países, periodo elegido. Solicitudes por hotel solicitado: un cliente cuenta en cada hotel que ha solicitado.',
    'Tutti i team e paesi, periodo scelto. Richieste per hotel richiesto: un cliente conta per ogni hotel che ha richiesto.',
    'Svi timovi i zemlje, odabrano razdoblje. Upiti po traženom hotelu — kupac se broji kod svakog hotela koji je zatražio.',
    'Všechny týmy a země, zvolené období. Poptávky podle poptaného hotelu — zákazník se počítá u každého hotelu, který poptal.',
    'Alle team og land, valgt periode. Forespørsler per forespurt hotell — en kunde telles for hvert hotell han har forespurt.',
    'Tüm takımlar ve ülkeler, seçilen dönem. Talep edilen otele göre talepler — bir müşteri talep ettiği her otelde sayılır.',
    'Minden csapat és ország, kiválasztott időszak. Érdeklődések a megkérdezett szálloda szerint — egy ügyfél minden megkérdezett szállodánál számít.')
add('ho.rankFiltered',
    'Gefilterte Buchungsdaten — für Kundenherkunft und Region gibt es keine Anfragen und Angebote je Hotel.',
    'Gefilterde boekingsdata — voor klantherkomst en regio zijn er geen aanvragen en offertes per hotel.',
    'Datos de reservas filtrados: para origen del cliente y región no hay solicitudes ni ofertas por hotel.',
    'Dati di prenotazione filtrati: per provenienza clienti e regione non ci sono richieste e offerte per hotel.',
    'Filtrirani podaci o rezervacijama — za podrijetlo kupaca i regiju nema upita i ponuda po hotelu.',
    'Filtrovaná data rezervací — pro původ zákazníků a region nejsou poptávky a nabídky podle hotelu k dispozici.',
    'Filtrerte bestillingsdata — for kundeopprinnelse og region finnes ingen forespørsler og tilbud per hotell.',
    'Filtrelenmiş rezervasyon verileri — müşteri kökeni ve bölge için otel bazında talep ve teklif yoktur.',
    'Szűrt foglalási adatok — ügyfélszármazás és régió szerint nincsenek szállodánkénti érdeklődések és ajánlatok.')
add('ho.rankSel', 'Gewählte Teams und Reiseländer, gewählter Zeitraum. Anfragen je angefragtem Hotel.',
    'Gekozen teams en bestemmingen, gekozen periode. Aanvragen per aangevraagd hotel.',
    'Equipos y destinos elegidos, periodo elegido. Solicitudes por hotel solicitado.',
    'Team e destinazioni scelti, periodo scelto. Richieste per hotel richiesto.',
    'Odabrani timovi i odredišta, odabrano razdoblje. Upiti po traženom hotelu.',
    'Zvolené týmy a destinace, zvolené období. Poptávky podle poptaného hotelu.',
    'Valgte team og reisemål, valgt periode. Forespørsler per forespurt hotell.',
    'Seçilen takımlar ve varış ülkeleri, seçilen dönem. Talep edilen otele göre talepler.',
    'Kiválasztott csapatok és úti célok, kiválasztott időszak. Érdeklődések a megkérdezett szálloda szerint.')
add('ho.more', '{n} Hotels mit Vorgängen im Zeitraum — die ersten 40 nach {m}.',
    '{n} hotels met verkeer in de periode — de eerste 40 op {m}.',
    '{n} hoteles con actividad en el periodo: los primeros 40 por {m}.',
    '{n} hotel con attività nel periodo: i primi 40 per {m}.',
    '{n} hotela s prometom u razdoblju — prvih 40 po {m}.',
    '{n} hotelů s transakcemi v období — prvních 40 podle {m}.',
    '{n} hoteller med aktivitet i perioden — de første 40 etter {m}.',
    'Dönemde işlem gören {n} otel — {m} sıralamasına göre ilk 40.',
    '{n} szálloda forgalommal az időszakban — az első 40 a következő szerint: {m}.')
add('ho.hotel', 'Hotel', 'Hotel', 'Hotel', 'Hotel', 'Hotel', 'Hotel', 'Hotell', 'Otel', 'Szálloda')
add('ho.land', 'Land', 'Land', 'País', 'Paese', 'Zemlja', 'Země', 'Land', 'Ülke', 'Ország')
add('ho.sortBy', 'Sortieren nach', 'Sorteren op', 'Ordenar por', 'Ordina per', 'Sortiraj po',
    'Řadit podle', 'Sorter etter', 'Sıralama ölçütü', 'Rendezés')
add('ho.metric', 'Kennzahl', 'Kerncijfer', 'Indicador', 'Indicatore', 'Pokazatelj',
    'Ukazatel', 'Nøkkeltall', 'Gösterge', 'Mutató')

# ---------------------------------------------------------------- Tabelle
add('tb.total', 'Gesamt', 'Totaal', 'Total', 'Totale', 'Ukupno', 'Celkem', 'Totalt',
    'Toplam', 'Összesen')
add('tb.copy', 'Tabelle kopieren', 'Tabel kopiëren', 'Copiar tabla', 'Copia tabella',
    'Kopiraj tablicu', 'Kopírovat tabulku', 'Kopier tabell', 'Tabloyu kopyala',
    'Táblázat másolása')
add('tb.copied', 'Kopiert', 'Gekopieerd', 'Copiado', 'Copiato', 'Kopirano', 'Zkopírováno',
    'Kopiert', 'Kopyalandı', 'Másolva')

# ---------------------------------------------------------------- Hinweise unter dem Funnel
add('nt.leadNA',
    'Die Region stammt aus Spalte H des Blattes Sales und existiert nur für Buchungen — Combit führt kein Bundesland. Solange ein Regionsfilter gesetzt ist, bleiben Anfragen, Angebote und alle daraus abgeleiteten Quoten leer.',
    'De regio komt uit kolom H van het blad Sales en bestaat alleen voor boekingen — Combit kent geen deelstaat. Zolang een regiofilter actief is, blijven aanvragen, offertes en alle daaruit afgeleide ratio’s leeg.',
    'La región procede de la columna H de la hoja Sales y solo existe para reservas: Combit no registra el estado federado. Mientras haya un filtro de región, solicitudes, ofertas y todos los ratios derivados quedan vacíos.',
    'La regione proviene dalla colonna H del foglio Sales ed esiste solo per le prenotazioni: Combit non registra il land. Finché è attivo un filtro di regione, richieste, offerte e tutti i tassi derivati restano vuoti.',
    'Regija dolazi iz stupca H lista Sales i postoji samo za rezervacije — Combit ne vodi saveznu pokrajinu. Dok je postavljen filtar regije, upiti, ponude i sve izvedene stope ostaju prazni.',
    'Region pochází ze sloupce H listu Sales a existuje jen u rezervací — Combit spolkovou zemi nevede. Dokud je nastaven filtr regionu, zůstanou poptávky, nabídky a všechny odvozené míry prázdné.',
    'Regionen kommer fra kolonne H i arket Sales og finnes bare for bestillinger — Combit fører ingen delstat. Så lenge et regionfilter er satt, står forespørsler, tilbud og alle avledede rater tomme.',
    'Bölge, Sales sayfasının H sütunundan gelir ve yalnızca rezervasyonlar için vardır — Combit eyalet bilgisi tutmaz. Bölge filtresi etkin olduğu sürece talepler, teklifler ve bunlardan türeyen tüm oranlar boş kalır.',
    'A régió a Sales lap H oszlopából származik, és csak foglalásokhoz létezik — a Combit nem tart nyilván tartományt. Amíg régiószűrő van beállítva, az érdeklődések, ajánlatok és minden ebből származtatott arány üres marad.')
add('nt.leadHistSkipped',
    'Vor 2024 liegen Anfragen und Angebote nur als Monatssumme je Team vor, ohne Reiseland und Herkunft. Für diesen Teil des Zeitraums werden sie bei gesetztem Filter nicht mitgezählt.',
    'Vóór 2024 bestaan aanvragen en offertes alleen als maandtotaal per team, zonder bestemming en herkomst. Voor dat deel van de periode tellen ze bij een actief filter niet mee.',
    'Antes de 2024, solicitudes y ofertas solo existen como suma mensual por equipo, sin destino ni origen. En esa parte del periodo no se cuentan si hay un filtro activo.',
    'Prima del 2024 richieste e offerte esistono solo come somma mensile per team, senza destinazione e provenienza. In quella parte del periodo non vengono conteggiate se è attivo un filtro.',
    'Prije 2024. upiti i ponude postoje samo kao mjesečni zbroj po timu, bez odredišta i podrijetla. Za taj dio razdoblja ne ulaze u zbroj kada je filtar postavljen.',
    'Před rokem 2024 existují poptávky a nabídky jen jako měsíční součet za tým, bez cílové země a původu. V této části období se při nastaveném filtru nezapočítávají.',
    'Før 2024 finnes forespørsler og tilbud bare som månedssum per team, uten reiseland og opprinnelse. For den delen av perioden telles de ikke med når et filter er satt.',
    '2024 öncesinde talep ve teklifler yalnızca takım bazında aylık toplam olarak vardır; varış ülkesi ve kaynak bilgisi yoktur. Filtre etkinken dönemin bu bölümü sayılmaz.',
    '2024 előtt az érdeklődések és ajánlatok csak csapatonkénti havi összegként állnak rendelkezésre, célország és származás nélkül. Szűrő esetén az időszak ezen része nem számít bele.')
add('nt.leadHistUsed',
    'Für Monate vor 2024 stammen Anfragen und Angebote aus den Blättern Leads und Props und liegen nur monatsgenau vor; angebrochene Monate bleiben in diesem Zeitraum unberücksichtigt.',
    'Voor maanden vóór 2024 komen aanvragen en offertes uit de bladen Leads en Props en bestaan alleen per maand; aangebroken maanden blijven in deze periode buiten beschouwing.',
    'Para los meses anteriores a 2024, solicitudes y ofertas proceden de las hojas Leads y Props y solo existen por mes; los meses incompletos no se consideran.',
    'Per i mesi precedenti al 2024 richieste e offerte provengono dai fogli Leads e Props ed esistono solo per mese; i mesi parziali non vengono considerati.',
    'Za mjesece prije 2024. upiti i ponude dolaze s listova Leads i Props i postoje samo po mjesecu; nepotpuni mjeseci se ne uzimaju u obzir.',
    'Pro měsíce před rokem 2024 pocházejí poptávky a nabídky z listů Leads a Props a existují jen po měsících; neúplné měsíce se nezapočítávají.',
    'For måneder før 2024 kommer forespørsler og tilbud fra arkene Leads og Props og finnes bare per måned; delvise måneder tas ikke med.',
    '2024 öncesi aylarda talep ve teklifler Leads ve Props sayfalarından gelir ve yalnızca ay bazındadır; tam olmayan aylar dikkate alınmaz.',
    'A 2024 előtti hónapokban az érdeklődések és ajánlatok a Leads és Props lapokról származnak, és csak havi bontásban állnak rendelkezésre; a töredékhónapok kimaradnak.')
add('nt.leadPartial',
    'Der gewählte Zeitraum beginnt oder endet mitten in einem Monat, für den nur Monatswerte vorliegen — diese Monate fehlen in Anfragen und Angeboten.',
    'De gekozen periode begint of eindigt midden in een maand waarvoor alleen maandwaarden bestaan — die maanden ontbreken bij aanvragen en offertes.',
    'El periodo elegido empieza o termina a mitad de un mes del que solo hay valores mensuales: esos meses faltan en solicitudes y ofertas.',
    'Il periodo scelto inizia o termina a metà di un mese per cui esistono solo valori mensili: quei mesi mancano in richieste e offerte.',
    'Odabrano razdoblje počinje ili završava usred mjeseca za koji postoje samo mjesečne vrijednosti — ti mjeseci nedostaju u upitima i ponudama.',
    'Zvolené období začíná nebo končí uprostřed měsíce, pro který existují jen měsíční hodnoty — tyto měsíce v poptávkách a nabídkách chybí.',
    'Valgt periode begynner eller slutter midt i en måned der bare månedsverdier finnes — disse månedene mangler i forespørsler og tilbud.',
    'Seçilen dönem, yalnızca aylık değerlerin bulunduğu bir ayın ortasında başlıyor veya bitiyor — bu aylar talep ve tekliflerde eksik kalır.',
    'A kiválasztott időszak olyan hónap közepén kezdődik vagy ér véget, amelyhez csak havi értékek vannak — ezek a hónapok hiányoznak az érdeklődésekből és ajánlatokból.')

# ---------------------------------------------------------------- Kopf- und Fusszeile
add('cv.line', '{n} Buchungen nach Buchungsdatum, {von} bis {bis} · {t} Teams · Stand {stand}',
    '{n} boekingen op boekingsdatum, {von} tot {bis} · {t} teams · per {stand}',
    '{n} reservas por fecha de reserva, de {von} a {bis} · {t} equipos · a {stand}',
    '{n} prenotazioni per data di prenotazione, dal {von} al {bis} · {t} team · al {stand}',
    '{n} rezervacija prema datumu rezervacije, {von} do {bis} · {t} timova · stanje {stand}',
    '{n} rezervací podle data rezervace, {von} až {bis} · {t} týmů · stav {stand}',
    '{n} bestillinger etter bestillingsdato, {von} til {bis} · {t} team · per {stand}',
    'Rezervasyon tarihine göre {n} rezervasyon, {von} – {bis} · {t} takım · {stand} itibarıyla',
    '{n} foglalás foglalási dátum szerint, {von} – {bis} · {t} csapat · {stand} állapot')
add('ft.line', 'Quelle: {wb} (Blätter Sales, FTE, Goals, Locations) und {cb} (Combit-Export). Erzeugt am {gen}. Alle Werte in Euro, sofern nicht anders angegeben.',
    'Bron: {wb} (bladen Sales, FTE, Goals, Locations) en {cb} (Combit-export). Gemaakt op {gen}. Alle bedragen in euro, tenzij anders vermeld.',
    'Fuente: {wb} (hojas Sales, FTE, Goals, Locations) y {cb} (exportación de Combit). Generado el {gen}. Todos los importes en euros salvo indicación contraria.',
    'Fonte: {wb} (fogli Sales, FTE, Goals, Locations) e {cb} (export Combit). Generato il {gen}. Tutti i valori in euro salvo diversa indicazione.',
    'Izvor: {wb} (listovi Sales, FTE, Goals, Locations) i {cb} (Combit izvoz). Izrađeno {gen}. Sve vrijednosti u eurima ako nije drugačije navedeno.',
    'Zdroj: {wb} (listy Sales, FTE, Goals, Locations) a {cb} (export z Combitu). Vytvořeno {gen}. Všechny hodnoty v eurech, není-li uvedeno jinak.',
    'Kilde: {wb} (arkene Sales, FTE, Goals, Locations) og {cb} (Combit-eksport). Generert {gen}. Alle verdier i euro hvis ikke annet er angitt.',
    'Kaynak: {wb} (Sales, FTE, Goals, Locations sayfaları) ve {cb} (Combit dışa aktarımı). Oluşturma: {gen}. Aksi belirtilmedikçe tüm değerler euro cinsindendir.',
    'Forrás: {wb} (Sales, FTE, Goals, Locations lapok) és {cb} (Combit export). Készült: {gen}. Minden érték euróban, hacsak másképp nincs jelezve.')

# ---------------------------------------------------------------- Einheiten
add('u.mio', 'Mio €', 'mln €', 'M €', 'Mln €', 'mil. €', 'mil. €', 'mill. €', 'mn €', 'M €')
add('u.tsd', 'Tsd €', 'dzd €', 'mil €', 'mila €', 'tis. €', 'tis. €', 'tusen €', 'bin €', 'e €')

# ---------------------------------------------------------------- Fehlerseite
add('err.title', 'Daten nicht erreichbar', 'Gegevens niet bereikbaar', 'Datos no disponibles',
    'Dati non raggiungibili', 'Podaci nisu dostupni', 'Data nejsou dostupná',
    'Data ikke tilgjengelig', 'Veriye ulaşılamıyor', 'Az adatok nem érhetők el')

# ---------------------------------------------------------------- Ansichten, Reports
add('view.cockpit', 'Cockpit', 'Cockpit', 'Cockpit', 'Cockpit', 'Cockpit', 'Cockpit', 'Cockpit', 'Kokpit', 'Cockpit')
add('view.reports', 'Reports', 'Rapporten', 'Informes', 'Report', 'Izvješća', 'Reporty', 'Rapporter', 'Raporlar', 'Jelentések')
add('rp.cmp', 'Monatsvergleich', 'Maandvergelijking', 'Comparativa mensual', 'Confronto mensile',
    'Mjesečna usporedba', 'Měsíční srovnání', 'Månedssammenligning', 'Aylık karşılaştırma', 'Havi összehasonlítás')
add('rp.tsr', 'Team Status Report', 'Team Status Report', 'Team Status Report', 'Team Status Report',
    'Team Status Report', 'Team Status Report', 'Team Status Report', 'Team Status Report', 'Team Status Report')
add('rp.csr', 'Country Status Report', 'Country Status Report', 'Country Status Report', 'Country Status Report',
    'Country Status Report', 'Country Status Report', 'Country Status Report', 'Country Status Report', 'Country Status Report')
add('rp.month', 'Berichtsmonat', 'Rapportmaand', 'Mes del informe', 'Mese del report', 'Mjesec izvješća',
    'Měsíc reportu', 'Rapportmåned', 'Rapor ayı', 'Jelentési hónap')
add('rp.present', 'Präsentieren', 'Presenteren', 'Presentar', 'Presenta', 'Prezentiraj', 'Prezentovat',
    'Presenter', 'Sun', 'Bemutatás')
add('rp.print', 'Drucken / PDF', 'Afdrukken / PDF', 'Imprimir / PDF', 'Stampa / PDF', 'Ispis / PDF',
    'Tisk / PDF', 'Skriv ut / PDF', 'Yazdır / PDF', 'Nyomtatás / PDF')
add('rp.printAll', 'Alle drucken', 'Alles afdrukken', 'Imprimir todos', 'Stampa tutti', 'Ispiši sve',
    'Vytisknout vše', 'Skriv ut alle', 'Tümünü yazdır', 'Összes nyomtatása')
add('rp.exit', 'Beenden', 'Afsluiten', 'Salir', 'Esci', 'Završi', 'Ukončit', 'Avslutt', 'Çık', 'Kilépés')
add('rp.more', 'Weitere', 'Overige', 'Otros', 'Altri', 'Ostali', 'Další', 'Øvrige', 'Diğer', 'További')
add('rp.mainCountries', 'Zielmärkte', 'Doelmarkten', 'Mercados destino', 'Mercati di destinazione',
    'Ciljna tržišta', 'Cílové trhy', 'Målmarkeder', 'Hedef pazarlar', 'Célpiacok')
add('rp.page', '{i} von {n}', '{i} van {n}', '{i} de {n}', '{i} di {n}', '{i} od {n}', '{i} z {n}',
    '{i} av {n}', '{i} / {n}', '{i} / {n}')
add('rp.cmpTitle', '{a} und {b}', '{a} en {b}', '{a} y {b}', '{a} e {b}', '{a} i {b}', '{a} a {b}',
    '{a} og {b}', '{a} ve {b}', '{a} és {b}')
add('rp.fyLabel', 'GJ {a} – {b}', 'BJ {a} – {b}', 'Ej. {a} – {b}', 'Es. {a} – {b}', 'PG {a} – {b}',
    'HR {a} – {b}', 'RÅ {a} – {b}', 'MY {a} – {b}', 'ÜÉ {a} – {b}')
add('rp.dataAsOf', 'Datenstand {d}', 'Datastand {d}', 'Datos a {d}', 'Dati al {d}', 'Podaci na dan {d}',
    'Stav dat {d}', 'Datagrunnlag {d}', 'Veri tarihi {d}', 'Adatok állapota: {d}')
add('rp.sum', 'Σ', 'Σ', 'Σ', 'Σ', 'Σ', 'Σ', 'Σ', 'Σ', 'Σ')
add('rp.deltaAP', 'Δ zu AP', 'Δ t.o.v. AP', 'Δ vs AP', 'Δ vs AP', 'Δ prema AP', 'Δ vůči AP',
    'Δ mot AP', 'AP farkı', 'Δ AP-hoz')
add('rp.deltaPY', 'Δ zum VJ', 'Δ t.o.v. VJ', 'Δ vs AA', 'Δ vs AP prec.', 'Δ prema PG', 'Δ vůči PR',
    'Δ mot FJ', 'GY farkı', 'Δ EÉ-hez')
add('rp.webShare', 'Web-Anteil', 'Webaandeel', 'Cuota web', 'Quota web', 'Web udio', 'Podíl webu',
    'Webandel', 'Web payı', 'Web arány')
add('rp.added', 'Ergänzt', 'Aanvullend', 'Añadido', 'Aggiunto', 'Dodano', 'Doplněno', 'Tillegg', 'Ek', 'Kiegészítés')
add('rp.addedLegend', 'zusätzlich zum bisherigen Excel-Report', 'aanvullend op het bestaande Excel-rapport',
    'adicional al informe Excel actual', 'in aggiunta al report Excel esistente',
    'dodatno uz dosadašnje Excel izvješće', 'navíc oproti dosavadnímu reportu v Excelu',
    'i tillegg til den eksisterende Excel-rapporten', 'mevcut Excel raporuna ek olarak',
    'a korábbi Excel-jelentésen felül')
add('rp.gjCum', 'Teams im Geschäftsjahr', 'Teams in het boekjaar', 'Equipos en el ejercicio',
    'Team nell’esercizio', 'Timovi u poslovnoj godini', 'Týmy v hospodářském roce',
    'Team i regnskapsåret', 'Mali yılda takımlar', 'Csapatok az üzleti évben')
add('rp.attain', 'Erfüllung', 'Realisatie', 'Cumplimiento', 'Raggiungimento', 'Ostvarenje', 'Plnění',
    'Måloppnåelse', 'Gerçekleşme', 'Teljesítés')
add('rp.apMonth', 'Teams im Monat', 'Teams in de maand', 'Equipos del mes', 'Team del mese',
    'Timovi u mjesecu', 'Týmy v měsíci', 'Team i måneden', 'Ayın takımları', 'Csapatok a hónapban')
add('rp.apFY', 'AP Geschäftsjahr gesamt', 'AP boekjaar totaal', 'AP ejercicio completo', 'AP esercizio totale',
    'AP cijela poslovna godina', 'AP celý hospodářský rok', 'AP hele regnskapsåret', 'AP tüm mali yıl',
    'AP teljes üzleti év')
add('rp.remaining', 'noch offen', 'nog open', 'pendiente', 'ancora da fare', 'preostalo', 'zbývá',
    'gjenstår', 'kalan', 'hátralévő')
add('rp.onTrack', 'im Plan', 'op koers', 'en plan', 'in linea', 'u planu', 'v plánu', 'i rute',
    'planda', 'terv szerint')
add('rp.behind', 'unter Plan', 'onder plan', 'por debajo del plan', 'sotto piano', 'ispod plana',
    'pod plánem', 'under plan', 'planın altında', 'terv alatt')
add('rp.win1', 'Monat', 'Maand', 'Mes', 'Mese', 'Mjesec', 'Měsíc', 'Måned', 'Ay', 'Hónap')
add('rp.win3', '3 Monate', '3 maanden', '3 meses', '3 mesi', '3 mjeseca', '3 měsíce', '3 måneder', '3 ay', '3 hónap')
add('rp.win12', '12 Monate', '12 maanden', '12 meses', '12 mesi', '12 mjeseci', '12 měsíců', '12 måneder', '12 ay', '12 hónap')
add('rp.trend', 'Trend', 'Trend', 'Tendencia', 'Trend', 'Trend', 'Trend', 'Trend', 'Eğilim', 'Trend')
add('rp.kpis', 'Kennzahlen', 'Kerncijfers', 'Indicadores', 'Indicatori', 'Pokazatelji', 'Ukazatele',
    'Nøkkeltall', 'Göstergeler', 'Mutatók')
add('rp.apSection', 'Annual Planning', 'Annual Planning', 'Annual Planning', 'Annual Planning',
    'Annual Planning', 'Annual Planning', 'Annual Planning', 'Annual Planning', 'Annual Planning')
add('rp.trendSection', 'Monatsverlauf', 'Maandverloop', 'Evolución mensual', 'Andamento mensile',
    'Mjesečno kretanje', 'Měsíční vývoj', 'Månedsutvikling', 'Aylık seyir', 'Havi alakulás')
add('rp.destSection', 'Reiseländer', 'Bestemmingen', 'Destinos', 'Destinazioni', 'Odredišta',
    'Cílové země', 'Reiseland', 'Varış ülkeleri', 'Célországok')
add('rp.hotelSection', 'Top-Hotels', 'Tophotels', 'Hoteles principales', 'Hotel principali',
    'Najbolji hoteli', 'Nejlepší hotely', 'Topphoteller', 'En iyi oteller', 'Legjobb szállodák')
add('rp.teamSection', 'Verkaufende Teams', 'Verkopende teams', 'Equipos que venden', 'Team che vendono',
    'Timovi koji prodaju', 'Prodávající týmy', 'Selgende team', 'Satış yapan takımlar', 'Értékesítő csapatok')
add('rp.herkSection', 'Kundenherkunft', 'Herkomst klanten', 'Origen de clientes', 'Provenienza clienti',
    'Podrijetlo klijenata', 'Původ zákazníků', 'Kundenes opprinnelse', 'Müşteri kaynağı', 'Ügyfelek származása')
add('rp.sportSection', 'Sportarten', 'Sporten', 'Deportes', 'Sport', 'Sportovi', 'Sporty', 'Idretter',
    'Spor dalları', 'Sportágak')
add('rp.sport', 'Sportart', 'Sport', 'Deporte', 'Sport', 'Sport', 'Sport', 'Idrett', 'Spor', 'Sportág')
add('rp.last12', 'letzte 12 Monate', 'laatste 12 maanden', 'últimos 12 meses', 'ultimi 12 mesi',
    'zadnjih 12 mjeseci', 'posledních 12 měsíců', 'siste 12 måneder', 'son 12 ay', 'utolsó 12 hónap')
add('rp.share', 'Anteil DB', 'Aandeel DB', 'Cuota margen', 'Quota margine', 'Udio doprinosa',
    'Podíl příspěvku', 'Andel DB', 'Katkı payı oranı', 'Fedezet aránya')
add('rp.dbPY', 'DB zum VJ', 'DB t.o.v. VJ', 'Margen vs AA', 'Margine vs AP prec.', 'Doprinos prema PG',
    'Příspěvek vůči PR', 'DB mot FJ', 'GY’ye göre katkı', 'Fedezet EÉ-hez')
add('rp.noApLeads', 'Für diesen Zeitraum liegt kein Annual Planning für Anfragen vor.',
    'Voor deze periode is er geen annual planning voor aanvragen.',
    'Para este periodo no hay annual planning de solicitudes.',
    'Per questo periodo non c’è annual planning per le richieste.',
    'Za ovo razdoblje nema annual planninga za upite.',
    'Pro toto období není k dispozici annual planning pro poptávky.',
    'For denne perioden finnes ingen annual planning for forespørsler.',
    'Bu dönem için talepler için annual planning yok.',
    'Erre az időszakra nincs annual planning az érdeklődésekre.')
add('rp.sglNote', 'Die Zeile „davon Teams aus SGL" aus dem Excel-Report fehlt noch — ihre Definition ist nicht in der Mappe hinterlegt.',
    'De rij „davon Teams aus SGL" uit het Excel-rapport ontbreekt nog — de definitie staat niet in de werkmap.',
    'Falta aún la fila «davon Teams aus SGL» del informe Excel: su definición no figura en el libro.',
    'Manca ancora la riga «davon Teams aus SGL» del report Excel: la definizione non è nella cartella.',
    'Redak „davon Teams aus SGL" iz Excel izvješća još nedostaje — definicija nije u radnoj knjizi.',
    'Řádek „davon Teams aus SGL" z reportu v Excelu zatím chybí — jeho definice v sešitu není.',
    'Raden «davon Teams aus SGL» fra Excel-rapporten mangler ennå — definisjonen står ikke i arbeidsboken.',
    'Excel raporundaki „davon Teams aus SGL" satırı henüz yok — tanımı çalışma kitabında bulunmuyor.',
    'Az Excel-jelentés „davon Teams aus SGL" sora még hiányzik — a definíciója nincs a munkafüzetben.')
add('rp.csrNote', 'Umsatz je Team entspricht der Zeile „U/Buchung" im Excel-Report — dort wird ebenfalls durch Teams geteilt.',
    'Omzet per team komt overeen met de rij „U/Buchung" in het Excel-rapport — ook daar wordt door teams gedeeld.',
    'Facturación por equipo corresponde a la fila «U/Buchung» del informe Excel, que también divide por equipos.',
    'Fatturato per team corrisponde alla riga «U/Buchung» del report Excel, che divide anch’essa per team.',
    'Promet po timu odgovara retku „U/Buchung" u Excel izvješću — i ondje se dijeli s timovima.',
    'Obrat na tým odpovídá řádku „U/Buchung" v reportu v Excelu — i tam se dělí týmy.',
    'Omsetning per team tilsvarer raden «U/Buchung» i Excel-rapporten — også der deles det på team.',
    'Takım başına ciro, Excel raporundaki „U/Buchung" satırına karşılık gelir — orada da takımlara bölünür.',
    'Az árbevétel/csapat megfelel az Excel-jelentés „U/Buchung" sorának — ott is csapatokkal osztanak.')
add('rp.printBlocked', 'Drucken ist in dieser Vorschau gesperrt. In der heruntergeladenen Datei oder auf dem Server funktioniert es.',
    'Afdrukken is in deze preview geblokkeerd. In het gedownloade bestand of op de server werkt het wel.',
    'La impresión está bloqueada en esta vista previa. Funciona en el archivo descargado o en el servidor.',
    'La stampa è bloccata in questa anteprima. Funziona nel file scaricato o sul server.',
    'Ispis je u ovom pregledu blokiran. Radi u preuzetoj datoteci ili na poslužitelju.',
    'Tisk je v tomto náhledu zablokován. Funguje ve staženém souboru nebo na serveru.',
    'Utskrift er sperret i denne forhåndsvisningen. Det fungerer i den nedlastede filen eller på serveren.',
    'Bu önizlemede yazdırma engellidir. İndirilen dosyada veya sunucuda çalışır.',
    'Ebben az előnézetben a nyomtatás tiltva van. A letöltött fájlban vagy a szerveren működik.')
add('rp.pfReady', 'Drucken ist in dieser Vorschau gesperrt. Der Bericht kommt deshalb als druckfertige Datei — öffnen, der Druckdialog startet von selbst, dort „Als PDF speichern“ wählen.',
    'Afdrukken is in deze preview geblokkeerd. Het rapport komt daarom als afdrukklaar bestand — openen, het afdrukvenster start vanzelf, kies daar „Opslaan als PDF“.',
    'La impresión está bloqueada en esta vista previa. Por eso el informe se entrega como archivo listo para imprimir: ábrelo, el diálogo de impresión se abre solo; elige «Guardar como PDF».',
    'La stampa è bloccata in questa anteprima. Il report arriva quindi come file pronto per la stampa: aprilo, la finestra di stampa si apre da sola; scegli «Salva come PDF».',
    'Ispis je u ovom pregledu blokiran. Izvješće stoga dolazi kao datoteka spremna za ispis — otvori je, dijalog za ispis pokreće se sam, ondje odaberi „Spremi kao PDF“.',
    'Tisk je v tomto náhledu zablokován. Report proto přijde jako soubor připravený k tisku — otevři ho, tiskové okno se spustí samo, tam zvol „Uložit jako PDF“.',
    'Utskrift er sperret i denne forhåndsvisningen. Rapporten kommer derfor som en utskriftsklar fil — åpne den, utskriftsdialogen starter av seg selv, velg «Lagre som PDF».',
    'Bu önizlemede yazdırma engellidir. Rapor bu yüzden yazdırmaya hazır bir dosya olarak gelir — dosyayı aç, yazdırma penceresi kendiliğinden açılır, orada „PDF olarak kaydet“i seç.',
    'Ebben az előnézetben a nyomtatás tiltva van. A jelentés ezért nyomtatásra kész fájlként érkezik — nyisd meg, a nyomtatási ablak magától elindul, ott válaszd a „Mentés PDF-ként“ lehetőséget.')
add('rp.pfBar', 'Druckansicht — A4 quer ist voreingestellt. Als Ziel „Als PDF speichern“ wählen, um ein PDF zu erhalten.',
    'Afdrukweergave — A4 liggend is ingesteld. Kies als bestemming „Opslaan als PDF“ voor een PDF.',
    'Vista de impresión: A4 horizontal predefinido. Elige «Guardar como PDF» como destino para obtener un PDF.',
    'Anteprima di stampa: A4 orizzontale preimpostato. Scegli «Salva come PDF» come destinazione per ottenere un PDF.',
    'Prikaz za ispis — unaprijed je postavljen A4 položeno. Za PDF kao odredište odaberi „Spremi kao PDF“.',
    'Náhled tisku — přednastaveno A4 na šířku. Pro PDF zvol jako cíl „Uložit jako PDF“.',
    'Utskriftsvisning — A4 liggende er forhåndsinnstilt. Velg «Lagre som PDF» som mål for å få en PDF.',
    'Baskı görünümü — A4 yatay önceden ayarlıdır. PDF almak için hedef olarak „PDF olarak kaydet“i seç.',
    'Nyomtatási nézet — A4 fekvő az alapbeállítás. PDF-hez célként a „Mentés PDF-ként“ lehetőséget válaszd.')
add('rp.printFail', 'Drucken ist hier gesperrt, und die Datei ließ sich nicht bereitstellen. Öffne das Cockpit über den Server oder als heruntergeladene HTML-Datei.',
    'Afdrukken is hier geblokkeerd en het bestand kon niet worden aangeboden. Open de cockpit via de server of als gedownload HTML-bestand.',
    'La impresión está bloqueada aquí y no se pudo ofrecer el archivo. Abre el cockpit desde el servidor o como archivo HTML descargado.',
    'Qui la stampa è bloccata e il file non è stato reso disponibile. Apri il cockpit dal server o come file HTML scaricato.',
    'Ispis je ovdje blokiran, a datoteku nije bilo moguće ponuditi. Otvori cockpit preko poslužitelja ili kao preuzetu HTML datoteku.',
    'Tisk je zde zablokován a soubor se nepodařilo nabídnout. Otevři cockpit přes server nebo jako stažený HTML soubor.',
    'Utskrift er sperret her, og filen kunne ikke tilbys. Åpne cockpiten via serveren eller som nedlastet HTML-fil.',
    'Burada yazdırma engelli ve dosya sunulamadı. Kokpiti sunucu üzerinden veya indirilen HTML dosyası olarak aç.',
    'Itt a nyomtatás tiltva van, és a fájlt nem sikerült felajánlani. Nyisd meg a cockpitot a szerveren vagy letöltött HTML-fájlként.')
add('ask.title', 'Frag das Cockpit', 'Vraag het cockpit', 'Pregunta al cockpit', 'Chiedi al cockpit',
    'Pitaj cockpit', 'Zeptej se cockpitu', 'Spør cockpiten', 'Kokpite sor', 'Kérdezd a cockpitot')
add('ask.hint', 'Freitext-Frage zu Buchungen, Anfragen, Teams, Hotels und Ländern — Claude rechnet mit den Daten dieses Cockpits.',
    'Vrije vraag over boekingen, aanvragen, teams, hotels en landen — Claude rekent met de data van dit cockpit.',
    'Pregunta libre sobre reservas, solicitudes, equipos, hoteles y países: Claude calcula con los datos de este cockpit.',
    'Domanda libera su prenotazioni, richieste, team, hotel e paesi: Claude calcola con i dati di questo cockpit.',
    'Slobodno pitanje o rezervacijama, upitima, timovima, hotelima i zemljama — Claude računa s podacima ovog cockpita.',
    'Volná otázka k rezervacím, poptávkám, týmům, hotelům a zemím — Claude počítá s daty tohoto cockpitu.',
    'Fritt spørsmål om bestillinger, forespørsler, team, hoteller og land — Claude regner med dataene i denne cockpiten.',
    'Rezervasyonlar, talepler, takımlar, oteller ve ülkeler hakkında serbest soru — Claude bu kokpitin verileriyle hesaplar.',
    'Szabad kérdés foglalásokról, érdeklődésekről, csapatokról, szállodákról és országokról — Claude a cockpit adataival számol.')
add('ask.ph', 'z. B. Welche Hotels in Kroatien hatten im GJ 2025/26 die meisten Anfragen?',
    'bijv. Welke hotels in Kroatië hadden in boekjaar 2025/26 de meeste aanvragen?',
    'p. ej. ¿Qué hoteles de Croacia tuvieron más solicitudes en el ejercicio 2025/26?',
    'es. Quali hotel in Croazia hanno avuto più richieste nell’esercizio 2025/26?',
    'npr. Koji su hoteli u Hrvatskoj imali najviše upita u poslovnoj godini 2025/26?',
    'např. Které hotely v Chorvatsku měly nejvíce poptávek v hospodářském roce 2025/26?',
    'f.eks. Hvilke hoteller i Kroatia hadde flest forespørsler i regnskapsåret 2025/26?',
    'örn. 2025/26 mali yılında Hırvatistan’da en çok talep alan oteller hangileri?',
    'pl. Mely horvátországi szállodák kapták a legtöbb érdeklődést a 2025/26-os üzleti évben?')
add('ask.btn', 'Fragen', 'Vragen', 'Preguntar', 'Chiedi', 'Pitaj', 'Zeptat se', 'Spør', 'Sor', 'Kérdezés')
add('ask.busy', 'Claude rechnet …', 'Claude rekent …', 'Claude está calculando…', 'Claude sta calcolando…',
    'Claude računa …', 'Claude počítá …', 'Claude regner …', 'Claude hesaplıyor…', 'Claude számol …')
add('ask.ex1', 'Wie steht das laufende Geschäftsjahr gegenüber dem Vorjahr?',
    'Hoe staat het lopende boekjaar ten opzichte van vorig jaar?',
    '¿Cómo va el ejercicio actual frente al año anterior?',
    'Come va l’esercizio in corso rispetto all’anno precedente?',
    'Kako stoji tekuća poslovna godina u odnosu na prošlu?',
    'Jak si stojí aktuální hospodářský rok oproti předchozímu?',
    'Hvordan ligger inneværende regnskapsår an mot fjoråret?',
    'Cari mali yıl geçen yıla göre nasıl gidiyor?',
    'Hogy áll a folyó üzleti év az előzőhöz képest?')
add('ask.ex2', 'Welches Team hat die höchste Abschlussquote in den letzten 12 Monaten?',
    'Welk team heeft de hoogste conversie in de laatste 12 maanden?',
    '¿Qué equipo tiene la mayor tasa de cierre en los últimos 12 meses?',
    'Quale team ha il tasso di chiusura più alto negli ultimi 12 mesi?',
    'Koji tim ima najvišu stopu zaključenja u zadnjih 12 mjeseci?',
    'Který tým má nejvyšší míru uzavření za posledních 12 měsíců?',
    'Hvilket team har høyest avslutningsrate de siste 12 månedene?',
    'Son 12 ayda en yüksek kapanış oranına sahip takım hangisi?',
    'Melyik csapatnak a legmagasabb a zárási aránya az elmúlt 12 hónapban?')
add('ask.ex3', 'Top 5 Hotels in Italien nach Deckungsbeitrag im GJ 2025/26',
    'Top 5 hotels in Italië naar dekkingsbijdrage in boekjaar 2025/26',
    'Top 5 hoteles en Italia por margen de contribución en el ejercicio 2025/26',
    'Top 5 hotel in Italia per margine di contribuzione nell’esercizio 2025/26',
    'Top 5 hotela u Italiji po doprinosu pokrića u poslovnoj godini 2025/26',
    'Top 5 hotelů v Itálii podle příspěvku na úhradu v hospodářském roce 2025/26',
    'Topp 5 hoteller i Italia etter dekningsbidrag i regnskapsåret 2025/26',
    '2025/26 mali yılında katkı payına göre İtalya’daki ilk 5 otel',
    'Top 5 olaszországi szálloda fedezeti hozzájárulás szerint a 2025/26-os üzleti évben')
add('ask.steps', 'So wurde gerechnet', 'Zo is gerekend', 'Cómo se calculó', 'Come è stato calcolato',
    'Kako je izračunato', 'Jak se počítalo', 'Slik ble det regnet', 'Nasıl hesaplandı', 'Így számoltunk')
add('ask.meta', '{s} s · heute noch {r} von {n} Fragen', '{s} s · vandaag nog {r} van {n} vragen',
    '{s} s · hoy quedan {r} de {n} preguntas', '{s} s · oggi restano {r} di {n} domande',
    '{s} s · danas još {r} od {n} pitanja', '{s} s · dnes ještě {r} z {n} otázek',
    '{s} s · i dag gjenstår {r} av {n} spørsmål', '{s} sn · bugün {n} sorudan {r} kaldı',
    '{s} mp · ma még {r} / {n} kérdés')
add('ask.left', 'Heute noch {r} von {n} Fragen.', 'Vandaag nog {r} van {n} vragen.', 'Hoy quedan {r} de {n} preguntas.',
    'Oggi restano {r} di {n} domande.', 'Danas još {r} od {n} pitanja.', 'Dnes ještě {r} z {n} otázek.',
    'I dag gjenstår {r} av {n} spørsmål.', 'Bugün {n} sorudan {r} kaldı.', 'Ma még {r} / {n} kérdés.')
add('ask.limit', 'Das Tageslimit von {n} Fragen ist erreicht. Morgen geht es weiter.',
    'De daglimiet van {n} vragen is bereikt. Morgen kan het weer.',
    'Se alcanzó el límite diario de {n} preguntas. Mañana se puede seguir.',
    'Il limite giornaliero di {n} domande è stato raggiunto. Si riprende domani.',
    'Dnevno ograničenje od {n} pitanja je dosegnuto. Sutra se nastavlja.',
    'Denní limit {n} otázek je vyčerpán. Zítra se pokračuje.',
    'Dagsgrensen på {n} spørsmål er nådd. I morgen går det igjen.',
    'Günlük {n} soru sınırına ulaşıldı. Yarın devam edilebilir.',
    'Elérted a napi {n} kérdéses korlátot. Holnap folytathatod.')
add('ask.error', 'Die Frage konnte gerade nicht beantwortet werden. Bitte später noch einmal versuchen.',
    'De vraag kon nu niet worden beantwoord. Probeer het later opnieuw.',
    'No se pudo responder la pregunta ahora. Inténtalo de nuevo más tarde.',
    'Non è stato possibile rispondere ora. Riprova più tardi.',
    'Na pitanje trenutno nije moguće odgovoriti. Pokušaj ponovno kasnije.',
    'Na otázku teď nelze odpovědět. Zkus to prosím později.',
    'Spørsmålet kunne ikke besvares nå. Prøv igjen senere.',
    'Soru şu anda yanıtlanamadı. Lütfen daha sonra tekrar deneyin.',
    'A kérdésre most nem sikerült válaszolni. Próbáld újra később.')
add('ask.note', 'KI-Antwort: Die Zahlen stammen aus den Cockpit-Daten, die Formulierung von Claude. Für Entscheidungen im Cockpit gegenprüfen.',
    'AI-antwoord: de cijfers komen uit de cockpitdata, de formulering van Claude. Controleer ze in het cockpit voor beslissingen.',
    'Respuesta de IA: las cifras proceden de los datos del cockpit, la redacción de Claude. Compruébalas en el cockpit antes de decidir.',
    'Risposta IA: i numeri provengono dai dati del cockpit, la formulazione da Claude. Verificali nel cockpit prima di decidere.',
    'AI odgovor: brojke su iz podataka cockpita, formulacija od Claudea. Za odluke provjeri u cockpitu.',
    'Odpověď AI: čísla pocházejí z dat cockpitu, formulace od Clauda. Před rozhodnutím je ověř v cockpitu.',
    'KI-svar: tallene kommer fra cockpitdataene, formuleringen fra Claude. Kontroller i cockpiten før beslutninger.',
    'Yapay zekâ yanıtı: rakamlar kokpit verilerinden, ifade Claude’dan. Kararlar için kokpitte kontrol edin.',
    'MI-válasz: a számok a cockpit adataiból, a megfogalmazás Claude-tól származik. Döntés előtt ellenőrizd a cockpitban.')
add('rp.leadsMonth', 'Anfragen im Monat', 'Aanvragen in de maand', 'Solicitudes del mes', 'Richieste del mese',
    'Upiti u mjesecu', 'Poptávky v měsíci', 'Forespørsler i måneden', 'Aydaki talepler', 'Érdeklődések a hónapban')
add('rp.leadsFY', 'Anfragen im Geschäftsjahr', 'Aanvragen in het boekjaar', 'Solicitudes en el ejercicio',
    'Richieste nell’esercizio', 'Upiti u poslovnoj godini', 'Poptávky v hospodářském roce',
    'Forespørsler i regnskapsåret', 'Mali yıldaki talepler', 'Érdeklődések az üzleti évben')
add('rp.apLeadsFY', 'AP-Anfragen Geschäftsjahr gesamt', 'AP-aanvragen boekjaar totaal', 'Solicitudes AP ejercicio completo',
    'Richieste AP esercizio totale', 'AP upiti poslovna godina ukupno', 'AP poptávky za hospodářský rok celkem',
    'AP-forespørsler regnskapsår totalt', 'AP talepleri mali yıl toplamı', 'AP-érdeklődések üzleti év összesen')
add('m.leadsall', 'Alle Anfragen', 'Alle aanvragen', 'Todas las solicitudes', 'Tutte le richieste',
    'Svi upiti', 'Všechny poptávky', 'Alle forespørsler', 'Tüm talepler', 'Összes érdeklődés')
add('m.bqall', 'Buchungsquote', 'Boekingsquote', 'Tasa de reserva', 'Tasso di prenotazione',
    'Stopa rezervacija', 'Míra rezervací', 'Bestillingsrate', 'Rezervasyon oranı', 'Foglalási arány')
add('m.bqneed', 'Nötige Quote für AP', 'Benodigde quote voor AP', 'Tasa necesaria para AP', 'Tasso necessario per AP',
    'Potrebna stopa za AP', 'Potřebná míra pro AP', 'Nødvendig rate for AP', 'AP için gereken oran', 'AP-hoz szükséges arány')
add('ho.bqHint', 'Buchungsquote = Teams ÷ alle Anfragen (ohne Unique-Regel), darunter der Vorjahreswert.',
    'Boekingsquote = teams ÷ alle aanvragen (zonder unique-regel), eronder de waarde van vorig jaar.',
    'Tasa de reserva = equipos ÷ todas las solicitudes (sin regla de únicos); debajo, el valor del año anterior.',
    'Tasso di prenotazione = team ÷ tutte le richieste (senza regola unique); sotto il valore dell’anno precedente.',
    'Stopa rezervacija = timovi ÷ svi upiti (bez pravila jedinstvenosti), ispod vrijednost prethodne godine.',
    'Míra rezervací = týmy ÷ všechny poptávky (bez pravidla unikátnosti), pod tím hodnota loňského roku.',
    'Bestillingsrate = team ÷ alle forespørsler (uten unik-regel), under fjorårets verdi.',
    'Rezervasyon oranı = takımlar ÷ tüm talepler (tekillik kuralı olmadan), altında geçen yılın değeri.',
    'Foglalási arány = csapatok ÷ összes érdeklődés (egyediségi szabály nélkül), alatta az előző évi érték.')
add('sp.FU', 'Fußball', 'Voetbal', 'Fútbol', 'Calcio', 'Nogomet', 'Fotbal', 'Fotball', 'Futbol', 'Labdarúgás')
add('sp.TU', 'Fußballturniere', 'Voetbaltoernooien', 'Torneos de fútbol', 'Tornei di calcio', 'Nogometni turniri',
    'Fotbalové turnaje', 'Fotballturneringer', 'Futbol turnuvaları', 'Labdarúgó tornák')
add('sp.SW', 'Schwimmen', 'Zwemmen', 'Natación', 'Nuoto', 'Plivanje', 'Plavání', 'Svømming', 'Yüzme', 'Úszás')
add('sp.LA', 'Leichtathletik', 'Atletiek', 'Atletismo', 'Atletica', 'Atletika', 'Atletika', 'Friidrett', 'Atletizm', 'Atlétika')
add('sp.TE', 'Tennis', 'Tennis', 'Tenis', 'Tennis', 'Tenis', 'Tenis', 'Tennis', 'Tenis', 'Tenisz')
add('sp.HA', 'Handball', 'Handbal', 'Balonmano', 'Pallamano', 'Rukomet', 'Házená', 'Håndball', 'Hentbol', 'Kézilabda')

# ---------------------------------------------------------------- Definitionen
DEFS = [
    ('stichtag',
     ('Stichtag', 'Peildatum', 'Fecha de referencia', 'Data di riferimento',
      'Mjerodavni datum', 'Rozhodné datum', 'Skjæringsdato', 'Esas tarih', 'Fordulónap'),
     ('Alle Buchungs-, Umsatz- und DB-Kennzahlen zählen nach Buchungsdatum, nicht nach Reisedatum. Gegen das Blatt Report verifiziert.',
      'Alle boekings-, omzet- en dekkingsbijdragecijfers tellen op boekingsdatum, niet op reisdatum. Geverifieerd tegen het blad Report.',
      'Reservas, facturación y margen se cuentan por fecha de reserva, no por fecha de viaje. Verificado contra la hoja Report.',
      'Prenotazioni, fatturato e margine contano per data di prenotazione, non per data di viaggio. Verificato con il foglio Report.',
      'Rezervacije, promet i doprinos broje se prema datumu rezervacije, ne prema datumu putovanja. Provjereno prema listu Report.',
      'Rezervace, obrat a příspěvek se počítají podle data rezervace, nikoli podle data cesty. Ověřeno proti listu Report.',
      'Bestillinger, omsetning og dekningsbidrag telles etter bestillingsdato, ikke reisedato. Verifisert mot arket Report.',
      'Rezervasyon, ciro ve katkı payı seyahat tarihine göre değil, rezervasyon tarihine göre sayılır. Report sayfasıyla doğrulandı.',
      'A foglalás, árbevétel és fedezet a foglalási dátum szerint számít, nem az utazás dátuma szerint. A Report lappal ellenőrizve.')),
    ('db',
     ('Deckungsbeitrag', 'Dekkingsbijdrage', 'Margen de contribución', 'Margine di contribuzione',
      'Doprinos pokriću', 'Příspěvek na úhradu', 'Dekningsbidrag', 'Katkı payı', 'Fedezeti összeg'),
     ('VK minus EK (Spalte MargIn im Blatt Sales). Nicht die Spalte Net MargIn.',
      'Verkoop minus inkoop (kolom MargIn in het blad Sales). Niet de kolom Net MargIn.',
      'Venta menos compra (columna MargIn de la hoja Sales). No la columna Net MargIn.',
      'Vendita meno acquisto (colonna MargIn nel foglio Sales). Non la colonna Net MargIn.',
      'Prodaja minus nabava (stupac MargIn na listu Sales). Ne stupac Net MargIn.',
      'Prodej minus nákup (sloupec MargIn na listu Sales). Nikoli sloupec Net MargIn.',
      'Salg minus innkjøp (kolonne MargIn i arket Sales). Ikke kolonnen Net MargIn.',
      'Satış eksi alım (Sales sayfasındaki MargIn sütunu). Net MargIn sütunu değil.',
      'Eladás mínusz beszerzés (a Sales lap MargIn oszlopa). Nem a Net MargIn oszlop.')),
    ('teams',
     ('Teams', 'Teams', 'Equipos', 'Team', 'Timovi', 'Týmy', 'Team', 'Takımlar', 'Csapatok'),
     ('Summe der Spalte Teams — eine Buchung kann mehrere Teams enthalten. Deshalb weicht Teams von Buchungen ab.',
      'Som van de kolom Teams — één boeking kan meerdere teams bevatten. Daarom wijkt Teams af van Boekingen.',
      'Suma de la columna Teams: una reserva puede incluir varios equipos. Por eso Equipos difiere de Reservas.',
      'Somma della colonna Teams: una prenotazione può contenere più team. Per questo Team differisce da Prenotazioni.',
      'Zbroj stupca Teams — jedna rezervacija može sadržavati više timova. Zato se Timovi razlikuju od Rezervacija.',
      'Součet sloupce Teams — jedna rezervace může obsahovat více týmů. Proto se Týmy liší od Rezervací.',
      'Sum av kolonnen Teams — én bestilling kan inneholde flere team. Derfor avviker Team fra Bestillinger.',
      'Teams sütununun toplamı — bir rezervasyon birden çok takım içerebilir. Bu nedenle Takımlar ile Rezervasyonlar farklıdır.',
      'A Teams oszlop összege — egy foglalás több csapatot is tartalmazhat. Ezért a Csapatok eltér a Foglalásoktól.')),
    ('leads',
     ('Anfragen', 'Aanvragen', 'Solicitudes', 'Richieste', 'Upiti', 'Poptávky',
      'Forespørsler', 'Talepler', 'Érdeklődések'),
     ('Ab 01/2024 aus dem Combit-Export, Belegart Anfrage, dedupliziert je Ansprechpartner, Team und AP-Jahr. Diese Regel reproduziert die Werte des Blattes Leads für 2024 auf rund vier Prozent genau. Bis 12/2023 aus dem Blatt Leads, monatsgenau. Je Hotel zählt eine Anfrage bei jedem Hotel, das der Kunde angefragt hat, einmal je Kunde, Team, AP-Jahr und Hotel. Die Summe über alle Hotels ist deshalb größer als die Zahl der unique Anfragen. AP-Anfragen: geplante Teams des Folgemonats geteilt durch die Buchungsquote dieses Monats im Vorjahr (Teams ÷ unique Anfragen des Vormonats) — wie im Blatt AP.',
      'Vanaf 01/2024 uit de Combit-export, documenttype Anfrage, ontdubbeld per contactpersoon, team en AP-jaar. Deze regel reproduceert de waarden van het blad Leads voor 2024 tot op ongeveer vier procent. Tot 12/2023 uit het blad Leads, per maand. Per hotel telt een aanvraag bij elk hotel dat de klant heeft aangevraagd, één keer per klant, team, AP-jaar en hotel. De som over alle hotels is daardoor groter dan het aantal unieke aanvragen. AP-aanvragen: geplande teams van de volgende maand gedeeld door de boekingsquote van die maand vorig jaar (teams ÷ unieke aanvragen van de maand ervoor) — zoals in het blad AP.',
      'Desde 01/2024 de la exportación de Combit, tipo Anfrage, deduplicado por contacto, equipo y año AP. Esta regla reproduce los valores de la hoja Leads de 2024 con un margen de alrededor del cuatro por ciento. Hasta 12/2023 de la hoja Leads, por mes. Por hotel, una solicitud cuenta en cada hotel que el cliente ha solicitado, una vez por cliente, equipo, año AP y hotel. Por eso la suma de todos los hoteles supera el número de solicitudes únicas. Solicitudes AP: equipos planificados del mes siguiente divididos por la tasa de reserva de ese mes el año anterior (equipos ÷ solicitudes únicas del mes previo), como en la hoja AP.',
      'Dal 01/2024 dall’export Combit, tipo documento Anfrage, deduplicato per referente, team e anno AP. Questa regola riproduce i valori del foglio Leads per il 2024 con uno scarto di circa il quattro per cento. Fino al 12/2023 dal foglio Leads, per mese. Per hotel una richiesta conta per ogni hotel richiesto dal cliente, una volta per cliente, team, anno AP e hotel. La somma di tutti gli hotel supera quindi il numero di richieste uniche. Richieste AP: team pianificati del mese successivo divisi per il tasso di prenotazione di quel mese nell’anno precedente (team ÷ richieste uniche del mese prima), come nel foglio AP.',
      'Od 01/2024 iz Combit izvoza, vrsta Anfrage, deduplicirano po kontaktu, timu i AP godini. Ovo pravilo reproducira vrijednosti lista Leads za 2024. s odstupanjem od oko četiri posto. Do 12/2023 s lista Leads, po mjesecu. Po hotelu se upit broji za svaki hotel koji je kupac zatražio, jednom po kupcu, timu, AP godini i hotelu. Zbroj svih hotela zato je veći od broja jedinstvenih upita. AP upiti: planirani timovi sljedećeg mjeseca podijeljeni stopom rezervacija tog mjeseca prethodne godine (timovi ÷ jedinstveni upiti prethodnog mjeseca), kao u listu AP.',
      'Od 01/2024 z exportu Combit, typ Anfrage, deduplikováno podle kontaktu, týmu a roku AP. Toto pravidlo reprodukuje hodnoty listu Leads za rok 2024 s přesností asi čtyři procenta. Do 12/2023 z listu Leads, po měsících. U hotelů se poptávka počítá u každého hotelu, který zákazník poptal, jednou za zákazníka, tým, rok AP a hotel. Součet za všechny hotely je proto vyšší než počet unikátních poptávek. AP poptávky: plánované týmy následujícího měsíce dělené mírou rezervací tohoto měsíce v předchozím roce (týmy ÷ unikátní poptávky předchozího měsíce), jako v listu AP.',
      'Fra 01/2024 fra Combit-eksporten, dokumenttype Anfrage, duplikater fjernet per kontakt, team og AP-år. Regelen gjenskaper verdiene i arket Leads for 2024 med omtrent fire prosents avvik. Til 12/2023 fra arket Leads, per måned. Per hotell telles en forespørsel for hvert hotell kunden har forespurt, én gang per kunde, team, AP-år og hotell. Summen over alle hotell er derfor større enn antall unike forespørsler. AP-forespørsler: planlagte team neste måned delt på bestillingsraten for den måneden i fjor (team ÷ unike forespørsler måneden før), som i arket AP.',
      '01/2024’ten itibaren Combit dışa aktarımından, belge türü Anfrage, kişi, takım ve AP yılına göre tekilleştirilmiş. Bu kural Leads sayfasının 2024 değerlerini yaklaşık yüzde dört sapmayla yeniden üretir. 12/2023’e kadar Leads sayfasından, ay bazında. Otel bazında bir talep, müşterinin talep ettiği her otel için sayılır; müşteri, takım, AP yılı ve otel başına bir kez. Bu nedenle tüm otellerin toplamı tekil taleplerin sayısından büyüktür. AP talepleri: sonraki ayın planlanan takımları, geçen yılın aynı ayındaki rezervasyon oranına bölünür (takımlar ÷ önceki ayın tekil talepleri), AP sayfasındaki gibi.',
      '2024/01-től a Combit exportból, Anfrage bizonylattípus, kapcsolattartó, csapat és AP-év szerint deduplikálva. Ez a szabály a Leads lap 2024-es értékeit nagyjából négy százalékos pontossággal adja vissza. 2023/12-ig a Leads lapról, havi bontásban. Szállodánként egy érdeklődés minden olyan szállodánál számít, amelyet az ügyfél megkérdezett, ügyfelenként, csapatonként, AP-évenként és szállodánként egyszer. Ezért az összes szálloda összege nagyobb, mint az egyedi érdeklődések száma. AP-érdeklődések: a következő hónap tervezett csapatai osztva az adott hónap előző évi foglalási arányával (csapatok ÷ az előző hónap egyedi érdeklődései), ahogy az AP lapon.')),
    ('props',
     ('Angebote', 'Offertes', 'Ofertas', 'Offerte', 'Ponude', 'Nabídky', 'Tilbud',
      'Teklifler', 'Ajánlatok'),
     ('Ab 01/2024 aus dem Combit-Export, Belegart Angebot, datiert auf das Versanddatum. Ein Vorgang kann mehrere Angebote erzeugen — deshalb liegt der Wert deutlich über den Anfragen. Bis 12/2023 aus dem Blatt Props, monatsgenau.',
      'Vanaf 01/2024 uit de Combit-export, documenttype Angebot, gedateerd op verzenddatum. Eén dossier kan meerdere offertes opleveren — daarom ligt de waarde ruim boven de aanvragen. Tot 12/2023 uit het blad Props, per maand.',
      'Desde 01/2024 de la exportación de Combit, tipo Angebot, con fecha de envío. Un expediente puede generar varias ofertas: por eso el valor supera con creces al de solicitudes. Hasta 12/2023 de la hoja Props, por mes.',
      'Dal 01/2024 dall’export Combit, tipo Angebot, datato alla data di invio. Una pratica può generare più offerte: per questo il valore supera nettamente le richieste. Fino al 12/2023 dal foglio Props, per mese.',
      'Od 01/2024 iz Combit izvoza, vrsta Angebot, datirano prema datumu slanja. Jedan predmet može stvoriti više ponuda — zato je vrijednost znatno veća od broja upita. Do 12/2023 s lista Props, po mjesecu.',
      'Od 01/2024 z exportu Combit, typ Angebot, datováno podle data odeslání. Jeden případ může vytvořit více nabídek — proto je hodnota výrazně vyšší než počet poptávek. Do 12/2023 z listu Props, po měsících.',
      'Fra 01/2024 fra Combit-eksporten, dokumenttype Angebot, datert til sendedato. Én sak kan gi flere tilbud — derfor ligger verdien klart over forespørslene. Til 12/2023 fra arket Props, per måned.',
      '01/2024’ten itibaren Combit dışa aktarımından, belge türü Angebot, gönderim tarihine göre tarihlendirilmiş. Bir dosya birden çok teklif üretebilir — bu nedenle değer taleplerin belirgin biçimde üzerindedir. 12/2023’e kadar Props sayfasından, ay bazında.',
      '2024/01-től a Combit exportból, Angebot bizonylattípus, a kiküldés dátumára datálva. Egy ügyből több ajánlat is születhet — ezért az érték jóval az érdeklődések fölött van. 2023/12-ig a Props lapról, havi bontásban.')),
    ('web',
     ('Web-Anteil', 'Webaandeel', 'Cuota web', 'Quota web', 'Web udio', 'Podíl webu',
      'Webandel', 'Web payı', 'Web arány'),
     ('Anteil der Anfragen mit Quelle website oder Erfassung über das Webformular. Erst ab 2024 verfügbar.',
      'Aandeel aanvragen met bron website of invoer via het webformulier. Pas vanaf 2024 beschikbaar.',
      'Proporción de solicitudes con origen website o registradas vía formulario web. Disponible solo desde 2024.',
      'Quota di richieste con origine website o registrate tramite modulo web. Disponibile solo dal 2024.',
      'Udio upita s izvorom website ili unesenih preko web obrasca. Dostupno tek od 2024.',
      'Podíl poptávek se zdrojem website nebo zadaných přes webový formulář. Dostupné až od roku 2024.',
      'Andel forespørsler med kilde website eller registrert via webskjema. Først tilgjengelig fra 2024.',
      'Kaynağı website olan veya web formu üzerinden kaydedilen taleplerin payı. Yalnızca 2024’ten itibaren mevcut.',
      'A website forrású vagy webűrlapon rögzített érdeklődések aránya. Csak 2024-től érhető el.')),
    ('fte',
     ('FTE', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE', 'FTE'),
     ('Mittelwert der Monatswerte aus dem Blatt FTE über die berührten Monate.',
      'Gemiddelde van de maandwaarden uit het blad FTE over de betrokken maanden.',
      'Media de los valores mensuales de la hoja FTE en los meses afectados.',
      'Media dei valori mensili del foglio FTE sui mesi interessati.',
      'Prosjek mjesečnih vrijednosti s lista FTE za obuhvaćene mjesece.',
      'Průměr měsíčních hodnot z listu FTE za dotčené měsíce.',
      'Gjennomsnitt av månedsverdiene fra arket FTE for de berørte månedene.',
      'İlgili aylar için FTE sayfasındaki aylık değerlerin ortalaması.',
      'Az FTE lap havi értékeinek átlaga az érintett hónapokra.')),
    ('ap',
     ('Annual Planning', 'Annual Planning', 'Annual Planning', 'Annual Planning',
      'Annual Planning', 'Annual Planning', 'Annual Planning', 'Annual Planning', 'Annual Planning'),
     ('Monatswerte aus dem Blatt Goals. Liegt ausschließlich für die Kennzahl Teams vor; alle anderen Kennzahlen haben keinen Planwert.',
      'Maandwaarden uit het blad Goals. Bestaat uitsluitend voor het kerncijfer Teams; alle andere kerncijfers hebben geen planwaarde.',
      'Valores mensuales de la hoja Goals. Existe únicamente para el indicador Equipos; los demás no tienen valor de plan.',
      'Valori mensili dal foglio Goals. Esiste solo per l’indicatore Team; gli altri non hanno valore di piano.',
      'Mjesečne vrijednosti s lista Goals. Postoji isključivo za pokazatelj Timovi; ostali pokazatelji nemaju planiranu vrijednost.',
      'Měsíční hodnoty z listu Goals. Existuje pouze pro ukazatel Týmy; ostatní ukazatele plánovanou hodnotu nemají.',
      'Månedsverdier fra arket Goals. Finnes bare for nøkkeltallet Team; øvrige nøkkeltall har ingen planverdi.',
      'Goals sayfasındaki aylık değerler. Yalnızca Takımlar göstergesi için vardır; diğer göstergelerin plan değeri yoktur.',
      'Havi értékek a Goals lapról. Kizárólag a Csapatok mutatóhoz létezik; a többi mutatónak nincs tervértéke.')),
    ('py',
     ('Vorjahr', 'Vorig jaar', 'Año anterior', 'Anno precedente', 'Prethodna godina',
      'Předchozí rok', 'Fjorår', 'Geçen yıl', 'Előző év'),
     ('Derselbe Zeitraum ein Kalenderjahr früher, taggenau verschoben.',
      'Dezelfde periode een kalenderjaar eerder, exact op de dag verschoven.',
      'El mismo periodo un año natural antes, desplazado día a día.',
      'Lo stesso periodo un anno solare prima, spostato giorno per giorno.',
      'Isto razdoblje godinu dana ranije, pomaknuto točno po danu.',
      'Stejné období o kalendářní rok dříve, posunuté přesně o den.',
      'Samme periode ett kalenderår tidligere, forskjøvet dag for dag.',
      'Bir takvim yılı önceki aynı dönem, gün gün kaydırılmış.',
      'Ugyanaz az időszak egy naptári évvel korábban, napra pontosan eltolva.')),
    ('gj',
     ('Geschäftsjahr', 'Boekjaar', 'Ejercicio', 'Esercizio', 'Poslovna godina',
      'Hospodářský rok', 'Regnskapsår', 'Mali yıl', 'Üzleti év'),
     ('Juli bis Juni, entsprechend der AP-Logik in Combit und im Blatt Goals.',
      'Juli tot juni, volgens de AP-logica in Combit en het blad Goals.',
      'De julio a junio, conforme a la lógica AP en Combit y en la hoja Goals.',
      'Da luglio a giugno, secondo la logica AP in Combit e nel foglio Goals.',
      'Od srpnja do lipnja, prema AP logici u Combitu i na listu Goals.',
      'Červenec až červen, podle logiky AP v Combitu a na listu Goals.',
      'Juli til juni, i tråd med AP-logikken i Combit og arket Goals.',
      'Temmuz–Haziran, Combit ve Goals sayfasındaki AP mantığına uygun olarak.',
      'Júliustól júniusig, a Combit és a Goals lap AP-logikája szerint.')),
    ('mpn',
     ('Marge/Pax/Nacht', 'Marge/pax/nacht', 'Margen/pax/noche', 'Margine/pax/notte',
      'Marža/pax/noćenje', 'Marže/pax/noc', 'Margin/pax/natt', 'Marj/pax/gece', 'Árrés/pax/éjszaka'),
     ('DB geteilt durch (Ø Pax je Buchung × Ø Nächte × Teams) — dieselbe Rechnung wie im Blatt Report, dort auf vier Nachkommastellen nachgeprüft.',
      'Dekkingsbijdrage gedeeld door (gem. pax per boeking × gem. nachten × teams) — dezelfde berekening als in het blad Report, daar tot op vier decimalen gecontroleerd.',
      'Margen dividido por (pax medios por reserva × noches medias × equipos): el mismo cálculo que en la hoja Report, comprobado allí con cuatro decimales.',
      'Margine diviso per (pax medi per prenotazione × notti medie × team): lo stesso calcolo del foglio Report, verificato lì a quattro decimali.',
      'Doprinos podijeljen s (prosj. pax po rezervaciji × prosj. noćenja × timovi) — isti izračun kao na listu Report, ondje provjeren na četiri decimale.',
      'Příspěvek dělený (prům. pax na rezervaci × prům. nocí × týmy) — stejný výpočet jako na listu Report, tam ověřeno na čtyři desetinná místa.',
      'Dekningsbidrag delt på (gj.sn. pax per bestilling × gj.sn. netter × team) — samme beregning som i arket Report, der kontrollert med fire desimaler.',
      'Katkı payı / (rezervasyon başına ort. pax × ort. gece × takım) — Report sayfasındakiyle aynı hesap, orada dört ondalık basamağa kadar doğrulandı.',
      'A fedezet osztva (átl. pax/foglalás × átl. éjszaka × csapat) — ugyanaz a számítás, mint a Report lapon, ott négy tizedesjegyig ellenőrizve.')),
    ('maps',
     ('Karten', 'Kaarten', 'Mapas', 'Mappe', 'Karte', 'Mapy', 'Kart', 'Haritalar', 'Térképek'),
     ('Die Umrisse stecken als Vektorgrafik in der Seite — Natural Earth, gemeinfrei, projiziert auf ETRS89-LAEA. Es wird kein Kartendienst aufgerufen, die Karten funktionieren deshalb auch ohne Internetverbindung. Die Farbstufen liegen auf einer Wurzelskala zum Maximum.',
      'De contouren zitten als vectorafbeelding in de pagina — Natural Earth, publiek domein, geprojecteerd op ETRS89-LAEA. Er wordt geen kaartdienst aangeroepen, dus de kaarten werken ook zonder internet. De kleurklassen liggen op een wortelschaal ten opzichte van het maximum.',
      'Los contornos están incrustados en la página como gráfico vectorial: Natural Earth, dominio público, proyección ETRS89-LAEA. No se llama a ningún servicio de mapas, así que funcionan sin conexión. Las clases de color siguen una escala de raíz respecto al máximo.',
      'I contorni sono incorporati nella pagina come grafica vettoriale: Natural Earth, pubblico dominio, proiezione ETRS89-LAEA. Non viene chiamato alcun servizio di mappe, quindi funzionano anche offline. Le classi di colore seguono una scala radice rispetto al massimo.',
      'Obrisi su ugrađeni u stranicu kao vektorska grafika — Natural Earth, javno dobro, projekcija ETRS89-LAEA. Ne poziva se nijedna kartografska usluga, pa karte rade i bez interneta. Boje su razvrstane po korijenskoj skali prema maksimumu.',
      'Obrysy jsou v stránce jako vektorová grafika — Natural Earth, volné dílo, projekce ETRS89-LAEA. Nevolá se žádná mapová služba, mapy tedy fungují i bez internetu. Barevné třídy leží na odmocninové škále k maximu.',
      'Omrissene ligger i siden som vektorgrafikk — Natural Earth, offentlig eiendom, projisert til ETRS89-LAEA. Ingen karttjeneste kalles, så kartene virker også uten internett. Fargeklassene følger en kvadratrotskala mot maksimum.',
      'Sınırlar sayfaya vektör grafik olarak gömülüdür — Natural Earth, kamu malı, ETRS89-LAEA projeksiyonu. Hiçbir harita servisi çağrılmaz, bu nedenle haritalar internetsiz de çalışır. Renk sınıfları maksimuma göre karekök ölçeğindedir.',
      'A körvonalak vektorgrafikaként a lapba vannak ágyazva — Natural Earth, közkincs, ETRS89-LAEA vetület. Semmilyen térképszolgáltatás nem hívódik meg, így a térképek internet nélkül is működnek. A színosztályok a maximumhoz viszonyított négyzetgyökös skálán állnak.')),
    ('dest',
     ('Reiseland', 'Bestemming', 'País de destino', 'Paese di destinazione', 'Odredišna zemlja',
      'Cílová země', 'Reiseland', 'Varış ülkesi', 'Célország'),
     ('Spalte K im Blatt Sales, in Combit die Spalte Destination. Beide Quellen werden auf dieselbe Schreibweise gebracht, damit Buchungen und Anfragen zusammenpassen.',
      'Kolom K in het blad Sales, in Combit de kolom Destination. Beide bronnen worden op dezelfde schrijfwijze gebracht zodat boekingen en aanvragen op elkaar aansluiten.',
      'Columna K de la hoja Sales; en Combit, la columna Destination. Ambas fuentes se normalizan a la misma notación para que reservas y solicitudes encajen.',
      'Colonna K nel foglio Sales, in Combit la colonna Destination. Le due fonti vengono normalizzate alla stessa notazione perché prenotazioni e richieste combacino.',
      'Stupac K na listu Sales, u Combitu stupac Destination. Oba se izvora svode na isti zapis kako bi se rezervacije i upiti poklapali.',
      'Sloupec K na listu Sales, v Combitu sloupec Destination. Oba zdroje se převádějí na stejný zápis, aby rezervace a poptávky odpovídaly.',
      'Kolonne K i arket Sales, i Combit kolonnen Destination. Begge kilder normaliseres til samme skrivemåte slik at bestillinger og forespørsler passer sammen.',
      'Sales sayfasında K sütunu, Combit’te Destination sütunu. Rezervasyonlar ile taleplerin eşleşmesi için her iki kaynak aynı yazıma getirilir.',
      'A Sales lap K oszlopa, a Combitban a Destination oszlop. Mindkét forrás azonos írásmódra kerül, hogy a foglalások és érdeklődések összeilljenek.')),
    ('herk',
     ('Kundenherkunft', 'Herkomst klant', 'Origen del cliente', 'Provenienza cliente',
      'Podrijetlo klijenta', 'Původ zákazníka', 'Kundens opprinnelse', 'Müşteri kaynağı',
      'Ügyfél származása'),
     ('Spalte G im Blatt Sales, in Combit die Spalte KundenHerkunft. Ebenfalls angeglichen.',
      'Kolom G in het blad Sales, in Combit de kolom KundenHerkunft. Eveneens gelijkgetrokken.',
      'Columna G de la hoja Sales; en Combit, la columna KundenHerkunft. También normalizada.',
      'Colonna G nel foglio Sales, in Combit la colonna KundenHerkunft. Anch’essa allineata.',
      'Stupac G na listu Sales, u Combitu stupac KundenHerkunft. Također usklađeno.',
      'Sloupec G na listu Sales, v Combitu sloupec KundenHerkunft. Rovněž sjednoceno.',
      'Kolonne G i arket Sales, i Combit kolonnen KundenHerkunft. Også harmonisert.',
      'Sales sayfasında G sütunu, Combit’te KundenHerkunft sütunu. O da eşitlenmiştir.',
      'A Sales lap G oszlopa, a Combitban a KundenHerkunft oszlop. Szintén egységesítve.')),
    ('region',
     ('Region', 'Regio', 'Región', 'Regione', 'Regija', 'Region', 'Region', 'Bölge', 'Régió'),
     ('Spalte H im Blatt Sales — Bundesland, Kanton oder Bundesstaat des Kunden. Existiert nur für Buchungen; Combit führt kein Bundesland. Ein gesetzter Regionsfilter lässt deshalb alle Kennzahlen aus dem Anfrage- und Angebotsbereich leer.',
      'Kolom H in het blad Sales — deelstaat, kanton of provincie van de klant. Bestaat alleen voor boekingen; Combit kent geen deelstaat. Een actief regiofilter laat daarom alle cijfers uit aanvragen en offertes leeg.',
      'Columna H de la hoja Sales: estado federado, cantón o provincia del cliente. Solo existe para reservas; Combit no registra el estado. Por eso, con filtro de región todos los indicadores de solicitudes y ofertas quedan vacíos.',
      'Colonna H nel foglio Sales: land, cantone o stato del cliente. Esiste solo per le prenotazioni; Combit non registra il land. Con un filtro di regione tutti gli indicatori di richieste e offerte restano quindi vuoti.',
      'Stupac H na listu Sales — savezna pokrajina, kanton ili država klijenta. Postoji samo za rezervacije; Combit ne vodi pokrajinu. Postavljen filtar regije zato ostavlja sve pokazatelje upita i ponuda praznima.',
      'Sloupec H na listu Sales — spolková země, kanton nebo stát zákazníka. Existuje jen u rezervací; Combit spolkovou zemi nevede. Nastavený filtr regionu proto nechává všechny ukazatele poptávek a nabídek prázdné.',
      'Kolonne H i arket Sales — delstat, kanton eller fylke for kunden. Finnes bare for bestillinger; Combit fører ingen delstat. Et satt regionfilter lar derfor alle nøkkeltall for forespørsler og tilbud stå tomme.',
      'Sales sayfasında H sütunu — müşterinin eyaleti, kantonu veya ili. Yalnızca rezervasyonlar için vardır; Combit eyalet tutmaz. Bu nedenle bölge filtresi seçiliyken talep ve teklif göstergelerinin tümü boş kalır.',
      'A Sales lap H oszlopa — az ügyfél tartománya, kantonja vagy állama. Csak foglalásokhoz létezik; a Combit nem tart nyilván tartományt. Beállított régiószűrő esetén ezért az érdeklődés- és ajánlatmutatók mind üresek maradnak.')),
    ('hotel',
     ('Hotel', 'Hotel', 'Hotel', 'Hotel', 'Hotel', 'Hotel', 'Hotell', 'Otel', 'Szálloda'),
     ('Spalte 9 im Blatt Sales trägt dieselbe WebID wie der Combit-Export und das Blatt Locations. Darüber hängen Anfragen, Angebote und Buchungen am selben Haus. Name, Land, Exklusivität und der Verkaufsstart stammen aus dem Blatt Locations.',
      'Kolom 9 in het blad Sales draagt dezelfde WebID als de Combit-export en het blad Locations. Daardoor hangen aanvragen, offertes en boekingen aan hetzelfde huis. Naam, land, exclusiviteit en verkoopstart komen uit het blad Locations.',
      'La columna 9 de la hoja Sales lleva el mismo WebID que la exportación de Combit y la hoja Locations. Así, solicitudes, ofertas y reservas cuelgan del mismo establecimiento. Nombre, país, exclusividad e inicio de venta proceden de Locations.',
      'La colonna 9 del foglio Sales porta lo stesso WebID dell’export Combit e del foglio Locations. Così richieste, offerte e prenotazioni fanno capo alla stessa struttura. Nome, paese, esclusività e inizio vendita provengono da Locations.',
      'Stupac 9 na listu Sales nosi isti WebID kao Combit izvoz i list Locations. Time upiti, ponude i rezervacije pripadaju istom objektu. Naziv, zemlja, ekskluzivnost i početak prodaje dolaze s lista Locations.',
      'Sloupec 9 na listu Sales nese stejné WebID jako export z Combitu a list Locations. Poptávky, nabídky a rezervace tak patří ke stejnému objektu. Název, země, exkluzivita a začátek prodeje pocházejí z listu Locations.',
      'Kolonne 9 i arket Sales bærer samme WebID som Combit-eksporten og arket Locations. Dermed hører forespørsler, tilbud og bestillinger til samme hus. Navn, land, eksklusivitet og salgsstart kommer fra arket Locations.',
      'Sales sayfasındaki 9. sütun, Combit dışa aktarımı ve Locations sayfasıyla aynı WebID’yi taşır. Böylece talepler, teklifler ve rezervasyonlar aynı tesise bağlanır. Ad, ülke, münhasırlık ve satış başlangıcı Locations sayfasından gelir.',
      'A Sales lap 9. oszlopa ugyanazt a WebID-t hordozza, mint a Combit export és a Locations lap. Így az érdeklődések, ajánlatok és foglalások ugyanahhoz a házhoz kapcsolódnak. A név, ország, exkluzivitás és értékesítési kezdet a Locations lapról származik.')),
    ('bq',
     ('Buchungsquote', 'Boekingsquote', 'Tasa de reserva', 'Tasso di prenotazione', 'Stopa rezervacija',
      'Míra rezervací', 'Bestillingsrate', 'Rezervasyon oranı', 'Foglalási arány'),
     ('Teams ÷ alle Anfragen im gewählten Zeitraum — jede Zeile mit Belegart Anfrage in C_AP, ohne Unique-Regel. Je Team und je Hotel, mit Vorjahr. Nötige Quote für AP = AP-Teams ÷ alle Anfragen: so hoch müsste die Quote sein, um die geplanten Teams mit den tatsächlichen Anfragen zu erreichen. Erst ab 01/2024, weil es davor keine einzelnen Anfragen gibt.',
      'Teams ÷ alle aanvragen in de gekozen periode — elke regel met documenttype Anfrage in C_AP, zonder unique-regel. Per team en per hotel, met vorig jaar. Benodigde quote voor AP = AP-teams ÷ alle aanvragen: zo hoog zou de quote moeten zijn om de geplande teams met de werkelijke aanvragen te halen. Pas vanaf 01/2024.',
      'Equipos ÷ todas las solicitudes del periodo: cada fila con tipo Anfrage en C_AP, sin regla de únicos. Por equipo y por hotel, con año anterior. Tasa necesaria para AP = equipos AP ÷ todas las solicitudes: la tasa necesaria para alcanzar los equipos planificados con las solicitudes reales. Solo desde 01/2024.',
      'Team ÷ tutte le richieste del periodo: ogni riga con tipo Anfrage in C_AP, senza regola unique. Per team e per hotel, con anno precedente. Tasso necessario per AP = team AP ÷ tutte le richieste: il tasso che servirebbe per raggiungere i team pianificati con le richieste reali. Solo dal 01/2024.',
      'Timovi ÷ svi upiti u razdoblju — svaki redak vrste Anfrage u C_AP, bez pravila jedinstvenosti. Po timu i po hotelu, s prethodnom godinom. Potrebna stopa za AP = AP timovi ÷ svi upiti: kolika bi stopa trebala biti da se sa stvarnim upitima dosegnu planirani timovi. Tek od 01/2024.',
      'Týmy ÷ všechny poptávky v období — každý řádek typu Anfrage v C_AP, bez pravidla unikátnosti. Podle týmu a hotelu, s loňským rokem. Potřebná míra pro AP = AP týmy ÷ všechny poptávky: jak vysoká by míra musela být, aby se se skutečnými poptávkami dosáhlo plánovaných týmů. Až od 01/2024.',
      'Team ÷ alle forespørsler i perioden — hver rad med dokumenttype Anfrage i C_AP, uten unik-regel. Per team og per hotell, med fjoråret. Nødvendig rate for AP = AP-team ÷ alle forespørsler: så høy måtte raten være for å nå de planlagte teamene med de faktiske forespørslene. Først fra 01/2024.',
      'Takımlar ÷ dönemdeki tüm talepler — C_AP’deki Anfrage türündeki her satır, tekillik kuralı olmadan. Takım ve otel bazında, geçen yılla. AP için gereken oran = AP takımları ÷ tüm talepler: gerçek taleplerle planlanan takımlara ulaşmak için gereken oran. Ancak 01/2024’ten itibaren.',
      'Csapatok ÷ összes érdeklődés az időszakban — minden Anfrage típusú sor a C_AP-ben, egyediségi szabály nélkül. Csapatonként és szállodánként, előző évvel. AP-hoz szükséges arány = AP-csapatok ÷ összes érdeklődés: ekkora aránnyal lehetne a valós érdeklődésekből elérni a tervezett csapatokat. Csak 2024/01-től.')),
    ('hotelview',
     ('Hotelblick', 'Hotelbeeld', 'Vista de hotel', 'Vista hotel', 'Prikaz hotela',
      'Pohled na hotel', 'Hotellvisning', 'Otel görünümü', 'Szállodanézet'),
     ('Nutzt den gewählten Zeitraum und die Filter für Bereich, Team und Reiseland. Ohne Filter zählen alle Teams; die Aufteilung steht in der Teamtabelle daneben. Mit Kundenherkunft oder Region gibt es keine Anfragen und Angebote je Hotel.',
      'Gebruikt de gekozen periode en de filters voor gebied, team en bestemming. Zonder filter tellen alle teams; de verdeling staat in de teamtabel ernaast. Met klantherkomst of regio zijn er geen aanvragen en offertes per hotel.',
      'Usa el periodo elegido y los filtros de área, equipo y destino. Sin filtro cuentan todos los equipos; el reparto figura en la tabla contigua. Con origen del cliente o región no hay solicitudes ni ofertas por hotel.',
      'Usa il periodo scelto e i filtri per area, team e destinazione. Senza filtro contano tutti i team; la ripartizione è nella tabella accanto. Con provenienza clienti o regione non ci sono richieste e offerte per hotel.',
      'Koristi odabrano razdoblje i filtre za područje, tim i odredište. Bez filtra broje se svi timovi; raspodjela je u tablici pokraj. Uz podrijetlo kupaca ili regiju nema upita i ponuda po hotelu.',
      'Používá zvolené období a filtry pro oblast, tým a destinaci. Bez filtru se počítají všechny týmy; rozdělení je v sousední tabulce. S původem zákazníků nebo regionem nejsou poptávky a nabídky podle hotelu k dispozici.',
      'Bruker valgt periode og filtrene for område, team og reisemål. Uten filter teller alle team; fordelingen står i tabellen ved siden av. Med kundeopprinnelse eller region finnes ingen forespørsler og tilbud per hotell.',
      'Seçilen dönemi ve alan, takım ve varış ülkesi filtrelerini kullanır. Filtre yoksa tüm takımlar sayılır; dağılım yandaki tablodadır. Müşteri kökeni veya bölge ile otel bazında talep ve teklif yoktur.',
      'A kiválasztott időszakot és a terület, csapat és úti cél szűrőit használja. Szűrő nélkül minden csapat számít; a megoszlás a melletti táblázatban látható. Ügyfélszármazás vagy régió esetén nincsenek szállodánkénti érdeklődések és ajánlatok.')),
    ('rank',
     ('Rangliste', 'Ranglijst', 'Clasificación', 'Classifica', 'Poredak', 'Pořadí',
      'Rangering', 'Sıralama', 'Rangsor'),
     ('Alle Hotels mit mindestens einem Vorgang im Zeitraum. Sobald Bereich, Team, Land oder Region eingegrenzt sind, entfallen die Spalten Anfragen und Angebote, weil diese Daten nicht gleichzeitig nach Hotel und Team oder Land vorliegen.',
      'Alle hotels met minstens één dossier in de periode. Zodra segment, team, land of regio is beperkt, vervallen de kolommen Aanvragen en Offertes, omdat die data niet tegelijk per hotel én team of land bestaan.',
      'Todos los hoteles con al menos una operación en el periodo. Al acotar área, equipo, país o región desaparecen las columnas Solicitudes y Ofertas, porque esos datos no existen a la vez por hotel y equipo o país.',
      'Tutti gli hotel con almeno una pratica nel periodo. Non appena si restringe settore, team, paese o regione, le colonne Richieste e Offerte scompaiono, perché quei dati non esistono contemporaneamente per hotel e team o paese.',
      'Svi hoteli s barem jednim predmetom u razdoblju. Čim se suze područje, tim, zemlja ili regija, nestaju stupci Upiti i Ponude jer ti podaci ne postoje istodobno po hotelu i timu ili zemlji.',
      'Všechny hotely s alespoň jednou transakcí v období. Jakmile se omezí oblast, tým, země nebo region, zmizí sloupce Poptávky a Nabídky, protože tato data neexistují současně podle hotelu a týmu nebo země.',
      'Alle hoteller med minst én sak i perioden. Så snart område, team, land eller region avgrenses, faller kolonnene Forespørsler og Tilbud bort, fordi disse dataene ikke finnes samtidig per hotell og team eller land.',
      'Dönemde en az bir işlemi olan tüm oteller. Alan, takım, ülke veya bölge daraltıldığında Talepler ve Teklifler sütunları kaybolur; çünkü bu veriler otel ile takım veya ülke kırılımında aynı anda bulunmaz.',
      'Minden szálloda, amelyhez az időszakban legalább egy ügy tartozik. Amint a terület, csapat, ország vagy régió szűkítve van, az Érdeklődések és Ajánlatok oszlopok eltűnnek, mert ezek az adatok nem állnak rendelkezésre egyszerre szállodánként és csapatonként vagy országonként.')),
]

for key, titles, bodies in DEFS:
    S['def.%s.t' % key] = dict(zip([c for c, _ in LANGS], titles))
    S['def.%s.d' % key] = dict(zip([c for c, _ in LANGS], bodies))

if __name__ == '__main__':
    codes = [c for c, _ in LANGS]
    missing = [(k, c) for k, v in S.items() for c in codes if not v.get(c)]
    if missing:
        print('Fehlende Uebersetzungen: %s' % missing[:10], file=sys.stderr)
    out = {c: {k: v.get(c) or v['de'] for k, v in S.items()} for c in codes}
    sys.stdout.write(
        '/* Oberflaechentexte. Laender- und Monatsnamen kommen zur Laufzeit\n'
        '   aus Intl, Regionsnamen bleiben als Eigennamen unveraendert.\n'
        '   Erzeugt von i18n/make_i18n.py - dort aendern, nicht hier. */\n'
        'const LANGS=' + json.dumps(LANGS, ensure_ascii=False) + ';\n'
        'const I18N=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('%d Schluessel x %d Sprachen' % (len(S), len(codes)), file=sys.stderr)
