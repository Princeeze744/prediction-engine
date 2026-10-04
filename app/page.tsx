'use client';
import Link from 'next/link';
import Slip from '@/components/Slip';
import NoDrawCard from '@/components/NoDraw';
import {useData,planOf,kick,niceDate,catLabel} from '@/lib/qs';

export default function HomePage(){
 const {data}=useData();
 const T=data?.daily10.today,F=data?.free.today;
 const hero=T?.tickets.find(t=>t.tier==='5 odds')||T?.tickets[0];
 const cats=data?.free.cats||[];
 const count=(c:string)=>F?F.items.reduce((a,it)=>a+it.picks.filter((p,i)=>c==='TOP FINGERPRINT'?i===0:p.cat===c).length,0):0;
 const best=(it:any)=>it.picks.filter((p:any)=>p.odds&&p.odds>=1.2).sort((a:any,b:any)=>b.consistency-a.consistency)[0]||it.picks[0];
 const top=F?F.items.map(it=>({it,p:best(it)})).sort((a,b)=>((b.p.odds||1)>=1.2?1:0)-((a.p.odds||1)>=1.2?1:0)||b.p.consistency-a.p.consistency).slice(0,6):[];
 return <main>
  <section className="hero">
   <div>
    <h1>Ten mixed tickets.<span className="l2">Every match day.</span></h1>
    <p>Our models read every football match on the board, pick the strongest markets, and build ten ready-to-play tickets from 3 odds to 20 odds. Saved before kick-off. Every result shown.</p>
    <div className="hero-cta"><Link href="/tickets" className="btn btn-gold">See today’s VIP tickets</Link><Link href="/picks" className="btn btn-ghost" style={{padding:'14px 22px',fontSize:15}}>Browse free picks</Link></div>
   </div>
   <div className="hero-slip">{hero&&T?<Slip t={hero} day={T.date} animate compact/>:
    <article className="slip slip-vip"><header className="slip-head"><div><span className="slip-tier">5 odds</span><span className="slip-no">Today’s ticket</span></div></header>
     <p className="slip-note" style={{paddingTop:8}}>Today’s tickets publish each morning. Check back shortly.</p><div className="slip-tear"/><footer className="slip-foot"><div><span className="slip-label">Total odds</span><strong className="slip-total">5.00</strong></div></footer></article>}</div>
  </section>

  <div className="wrap" style={{paddingTop:0}}>
   <section className="steps" aria-label="How to use QuantSport">
    <Link href="/picks" className="step" data-c="sky"><i>1</i><b>Start with free picks</b><span>Single picks in eight markets. Good for building your own ticket.</span></Link>
    <Link href="/tickets" className="step" data-c="gold"><i>2</i><b>Take a ready ticket</b><span>Ten mixed tickets a day at 3, 5, 10 and 20 odds. Copy and play.</span></Link>
    <Link href="/nodraw" className="step" data-c="rose"><i>3</i><b>Add a No Draw leg</b><span>Our special pick: matches that almost never end level.</span></Link>
    <Link href="/tickets#record" className="step" data-c="lime"><i>4</i><b>Check the record</b><span>Every ticket stays on the site with its result, won or lost.</span></Link>
   </section>
   <section className="section" style={{marginTop:28}}>
    <div className="section-head"><div><h2 className="h2">Today’s VIP tickets</h2><p>Open to everyone for now. Tap a size to see its tickets.</p></div><Link href="/tickets" className="ghost-link">See all 10 tickets</Link></div>
    <div className="tiers">
     {(data?.daily10.tiers||[{tier:'3 odds',count:3},{tier:'5 odds',count:3},{tier:'10 odds',count:3},{tier:'20 odds',count:1}]).map(x=>{const r=data?.tickets[planOf[x.tier]]?.record;return <Link href={'/tickets#t-'+x.tier.split(' ')[0]} className="tier" key={x.tier}>
      <b>{x.tier.replace(' odds','')}×</b><strong>{x.count} {x.count===1?'ticket':'tickets'} at {x.tier}</strong><span>{r?.hit!=null?`Won ${r.hit}% of ${r.tickets} test tickets`:'Mixed markets, no repeated match'}</span></Link>})}
    </div>
   </section>

   {(()=>{const yd=data?.daily10.history.find(d=>d.date!==T?.date&&d.tickets.some(t=>t.status==='WON'||t.status==='LOST'));if(!yd)return null;
    const w=yd.tickets.filter(t=>t.status==='WON'),l=yd.tickets.filter(t=>t.status==='LOST');
    const fd=data?.free.history.find(d=>d.date===yd.date);let fw=0,fn=0;fd?.items.forEach(it=>{const p=it.picks[0];if(p?.status==='WON'||p?.status==='LOST'){fn++;if(p.status==='WON')fw++}});
    const nd=data?.nodraw?.history.find(d=>d.date===yd.date);const ns=nd?nd.items.filter(i=>i.status==='WON'||i.status==='LOST'):[],nw=ns.filter(i=>i.status==='WON').length;
    return <section className="section" style={{marginTop:36}}>
     <div className="section-head"><div><h2 className="h2">Last results</h2><p>{niceDate(yd.date)}. Every ticket and pick, won or lost.</p></div><Link href="/tickets#record" className="ghost-link">See every ticket</Link></div>
     <div className="track results">
      <Link href="/tickets#record"><b style={{color:'var(--won)'}}>{w.length}<small> of {yd.tickets.length}</small></b><span>VIP tickets won{w.length?': '+w.map(t=>t.tier+' @ '+t.odds.toFixed(2)).join(', '):''}</span></Link>
      <Link href="/tickets#record"><b style={{color:'var(--lost)'}}>{l.length}</b><span>VIP tickets lost{yd.tickets.length-w.length-l.length?`, ${yd.tickets.length-w.length-l.length} still pending`:''}</span></Link>
      <Link href={'/picks?d='+yd.date}><b>{fn?Math.round(fw/fn*100):0}%</b><span>Free top picks won: {fw} of {fn}</span></Link>
      <Link href="/nodraw"><b style={{color:'var(--rose)'}}>{ns.length?nw+'/'+ns.length:'·'}</b><span>No Draw picks won</span></Link>
     </div></section>})()}

   {data?<div className="section"><NoDrawCard data={data} limit={4}/></div>:null}

   <section className="section">
    <div className="section-head"><div><h2 className="h2">Free picks today</h2><p>{F?`${F.items.length} matches qualified for ${niceDate(F.date)}. Pick a market to see them.`:'Single picks in eight popular markets, straight from the engine.'}</p></div><Link href="/picks" className="ghost-link">See all free picks</Link></div>
    <div className="chips">{cats.map(c=><Link key={c} href={`/picks?m=${encodeURIComponent(c)}`} className="chip">{catLabel(c)}<i>{count(c)}</i></Link>)}</div>
    <div className="picks">{top.length?top.map(({it,p})=>{return <div className="pick" key={it.fid}>
      <span className="pick-time">{kick(it.kickoff)}</span>
      <span className="pick-teams"><b>{it.home} v {it.away}</b><small>{it.league}</small></span>
      <span className="pick-market">{p.option}</span>
      <span className="meter-wrap"><span className="meter"><i style={{width:p.consistency+'%'}}/></span><small>{p.neighbours} similar past matches</small></span>
      <span className="pick-odds">{p.odds?p.odds.toFixed(2):'·'}</span>
      <span className="pick-status"><span className="status pending">{p.consistency}%</span></span></div>})
     :<div className="empty-state"><b>Free picks publish each morning.</b>They appear here as soon as today’s matches are analysed.</div>}</div>
   </section>

   <section className="section">
    <div className="band">
     <div><h2 className="h2">We show the losses too.</h2><p className="lede">Bigger odds win less often, and nobody wins every ticket. So every ticket is locked before kick-off, settled from the final score, and left on the site whether it won or lost.</p>
      <p style={{marginTop:18}}><Link href="/tickets#record" className="ghost-link">Open the full record</Link></p></div>
     <div className="rates">{(data?.daily10.tiers||[]).map(x=>{const r=data?.tickets[planOf[x.tier]]?.record;const h=r?.hit||0;return <div className="rate" key={x.tier}><b>{x.tier}</b><span className="meter"><i style={{width:Math.max(h,3)+'%'}}/></span><em>{h}%</em></div>})}
      <small style={{color:'var(--dim)'}}>Share of test tickets that won, by ticket size.</small></div>
    </div>
   </section>
  </div>
 </main>;
}
