import './theme.css';
import Image from 'next/image';
import Link from 'next/link';
import Particles from '@/components/Particles';
import Intro from '@/components/Intro';
import {HeaderNav,MobileNav} from '@/components/Nav';
const site=process.env.VERCEL_PROJECT_PRODUCTION_URL?`https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`:'http://localhost:3001';
export const metadata={metadataBase:new URL(site),openGraph:{title:'QuantSport AI',description:'Free football picks and ten mixed tickets every match day. Saved before kick-off, every result shown.',siteName:'QuantSport AI',type:'website',url:'/'},twitter:{card:'summary_large_image'},title:'QuantSport AI: daily football picks and mixed tickets',description:'Ten mixed accumulator tickets and free football picks every match day, saved before kick-off with every result shown.'};
export const viewport={themeColor:'#04100c'};
/* Runs before the page paints: the opening screen plays once per visit, not on every page. */
const seen=`try{if(sessionStorage.getItem('qs-intro'))document.documentElement.setAttribute('data-seen','1');else sessionStorage.setItem('qs-intro','1')}catch(e){}`;
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en" data-scroll-behavior="smooth" suppressHydrationWarning><body suppressHydrationWarning>
<script dangerouslySetInnerHTML={{__html:seen}}/>
<Intro/>
<Particles/>
<header><Link href="/" className="brand"><span className="brand-mark"><Image src="/logo.png" alt="" width={40} height={40}/></span><span>QUANTSPORT <b>AI</b></span></Link>
 <HeaderNav/>
 <Link href="/tickets" className="member">Today’s 10 tickets</Link></header>
{children}
<footer><div className="foot"><div><b>QUANTSPORT AI</b><p>Picks and tickets are saved before kick-off and never edited. Every loss stays on the site. Bet only what you can afford to lose. 18+.</p></div>
 <nav aria-label="Footer"><Link href="/picks">Free picks</Link><Link href="/tickets">VIP tickets</Link><Link href="/nodraw">No Draw</Link><Link href="/models">Models</Link></nav></div></footer>
<MobileNav/>
</body></html>}
