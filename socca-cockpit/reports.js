/* ======================================================================
   Reports — Monatsvergleich, Team Status Report, Country Status Report
   ----------------------------------------------------------------------
   Läuft innerhalb von start(D) und nutzt dessen Helfer (t, nf, MONTHS,
   cname, emptyBase, MBY). Die Reports rechnen immer in ganzen Monaten und
   ignorieren die Filter des Cockpits — sie haben ihre eigene Auswahl.
   ====================================================================== */

/* --- Monatsindex je Zeile einmal vorberechnen ------------------------ */
const monthOfDay = i => { const d=i2d(i); return (d.getUTCFullYear()-2019)*12 + d.getUTCMonth(); };
const RB = new Map(), RL = new Map();
for(const r of D.bookings){ const m=monthOfDay(r[0]); (RB.get(m)||RB.set(m,[]).get(m)).push(r); }
for(const r of D.leadDaily){ const m=monthOfDay(r[0]); (RL.get(m)||RL.set(m,[]).get(m)).push(r); }
const LAST_M = monthOfDay(maxDay);
const FIRST_M = monthOfDay(minDay);
const CUTM = D.meta.leadCutMonth ?? 60;

/* Teamreihenfolge wie in der bisherigen Monatsübersicht, weitere dahinter */
const TEAM_ORDER = ['FUSU','FUNO','FUSO','FUFA','FUCH','FUAT','FUIT','FUCZ','FUES','FUHR',
                    'FUNL','FUNW','FUTU','TECA','SWIM','LATR'];
/* Zielmärkte des CSR */
const CSR_MAIN = ['ES','I','HR','CZ','A','HU','TR'];

/* --- Aggregation über ganze Monate ------------------------------------ */
/* p: {team, dest, herk} — jedes Feld optional */
function rAgg(m0, m1, p={}){
  const b = emptyBase();
  const ti = p.team ? D.teams.indexOf(p.team) : -1;
  const di = p.dest ? D.dests.indexOf(p.dest) : -1;
  const hi = p.herk ? D.regs.indexOf(p.herk)  : -1;
  for(let m=m0; m<=m1; m++){
    for(const r of (RB.get(m)||[])){
      if(p.team && r[1]!==ti) continue;
      if(p.dest && r[12]!==di) continue;
      if(p.herk && r[3]!==hi)  continue;
      b.book++; b.vk+=r[5]; b.ek+=r[6]; b.db+=r[7];
      b.teams+=r[8]; b.pax+=r[9]; b.nights+=r[10]; b.paxn+=r[9]*r[10];
    }
    if(m>=CUTM){
      for(const r of (RL.get(m)||[])){
        if(p.team && r[1]!==ti) continue;
        if(p.dest && r[3]!==di) continue;
        if(p.herk && r[2]!==hi) continue;
        b.leads+=r[4]; b.web+=r[5]; b.props+=r[6]; b.leadsAll+=(r[7]||0);
      }
    }
  }
  b.bqNA = m0 < CUTM;                    // alle Anfragen erst ab 2024
  /* Vor 2024 nur Monatssummen je Team, ohne Land */
  if(m0<CUTM){
    if(p.dest || p.herk){ b.leadNA = true; }
    else {
      for(const r of D.leadMonthly){ if(r[0]<m0||r[0]>m1||r[0]>=CUTM) continue;
        if(p.team && r[1]!==ti) continue; b.leads+=r[2]; }
      for(const r of D.propMonthly){ if(r[0]<m0||r[0]>m1||r[0]>=CUTM) continue;
        if(p.team && r[1]!==ti) continue; b.props+=r[2]; }
      b.webNA = true;
    }
  }
  /* FTE und AP gibt es nur je Team */
  b.dimFiltered = !!(p.dest || p.herk);
  if(!b.dimFiltered){
    const per=new Map();
    for(const r of D.fte){ if(r[0]<m0||r[0]>m1) continue; if(p.team && r[1]!==ti) continue;
      per.set(r[0],(per.get(r[0])||0)+r[2]); }
    b.fte = per.size ? [...per.values()].reduce((a,c)=>a+c,0)/per.size : 0;
    for(const r of D.ap){ if(r[0]<m0||r[0]>m1) continue; if(p.team && r[1]!==ti) continue; b.apTeams+=r[2]; }
    b.apLeads=0; b.hasApLeads=false;
    for(const r of (D.apLeads||[])){ if(r[0]<m0||r[0]>m1) continue; if(p.team && r[1]!==ti) continue;
      b.apLeads+=r[2]; b.hasApLeads=true; }
  }
  return b;
}
const rv = (id,b) => {
  if(id==='web'||id==='webq'){ if(b.webNA) return null; }
  return metricVal(id,b);
};

