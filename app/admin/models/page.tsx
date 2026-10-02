'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';

type Sum={picks:number;won?:number;lost?:number;void?:number;hit?:number|null;avg_odds?:number;profit?:number;roi?:number;roi_best?:number};
type Day=Sum&{date:string};
type Rec={date:string;match:string;league:string;score:string;ht:string;odds:number;best:number;status:'WON'|'LOST'|'VOID';profit:number};
type Today={kickoff:string;match:string;league:string;odds:number;best:number};
type Model={id:string;group:string;worst_day_hit:number|null;name:string;sporty:string;why:string;rule:string;record:Sum;found:Sum;unseen:Sum;days_positive:number;days:number;daily:Day[];today_date:string|null;today:Today[];picks:Rec[]};
type TSum={tickets:number;won?:number;hit?:number;avg_odds?:number;profit?:number;roi?:number;one_leg_short?:number};
type Leg={kickoff?:string;match:string;league?:string;pick:string;model:string;odds:number;status?:string;score?:string};
type Ticket={date?:string;odds:number;status?:string;profit?:number;lost_legs?:number;legs:Leg[]};
type Plan={size:number;group:string;about:string;record:TSum;found:TSum;unseen:TSum;daily:(TSum&{date:string})[];today:Ticket[];recent:Ticket[]};
type Data={tickets:Record<string,Plan>;generated:string;split:string;note:string;models:Model[]};
const pct=(v?:number|null)=>v===null||v===undefined?'—':`${v>0?'+':''}${v}%`;
const time=(k:string)=>{const d=new Date(k);return isNaN(d.getTime())?k:d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})};

