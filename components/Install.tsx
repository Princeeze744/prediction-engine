'use client';
import {useEffect,useState} from 'react';
import {Download,X,Share,PlusSquare} from 'lucide-react';
/* "Install app": one tap on Android and desktop Chrome/Edge. iPhones do not allow one-tap install, so we show the two taps needed. Hidden once installed. */
type BIP=Event&{prompt:()=>Promise<void>;userChoice:Promise<{outcome:string}>};
export default function Install(){
 const [ev,setEv]=useState<BIP|null>(null),[ios,setIos]=useState(false),[show,setShow]=useState(false),[help,setHelp]=useState(false);
 useEffect(()=>{
  if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
  const standalone=window.matchMedia('(display-mode: standalone)').matches||(navigator as any).standalone;if(standalone)return;
  let off=false;try{off=localStorage.getItem('qs-install-off')==='1'}catch{}
  const ua=navigator.userAgent,isIos=/iphone|ipad|ipod/i.test(ua)||(/Macintosh/.test(ua)&&navigator.maxTouchPoints>1);
  if(isIos){setIos(true);if(!off)setShow(true)}
  const h=(e:Event)=>{e.preventDefault();setEv(e as BIP);if(!off)setShow(true)};
  const done=()=>{setShow(false);setEv(null)};
  window.addEventListener('beforeinstallprompt',h);window.addEventListener('appinstalled',done);
  return()=>{window.removeEventListener('beforeinstallprompt',h);window.removeEventListener('appinstalled',done)}},[]);
 const go=async()=>{if(ev){await ev.prompt();const c=await ev.userChoice;if(c.outcome==='accepted')setShow(false);setEv(null)}else setHelp(true)};
 const close=()=>{setShow(false);try{localStorage.setItem('qs-install-off','1')}catch{}};
 if(!show&&!help)return null;
 return <>
  {show?<div className="install" role="dialog" aria-label="Install the QuantSport app">
   <img src="/icon-192.png" alt="" width={44} height={44}/>
   <div><b>Get the QuantSport app</b><span>Opens from your home screen. Free, no app store needed.</span></div>
   <button className="btn btn-lime" onClick={go}><Download size={16}/>Install</button>
   <button className="install-x" onClick={close} aria-label="Not now"><X size={18}/></button></div>:null}
  {help?<div className="install-help" role="dialog" aria-label="How to install" onClick={()=>setHelp(false)}><div onClick={e=>e.stopPropagation()}>
   <h3>Add QuantSport to your home screen</h3>
   {ios?<ol><li><Share size={18}/> Tap the <b>Share</b> button at the bottom of Safari.</li><li><PlusSquare size={18}/> Scroll down and tap <b>Add to Home Screen</b>.</li><li>Tap <b>Add</b>. The QuantSport icon appears with your apps.</li></ol>
    :<ol><li>Open your browser menu (the three dots at the top).</li><li>Tap <b>Install app</b> or <b>Add to Home screen</b>.</li><li>Tap <b>Install</b>. The QuantSport icon appears with your apps.</li></ol>}
   <button className="btn btn-gold" onClick={()=>setHelp(false)}>Got it</button></div></div>:null}
 </>}