/* --- Fenster ----------------------------------------------------------- */
const W = {
  m1:  M => [M, M],
  m3:  M => [M-2, M],
  m12: M => [M-11, M],
};
/* Geschäftsjahr beginnt im Juli */
const fyStart = M => M - (((M % 12) - 6 + 12) % 12);
const monLabel = (M, long) => {
  const d = mStart(M);
  if(long) return new Intl.DateTimeFormat(LOC,{month:'long',year:'numeric',timeZone:'UTC'}).format(d);
  return `${MONTHS[d.getUTCMonth()]} ${String(d.getUTCFullYear()).slice(2)}`;
};

/* --- Formatierung für Reporttabellen: volle Beträge -------------------- */
function rf(id, v){
  if(v===null||v===undefined||!isFinite(v)) return '—';
  const m = MBY[id];
  if(m.pct) return nf(v*100,1)+' %';
  if(m.fac) return nf(v,2)+' ×';
  if(m.cur) return nf(v, id==='mpn' ? 2 : 0)+' €';
  return nf(v, m.d);
}
function trendCell(cur, ref, invert){
  if(cur===null||ref===null||!isFinite(cur)||!isFinite(ref)||ref===0) return '<td class="tr">—</td>';
  const p=(cur-ref)/Math.abs(ref);
  const good = invert ? p<0 : p>0;
  const cls = Math.abs(p)<0.005 ? '' : (good ? 'pos' : 'neg');
  return `<td class="tr ${cls}">${p>0?'+':''}${nf(p*100,1)} %</td>`;
}
function deltaCell(v, fmtfn){
  if(v===null||!isFinite(v)) return '<td class="dl">—</td>';
  const r = Math.round(v);
  const cls = r>0 ? 'pos' : (r<0 ? 'neg' : '');
  return `<td class="dl ${cls}">${r>0?'+':''}${fmtfn?fmtfn(v):nf(v,0)}</td>`;
}
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');

/* ======================================================================
   1) Monatsvergleich
   ====================================================================== */
