'use client';
import Link from 'next/link';
import {kick,niceDate,type Data,type NDItem} from '@/lib/qs';
/* The No Draw spotlight: "Home or Away" (12 on SportyBet). Sweet = the strict rule. Wide = looser rule, more matches, lower hit rate. */
export function NDRow({it}:{it:NDItem}){const st=(it.status||'').toLowerCase();
 return <div className={`pick nd-row${it.tier==='Sweet'?' nd-sweet':''}`}>
  <span className="pick-time">{kick(it.kickoff)}</span>
  <span className="pick-teams"><b>{it.home} v {it.away}</b><small>{it.league}{it.score?`. Final score ${it.score}`:''}</small></span>
  <span className="pick-market">Home or Away (12)<small>Favourite {it.fav.toFixed(2)} · Over 2.5 at {it.o25.toFixed(2)}</small></span>
  <span className="nd-tag">{it.tier==='Sweet'?'Sweet':'Wide'}</span>
  <span className="pick-odds">{it.odds.toFixed(2)}</span>
  <span className="pick-status">{it.status?<span className={`status ${st}`}>{it.status==='WON'?'Won':it.status==='VOID'?'Postponed':'Lost'}{it.score?' '+it.score:''}</span>:<span className="status pending">Pending</span>}</span></div>}
export default function NoDrawCard({data,limit=4}:{data:Data;limit?:number}){
 const N=data.nodraw;if(!N||!N.tiers?.length)return null;
 const T=N.today,sweet=T?T.items.filter(i=>i.tier==='Sweet'):[],wide=T?T.items.filter(i=>i.tier!=='Sweet'):[];
 const rs=N.tiers.find(t=>t.tier==='Sweet'),rw=N.tiers.find(t=>t.tier==='Wide');
 const show=[...sweet,...wide].slice(0,limit);
 return <section className="nd-card">
  <div className="nd-top">
   <div><span className="kicker nd-kicker">Special pick</span><h2 className="h2">No Draw Sweet</h2>
    <p>Matches where a draw is very unlikely. You win if either team wins. On SportyBet it is <b>Double Chance, Home or Away (12)</b>.</p></div>
   <div className="nd-stats">
    {rs?<div><b>{rs.hit}%</b><span>Sweet: won {rs.won} of {rs.picks} past matches</span></div>:null}
    {rw?<div><b>{rw.hit}%</b><span>Wide: won {rw.won} of {rw.picks} past matches</span></div>:null}
   </div>
  </div>
  {T?<><p className="nd-today">{niceDate(T.date)}: <b>{sweet.length}</b> Sweet {sweet.length===1?'match':'matches'} and <b>{wide.length}</b> Wide.{sweet.length<=2?' Sweet needs a very heavy favourite in a high-scoring game, so some days have only a few.':''}</p>
   {show.length?<div className="picks">{show.map(it=><NDRow key={it.fid} it={it}/>)}</div>:<div className="picks"><div className="empty-state"><b>No match passes the No Draw test today.</b>We do not force a pick when the conditions are not met.</div></div>}</>
   :<div className="picks"><div className="empty-state"><b>Today’s No Draw matches publish each morning.</b></div></div>}
  <p style={{margin:'18px 0 0'}}><Link href="/nodraw" className="ghost-link nd-link">{T&&T.items.length>show.length?`See all ${T.items.length} No Draw matches`:'Open the No Draw page and record'}</Link></p>
 </section>}
