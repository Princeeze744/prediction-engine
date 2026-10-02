import type {Match} from './data';
export type ScanResult={sport:string;engine?:string;parsed:number;upcoming:number;qualified:number;qualifiedMarkets?:number;highModel:number;supporting:number;items:Match[];rejected:any[]};
export async function scanWithCore(sport:string,raw:string):Promise<ScanResult>{
 const base=process.env.NEXT_PUBLIC_QUANTSPORT_CORE_URL || 'http://127.0.0.1:8000';
 const res=await fetch(`${base}/scan`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sport,raw})});
 if(!res.ok){let msg='QuantSport Core scan failed';try{const x=await res.json();msg=x.detail||msg}catch{};throw new Error(msg)}
 return res.json();
}