function reportCompare(M){
  const PY = M-12;
  const active = new Set();
  for(const m of [M,PY]) for(const r of (RB.get(m)||[])) if(r[1]>=0) active.add(D.teams[r[1]]);
  for(const m of [M,PY]) for(const r of (RL.get(m)||[])) active.add(D.teams[r[1]]);
  const teams = TEAM_ORDER.filter(x=>D.teams.includes(x));
  const others = D.teams.filter(x=>!TEAM_ORDER.includes(x) && active.has(x));
  const fy0 = fyStart(M);

  const cur={}, vj={}, fy={};
  for(const tm of [...teams, ...others]){
    cur[tm]=rAgg(M,M,{team:tm}); vj[tm]=rAgg(PY,PY,{team:tm}); fy[tm]=rAgg(fy0,M,{team:tm});
  }
  const sumOf = (src, list) => { const b=emptyBase(); b.hasApLeads=false; b.apLeads=0;
    for(const tm of list){ const x=src[tm];
      for(const k of ['book','vk','ek','db','teams','pax','nights','paxn','leads','web','props','leadsAll','apTeams','apLeads','fte'])
        b[k]+=x[k]||0;
      b.hasApLeads = b.hasApLeads || x.hasApLeads; b.webNA = b.webNA || x.webNA; b.bqNA = b.bqNA || x.bqNA; }
    return b; };
  const all=[...teams,...others];
  if(others.length){ cur.__oth=sumOf(cur,others); vj.__oth=sumOf(vj,others); fy.__oth=sumOf(fy,others); }
  cur.__sum=sumOf(cur,all); vj.__sum=sumOf(vj,all); fy.__sum=sumOf(fy,all);
  const cols=[...teams, ...(others.length?['__oth']:[]), '__sum'];
  const L0=monLabel(PY), L1=monLabel(M);
  const hasApL = cur.__sum.hasApLeads;

  const row = (lab, sub, fn, cls='') =>
    `<tr class="${cls}"><th class="rl">${lab}</th><th class="rs">${sub}</th>`+
    cols.map(c=>`<td${c==='__sum'?' class="sm"':''}>${fn(c)}</td>`).join('')+`</tr>`;
  const drow = (lab, sub, fn) =>
    `<tr class="dr"><th class="rl">${lab}</th><th class="rs">${sub}</th>`+
    cols.map(c=>deltaCell(fn(c)).replace('<td class="dl', c==='__sum'?'<td class="dl sm':'<td class="dl')).join('')+`</tr>`;
  const gap = `<tr class="gap"><td colspan="${cols.length+2}"></td></tr>`;
  const n0 = v => v===null||!isFinite(v) ? '—' : nf(v,0);
  const eur = v => v===null||!isFinite(v) ? '—' : nf(v,0)+' €';
  const pct = v => v===null||!isFinite(v) ? '—' : nf(v*100,0)+' %';

  let h=`<table class="rt cmp"><thead><tr><th></th><th></th>`+
    cols.map(c=>`<th${c==='__sum'?' class="sm"':''}${c==='__oth'?` title="${others.join(', ')}"`:''}>${
      c==='__sum'?t('rp.sum'):(c==='__oth'?t('rp.more'):c)}</th>`).join('')+`</tr></thead><tbody>`;

  h+=row(MBY.leads.n, L0, c=>n0(rv('leads',vj[c])));
  h+=row('', L1, c=>`<b>${n0(rv('leads',cur[c]))}</b>`);
  if(hasApL){
    h+=row('', t('t.ap'), c=>n0(cur[c].apLeads), 'ap');
    h+=drow('', t('rp.deltaAP'), c=>(rv('leads',cur[c])??0)-cur[c].apLeads);
  }
  h+=gap;
  h+=row(MBY.web.n, L0, c=>n0(rv('web',vj[c])));
  h+=row('', L1, c=>`<b>${n0(rv('web',cur[c]))}</b>`);
  h+=gap;
  h+=row(t('rp.webShare'), L0, c=>pct(rv('webq',vj[c])));
  h+=row('', L1, c=>`<b>${pct(rv('webq',cur[c]))}</b>`);
  h+=gap;
  h+=row(MBY.props.n, L0, c=>n0(rv('props',vj[c])));
  h+=row('', L1, c=>`<b>${n0(rv('props',cur[c]))}</b>`);
  h+=gap;
  h+=row(MBY.teams.n, L0, c=>n0(vj[c].teams));
  h+=row('', L1, c=>`<b>${n0(cur[c].teams)}</b>`);
  h+=row('', t('t.ap'), c=>n0(cur[c].apTeams), 'ap');
  h+=drow('', t('rp.deltaAP'), c=>cur[c].teams-cur[c].apTeams);
  h+=gap;
  h+=row(MBY.db.n, L0, c=>eur(vj[c].db));
  h+=row('', L1, c=>`<b>${eur(cur[c].db)}</b>`);
  h+=drow('', t('rp.deltaPY'), c=>cur[c].db-vj[c].db);
  /* Ergänzungen */
  h+=`<tr class="sep"><td colspan="${cols.length+2}">${t('rp.added')}</td></tr>`;
  h+=row(t('rp.gjCum'), t('rp.fyLabel',{a:monLabel(fy0),b:monLabel(M)}), c=>`<b>${n0(fy[c].teams)}</b>`, 'add');
  h+=row('', t('t.ap'), c=>n0(fy[c].apTeams), 'ap add');
  h+=row('', t('rp.attain'), c=>{
    const a=fy[c].apTeams; if(!a) return '—';
    const q=fy[c].teams/a; const cls=q>=1?'pos':(q>=0.9?'':'neg');
    return `<span class="pill ${cls}">${nf(q*100,0)} %</span>`; }, 'add');
  h+=gap;
  h+=row(MBY.quote2.n, L0, c=>pct(rv('quote2',vj[c])), 'add');
  h+=row('', L1, c=>`<b>${pct(rv('quote2',cur[c]))}</b>`, 'add');
  h+=gap;
  h+=row(MBY.dbteam.n, L0, c=>eur(rv('dbteam',vj[c])), 'add');
  h+=row('', L1, c=>`<b>${eur(rv('dbteam',cur[c]))}</b>`, 'add');
  h+=`</tbody></table>`;

  const notes=[];
  if(!hasApL) notes.push(t('rp.noApLeads'));
  return page({
    kind: t('rp.cmp'),
    title: t('rp.cmpTitle',{a:monLabel(PY,true), b:monLabel(M,true)}),
    meta: monLabel(M,true),
    sheets: [`<div class="tablewrap rtw">${h}</div>`],
    notes
  });
}

/* ======================================================================
   2) + 3) Status Reports — gemeinsamer Kennzahlenblock
   ====================================================================== */
function kpiBlock(M, p, ids){
  const wins=[['m1',t('rp.win1')],['m3',t('rp.win3')],['m12',t('rp.win12')]];
  const A={};
  for(const [k] of wins){
    const [a,b]=W[k](M); A[k]={cur:rAgg(a,b,p), vj:rAgg(a-12,b-12,p)};
  }
  let h=`<table class="rt kpi"><thead><tr><th rowspan="2"></th>`+
    wins.map(([,l])=>`<th colspan="3" class="grp">${l}</th>`).join('')+`</tr><tr>`+
    wins.map(()=>`<th>${t('t.py')}</th><th>${t('pn.ist')}</th><th>${t('rp.trend')}</th>`).join('')+
    `</tr></thead><tbody>`;
  for(const id of ids){
    const star = id.startsWith('*'); const mid = star ? id.slice(1) : id;
    h+=`<tr${star?' class="add"':''}><th class="rl">${MBY[mid].n}${star?' <span class="st">★</span>':''}</th>`;
    for(const [k] of wins){
      const c=rv(mid,A[k].cur), v=rv(mid,A[k].vj);
      h+=`<td class="vj">${rf(mid,v)}</td><td class="is">${rf(mid,c)}</td>`+trendCell(c,v, mid==='ek');
    }
    h+=`</tr>`;
  }
  h+=`</tbody></table>`;
  return {html:h, A};
}

