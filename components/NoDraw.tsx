'use client';
import Link from 'next/link';
import Slip from '@/components/Slip';
import {kick,niceDate,ndOf,type Data,type NDItem,type NDOpt,type NDDay,type Ticket} from '@/lib/qs';
/* The No Draw spotlight: "Home or Away" (12 on SportyBet). Sweet = the strict rule. Wide = looser rule, more matches, lower hit rate.
   The same matches also carry two companion picks: Over 1.5 goals and Favourite to win. */
export const ND_OPTS:{k:NDOpt;label:string}[]=[{k:'nd',label:'No Draw (12)'},{k:'o15',label:'Over 1.5'},{k:'fav',label:'Favourite wins'}];
const word=(s?:string)=>s==='WON'?'Won':s==='VOID'?'Postponed':'Lost';
export function NDRow({it,opt='nd'}:{it:NDItem;opt?:NDOpt}){const o=ndOf(it,opt),st=(o.status||'').toLowerCase();
 return <div className={`pick nd-row${it.tier==='Sweet'?' nd-sweet':''}`}>
  <span className="pick-time">{kick(it.kickoff)}</span>
  <span className="pick-teams"><b>{it.home} v {it.away}</b><small>{it.league}{it.score?`. Final score ${it.score}`:''}</small></span>
  <span className="pick-market">{o.pick}<small>Favourite {it.fav.toFixed(2)} · Over 2.5 at {it.o25.toFixed(2)}</small></span>
  <span className="nd-tag">{it.tier==='Sweet'?'Sweet':'Wide'}</span>
  <span className="pick-odds">{o.odds?o.odds.toFixed(2):'·'}</span>
  <span className="pick-status">{o.status?<span className={`status ${st}`}>{word(o.status)}{it.score?' '+it.score:''}</span>:<span className="status pending">Pending</span>}</span></div>}
/* The Sweet matches as one slip, with the accumulated odds shown the VIP way. */
export function ndTicket(items:NDItem[],opt:NDOpt,title:string):Ticket|null{
 const legs=items.map(it=>({it,o:ndOf(it,opt)})).filter(x=>x.o.odds&&x.o.odds>1&&x.o.status!=='VOID').map(({it,o})=>({fid:it.fid,kickoff:it.kickoff,match:`${it.home} - ${it.away}`,league:it.league,pick:o.pick,model:'ND',odds:o.odds as number,status:o.status,score:it.score}));
 if(!legs.length)return null;
 const sts=legs.map(l=>l.status||'PENDING');
 return {no:1,tier:title,target:0,odds:legs.reduce((a,l)=>a*l.odds,1),reached:true,repeats:false,legs,status:sts.includes('LOST')?'LOST':sts.every(s=>s==='WON')?'WON':'PENDING'}}
export function NDSlip({day,opt,tier='Sweet'}:{day:NDDay;opt:NDOpt;tier?:string}){
 const t=ndTicket(day.items.filter(i=>tier==='All'||i.tier===tier),opt,ND_OPTS.find(x=>x.k===opt)!.label);
 if(!t)return null;
 return <Slip t={t} day={day.date} vip={false} tone="rose" plain label={`${tier==='All'?'All':tier} · ${t.legs.length} ${t.legs.length===1?'match':'matches'}`}/>}
export default function NoDrawCard({data,limit=4}:{data:Data;limit?:number}){
 const N=data.nodraw;if(!N||!N.tiers?.length)return null;
 const T=N.today,sweet=T?T.items.filter(i=>i.tier==='Sweet'):[],wide=T?T.items.filter(i=>i.tier!=='Sweet'):[];
 const rs=N.tiers.find(t=>t.tier==='Sweet'),rw=N.tiers.find(t=>t.tier==='Wide'),ex=N.extras?.Sweet;
 const show=[...sweet,...wide].slice(0,limit);
 return <section className="nd-card">
  <div className="nd-top">
   <div><span className="kicker nd-kicker">Special pick</span><h2 className="h2">No Draw Sweet</h2>
    <p>Matches where a draw is very unlikely. You win if either team wins. On SportyBet it is <b>Double Chance, Home or Away (12)</b>.{ex?' The same matches also come with Over 1.5 and Favourite to win.':''}</p></div>
   <div className="nd-stats">
    {rs?<div><b>{rs.hit}%</b><span>Sweet: won {rs.won} of {rs.picks} past matches</span></div>:null}
    {rw?<div><b>{rw.hit}%</b><span>Wide: won {rw.won} of {rw.picks} past matches</span></div>:null}
   </div>
  </div>
  {T?<><p className="nd-today">{niceDate(T.date)}: <b>{sweet.length}</b> Sweet {sweet.length===1?'match':'matches'} and <b>{wide.length}</b> Wide.{sweet.length<=2?' Sweet needs a very heavy favourite in a high-scoring game, so some days have only a few.':''}</p>
   {show.length?<div className="picks">{show.map(it=><NDRow key={it.fid} it={it}/>)}</div>:<div className="picks"><div className="empty-state"><b>No match passes the No Draw test today.</b>We do not force a pick when the conditions are not met.</div></div>}</>
   :<div className="picks"><div className="empty-state"><b>Today’s No Draw matches publish each morning.</b></div></div>}
  <p style={{margin:'18px 0 0'}}><Link href="/nodraw" className="ghost-link nd-link">{T&&T.items.length>show.length?`See all ${T.items.length} No Draw matches and the full ticket`:'Open the No Draw page and record'}</Link></p>
 </section>}
