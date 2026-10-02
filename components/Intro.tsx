import Image from 'next/image';
import Ball from './Ball';
/* Opening screen: logo, a football rolling along the line, then the site. Plays once per visit (see the small script in layout). */
export default function Intro(){return <div className="intro" aria-hidden="true">
 <div className="intro-in">
  <span className="intro-logo"><Image src="/logo.png" alt="" width={84} height={84} priority/></span>
  <strong>QUANTSPORT <b>AI</b></strong>
  <div className="intro-track"><i/><span className="intro-ball"><Ball size={34}/></span></div>
  <small>Reading today’s matches</small>
 </div></div>}