/* Kleines Balkendiagramm: 12 Monate Ist, Vorjahr als Strich, optional AP */
function miniChart(M, p, id, withAP){
  const pts=[];
  for(let m=M-11;m<=M;m++){
    const c=rAgg(m,m,p), v=rAgg(m-12,m-12,p);
    pts.push({m, c:rv(id,c), v:rv(id,v),
              ap: withAP ? (id==='leads' ? (c.hasApLeads ? c.apLeads : null) : c.apTeams) : null});
  }
  const W0=560,H0=170,PL=44,PR=8,PT=10,PB=24;
  const hi=Math.max(1e-9,...pts.map(x=>Math.max(x.c||0,x.v||0,x.ap||0)));
  const bw=(W0-PL-PR)/pts.length, Y=v=>PT+(H0-PT-PB)*(1-v/hi);
  let s=`<svg viewBox="0 0 ${W0} ${H0}" role="img" aria-label="${esc(MBY[id].n)}">`;
  for(let i=0;i<=3;i++){ const v=hi*i/3;
    s+=`<line class="gridline" x1="${PL}" x2="${W0-PR}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}"/>`+
       `<text class="axis" x="${PL-6}" y="${(Y(v)+4).toFixed(1)}" text-anchor="end">${fmt(id,v)}</text>`; }
  pts.forEach((x,i)=>{
    const X=PL+i*bw;
    if(x.c>0){ const y=Y(x.c); s+=`<rect x="${(X+2).toFixed(1)}" y="${y.toFixed(1)}" width="${Math.max(1,bw-4).toFixed(1)}" height="${(H0-PB-y).toFixed(1)}" fill="var(--s-ist)" rx="2"/>`; }
    if(x.v>0){ const y=Y(x.v); s+=`<line x1="${(X+2).toFixed(1)}" x2="${(X+bw-2).toFixed(1)}" y1="${y.toFixed(1)}" y2="${y.toFixed(1)}" stroke="var(--s-vj)" stroke-width="2.5"/>`; }
    if(withAP && x.ap>0){ const y=Y(x.ap); s+=`<circle cx="${(X+bw/2).toFixed(1)}" cy="${y.toFixed(1)}" r="3.5" fill="var(--s-ap)" stroke="var(--surface)" stroke-width="1.5"/>`; }
    const d=mStart(x.m);
    if(i%2===(pts.length-1)%2) s+=`<text class="axis" x="${(X+bw/2).toFixed(1)}" y="${H0-7}" text-anchor="middle">${MONTHS[d.getUTCMonth()]}</text>`;
    s+=`<rect class="hit" x="${X.toFixed(1)}" y="${PT}" width="${bw.toFixed(1)}" height="${H0-PT-PB}" data-tip="${esc(monLabel(x.m))}\n${esc(t('pn.ist'))}: ${esc(rf(id,x.c))}\n${esc(t('ctl.py'))}: ${esc(rf(id,x.v))}${withAP?'\n'+esc(t('t.ap'))+': '+esc(rf(id,x.ap)):''}"/>`;
  });
  s+=`</svg>`;
  const leg=`<div class="legend"><span><i style="background:var(--s-ist)"></i>${t('pn.ist')}</span>`+
    `<span><i style="background:var(--s-vj);height:3px"></i>${t('ctl.py')}</span>`+
    (withAP?`<span><i style="background:var(--s-ap);border-radius:50%"></i>${t('t.ap')}</span>`:'')+`</div>`;
  return s+leg;
}

/* Aufteilung nach einer Dimension, 12 Monate, mit Vorjahr */
function splitTable(M, p, dim, limit, label){
  const [a,b]=W.m12(M);
  const keyOf = r => dim==='dest' ? (r[12]>=0?D.dests[r[12]]:null)
                   : dim==='herk' ? (r[3]>=0?D.regs[r[3]]:null)
                   : dim==='team' ? (r[1]>=0?D.teams[r[1]]:null)
                   : dim==='sport'? (r[2]>=0?D.sports[r[2]]:null)
                   : (r[4]>=0?r[4]:null);
  const ti=p.team?D.teams.indexOf(p.team):-1, di=p.dest?D.dests.indexOf(p.dest):-1;
  const acc=(m0,m1)=>{ const o=new Map();
    for(let m=m0;m<=m1;m++) for(const r of (RB.get(m)||[])){
      if(p.team && r[1]!==ti) continue; if(p.dest && r[12]!==di) continue;
      const k=keyOf(r); if(k===null) continue;
      let x=o.get(k); if(!x){ x={teams:0,book:0,vk:0,db:0}; o.set(k,x); }
      x.teams+=r[8]; x.book++; x.vk+=r[5]; x.db+=r[7]; }
    return o; };
  const cur=acc(a,b), vj=acc(a-12,b-12);
  const tot=[...cur.values()].reduce((s,x)=>s+x.db,0);
  const rows=[...cur.entries()].sort((x,y)=>y[1].db-x[1].db).slice(0,limit);
  const name = k => dim==='dest'||dim==='herk' ? cname(k)
                  : dim==='sport' ? (t('sp.'+k)!=='sp.'+k ? t('sp.'+k) : k)
                  : dim==='hotel' ? esc(D.hotels[k][1]) : k;
  let h=`<table class="rt split"><thead><tr><th>${label}</th><th>${MBY.teams.n}</th><th>${MBY.vk.n}</th>`+
        `<th>${MBY.db.n}</th><th>${MBY.ros.n}</th><th>${t('rp.share')}</th><th>${t('rp.dbPY')}</th></tr></thead><tbody>`;
  for(const [k,x] of rows){
    const v=vj.get(k); const ros=x.vk?x.db/x.vk:null;
    h+=`<tr><th class="rl">${name(k)}</th><td>${nf(x.teams,0)}</td><td>${nf(x.vk,0)} €</td>`+
       `<td><b>${nf(x.db,0)} €</b></td><td>${ros===null?'—':nf(ros*100,1)+' %'}</td>`+
       `<td>${tot?nf(x.db/tot*100,0)+' %':'—'}</td>`+trendCell(x.db, v?v.db:null)+`</tr>`;
  }
  if(!rows.length) h+=`<tr><td colspan="7" class="empty">${t('ho.noBookings')}</td></tr>`;
  h+=`</tbody></table>`;
  return h;
}

