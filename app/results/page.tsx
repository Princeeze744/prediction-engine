'use client';
import {useState} from 'react';
import Link from 'next/link';
import Slip from '@/components/Slip';
import {Loader} from '@/components/Ball';
import {NDSlip} from '@/components/NoDraw';
import {useData,niceDate} from '@/lib/qs';
/* Results: pick a day, see everything that was published that day and how it ended. */
export default function Results(){
 const {data,err}=useData();const [day,setDay]=useState(''),[show,setShow]=useState('vip');
 if(err)return <main className="wrap"><div className="page-title"><h1>Results</h1><p>Nothing published yet.</p></div></main>;
 if(!data)return <main className="wrap"><Loader label="Loading results"/></main>;
 const H=data.daily10.history,today=data.daily10.today?.date;
 const def=H.find(d=>d.date!==today&&d.tickets.some(t=>t.status==='WON'||t.status==='LOST'))||H[0];
 const D=H.find(d=>d.date===day)||def;
 if(!D)return <main className="wrap"><div className="page-title"><h1>Results</h1><p>Results appear here once the first day’s matches have finished.</p></div></main>;
 const w=D.tickets.filter(t=>t.status==='WON'),l=D.tickets.filter(t=>t.status==='LOST'),p=D.tickets.length-w.length-l.length;
 const fd=data.free.history.find(d=>d.date===D.date);let fw=0,fn=0;fd?.items.forEach(it=>{const x=it.picks[0];if(x?.status==='WON'||x?.status==='LOST'){fn++;if(x.status==='WON')fw++}});
 const nd=data.nodraw?.history.find(d=>d.date===D.date),ns=nd?nd.items.filter(i=>i.status==='WON'||i.status==='LOST'):[],nw=ns.filter(i=>i.status==='WON').length;
 const sp=data.specials?.history.find(d=>d.date===D.date),sw=sp?sp.tickets.filter(t=>t.status==='WON').length:0;
 const tabs=[['vip',`VIP tickets`,D.tickets.length],...(sp?.tickets.length?[['sp','Specials',sp.tickets.length]]:[]),...(nd?.items.length?[['nd','No Draw',nd.items.length]]:[]),['opt','By option',data.daily10.by_model?.length||0]] as [string,string,number][];
 return <main className="wrap">
  <div className="page-title"><span>Nothing is removed</span><h1>Results</h1><p>Choose a day to see every ticket and pick we published and how it ended.</p></div>

  <div className="chips daybar" role="tablist" aria-label="Day" style={{paddingBottom:10}}>{H.slice(0,10).map((d,i)=><button key={d.date} role="tab" aria-selected={D.date===d.date} className={`chip${D.date===d.date?' on':''}`} onClick={()=>setDay(d.date)}>{d.date===today?'Today':niceDate(d.date).split(' ').slice(0,2).join(' ')}</button>)}</div>

  <div className="track results">
   <a onClick={()=>setShow('vip')}><b style={{color:'var(--won)'}}>{w.length}<small> of {D.tickets.length}</small></b><span>VIP tickets won{w.length?': '+w.map(t=>t.tier+' @ '+t.odds.toFixed(2)).join(', '):''}{p?`. ${p} still in play`:''}</span></a>
   <a onClick={()=>setShow(sp?.tickets.length?'sp':'vip')}><b>{sp?.tickets.length?<>{sw}<small> of {sp.tickets.length}</small></>:'–'}</b><span>Specials won{sp?.backfilled?' (added afterwards)':''}</span></a>
   <Link href={'/picks?d='+D.date}><b>{fn?Math.round(fw/fn*100)+'%':'–'}</b><span>Free top picks won{fn?`: ${fw} of ${fn}`:''}</span></Link>
   <a onClick={()=>setShow(nd?.items.length?'nd':'vip')}><b style={{color:'var(--rose)'}}>{ns.length?nw+'/'+ns.length:'–'}</b><span>No Draw picks won</span></a>
  </div>

  <div className="tabs" role="tablist" aria-label="What to show">{tabs.map(([k,label,n])=><button key={k} role="tab" aria-selected={show===k} className={show===k?'on':''} onClick={()=>setShow(k)}>{label}<i>{n}</i></button>)}</div>

  {show==='vip'?<><p className="tab-intro"><b>{niceDate(D.date)}.</b> Locked at {D.created.slice(11)}. {w.length} won, {l.length} lost{p?`, ${p} still in play`:''}.</p>
   <div className="slip-grid">{D.tickets.map(t=><Slip key={t.no} t={t} day={D.date}/>)}</div></>:null}
  {show==='sp'&&sp?.backfilled?<p className="note"><b>Shown for the record, not published at the time.</b> Specials started on Sunday 4 October. These are the tickets the same rules would have made on {niceDate(sp.date)}, built on {sp.backfilled} from that morning’s saved prices. They are not counted in the Specials win record.</p>:null}
  {show==='sp'&&sp?<div className="slip-grid">{sp.tickets.map(t=><Slip key={t.no} t={t} day={sp.date} plain label={t.sporty}/>)}</div>:null}
  {show==='nd'&&nd?<><div className="nd-slipwrap"><NDSlip day={nd} opt="nd" tier="Sweet"/></div><p><Link href="/nodraw" className="ghost-link nd-link">Open the No Draw page for Over 1.5, Favourite wins and the Wide list</Link></p></>:null}
  {show==='opt'?<><p className="tab-intro"><b>Which options are delivering.</b> Every pick that has appeared on a published VIP ticket, all days together, counted by option.</p>
   <div className="history-table">
    <div className="history-row history-head sb"><span>Option</span><span>Picks</span><span>Won</span><span>Win rate</span></div>
    {(data.daily10.by_model||[]).slice(0,20).map(m=><div className="history-row sb" key={m.id}><span><b>{m.name}</b><small>{m.sporty}</small></span><span>{m.picks}</span><span style={{color:'var(--won)'}}>{m.won}</span><span><b>{m.hit}%</b>{m.picks<30?<small>few picks yet</small>:null}</span></div>)}
   </div></>:null}

  <Link href="/models" className="linkcard" data-c="chalk"><div><b>How the models work</b><span>Every model, its rule, its test record and today’s picks.</span></div><em>Open</em></Link>
 </main>;
}
