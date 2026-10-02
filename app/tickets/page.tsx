'use client';
import {useState} from 'react';
import Link from 'next/link';
import Slip from '@/components/Slip';
import NoDrawCard from '@/components/NoDraw';
import {Loader} from '@/components/Ball';
import {useData,planOf,niceDate} from '@/lib/qs';

export default function Tickets(){
 const {data,err}=useData();const [open,setOpen]=useState('');
 if(err)return <main className="wrap"><div className="page-title"><h1>Today’s VIP tickets</h1><p>Today’s tickets are not published yet. They appear after the morning update.</p></div></main>;
 if(!data)return <main className="wrap"><Loader label="Loading tickets"/></main>;
 const D=data.daily10,T=D.today,past=D.history.filter(d=>!T||d.date!==T.date);
 return <main className="wrap">
  <div className="page-title"><span>VIP picks, open to everyone for now</span><h1>Today’s 10 tickets</h1>
   <p>Three tickets at 3 odds, three at 5, three at 10 and one at 20. Each mixes different markets from our best models, and a match appears on only one ticket whenever the day has enough games.</p></div>

  <div className="tiers">{D.tiers.map(x=>{const r=data.tickets[planOf[x.tier]]?.record,l=D.live[x.tier];return <a href={'#t-'+x.tier.split(' ')[0]} className="tier" key={x.tier}>
   <b>{x.tier.replace(' odds','')}×</b><strong>{x.count} {x.count===1?'ticket':'tickets'}</strong><span>Won {r?.hit??'·'}% of {r?.tickets??0} test tickets{l?`. Live: ${l.won} of ${l.tickets}`:''}</span></a>})}</div>
  <div className="jump" aria-label="Jump to">{D.tiers.map(x=><a key={x.tier} href={'#t-'+x.tier.split(' ')[0]}>{x.tier}</a>)}<a href="#nodraw" data-c="rose">No Draw</a><a href="#record">Previous days</a></div>
  <p className="note"><b>How to read this.</b> On past results a 3-odds ticket won about 3 times in 10, a 5-odds ticket 2 in 10, a 10-odds ticket 1 in 8, and a 20-odds ticket rarely. Tickets are locked before kick-off and never edited. Stake only what you can afford to lose.</p>

  {T?D.tiers.map(x=>{const list=T.tickets.filter(t=>t.tier===x.tier);if(!list.length)return null;return <section className="section" style={{marginTop:44}} key={x.tier} id={'t-'+x.tier.split(' ')[0]}>
    <div className="section-head"><div><h2 className="h2">{x.tier}</h2><p>{niceDate(T.date)}. Locked at {T.created.slice(11)}.</p></div></div>
    <div className={`slip-grid${list.length===1?' one':''}`}>{list.map(t=><Slip key={t.no} t={t} day={T.date}/>)}</div></section>})
   :<div className="empty-state"><b>Today’s tickets are not published yet.</b>They appear after the morning update.</div>}

  <div className="section" id="nodraw"><NoDrawCard data={data} limit={6}/></div>

  <section className="section" id="record">
   <div className="section-head"><div><h2 className="h2">Previous days</h2><p>Every ticket we published, with its result. Nothing is removed.</p></div></div>
   <div className="history-table">
    <div className="history-row history-head"><span>Day</span><span>Tickets</span><span>Won</span><span>Lost</span><span></span></div>
    {past.length?past.map(d=>{const w=d.tickets.filter(t=>t.status==='WON').length,l=d.tickets.filter(t=>t.status==='LOST').length,p=d.tickets.length-w-l;return <div key={d.date}>
     <div className="history-row" onClick={()=>setOpen(open===d.date?'':d.date)} style={{cursor:'pointer'}}><span><b>{niceDate(d.date)}</b><small>locked {d.created}</small></span><span>{d.tickets.length}</span><span style={{color:'var(--won)'}}>{w}</span><span>{l}{p?<small>{p} pending</small>:null}</span><span><button className="btn btn-ghost">{open===d.date?'Hide tickets':'Show tickets'}</button></span></div>
     {open===d.date?<div style={{padding:'16px 18px 22px'}}><div className="slip-grid">{d.tickets.map(t=><Slip key={t.no} t={t} day={d.date}/>)}</div></div>:null}</div>})
     :<div className="empty-state"><b>No previous days yet.</b>Each day’s tickets move here, with every result, once the next day is published.</div>}
   </div>
  </section>
  <p style={{marginTop:28}}><Link href="/models" className="ghost-link">See the models behind the tickets</Link></p>
 </main>;
}