/* Annual-Planning-Kacheln für den TSR: Teams und Anfragen gegen AP */
function apTiles(M, team, kind){
  const fy0=fyStart(M), fy1=fy0+11;
  const mon=rAgg(M,M,{team}), ytd=rAgg(fy0,M,{team}), full=rAgg(fy0,fy1,{team});
  const tile=(k,v,sub,cls='')=>`<div class="rtile ${cls}"><span class="k">${k}</span><span class="v">${v}</span><span class="sub">${sub}</span></div>`;
  const rowOf=(ist, plan, kMon, kFY, kPlanFY)=>{
    const [im, iy]=ist, [pm, py, pf]=plan;
    const q = py ? iy/py : null, d = im-pm, rest = pf - iy;
    const ok = q!==null && Math.round(q*100)>=100;
    return `<div class="rtiles">`+
      tile(kMon, nf(im,0), `${t('t.ap')} ${nf(pm,0)} · <span class="${d>=0?'pos':'neg'}">${d>=0?'+':''}${nf(d,0)}</span>`)+
      tile(kFY, nf(iy,0), `${t('t.ap')} ${nf(py,0)} · ${t('rp.fyLabel',{a:monLabel(fy0),b:monLabel(M)})}`)+
      tile(t('rp.attain'), q===null?'—':nf(q*100,0)+' %', q===null?'':(ok?t('rp.onTrack'):t('rp.behind')), q===null?'':(ok?'ok':(q>=0.9?'':'bad')))+
      tile(kPlanFY, nf(pf,0), `${t('rp.remaining')}: ${nf(Math.max(0,rest),0)}`)+
    `</div>`;
  };
  if(kind==='leads'){
    if(!full.hasApLeads) return `<p class="empty">${t('rp.noApLeads')}</p>`;
    return rowOf([rv('leads',mon)??0, rv('leads',ytd)??0], [mon.apLeads, ytd.apLeads, full.apLeads],
                 t('rp.leadsMonth'), t('rp.leadsFY'), t('rp.apLeadsFY'));
  }
  return rowOf([mon.teams, ytd.teams], [mon.apTeams, ytd.apTeams, full.apTeams],
               t('rp.apMonth'), t('rp.gjCum'), t('rp.apFY'));
}

/* ======================================================================
   2) Team Status Report
   ====================================================================== */
function reportTSR(M, team){
  const p={team};
  const ids=['leads','props','teams','book','vk','db','ros','quote2','uteam','dbteam','anights','apax','mpn',
             '*webq','*quote3','*quote1','*fte','*dbfte','*bookfte'];
  const k=kpiBlock(M,p,ids);
  const sheets = [
    `<div class="rgrid g2">
       <div class="rcard span2"><h4>${t('rp.kpis')}</h4><div class="tablewrap rtw">${k.html}</div></div>
       <div class="rcard"><h4>${t('rp.apSection')} · ${MBY.teams.n} <span class="st">★</span></h4>${apTiles(M,team,'teams')}</div>
       <div class="rcard"><h4>${t('rp.trendSection')} · ${MBY.teams.n} <span class="st">★</span></h4>${miniChart(M,p,'teams',true)}</div>
     </div>`,
    `<div class="rgrid g2">
       <div class="rcard"><h4>${t('rp.destSection')} · ${t('rp.last12')}</h4>${splitTable(M,p,'dest',10,t('ctl.dest'))}</div>
       <div class="rcard"><h4>${t('rp.hotelSection')} · ${t('rp.last12')} <span class="st">★</span></h4>${splitTable(M,p,'hotel',10,t('ho.hotel'))}</div>
       <div class="rcard"><h4>${t('rp.apSection')} · ${MBY.leads.n} <span class="st">★</span></h4>${apTiles(M,team,'leads')}</div>
       <div class="rcard"><h4>${t('rp.trendSection')} · ${MBY.leads.n} <span class="st">★</span></h4>${miniChart(M,p,'leads',true)}</div>
     </div>`];
  return page({
    kind: t('rp.tsr'), title: team,
    meta: monLabel(M,true),
    sheets, notes:[t('rp.sglNote')]
  });
}

