'use client';
import {useEffect,useRef} from 'react';
/* Drifting points that link when they come close: the "pattern detection" backdrop behind every page.
   Built to stay light: glow is drawn once into a small sprite, 30 frames a second, fewer points on phones, paused when hidden or scrolling fast. */
export default function Particles(){
 const ref=useRef<HTMLCanvasElement>(null);
 useEffect(()=>{
  const c=ref.current;if(!c)return;const ctx=c.getContext('2d',{alpha:true});if(!ctx)return;
  const still=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const small=window.matchMedia('(max-width: 720px)').matches;
  const dpr=Math.min(window.devicePixelRatio||1,small?1:1.5);
  let w=0,h=0,raf=0,last=0;const mouse={x:-999,y:-999};
  const sprite=(rgb:string)=>{const s=document.createElement('canvas');s.width=s.height=32;const g=s.getContext('2d')!;const gr=g.createRadialGradient(16,16,0,16,16,16);
   gr.addColorStop(0,`rgba(${rgb},1)`);gr.addColorStop(.25,`rgba(${rgb},.55)`);gr.addColorStop(1,`rgba(${rgb},0)`);g.fillStyle=gr;g.fillRect(0,0,32,32);return s};
  const lime=sprite('190,255,90'),gold=sprite('255,203,82');
  type P={x:number;y:number;vx:number;vy:number;r:number;gold:boolean};let pts:P[]=[];
  const size=()=>{w=window.innerWidth;h=window.innerHeight;c.width=w*dpr;c.height=h*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);
   const n=small?22:Math.round(Math.min(56,Math.max(30,(w*h)/30000)));
   pts=Array.from({length:n},()=>({x:Math.random()*w,y:Math.random()*h,vx:(Math.random()-.5)*.5,vy:(Math.random()-.5)*.5,r:Math.random()*5+5,gold:Math.random()<.12}))};
  const R=small?100:130,R2=R*R;
  const draw=(t:number)=>{if(!still)raf=requestAnimationFrame(draw);if(t-last<33&&!still)return;last=t;
   ctx.clearRect(0,0,w,h);ctx.lineWidth=1;
   for(let i=0;i<pts.length;i++){const p=pts[i];
    if(!still){p.x+=p.vx;p.y+=p.vy;const dx=p.x-mouse.x,dy=p.y-mouse.y,d2=dx*dx+dy*dy;if(d2<19600&&d2>1){const d=Math.sqrt(d2);p.x+=dx/d*1.1;p.y+=dy/d*1.1}
     if(p.x<-20)p.x=w+20;else if(p.x>w+20)p.x=-20;if(p.y<-20)p.y=h+20;else if(p.y>h+20)p.y=-20}
    for(let j=i+1;j<pts.length;j++){const q=pts[j],ax=p.x-q.x,ay=p.y-q.y,dd=ax*ax+ay*ay;if(dd<R2){ctx.strokeStyle=`rgba(182,255,60,${((1-dd/R2)*.2).toFixed(3)})`;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.stroke()}}
    ctx.drawImage(p.gold?gold:lime,p.x-p.r,p.y-p.r,p.r*2,p.r*2)}};
  const mm=(e:MouseEvent)=>{mouse.x=e.clientX;mouse.y=e.clientY};
  const vis=()=>{cancelAnimationFrame(raf);if(!document.hidden&&!still)raf=requestAnimationFrame(draw)};
  let rz=0;const onResize=()=>{clearTimeout(rz);rz=window.setTimeout(()=>{if(Math.abs(window.innerWidth-w)>40||!small)size()},200)};
  size();if(still)draw(0);else raf=requestAnimationFrame(draw);
  window.addEventListener('resize',onResize);if(!small)window.addEventListener('mousemove',mm,{passive:true});document.addEventListener('visibilitychange',vis);
  return()=>{cancelAnimationFrame(raf);window.removeEventListener('resize',onResize);window.removeEventListener('mousemove',mm);document.removeEventListener('visibilitychange',vis)}
 },[]);
 return <canvas ref={ref} className="qs-particles" aria-hidden="true"/>;
}
