'use client';
import {useEffect,useState} from 'react';
export type Leg={fid:number;kickoff?:string;match:string;league?:string;pick:string;model:string;odds:number;status?:string;score?:string;ht?:string};
export type Ticket={no:number;tier:string;target:number;odds:number;reached:boolean;repeats:boolean;legs:Leg[];status?:string;lost_legs?:number};
export type DaySet={date:string;created:string;tickets:Ticket[]};
export type Rec={tickets?:number;picks?:number;won?:number;hit?:number;avg_odds?:number;roi?:number};
export type FreePick={option:string;cat:string;consistency:number;neighbours:string;odds:number|null;status?:string};
export type FreeItem={fid:number;home:string;away:string;league:string;kickoff:string;odds:number[];picks:FreePick[];score?:string};
export type FreeDay={date:string;created:string;items:FreeItem[]};
export type NDItem={fid:number;tier:string;home:string;away:string;league:string;kickoff:string;fav:number;o25:number;odds:number;score?:string;status?:string;fav_side?:string;o15?:number|null;o15_status?:string;fav_status?:string};
export type NDDay={date:string;created:string;items:NDItem[];companions_added?:string};
export type NDOpt='nd'|'o15'|'fav';
export const ndOf=(it:NDItem,o:NDOpt)=>o==='o15'?{pick:'Over 1.5 goals',odds:it.o15??null,status:it.o15_status}:o==='fav'?{pick:`${it.fav_side==='Away'?it.away:it.home} to win`,odds:it.fav_side?it.fav:null,status:it.fav_status}:{pick:'Home or Away (12)',odds:it.odds as number|null,status:it.status};
export type XRec={picks:number;won:number;hit:number|null;avg_odds:number|null};
export type Special=Ticket&{model:string;sporty:string;record:{hit:number;picks:number;avg_odds:number}};
export type NDTier={tier:string;rule:string;picks:number;won:number;hit:number;avg_odds:number;found:number|null;unseen:number|null;per_day:number;worst_day:number};
export type DareLeg=Leg&{model:string};
export type DareModel={id:string;name:string;sporty:string;why:string;test:{picks:number;hit:number;avg_odds:number;roi:number};live:{picks:number;won:number;hit:number;avg_odds:number;profit:number;roi:number}|null};
export type Data={generated:string;
 dare?:{models:DareModel[];history:{date:string;created:string;picks:DareLeg[]}[];started:string|null};
 nodraw?:{tiers:NDTier[];today:NDDay|null;history:NDDay[];live:Record<string,Rec>;extras?:Record<string,{over15:XRec;favwin:XRec}>};
 specials?:{today:{date:string;created:string;tickets:Special[];backfilled?:string}|null;history:{date:string;created:string;tickets:Special[];backfilled?:string}[];live:Record<string,{name:string;tickets:number;won:number}>;target:number};
 daily10:{today:DaySet|null;history:DaySet[];live:Record<string,Rec>;backtest:Record<string,Rec>;tiers:{tier:string;target:number;count:number}[];by_model?:{id:string;name:string;sporty:string;picks:number;won:number;hit:number}[]};
 free:{cats:string[];today:FreeDay|null;history:FreeDay[];live:Record<string,Rec>;backtest:Record<string,Rec>};
 tickets:Record<string,{record:Rec}>};
export const planOf:Record<string,string>={'3 odds':'Mix 3 odds','5 odds':'Mix 5 odds','10 odds':'Mix 10 odds','20 odds':'Mix 20 odds'};
export const kick=(k?:string)=>{if(!k)return '';const d=new Date(k);return isNaN(d.getTime())?k:d.toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',hour12:false})};
export const niceDate=(s?:string)=>{if(!s)return '';const d=new Date(s+'T12:00:00');return isNaN(d.getTime())?s:d.toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'long'})};
/* The data file is fetched once and shared by every page, so moving between pages is instant. It refreshes itself every 2 minutes. */
let cache:Data|null=null,at=0,pending:Promise<Data>|null=null;
const load=()=>pending||(pending=fetch('/research/models.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('not published yet');return r.json()}).then((d:Data)=>{cache=d;at=Date.now();return d}).finally(()=>{pending=null}));
export function useData(){const [data,setData]=useState<Data|null>(cache),[err,setErr]=useState('');
 useEffect(()=>{let live=true;if(!cache||Date.now()-at>120000)load().then(d=>{if(live)setData(d)}).catch(e=>{if(live&&!cache)setErr(String(e.message||e))});return()=>{live=false}},[]);
 return {data,err}}

export const catLabel=(c:string)=>({'TOP FINGERPRINT':'Top pick','HOME 1+':'Home 1+','AWAY 1+':'Away 1+','OVER 1.5':'Over 1.5','OVER 2.5':'Over 2.5','UNDER 3.5':'Under 3.5','1X':'1X','X2':'X2'} as Record<string,string>)[c]||c;
