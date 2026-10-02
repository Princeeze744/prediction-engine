'use client';
import {useEffect,useState} from 'react';
import type {Ticket} from '@/lib/qs';
import {kick} from '@/lib/qs';
/* The betting slip: the one object the whole site is built around. */
export default function Slip({t,day,vip=true,animate=false,compact=false}:{t:Ticket;day:string;vip?:boolean;animate?:boolean;compact?:boolean}){
 const [copied,setCopied]=useState(false);
 const [shown,setShown]=useState(animate?0:t.legs.length);
 useEffect(()=>{if(!animate)return;if(window.matchMedia('(prefers-reduced-motion: reduce)').matches){setShown(t.legs.length);return}
  let i=0;const id=setInterval(()=>{i++;setShown(i);if(i>=t.legs.length)clearInterval(id)},520);return()=>clearInterval(id)},[animate,t.legs.length]);
 const running=t.legs.slice(0,shown).reduce((a,l)=>a*l.odds,1);
 const total=animate&&shown<t.legs.length?running:t.odds;
 const st=(t.status||'PENDING').toLowerCase();
 const copy=()=>{const txt=`QuantSport ${t.tier} ticket, ${day}, total odds ${t.odds.toFixed(2)}\n`+t.legs.map((l,i)=>`${i+1}. ${l.match}: ${l.pick} @ ${l.odds.toFixed(2)}`).join('\n');navigator.clipboard?.writeText(txt);setCopied(true);setTimeout(()=>setCopied(false),1600)};
 return <article className={`slip slip-${st}${vip?' slip-vip':''}${compact?' slip-compact':''}`}>
  <header className="slip-head">
   <div><span className="slip-tier">{t.tier}</span><span className="slip-no">Ticket {t.no}</span></div>
   {t.status&&t.status!=='PENDING'?<span className={`badge badge-${st}`}>{t.status==='WON'?'Won':'Lost'}</span>:<span className="slip-count">{t.legs.length} picks</span>}
  </header>
  <ol className="slip-legs">
   {t.legs.map((l,i)=><li key={i} className={`leg${i<shown?' leg-in':''}${l.status?' leg-'+l.status.toLowerCase():''}`}>
    <span className="leg-time">{kick(l.kickoff)||'·'}</span>
    <span className="leg-main"><b>{l.match}</b><em>{l.pick}</em>{l.score?<small>Full time {l.score}, half time {l.ht}</small>:null}</span>
    <span className="leg-odds">{l.odds.toFixed(2)}</span>
   </li>)}
  </ol>
  <div className="slip-tear" aria-hidden="true"/>
  <footer className="slip-foot">
   <div><span className="slip-label">Total odds</span><strong className="slip-total">{total.toFixed(2)}</strong></div>
   {!compact&&<button className="btn btn-ghost" onClick={copy} aria-live="polite">{copied?'Copied':'Copy ticket'}</button>}
  </footer>
  {!compact&&t.repeats?<p className="slip-note">Few matches today, so this ticket shares a match with another ticket.</p>:null}
  {!compact&&!t.reached?<p className="slip-note">Not enough qualifying matches to reach {t.target} odds today.</p>:null}
 </article>;
}
