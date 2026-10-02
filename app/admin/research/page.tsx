'use client';
import {useEffect,useMemo,useState} from 'react';
import Link from 'next/link';

type Pick={source:'LIVE'|'BACKTEST';fixture_id:number;date:string;league:string;home:string;away:string;api:string;odds:number;kickoff?:string;snapshot?:string;status:'WON'|'LOST'|'PENDING';score:string|null;profit:number|null};
type Sum={picks:number;settled:number;won:number;lost:number;pending:number;hit:number|null;profit:number;roi:number|null;avg_odds:number|null};
type Day=Sum&{date:string;source:string};
type Data={generated:string;signal:string;rules:string;summary:{LIVE:Sum;BACKTEST:Sum};daily:Day[];picks:Pick[]};

const fmt=(v:number|null|undefined,suf='')=>v===null||v===undefined?'—':`${v>0&&suf==='u'?'+':''}${v}${suf==='u'?' u':suf}`;

export default function Research(){
 const [data,setData]=useState<Data|null>(null),[err,setErr]=useState(''),[source,setSource]=useState<'LIVE'|'BACKTEST'>('BACKTEST'),[days,setDays]=useState(5),[status,setStatus]=useState('ALL');
 useEffect(()=>{fetch('/research/nodraw.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('nodraw.json not found');return r.json()}).then((d:Data)=>{setData(d);if(d.summary.LIVE.picks>0)setSource('LIVE')}).catch(e=>setErr(String(e.message||e)))},[]);
 const dates=useMemo(()=>data?[...new Set(data.picks.filter(p=>p.source===source).map(p=>p.date))].sort().reverse():[],[data,source]);
 const keep=useMemo(()=>new Set(days?dates.slice(0,days):dates),[dates,days]);
 const picks=useMemo(()=>data?data.picks.filter(p=>p.source===source&&keep.has(p.date)&&(status==='ALL'||p.status===status)):[],[data,source,keep,status]);
 const daily=useMemo(()=>data?data.daily.filter(d=>d.source===source&&keep.has(d.date)):[],[data,source,keep]);
 const s=useMemo(()=>{const st=picks.filter(p=>p.status!=='PENDING'),won=st.filter(p=>p.status==='WON').length,profit=Math.round(st.reduce((a,p)=>a+(p.profit||0),0)*100)/100;return{picks:picks.length,won,lost:st.length-won,pending:picks.length-st.length,hit:st.length?Math.round(won/st.length*1000)/10:null,profit,roi:st.length?Math.round(profit/st.length*1000)/10:null}},[picks]);

 if(err)return <main className="inside history-page"><div className="page-title"><span>PRIVATE • RESEARCH LAB</span><h1>No-Draw Signal</h1><p>Could not load research data: {err}. Run <code>python tools\build_research_nodraw.py</code> in the v22 folder, then refresh.</p></div></main>;
 if(!data)return <main className="inside history-page"><div className="page-title"><span>PRIVATE • RESEARCH LAB</span><h1>Loading…</h1></div></main>;

 return <main className="inside history-page">
  <div className="page-title"><span>PRIVATE • RESEARCH LAB • PAPER TEST ONLY</span><h1>No-Draw Signal</h1>
   <p>{data.signal}. {data.rules}</p></div>

  <div className="history-note" style={{borderLeft:'3px solid #e0a100',paddingLeft:12}}>
   <b>Not published intelligence.</b> BACKTEST picks use predictions downloaded after the matches and cannot prove the edge. Only LIVE picks — captured before kick-off — count as evidence. Do not stake real money until LIVE has 300+ settled picks above +5% ROI.
  </div>

  <div className="history-controls">
   <div className="feed-tabs">
    <button className={source==='LIVE'?'active':''} onClick={()=>setSource('LIVE')}>🟢 LIVE pre-match ({data.summary.LIVE.picks})</button>
    <button className={source==='BACKTEST'?'active':''} onClick={()=>setSource('BACKTEST')}>🧪 Backtest ({data.summary.BACKTEST.picks})</button>
   </div>
   <div className="history-selects">
    <select value={days} onChange={e=>setDays(Number(e.target.value))}><option value={1}>Last 1 day</option><option value={5}>Last 5 days</option><option value={7}>Last 7 days</option><option value={30}>Last 30 days</option><option value={0}>All days</option></select>
    <select value={status} onChange={e=>setStatus(e.target.value)}><option>ALL</option><option>WON</option><option>LOST</option><option>PENDING</option></select>
   </div>
  </div>

  <section className="track history-kpis">
   <div><b>{s.picks}</b><span>PICKS</span></div>
   <div><b>{s.won} / {s.lost}</b><span>WON / LOST</span></div>
   <div><b>{fmt(s.hit,'%')}</b><span>NO-DRAW RATE</span></div>
   <div><b>{fmt(s.profit,'u')}</b><span>PROFIT (1 UNIT EACH)</span></div>
   <div><b>{fmt(s.roi,'%')}</b><span>ROI</span></div>
  </section>
  <div className="history-note">Break-even needs about {data.summary[source].avg_odds?Math.round(100/data.summary[source].avg_odds):'—'}% no-draw at average odds of {data.summary[source].avg_odds ?? '—'}. Each loss costs 1 unit; each win pays roughly 0.2–0.3. Data generated {data.generated}.</div>

  <section className="history-table">
   <div className="history-row history-head"><span>DAY</span><span>PICKS</span><span>WON / LOST</span><span>NO-DRAW RATE</span><span>PROFIT · ROI</span></div>
   {daily.length?daily.map(d=><div className="history-row" key={d.date+d.source}>
    <span><b>{d.date}</b><small>{d.pending?`${d.pending} pending`:'all settled'}</small></span>
    <span>{d.picks}<small>avg odds {d.avg_odds}</small></span>
    <span>{d.won} / {d.lost}</span>
    <span>{fmt(d.hit,'%')}</span>
    <span className="final-score">{fmt(d.profit,'u')}<small>{fmt(d.roi,'%')}</small></span>
   </div>):<div className="empty-state"><b>No {source==='LIVE'?'live pre-match':'backtest'} picks yet.</b><span>{source==='LIVE'?'The 9:00 scheduled snapshot adds picks every day; results settle after the 8:00 results run and a rebuild.':'Run the collectors, then rebuild.'}</span></div>}
  </section>

  <section className="history-table" style={{marginTop:28}}>
   <div className="history-row history-head"><span>FIXTURE</span><span>API PLACEHOLDER</span><span>SCORE (90′)</span><span>BEST “12” ODDS</span><span>RESULT</span></div>
   {picks.length?picks.map(p=><div className="history-row" key={p.source+p.fixture_id}>
    <span><b>{p.home}</b> — <b>{p.away}</b><small>{p.date} · {p.league}</small></span>
    <span>{p.api}<small>{p.source==='LIVE'?`captured ${p.snapshot}`:'fetched after match'}</small></span>
    <span className="final-score">{p.score||'—'}</span>
    <span>{p.odds.toFixed(2)}<small>{p.profit===null?'':`${p.profit>0?'+':''}${p.profit} u`}</small></span>
    <span><i className={`status ${p.status.toLowerCase()}`}>{p.status}</i></span>
   </div>):<div className="empty-state"><b>No picks match these filters.</b></div>}
  </section>
  <p style={{marginTop:24}}><Link href="/admin" className="ghost-link">← Back to Command Center</Link></p>
 </main>;
}
