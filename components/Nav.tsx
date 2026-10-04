'use client';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {Home,ListChecks,Ticket,Trophy,ShieldCheck} from 'lucide-react';
/* One menu definition for desktop and phone. The page you are on lights up in its own colour. */
const ITEMS=[
 {href:'/',label:'Today',short:'Today',c:'lime',I:Home},
 {href:'/picks',label:'Free picks',short:'Free',c:'sky',I:ListChecks},
 {href:'/tickets',label:'VIP tickets',short:'VIP',c:'gold',I:Ticket},
 {href:'/nodraw',label:'No Draw',short:'No Draw',c:'rose',I:ShieldCheck},
 {href:'/results',label:'Results',short:'Results',c:'chalk',I:Trophy}];
const on=(p:string,h:string)=>h==='/'?p==='/':p===h||p.startsWith(h+'/');
export function HeaderNav(){const p=usePathname()||'/';
 return <><nav aria-label="Main" className="main-nav">{ITEMS.map(x=><Link key={x.href} href={x.href} data-c={x.c} className={on(p,x.href)?'on':''} aria-current={on(p,x.href)?'page':undefined}>{x.label}</Link>)}</nav>
  <span key={p} className="route-bar" aria-hidden="true"/></>}
export function MobileNav(){const p=usePathname()||'/';
 return <div className="mobile-nav">{ITEMS.map(x=><Link key={x.href} href={x.href} data-c={x.c} className={on(p,x.href)?'on':''} aria-current={on(p,x.href)?'page':undefined}><x.I/>{x.short}</Link>)}</div>}
