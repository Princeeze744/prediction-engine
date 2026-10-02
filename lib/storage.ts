'use client';
import type {Match,Pick} from './data';
export type PublishedBatch={id:string;publishedAt:string;sport:string;modelVersion:string;source:string;items:Match[];raw:string};
export type ResultStatus='WON'|'LOST'|'PENDING'|'VOID';
export type FixtureResult={key:string;sport:string;home:string;away:string;homeScore:number;awayScore:number;scoreLabel:string;updatedAt:string};
export type SettledMarket={key:string;batchId:string;matchId:string;sport:string;home:string;away:string;market:string;tier:string;isTop:boolean;consistency:number;neighbours:string;publishedAt:string;homeScore?:number;awayScore?:number;scoreLabel?:string;status:ResultStatus;settledAt?:string};
const KEY='quantsport_publications_v2';
const RESULT_KEY='quantsport_results_v1';
export function getBatches():PublishedBatch[]{if(typeof window==='undefined')return[];try{return JSON.parse(localStorage.getItem(KEY)||'[]')}catch{return[]}}
export function saveBatch(batch:PublishedBatch){const all=getBatches();localStorage.setItem(KEY,JSON.stringify([batch,...all].slice(0,100)));window.dispatchEvent(new Event('quantsport:published'))}
export function clearBatches(){localStorage.removeItem(KEY);window.dispatchEvent(new Event('quantsport:published'))}
export const norm=(s:string)=>s.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
export const fixtureKey=(sport:string,home:string,away:string)=>`${sport}|${norm(home)}|${norm(away)}`;
export function getResults():FixtureResult[]{if(typeof window==='undefined')return[];try{return JSON.parse(localStorage.getItem(RESULT_KEY)||'[]')}catch{return[]}}
export function upsertResults(rows:FixtureResult[]){const map=new Map(getResults().map(x=>[x.key,x]));rows.forEach(x=>map.set(x.key,x));localStorage.setItem(RESULT_KEY,JSON.stringify([...map.values()]));window.dispatchEvent(new Event('quantsport:results'))}
export function allMarkets(m:Match):Pick[]{return [m.top,...m.support]}
function teamScored(market:string,team:string){const a=norm(market),t=norm(team);return a.includes(`${t} to score`)||a.includes(`${t} team total`)||a.includes(`${t} over 0 5`)||a.includes(`${t} 1`)}
export function settlePick(m:Match,p:Pick,r?:FixtureResult):ResultStatus{if(!r)return 'PENDING';const a=norm(p.market),hg=r.homeScore,ag=r.awayScore,total=hg+ag;
 if(m.sport==='football'){
  if(a==='1x'||a.includes('double chance 1x'))return hg>=ag?'WON':'LOST';
  if(a==='x2'||a.includes('double chance x2'))return ag>=hg?'WON':'LOST';
  if(a==='12'||a.includes('home or away'))return hg!==ag?'WON':'LOST';
  if(a.includes('over 1 5'))return total>1.5?'WON':'LOST'; if(a.includes('over 2 5'))return total>2.5?'WON':'LOST'; if(a.includes('over 3 5'))return total>3.5?'WON':'LOST';
  if(a.includes('under 1 5'))return total<1.5?'WON':'LOST'; if(a.includes('under 2 5'))return total<2.5?'WON':'LOST'; if(a.includes('under 3 5'))return total<3.5?'WON':'LOST';
  if(a.includes('btts')||a.includes('both teams to score')||a==='gg')return hg>0&&ag>0?'WON':'LOST';
  if(a.includes('home team to score')||teamScored(p.market,m.home))return hg>0?'WON':'LOST';
  if(a.includes('away team to score')||teamScored(p.market,m.away))return ag>0?'WON':'LOST';
  if(a.includes('home win')||a==='1')return hg>ag?'WON':'LOST'; if(a.includes('away win')||a==='2')return ag>hg?'WON':'LOST'; if(a==='draw'||a==='x')return hg===ag?'WON':'LOST';
 }
 if(m.sport==='basketball'){
  const nums=[...p.market.matchAll(/(\d+(?:\.\d+)?)/g)].map(x=>Number(x[1]));const line=nums.at(-1);if(line!=null){if(a.includes(norm(m.home))&&a.includes('point'))return hg>=line?'WON':'LOST';if(a.includes(norm(m.away))&&a.includes('point'))return ag>=line?'WON':'LOST';if(a.includes('game total')||a.includes('total'))return a.includes('under')?(total<line?'WON':'LOST'):(total>=line?'WON':'LOST')}if(a.includes(norm(m.home))&&a.includes('winner'))return hg>ag?'WON':'LOST';if(a.includes(norm(m.away))&&a.includes('winner'))return ag>hg?'WON':'LOST';
 }
 if(m.sport==='tennis'){if(a.includes(norm(m.home))&&(a.includes('winner')||a.includes('match')))return hg>ag?'WON':'LOST';if(a.includes(norm(m.away))&&(a.includes('winner')||a.includes('match')))return ag>hg?'WON':'LOST';if(a.includes('under 2 5 set'))return total<2.5?'WON':'LOST';}
 return 'PENDING'}
export function getSettledMarkets():SettledMarket[]{const results=new Map(getResults().map(r=>[r.key,r]));const out:SettledMarket[]=[];for(const b of getBatches())for(const m of b.items){const r=results.get(fixtureKey(b.sport,m.home,m.away));for(const p of allMarkets(m)){const status=settlePick(m,p,r);out.push({key:`${b.id}|${m.id}|${p.market}`,batchId:b.id,matchId:m.id,sport:b.sport,home:m.home,away:m.away,market:p.market,tier:p.tier,isTop:p===m.top,consistency:p.consistency,neighbours:p.neighbours,publishedAt:b.publishedAt,homeScore:r?.homeScore,awayScore:r?.awayScore,scoreLabel:r?.scoreLabel,status,settledAt:r?.updatedAt})}}return out}