/* ======================================================================
   3) Country Status Report
   ====================================================================== */
function reportCSR(M, dest){
  const p={dest};
  const ids=['leads','props','teams','book','vk','db','ros','quote2','uteam','dbteam','anights','apax','mpn',
             '*webq','*quote3','*quote1'];
  const k=kpiBlock(M,p,ids);
  const sheets = [
    `<div class="rgrid g2">
       <div class="rcard span2"><h4>${t('rp.kpis')}</h4><div class="tablewrap rtw">${k.html}</div></div>
       <div class="rcard"><h4>${t('rp.trendSection')} · ${MBY.teams.n} <span class="st">★</span></h4>${miniChart(M,p,'teams',false)}</div>
       <div class="rcard"><h4>${t('rp.sportSection')} · ${t('rp.last12')} <span class="st">★</span></h4>${splitTable(M,p,'sport',6,t('rp.sport'))}</div>
     </div>`,
    `<div class="rgrid g2">
       <div class="rcard"><h4>${t('rp.teamSection')} · ${t('rp.last12')}</h4>${splitTable(M,p,'team',10,t('ctl.team'))}</div>
       <div class="rcard"><h4>${t('rp.herkSection')} · ${t('rp.last12')}</h4>${splitTable(M,p,'herk',10,t('ctl.herk'))}</div>
       <div class="rcard span2"><h4>${t('rp.hotelSection')} · ${t('rp.last12')} <span class="st">★</span></h4>${splitTable(M,p,'hotel',10,t('ho.hotel'))}</div>
     </div>`];
  return page({
    kind: t('rp.csr'), title: cname(dest).replace(/\s*\([^)]*\)$/,''),
    meta: monLabel(M,true),
    sheets, notes:[t('rp.csrNote')]
  });
}

/* --- Seitenrahmen ------------------------------------------------------ */
function page({kind,title,meta,sheets,notes}){
  // Datenstand = letzter Buchungstag in der Mappe, nicht der Zeitpunkt des Builds
  const stand = LAST.toLocaleDateString(LOC,{day:'2-digit',month:'2-digit',year:'numeric',timeZone:'UTC'});
  return `<article class="rp-page">
    <div class="rp-head">
      <div><div class="eyebrow">SOCCA GROUP · ${esc(kind)}</div><h2>${esc(title)}</h2></div>
      <div class="rp-meta"><b>${esc(meta)}</b><span>${esc(t('rp.dataAsOf',{d:stand}))}</span></div>
    </div>
    ${sheets.map((sh,i)=> i===0 ? `<div class="rp-sheet">${sh}</div>`
      : `<div class="rp-sheet"><div class="rp-mini"><b>${esc(title)}</b><span>${esc(kind)} · ${esc(meta)}</span></div>${sh}</div>`).join('')}
    <div class="rp-foot">
      <span><span class="st">★</span> ${esc(t('rp.addedLegend'))}</span>
      ${(notes||[]).filter(Boolean).map(n=>`<span>${esc(n)}</span>`).join('')}
    </div>
  </article>`;
}

/* ======================================================================
   Bedienung
   ====================================================================== */
const RS = { kind:'cmp', month:LAST_M, team:'FUSU', dest:'HR', present:false };

function reportList(){
  if(RS.kind==='tsr') return TEAM_ORDER.filter(x=>D.teams.includes(x));
  if(RS.kind==='csr') return CSR_MAIN.filter(x=>D.dests.includes(x));
  return null;
}
function renderOne(kind, M, key){
  if(kind==='tsr') return reportTSR(M, key);
  if(kind==='csr') return reportCSR(M, key);
  return reportCompare(M);
}

