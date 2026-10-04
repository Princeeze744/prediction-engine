'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';
import Slip from '@/components/Slip';
import {Loader} from '@/components/Ball';
import {useData,planOf,niceDate} from '@/lib/qs';
/* VIP: one group of tickets on screen at a time, chosen with the tabs. Past days live on the Results page. */
export default function Tickets(){
 const {data,err}=useData();const [tab,setTab]=useState('3');
 useEffect(()=>{const rd=()=>{const h=window.location.hash.replace('#t-','').replace('#','');if(['3','5','10','20','specials'].includes(h))setTab(h)};rd();window.addEventListener('hashchange',rd);return()=>window.removeEventListener('hashchange',rd)},[]);
 if(err)return <main className="wrap"><div className="page-title"><h1>Today’s VIP tickets</h1><p>Today’s tickets are not published yet. They appear after the morning update.</p></div></main>;
 if(!data)return <main className="wrap"><Loader label="Loading tickets"/></main>;
 const D=data.daily10,T=D.today,S=data.specials?.today,SL=data.specials?.live||{};
 const tier=D.tiers.find(x=>x.tier.split(' ')[0]===tab),list=T&&tier?T.tickets.filter(t=>t.tier===tier.tier):[];
 const r=tier?data.tickets[planOf[tier.tier]]?.record:null,l=tier?D.live[tier.tier]:null;
 const nd=data.nodraw?.today,nSweet=nd?nd.items.filter(i=>i.tier==='Sweet').length:0;
 return <main className="wrap">
  <div className="page-title"><span>VIP picks, open to everyone for now</span><h1>Today’s tickets</h1>
   <p>{T?`${niceDate(T.date)}. Locked at ${T.created.slice(11)}, before kick-off, and never edited.`:'Ready-made tickets, published each morning.'} Choose a ticket size below.</p></div>

  <div className="tabs" role="tablist" aria-label="Ticket size">
   {D.tiers.map(x=>{const k=x.tier.split(' ')[0];return <button key={k} role="tab" aria-selected={tab===k} className={tab===k?'on':''} onClick={()=>setTab(k)}>{x.tier}<i>{T?T.tickets.filter(t=>t.tier===x.tier).length:x.count}</i></button>})}
   {S?.tickets.length?<button role="tab" aria-selected={tab==='specials'} className={tab==='specials'?'on':''} onClick={()=>setTab('specials')}>Specials<i>{S.tickets.length}</i></button>:null}
  </div>

  {tab!=='specials'&&tier?<section>
   <p className="tab-intro"><b>{tier.tier} tickets.</b> Mixed markets from our best models; a match appears on only one ticket when the day has enough games. {r?.hit!=null?`In testing, ${r.hit}% of ${r.tickets} tickets of this size won.`:''}{l?` Published so far: ${l.won} of ${l.tickets} won.`:''}</p>
   {list.length?<div className={`slip-grid${list.length===1?' one':''}`}>{list.map(t=><Slip key={t.no} t={t} day={T!.date}/>)}</div>
    :<div className="picks"><div className="empty-state"><b>Today’s tickets are not published yet.</b>They appear after the morning update.</div></div>}
  </section>:null}

  {tab==='specials'&&S?<section>
   <p className="tab-intro"><b>Specials: one market per ticket.</b> Each day the engine takes the options with the strongest long-run record that have enough matches, and builds tickets of about 3 odds from each.</p>
   <div className="slip-grid">{S.tickets.map(t=>{const sl=SL[t.model];return <div key={t.no}><Slip t={t} day={S.date} plain label={t.sporty}/>
    <p className="slip-under">Past record of this option: {t.record.hit}% of {t.record.picks} picks at average odds {t.record.avg_odds.toFixed(2)}{sl?`. Specials so far: ${sl.won} of ${sl.tickets} tickets won.`:'.'}</p></div>})}</div>
   <p className="note"><b>How the options are chosen.</b> By their whole record, checked on days the model had not seen. We tested choosing by “what won yesterday” and it does not carry over to the next day, so we do not do that.</p>
  </section>:null}

  <p className="note"><b>How to read this.</b> Bigger odds win less often: on past results a 3-odds ticket won about 3 times in 10, a 5-odds ticket 2 in 10, a 10-odds ticket 1 in 8, and a 20-odds ticket rarely. Stake only what you can afford to lose.</p>

  <Link href="/nodraw" className="linkcard" data-c="rose"><div><b>No Draw Sweet</b><span>{nd?`${nSweet} Sweet ${nSweet===1?'match':'matches'} today, with Over 1.5 and Favourite wins on the same games.`:'Our special pick: matches that almost never end level.'}</span></div><em>Open</em></Link>
  <Link href="/results" className="linkcard" data-c="lime"><div><b>Results</b><span>Every ticket from previous days with its result, and which options are delivering.</span></div><em>Open</em></Link>
 </main>;
}
