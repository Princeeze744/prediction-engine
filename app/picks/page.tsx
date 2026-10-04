'use client';
import {useEffect,useMemo,useState} from 'react';
import Link from 'next/link';
import {Loader} from '@/components/Ball';
import Slip from '@/components/Slip';
import {useData,kick,niceDate,catLabel,type FreeItem,type FreePick} from '@/lib/qs';
const label=catLabel;

export default function Picks(){
 const {data,err}=useData();const [cat,setCat]=useState('TOP FINGERPRINT'),[day,setDay]=useState('');
 useEffect(()=>{const q=new URLSearchParams(window.location.search),m=q.get('m'),d=q.get('d');if(m)setCat(m);if(d)setDay(d)},[]);
 const F=data?.free;
 const D=F?(F.history.find(d=>d.date===day)||F.today||F.history[0]||null):null;
 const rows=useMemo(()=>{if(!D)return [] as {it:FreeItem;p:FreePick}[];const r:{it:FreeItem;p:FreePick}[]=[];
  for(const it of D.items){it.picks.forEach((p,i)=>{if(cat==='TOP FINGERPRINT'?i===0:p.cat===cat)r.push({it,p})})}
  return r.sort((a,b)=>(a.it.kickoff||'').localeCompare(b.it.kickoff||''))},[D,cat]);
 if(err)return <main className="wrap"><div className="page-title"><h1>Free picks</h1><p>Today’s picks are not published yet. They appear after the morning update.</p></div></main>;
 if(!data||!F)return <main className="wrap"><Loader label="Loading picks"/></main>;
 const count=(c:string)=>D?D.items.reduce((a,it)=>a+it.picks.filter((p,i)=>c==='TOP FINGERPRINT'?i===0:p.cat===c).length,0):0;
 const rec=F.backtest[cat],live=F.live[cat];
 const settled=rows.filter(r=>r.p.status==='WON'||r.p.status==='LOST'),won=settled.filter(r=>r.p.status==='WON').length;
 const priced=rows.filter(r=>r.p.odds&&r.p.odds>1&&r.p.status!=='VOID');
 const acc=(l:typeof priced)=>l.reduce((a,r)=>a*(r.p.odds as number),1);
 const fmt=(x:number)=>x>=1e6?(x/1e6).toFixed(1)+'M':x>=10000?Math.round(x).toLocaleString('en-GB'):x.toFixed(2);
 const solid=priced.filter(r=>(r.p.odds as number)>=1.1);
 const best5=[...(solid.length>=5?solid:priced)].sort((a,b)=>b.p.consistency-a.p.consistency||(a.p.odds as number)-(b.p.odds as number)).slice(0,5);
 const best5ids=new Set(best5.map(r=>r.it.fid+r.p.option));
 const b5st=best5.some(r=>r.p.status==='LOST')?'lost':best5.length&&best5.every(r=>r.p.status==='WON')?'won':'';
 return <main className="wrap">
  <div className="page-title"><span>Free for everyone</span><h1>Free picks</h1>
   <p>Single picks in eight popular markets. The engine compares each match with the 50 most similar past matches and only shows a pick when the market came in often enough.</p></div>

  <div className="chips" role="tablist" aria-label="Markets">{F.cats.map(c=><button key={c} role="tab" aria-selected={cat===c} className={`chip${cat===c?' on':''}`} onClick={()=>setCat(c)}>{label(c)}<i>{count(c)}</i></button>)}</div>
  <div className="history-controls" style={{marginTop:0}}>
   <p style={{margin:0,color:'var(--dim)'}}>{D?niceDate(D.date):''}. {rows.length} {rows.length===1?'pick':'picks'}{settled.length?`, ${won} of ${settled.length} won so far`:''}. {rec?`Past record for this market: ${rec.hit}% of ${rec.picks} picks won.`:''}{live?.picks?` Live: ${live.won} of ${live.picks}.`:''}</p>
   {F.history.length>1?<div className="chips daybar" role="tablist" aria-label="Day">{F.history.slice(0,7).map((d,i)=><button key={d.date} role="tab" aria-selected={D?.date===d.date} className={`chip${D?.date===d.date?' on':''}`} onClick={()=>setDay(d.date)}>{F.today&&d.date===F.today.date?'Today':i===1&&F.today&&F.history[0].date===F.today.date?'Yesterday':niceDate(d.date).split(' ').slice(0,2).join(' ')}</button>)}</div>:null}
  </div>

  {priced.length?<div className="acc">
   <Slip vip={false} tone="sky" plain day={D?.date||''} label={`Best ${best5.length} · free ticket`} t={{no:1,tier:label(cat),target:0,odds:acc(best5),reached:true,repeats:false,status:b5st==='won'?'WON':b5st==='lost'?'LOST':'PENDING',
    legs:[...best5].sort((a,b)=>(a.it.kickoff||'').localeCompare(b.it.kickoff||'')).map(r=>({fid:r.it.fid,kickoff:r.it.kickoff,match:`${r.it.home} - ${r.it.away}`,pick:r.p.option,model:'FREE',odds:r.p.odds as number,status:r.p.status,score:r.it.score}))}}/>
   <div className="acc-box"><span>All {priced.length} together</span><b>{fmt(acc(priced))}</b><small>Accumulated odds if every {label(cat).toLowerCase()} pick is played on one ticket. The more picks, the harder it is to win.</small></div>
  </div>:null}

  <div className="picks">{rows.length?rows.map(({it,p},i)=><div className={`pick${best5ids.has(it.fid+p.option)?' pick-star':''}`} key={it.fid+p.option+i}>
    <span className="pick-time">{kick(it.kickoff)}</span>
    <span className="pick-teams"><b>{best5ids.has(it.fid+p.option)?'★ ':''}{it.home} v {it.away}</b><small>{it.league}{it.score?`. Final score ${it.score}`:''}</small></span>
    <span className="pick-market">{p.option}<small>1 {it.odds[0].toFixed(2)} · X {it.odds[1].toFixed(2)} · 2 {it.odds[2].toFixed(2)}</small></span>
    <span className="meter-wrap"><span className="meter"><i style={{width:p.consistency+'%'}}/></span><small>{p.consistency}% · {p.neighbours} similar matches</small></span>
    <span className="pick-odds">{p.odds?p.odds.toFixed(2):'·'}</span>
    <span className="pick-status">{p.status?<span className={`status ${p.status.toLowerCase()}`}>{p.status==='WON'?'Won':p.status==='VOID'?'Postponed':'Lost'}{it.score?' '+it.score:''}</span>:<span className="status pending">Pending</span>}</span>
   </div>):<div className="empty-state"><b>No {label(cat).toLowerCase()} picks for this day.</b>Try another market above.</div>}</div>

  <p className="note"><b>About the percentages.</b> The bar shows how often this market came in across the 50 most similar past matches. It is a measure of consistency, not a promise. Most of these picks have short odds, so use them as building blocks, not as a way to get rich.</p>
  <p style={{marginTop:22}}><Link href="/tickets" className="btn btn-gold">See today’s 10 VIP tickets</Link></p>
 </main>;
}