function initReports(){
  const ms=document.getElementById('rpMonth');
  const fillMonths=()=>{
    const v=RS.month; let h='';
    for(let m=LAST_M;m>=Math.max(FIRST_M,CUTM-12);m--) h+=`<option value="${m}">${monLabel(m,true)}</option>`;
    ms.innerHTML=h; ms.value=v;
  };
  const fillKeys=()=>{
    const el=document.getElementById('rpKey'), lab=document.getElementById('rpKeyLab');
    if(RS.kind==='cmp'){ el.parentElement.hidden=true; return; }
    el.parentElement.hidden=false;
    if(RS.kind==='tsr'){
      lab.textContent=t('ctl.team');
      const main=TEAM_ORDER.filter(x=>D.teams.includes(x)), rest=D.teams.filter(x=>!TEAM_ORDER.includes(x));
      el.innerHTML=main.map(x=>`<option>${x}</option>`).join('')+
        (rest.length?`<optgroup label="${t('rp.more')}">`+rest.map(x=>`<option>${x}</option>`).join('')+`</optgroup>`:'');
      el.value=RS.team;
    } else {
      lab.textContent=t('ctl.dest');
      const main=CSR_MAIN.filter(x=>D.dests.includes(x)), rest=D.dests.filter(x=>!CSR_MAIN.includes(x));
      el.innerHTML=`<optgroup label="${t('rp.mainCountries')}">`+main.map(x=>`<option value="${x}">${cname(x)}</option>`).join('')+`</optgroup>`+
        `<optgroup label="${t('rp.more')}">`+rest.map(x=>`<option value="${x}">${cname(x)}</option>`).join('')+`</optgroup>`;
      el.value=RS.dest;
    }
  };
  RS.refreshSelects=()=>{ fillMonths(); fillKeys(); };
  document.querySelectorAll('#rpKind [data-k]').forEach(b=>b.onclick=()=>{ RS.kind=b.dataset.k; fillKeys(); drawReport(); });
  ms.onchange=()=>{ RS.month=+ms.value; drawReport(); };
  document.getElementById('rpKey').onchange=e=>{ if(RS.kind==='tsr') RS.team=e.target.value; else RS.dest=e.target.value; drawReport(); };
  document.getElementById('rpPrint').onclick=()=>printReports(false);
  document.getElementById('rpPrintAll').onclick=()=>printReports(true);
  document.getElementById('rpPresent').onclick=()=>togglePresent(true);
  document.getElementById('rpExit').onclick=()=>togglePresent(false);
  document.getElementById('rpPrev').onclick=()=>step(-1);
  document.getElementById('rpNext').onclick=()=>step(1);
  document.addEventListener('keydown',e=>{
    if(!RS.present) return;
    if(e.key==='ArrowRight'||e.key==='PageDown'||e.key===' '){ e.preventDefault(); step(1); }
    else if(e.key==='ArrowLeft'||e.key==='PageUp'){ e.preventDefault(); step(-1); }
    else if(e.key==='Escape'){ togglePresent(false); }
  });
  document.addEventListener('fullscreenchange',()=>{ if(!document.fullscreenElement && RS.present) togglePresent(false); });
  fillMonths(); fillKeys();
}

/* Im Präsentationsmodus: bei TSR/CSR durch Teams bzw. Länder blättern,
   beim Monatsvergleich durch die Monate. */
function step(dir){
  const list=reportList();
  if(!list){
    RS.month=Math.max(FIRST_M,Math.min(LAST_M,RS.month+dir));
    document.getElementById('rpMonth').value=RS.month;
  } else {
    const cur = RS.kind==='tsr'?RS.team:RS.dest;
    let i=list.indexOf(cur); i = i<0 ? 0 : (i+dir+list.length)%list.length;
    if(RS.kind==='tsr') RS.team=list[i]; else RS.dest=list[i];
    document.getElementById('rpKey').value=list[i];
  }
  drawReport();
}

function togglePresent(on){
  RS.present=on;
  const box=document.getElementById('rpStage');
  document.body.classList.toggle('presenting',on);
  if(on){ try{ box.requestFullscreen && box.requestFullscreen().catch(()=>{}); }catch(e){} }
  else if(document.fullscreenElement){ try{ document.exitFullscreen(); }catch(e){} }
  drawReport();
}

