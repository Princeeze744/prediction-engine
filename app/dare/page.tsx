'use client';
import {useState} from 'react';
import Link from 'next/link';
import {Loader} from '@/components/Ball';
import {useData,niceDate,kick} from '@/lib/qs';
/* Dare: high-odds singles on a paper trial. Saved before kick-off every day, settled every night, shown win or lose. */
export default function Dare(){
 const {data,err}=useData();const [day,setDay]=useState(''),[mod,setMod]=useState('');
 if(err)return <main className="wrap"><div className="page-title"><h1>Dare</h1><p>Nothing published yet.</p></div></main>;
 if(!data)return <main className="wrap"><Loader label="Loading Dare"/></main>;
 const R=data.dare;
 if(!R||!R.models?.length)return <main className="wrap"><div className="page-title"><span>On trial</span><h1>Dare</h1><p>This section fills in after the next morning update.</p></div></main>;
 const D=R.history.find(d=>d.date===day)||R.history[0]||null;
 const M=mod||R.models[0].id,cur=R.models.find(m=>m.id===M)!;
 const picks=D?D.picks.filter(p=>p.model===M).sort((a,b)=>new Date(a.kickoff||'').getTime()-new Date(b.kickoff||'').getTime()):[];
 const st=picks.filter(p=>p.status==='WON'||p.status==='LOST'),w=st.filter(p=>p.status==='WON');
 const profit=st.reduce((a,p)=>a+(p.status==='WON'?p.odds-1:-1),0);
 return <main className="wrap">
  <div className="page-title"><span style={{color:'var(--sky)'}}>On trial, not a recommendation yet</span><h1>Dare</h1>
   <p>High-odds singles, each priced about 3 to 5. They win roughly one time in three or four, so most picks lose and the wins have to pay for them. We save every pick before kick-off and count the result here, so the record is built on days the models have never seen.{R.started?` Trial started ${niceDate(R.started)}.`:''}</p></div>

  <div className="history-table">
   <div className="history-row history-head dr"><span>Option</span><span>Test record</span><span>Live trial</span><span>Live profit</span></div>
   {R.models.map(m=><div key={m.id} className="history-row dr" onClick={()=>setMod(m.id)} style={{cursor:'pointer',outline:m.id===M?'2px solid var(--sky)':'none',outlineOffset:-2}}>
    <span><b>{m.name}</b><small>{m.sporty}</small></span>
    <span>{m.test.hit}% of {m.test.picks}<small>avg odds {m.test.avg_odds?.toFixed(2)}</small></span>
    <span>{m.live?<>{m.live.won} of {m.live.picks}<small>{m.live.hit}% won</small></>:<small>no results yet</small>}</span>
    <span>{m.live?<b style={{color:m.live.profit>=0?'var(--won)':'var(--lost)'}}>{m.live.profit>=0?'+':''}{m.live.profit.toFixed(1)} units</b>:'–'}{m.live&&m.live.picks<100?<small>too few to judge</small>:null}</span></div>)}
  </div>
  <p className="note"><b>How to read this.</b> “Units” assumes 1 unit staked on every pick. The test record comes from 25 to 30 September and these five were the best of thousands of patterns tried, so part of it is luck. Only the live trial counts as proof, and it needs at least 100 picks per option before it means anything.</p>

  {R.history.length>1?<div className="chips daybar" role="tablist" aria-label="Day" style={{marginTop:22}}>{R.history.slice(0,8).map(d=><button key={d.date} role="tab" aria-selected={D?.date===d.date} className={`chip${D?.date===d.date?' on':''}`} onClick={()=>setDay(d.date)}>{niceDate(d.date).split(' ').slice(0,2).join(' ')}</button>)}</div>:null}
  <div className="section-head" style={{marginTop:22}}><div><h2 className="h2" style={{fontSize:'clamp(24px,3.4vw,38px)'}}>{cur.name}</h2><p>{cur.why}</p></div></div>
  <p style={{margin:'0 0 12px',color:'var(--dim)'}}>{D?niceDate(D.date):''}. {picks.length} {picks.length===1?'pick':'picks'}{st.length?`, ${w.length} of ${st.length} won, ${profit>=0?'+':''}${profit.toFixed(1)} units`:''}.</p>
  <div className="picks">{picks.length?picks.map((p,i)=><div className="pick nd-row" key={p.fid+'-'+i}>
    <span className="pick-time">{kick(p.kickoff)}</span>
    <span className="pick-teams"><b>{p.match}</b><small>{p.league}{p.score?`. HT ${p.ht||'?'}, FT ${p.score}`:''}</small></span>
    <span className="pick-market" style={{color:'var(--sky)'}}>{p.pick}</span>
    <span/>
    <span className="pick-odds">{p.odds.toFixed(2)}</span>
    <span className="pick-status">{p.status?<span className={`status ${p.status.toLowerCase()}`}>{p.status==='WON'?'Won':p.status==='VOID'?'Postponed':'Lost'}{p.score?' '+p.score:''}</span>:<span className="status pending">Pending</span>}</span></div>)
   :<div className="empty-state"><b>No match fits this rule on this day.</b></div>}</div>
  <p style={{marginTop:22}}><Link href="/results" className="ghost-link">Back to Results</Link></p>
 </main>;
}
