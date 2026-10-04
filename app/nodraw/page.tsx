'use client';
import {useState} from 'react';
import Link from 'next/link';
import {Loader} from '@/components/Ball';
import {NDRow,NDSlip,ND_OPTS} from '@/components/NoDraw';
import {useData,niceDate,ndOf,type NDOpt} from '@/lib/qs';

export default function NoDrawPage(){
 const {data,err}=useData();const [tier,setTier]=useState('All'),[day,setDay]=useState(''),[opt,setOpt]=useState<NDOpt>('nd');
 if(err)return <main className="wrap"><div className="page-title"><h1>No Draw Sweet</h1><p>Today’s matches are not published yet. They appear after the morning update.</p></div></main>;
 if(!data)return <main className="wrap"><Loader label="Loading No Draw"/></main>;
 const N=data.nodraw;
 if(!N||!N.tiers?.length)return <main className="wrap"><div className="page-title"><span className="nd-kicker">Special pick</span><h1>No Draw Sweet</h1><p>This section fills in after the next morning update.</p></div></main>;
 const D=N.history.find(d=>d.date===day)||N.today||N.history[0]||null;
 const items=D?D.items.filter(i=>tier==='All'||i.tier===tier).sort((a,b)=>(a.tier===b.tier?0:a.tier==='Sweet'?-1:1)||(a.kickoff||'').localeCompare(b.kickoff||'')):[];
 const n=(t:string)=>D?D.items.filter(i=>t==='All'||i.tier===t).length:0;
 const st=items.map(i=>ndOf(i,opt).status),settled=st.filter(s=>s==='WON'||s==='LOST'),won=settled.filter(s=>s==='WON').length;
 const late=!!(D?.companions_added&&opt!=='nd'&&D.companions_added.slice(0,10)>D.date);
 const ex=N.extras;
 return <main className="wrap">
  <div className="page-title"><span className="nd-kicker">Special pick</span><h1>No Draw Sweet</h1>
   <p>Some matches almost never end level. For those, we pick <b style={{color:'var(--chalk)'}}>Home or Away</b>: you win if either team wins and lose only on a draw. On SportyBet choose Double Chance, then 12. The same matches also carry two companion picks: Over 1.5 goals and Favourite to win.</p></div>

  <div className="nd-tiers">{N.tiers.map(t=><div className={`nd-tier${t.tier==='Sweet'?' sweet':''}`} key={t.tier}>
   <span>{t.tier==='Sweet'?'Sweet · strict rule':'Wide · looser rule'}</span><b>{t.hit}%</b>
   <p>No Draw won {t.won} of {t.picks} past matches. Average odds {t.avg_odds.toFixed(2)}.</p>
   {ex?.[t.tier]?<p className="nd-comp">Over 1.5: <b>{ex[t.tier].over15.hit}%</b> at {ex[t.tier].over15.avg_odds?.toFixed(2)} · Favourite wins: <b>{ex[t.tier].favwin.hit}%</b> at {ex[t.tier].favwin.avg_odds?.toFixed(2)}</p>:null}
   <small>{t.rule}.{t.found!=null&&t.unseen!=null?` First days ${t.found}%, later unseen days ${t.unseen}%.`:''} Worst day {t.worst_day}%.</small></div>)}</div>

  <div className="chips nd-opts" role="tablist" aria-label="Pick type">{ND_OPTS.map(o=><button key={o.k} role="tab" aria-selected={opt===o.k} className={`chip nd-chip${opt===o.k?' on':''}`} onClick={()=>setOpt(o.k)}>{o.label}</button>)}</div>
  {N.history.length>1?<div className="chips daybar" role="tablist" aria-label="Day">{N.history.slice(0,7).map((d,i)=><button key={d.date} role="tab" aria-selected={D?.date===d.date} className={`chip${D?.date===d.date?' on':''}`} onClick={()=>setDay(d.date)}>{N.today&&d.date===N.today.date?'Today':i===1&&N.today&&N.history[0].date===N.today.date?'Yesterday':niceDate(d.date).split(' ').slice(0,2).join(' ')}</button>)}</div>:null}
  {late?<p className="note"><b>Added afterwards.</b> On {niceDate(D!.date)} only the No Draw pick was published. This companion pick was added to the same matches on {D!.companions_added}, using that morning’s prices, so you can see how it would have done. It was not offered at the time.</p>:null}

  {D?<div className="nd-slipwrap"><NDSlip day={D} opt={opt} tier="Sweet"/></div>:null}

  <div className="history-controls">
   <div className="chips" role="tablist" aria-label="Rule" style={{paddingBottom:0}}>{['All','Sweet','Wide'].map(t=><button key={t} role="tab" aria-selected={tier===t} className={`chip nd-chip${tier===t?' on':''}`} onClick={()=>setTier(t)}>{t}<i>{n(t)}</i></button>)}</div>
  </div>
  <p style={{margin:'10px 0 14px',color:'var(--dim)'}}>{D?`${niceDate(D.date)}. ${items.length} ${items.length===1?'match':'matches'}`:''}{settled.length?`, ${won} of ${settled.length} won so far`:''}.</p>
  <div className="picks">{items.length?items.map(it=><NDRow key={it.fid} it={it} opt={opt}/>):<div className="empty-state"><b>No match passes this rule on this day.</b>We do not force a pick when the conditions are not met.</div>}</div>

  <p className="note"><b>How to use it.</b> These are short-odds picks that win often, so they are steady legs for a ticket. The prices are set close to the win rate: in testing, Sweet No Draw won about 94 in 100 at average odds of 1.05, which roughly breaks even on its own. About 1 in 16 Sweet picks and 1 in 9 Wide picks still lost.</p>
  <p className="note"><b>Why some days have only a few.</b> The Sweet rule needs a favourite priced under 1.25 in a game priced for goals. Wide loosens the rule to give more matches at a lower win rate.</p>
  <p style={{marginTop:22}}><Link href="/tickets" className="btn btn-gold">See today’s VIP tickets</Link></p>
 </main>;
}