function drawReport(){
  if(!document.getElementById('rpCanvas')) return;
  document.querySelectorAll('#rpKind [data-k]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.k===RS.kind)));
  const key = RS.kind==='tsr'?RS.team:RS.dest;
  document.getElementById('rpCanvas').innerHTML = renderOne(RS.kind, RS.month, key);
  const list=reportList();
  const pos=document.getElementById('rpPos');
  if(list){ const i=list.indexOf(key); pos.textContent = i>=0 ? t('rp.page',{i:i+1,n:list.length}) : ''; }
  else pos.textContent = monLabel(RS.month,true);
  document.getElementById('rpPrintAll').hidden = !list;
  bindTips('#rpCanvas');
}

/* Drucken / PDF.
   Normalfall: Browser-Druckdialog über window.print(). In abgeschotteten
   Vorschauen (Artefakt, Dateivorschau) ignoriert der Browser print()
   stillschweigend — erkennbar daran, dass kein beforeprint kommt. Dann wird
   der Bericht als eigenständige, druckfertige HTML-Datei ausgegeben, die sich
   beim Öffnen selbst druckt. */
const DL_CAP = (window.claude && typeof window.claude.use === 'function')
  ? window.claude.use('downloads').catch(() => null) : Promise.resolve(null);

function printCleanup(){
  document.body.classList.remove('printing');
  document.getElementById('printArea').innerHTML = '';
}

function printFileName(all){
  const kind = RS.kind==='tsr' ? 'TSR' : RS.kind==='csr' ? 'CSR' : 'Monatsvergleich';
  const key = RS.kind==='cmp' ? '' : (all ? 'alle' : (RS.kind==='tsr' ? RS.team : RS.dest));
  return [kind, key, monLabel(RS.month,true)].filter(Boolean).join('_')
    .replace(/\s+/g,'_').replace(/[^\p{L}\p{N}_-]/gu,'') + '.html';
}

function printDocument(html, title){
  const css = [...document.querySelectorAll('style')].map(x=>x.textContent).join('\n');
  const fonts = [...document.querySelectorAll('link[rel="stylesheet"],link[rel="preconnect"]')]
    .map(l=>l.outerHTML).join('\n');
  const esc = v => String(v).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  return '<!doctype html>\n<html lang="'+esc(document.documentElement.lang||'de')+'" data-theme="light">\n<head>\n'
    + '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
    + '<title>'+esc(title)+'</title>\n' + fonts + '\n<style>\n' + css + '\n'
    + '#printArea{display:block !important;max-width:1180px;margin:0 auto;padding:16px}\n'
    + '#printArea .rp-page{margin-bottom:24px}\n'
    + '.pf-bar{position:sticky;top:0;z-index:5;display:flex;gap:16px;align-items:center;justify-content:space-between;'
    + 'padding:10px 16px;background:var(--surface);border-bottom:1px solid var(--border);font-size:13px;color:var(--fg-muted)}\n'
    + '@media print{.pf-bar{display:none !important}#printArea{padding:0;max-width:none}}\n'
    + '</style>\n</head>\n<body class="printing">\n'
    + '<div class="pf-bar"><span>'+esc(t('rp.pfBar'))+'</span>'
    + '<button class="chip" onclick="window.print()">'+esc(t('rp.print'))+'</button></div>\n'
    + '<div id="printArea">'+html+'</div>\n'
    + '<script>addEventListener("load",function(){setTimeout(function(){window.print()},500)});<\/script>\n'
    + '</body>\n</html>\n';
}

function rpToast(msg, ms){
  let el = document.getElementById('rpToast');
  if(!el){ el=document.createElement('div'); el.id='rpToast'; el.setAttribute('role','status'); document.body.appendChild(el); }
  el.textContent = msg; el.hidden = false;
  clearTimeout(rpToast.tm); rpToast.tm = setTimeout(()=>{ el.hidden = true; }, ms||9000);
}

async function printFallback(html, all){
  const name = printFileName(all);
  const doc = printDocument(html, name.replace(/\.html$/,'').replace(/_/g,' '));
  // 1. Im claude.ai-Artefakt: Datei über die Download-Freigabe anbieten
  const dl = await DL_CAP;
  if(dl){
    try{ await dl.save({filename:name, data:doc}); rpToast(t('rp.pfReady')); return; }
    catch(e){ if(e && e.code==='declined') return; }
  }
  const url = URL.createObjectURL(new Blob([doc], {type:'text/html'}));
  setTimeout(()=>URL.revokeObjectURL(url), 120000);
  // 2. Neuer Tab
  try{ const w = window.open(url, '_blank'); if(w){ rpToast(t('rp.pfReady')); return; } }catch(e){}
  // 3. Klassischer Download
  try{
    const a=document.createElement('a'); a.href=url; a.download=name; document.body.appendChild(a); a.click(); a.remove();
    rpToast(t('rp.pfReady')); return;
  }catch(e){}
  rpToast(t('rp.printFail'), 12000);
}

function printReports(all){
  const area=document.getElementById('printArea');
  const list=reportList();
  const html = (all && list) ? list.map(k=>renderOne(RS.kind,RS.month,k)).join('')
                             : renderOne(RS.kind,RS.month, RS.kind==='tsr'?RS.team:RS.dest);
  area.innerHTML = html;
  document.body.classList.add('printing');
  let opened = false;
  const onBefore = () => { opened = true; };
  window.addEventListener('beforeprint', onBefore, {once:true});
  window.addEventListener('afterprint', printCleanup, {once:true});
  try{ window.print(); }catch(e){}
  // print() blockiert in den meisten Browsern, bis der Dialog zu ist; der
  // kurze Aufschub fängt Browser ab, die beforeprint verzögert melden.
  setTimeout(()=>{
    window.removeEventListener('beforeprint', onBefore);
    if(opened) return;
    window.removeEventListener('afterprint', printCleanup);
    printCleanup();
    printFallback(html, all && !!list);
  }, 400);
}

/* Ansicht wechseln: Cockpit oder Reports */
function setView(v){
  STATE_VIEW = v;
  document.body.dataset.view = v;
  document.querySelectorAll('#viewSw [data-v]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.v===v)));
  try{ localStorage.setItem('socca.view', v); }catch(e){}
  if(v==='reports') drawReport(); else { syncCtrlHeight(); render(); }
}
let STATE_VIEW = 'cockpit';
