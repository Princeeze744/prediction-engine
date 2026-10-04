'use client';
import {useState} from 'react';
import Link from 'next/link';
import {Loader} from '@/components/Ball';
import {NDRow} from '@/components/NoDraw';
import {useData,niceDate} from '@/lib/qs';

export default function NoDrawPage(){
 const {data,err}=useData();const [tier,setTier]=useState('All'),[day,setDay]=useState('');
 if(err)return <main className="wrap"><div className="page-title"><h1>No Draw Sweet</h1><p>Today’s matches are not published yet. They appear after the morning update.</p></div></main>;
 if(!data)return <main className="wrap"><Loader label="Loading No Draw"/></main>;
 const N=data.nodraw;
 if(!N||!N.tiers?.length)return <main className="wrap"><div className="page-title"><span className="nd-kicker">Special pick</span><h1>No Draw Sweet</h1><p>This section fills in after the next morning update.</p></div></main>;
 const D=N.history.find(d=>d.date===day)||N.today||N.history[0]||null;
 const items=D?D.items.filter(i=>tier==='All'||i.tier===tier).sort((a,b)=>(a.tier===b.tier?0:a.tier==='Sweet'?-1:1)||(a.kickoff||'').localeCompare(b.kickoff||'')):[];
 const n=(t:string)=>D?D.items.filter(i=>t==='All'||i.tier===t).length:0;
 const settled=items.filter(i=>i.status==='WON'||i.status==='LOST'),won=settled.filter(i=>i.status==='WON').length;
 return <main className="wrap">
  <div className="page-title"><span className="nd-kicker">Special pick</span><h1>No Draw Sweet</h1>
   <p>Some matches almost never end level. For those, we pick <b style={{color:'var(--chalk)'}}>Home or Away</b>: you win if either team wins and lose only on a draw. On SportyBet choose Double Chance, then 12.</p></div>

  <div className="nd-tiers">{N.tiers.map(t=><div className={`nd-tier${t.tier==='Sweet'?' sweet':''}`} key={t.tier}>
   <span>{t.tier==='Sweet'?'Sweet · strict rule':'Wide · looser rule'}</span><b>{t.hit}%</b>
   <p>Won {t.won} of {t.picks} past matches. Average odds {t.avg_odds.toFixed(2)}. About {Math.round(t.per_day)} matches on a busy day.</p>
   <small>{t.rule}.{t.found!=null&&t.unseen!=null?` First days ${t.found}%, later unseen days ${t.unseen}%.`:''} Worst day {t.worst_day}%.</small></div>)}</div>

  <div className="history-controls">
   <div className="chips" role="tablist" aria-label="Rule" style={{paddingBottom:0}}>{['All','Sweet','Wide'].map(t=><button key={t} role="tab" aria-selected={tier===t} className={`chip nd-chip${tier===t?' on':''}`} onClick={()=>setTier(t)}>{t}<i>{n(t)}</i></button>)}</div>
   {N.history.length>1?<div className="history-selects"><select aria-label="Day" value={D?.date||''} onChange={e=>setDay(e.target.value)}>{N.history.map(d=><option key={d.date} value={d.date}>{niceDate(d.date)}</option>)}</select></div>:null}
  </div>
  <p style={{margin:'10px 0 14px',color:'var(--dim)'}}>{D?`${niceDate(D.date)}. ${items.length} ${items.length===1?'match':'matches'}`:''}{settled.length?`, ${won} of ${settled.length} won so far`:''}.</p>
  <div className="picks">{items.length?items.map(it=><NDRow key={it.fid} it={it}/>):<div className="empty-state"><b>No match passes this rule on this day.</b>We do not force a pick when the conditions are not met.</div>}</div>

  <p className="note"><b>Why some days have only one or two.</b> The Sweet rule needs a favourite priced under 1.25 in a game priced for goals. Midweek cup and international days have many such games; a quiet Friday may have one. Wide loosens the rule to give more matches at a slightly lower win rate.</p>
  <p className="note"><b>How to use it.</b> The odds are small (around 1.05 to 1.10), so a No Draw pick is a steady leg to add to a ticket, not a profit on its own. About 1 in 16 Sweet picks and 1 in 9 Wide picks still lost in testing.</p>
  <p style={{marginTop:22}}><Link href="/tickets" className="btn btn-gold">See today’s 10 VIP tickets</Link></p>
 </main>;
}