export default function Models(){
 const [grp,setGrp]=useState<string>('HIGH HIT');
 const [plan,setPlan]=useState<string>('Power 5'),[tview,setTview]=useState<'today'|'record'>('record');
 const [data,setData]=useState<Data|null>(null),[err,setErr]=useState(''),[open,setOpen]=useState<string>(''),[tab,setTab]=useState<'today'|'record'>('today');
 useEffect(()=>{fetch('/research/models.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('models.json not found');return r.json()}).then((d:Data)=>{setData(d);setOpen(d.models[0]?.id||'')}).catch(e=>setErr(String(e.message||e)))},[]);
 if(err)return <main className="inside history-page"><div className="page-title"><span>PRIVATE • MODEL LAB</span><h1>10 Market Models</h1><p>Could not load data: {err}. Run <code>python tools\build_models.py</code> in the v22 folder, then refresh.</p></div></main>;
 if(!data)return <main className="inside history-page"><div className="page-title"><span>PRIVATE • MODEL LAB</span><h1>Loading…</h1></div></main>;
 const list=data.models.filter(x=>x.group===grp);
 const m=list.find(x=>x.id===open)||list[0]||data.models[0];
 const tot=list.reduce((a,x)=>({picks:a.picks+(x.record.picks||0),profit:a.profit+(x.record.profit||0),today:a.today+x.today.length}),{picks:0,profit:0,today:0});
 return <main className="inside history-page">
  <div className="page-title"><span>MODEL LAB • TESTED ON UNSEEN DAYS • EVERY LOSS SHOWN</span><h1>Models & Tickets</h1>
   <p>Thirty fixed rules across different SportyBet-style markets, plus ready-made accumulator tickets built from them. Each was found on the first days and re-tested on days it had not seen.</p></div>
  <div className="history-note" style={{borderLeft:'3px solid #e0a100',paddingLeft:12}}><b>Read this first.</b> {data.note}</div>


  {(()=>{const P=data.tickets?.[plan];if(!P)return null;const names=Object.keys(data.tickets);return <>
   <div className="page-title" style={{marginTop:8}}><span>ACCUMULATOR TICKETS • ONE PICK PER MATCH</span><h1 style={{fontSize:'clamp(26px,4vw,40px)'}}>{plan}: {P.record.hit}% of tickets won at average odds {P.record.avg_odds}</h1><p>{P.about} First days {P.found.hit}% / unseen days {P.unseen.hit}%. {P.record.one_leg_short} of the losing tickets missed by a single pick.</p></div>
   <div className="history-controls"><div className="feed-tabs">{names.map(n=><button key={n} className={plan===n?'active':''} onClick={()=>setPlan(n)}>{n} · {data.tickets[n].record.hit}% @ {data.tickets[n].record.avg_odds}</button>)}</div>
    <div className="feed-tabs"><button className={tview==='today'?'active':''} onClick={()=>setTview('today')}>📅 Today’s tickets ({P.today.length})</button><button className={tview==='record'?'active':''} onClick={()=>setTview('record')}>📊 Ticket record ({P.record.tickets})</button></div></div>
   <section className="track history-kpis"><div><b>{P.record.tickets}</b><span>TICKETS</span></div><div><b>{P.record.hit}%</b><span>TICKETS WON</span></div><div><b>{P.record.avg_odds}</b><span>AVG TICKET ODDS</span></div><div><b>{pct(P.record.roi)}</b><span>ROI (1 UNIT PER TICKET)</span></div></section>
   {tview==='today'&&<section className="history-table">{P.today.length?P.today.map((tk,i)=><div key={i} style={{borderBottom:'1px solid rgba(0,0,0,.08)',padding:'6px 0'}}>
     <div className="history-row history-head"><span>TICKET {i+1} · {tk.legs.length} PICKS · MIXED MARKETS</span><span>KICK-OFF</span><span>PICK</span><span>ODDS</span><span>TICKET ODDS {tk.odds.toFixed(2)}</span></div>
     {tk.legs.map((l,j)=><div className="history-row" key={j}><span><b>{l.match}</b><small>{l.league}</small></span><span>{time(l.kickoff||'')}</span><span>{l.pick}<small>{l.model}</small></span><span className="final-score">{l.odds.toFixed(2)}</span><span></span></div>)}</div>)
     :<div className="empty-state"><b>No tickets loaded for today.</b><span>Run QS_Today_AllMarkets.ps1, then python tools\build_models.py, and refresh.</span></div>}</section>}
   {tview==='record'&&<><section className="history-table"><div className="history-row history-head"><span>DAY</span><span>TICKETS</span><span>WON</span><span>AVG ODDS</span><span>PROFIT · ROI</span></div>
     {P.daily.map(d=><div className="history-row" key={d.date}><span><b>{d.date}</b><small>{d.date<=data.split?'found on this day':'unseen test day'}</small></span><span>{d.tickets}</span><span>{d.won} · {d.hit}%</span><span>{d.avg_odds}</span><span className="final-score">{(d.profit||0)>0?'+':''}{d.profit} u<small>{pct(d.roi)}</small></span></div>)}</section>
    <section className="history-table" style={{marginTop:20}}><div className="history-row history-head"><span>RECENT TICKETS · PICKS</span><span>DATE</span><span>LEGS LOST</span><span>TICKET ODDS</span><span>RESULT</span></div>
     {P.recent.slice(0,25).map((tk,i)=><div className="history-row" key={i}><span>{tk.legs.map((l,j)=><small key={j} style={{display:'block',opacity:l.status==='LOST'?1:.75,fontWeight:l.status==='LOST'?700:400}}>{l.status==='LOST'?'✗':'✓'} {l.match} {l.score} · {l.pick} @ {l.odds.toFixed(2)}</small>)}</span><span>{tk.date}</span><span>{tk.lost_legs}</span><span className="final-score">{tk.odds.toFixed(2)}</span><span><i className={`status ${(tk.status||'').toLowerCase()}`}>{tk.status}</i></span></div>)}</section></>}
  </>})()}

  <div className="page-title" style={{marginTop:40}}><span>THE MODELS BEHIND THE TICKETS</span><h1 style={{fontSize:'clamp(26px,4vw,40px)'}}>Single-pick models</h1></div>
  <section className="track history-kpis">
   <div><b>{list.length}</b><span>MODELS</span></div>
   <div><b>{tot.picks}</b><span>SETTLED PICKS</span></div>
   <div><b>{tot.profit>0?'+':''}{tot.profit.toFixed(1)} u</b><span>COMBINED PROFIT (1 UNIT EACH)</span></div>
   <div><b>{tot.today}</b><span>PICKS TODAY</span></div>
  </section>

  <div className="history-controls"><div className="feed-tabs">
   <button className={grp==='HIGH HIT'?'active':''} onClick={()=>setGrp('HIGH HIT')}>🎯 High hit-rate models (90%+)</button>
   <button className={grp==='ACCA 1.20-1.50'?'active':''} onClick={()=>setGrp('ACCA 1.20-1.50')}>🎟️ Accumulator models (odds 1.20–1.50)</button>
   <button className={grp==='VALUE'?'active':''} onClick={()=>setGrp('VALUE')}>💰 Value models (higher odds)</button>
  </div></div>
  <section className="history-table">
   <div className="history-row history-head"><span>MODEL · SPORTYBET MARKET</span><span>PICKS · HIT RATE</span><span>AVG ODDS</span><span>ROI · FIRST / UNSEEN DAYS</span><span>DAYS IN PROFIT</span></div>
   {list.map(x=><div className="history-row" key={x.id} onClick={()=>setOpen(x.id)} style={{cursor:'pointer',outline:x.id===m.id?'2px solid #b8ff2c':'none',outlineOffset:-2}}>
    <span><b>{x.id} · {x.name}</b><small>{x.sporty}</small></span>
    <span>{x.record.picks} · <b>{x.record.hit}%</b><small>first {x.found.hit}% / unseen {x.unseen.hit}% · worst day {x.worst_day_hit}%</small></span>
    <span>{x.record.avg_odds?.toFixed(2)}</span>
    <span className="final-score">{pct(x.record.roi)}<small>{pct(x.found.roi)} / {pct(x.unseen.roi)}</small></span>
    <span>{x.days_positive} of {x.days}<small>{x.today.length} today</small></span>
   </div>)}
  </section>

  <div className="page-title" style={{marginTop:36}}><span>{m.id} • {m.sporty}</span><h1 style={{fontSize:'clamp(26px,4vw,40px)'}}>{m.name}</h1><p>{m.why}</p>
   <p style={{fontSize:13,opacity:.75}}>Rule: {m.rule}. Best-price ROI: {pct(m.record.roi_best)}.</p></div>
  <div className="history-controls"><div className="feed-tabs">
   <button className={tab==='today'?'active':''} onClick={()=>setTab('today')}>📅 Today’s picks ({m.today.length})</button>
   <button className={tab==='record'?'active':''} onClick={()=>setTab('record')}>📊 Record ({m.record.picks})</button>
  </div></div>

  {tab==='today'&&<section className="history-table">
   <div className="history-row history-head"><span>FIXTURE</span><span>KICK-OFF</span><span>PICK</span><span>TYPICAL ODDS</span><span>BEST ODDS</span></div>
   {m.today.length?m.today.map((t,i)=><div className="history-row" key={i}>
    <span><b>{t.match}</b><small>{t.league}</small></span><span>{time(t.kickoff)}<small>{m.today_date}</small></span>
    <span>{m.sporty}</span><span className="final-score">{t.odds.toFixed(2)}</span><span>{t.best.toFixed(2)}</span>
   </div>):<div className="empty-state"><b>No picks loaded for today.</b><span>Run QS_Today_AllMarkets.ps1, then python tools\build_models.py, and refresh.</span></div>}
  </section>}

  {tab==='record'&&<>
   <section className="history-table">
    <div className="history-row history-head"><span>DAY</span><span>PICKS</span><span>WON / LOST</span><span>HIT RATE</span><span>PROFIT · ROI</span></div>
    {m.daily.map(d=><div className="history-row" key={d.date}><span><b>{d.date}</b><small>{d.date<=data.split?'found on this day':'unseen test day'}</small></span>
     <span>{d.picks}<small>avg odds {d.avg_odds}</small></span><span>{d.won} / {d.lost}{d.void?<small>{d.void} void</small>:null}</span><span>{d.hit}%</span>
     <span className="final-score">{(d.profit||0)>0?'+':''}{d.profit} u<small>{pct(d.roi)}</small></span></div>)}
   </section>
   <section className="history-table" style={{marginTop:28}}>
    <div className="history-row history-head"><span>FIXTURE</span><span>HALF-TIME</span><span>FULL-TIME</span><span>ODDS</span><span>RESULT</span></div>
    {m.picks.slice(0,150).map((p,i)=><div className="history-row" key={i}><span><b>{p.match}</b><small>{p.date} · {p.league}</small></span>
     <span>{p.ht}</span><span className="final-score">{p.score}</span><span>{p.odds.toFixed(2)}<small>{p.profit>0?'+':''}{p.profit} u</small></span>
     <span><i className={`status ${p.status.toLowerCase()}`}>{p.status}</i></span></div>)}
   </section></>}
  <p style={{marginTop:24}}><Link href="/admin" className="ghost-link">← Back to Command Center</Link> · <Link href="/admin/research" className="ghost-link">No-Draw research →</Link></p>
  <p style={{fontSize:12,opacity:.6}}>Data generated {data.generated}.</p>
 </main>;
}
