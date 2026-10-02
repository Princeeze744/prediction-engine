import {fixtureKey,type FixtureResult,type PublishedBatch,norm} from './storage';
export type ParseSummary={matched:FixtureResult[];unmatched:string[];ignored:string[]};
const scorePatterns=[/^(.*?)\s+(\d+)\s*[-–—:]\s*(\d+)\s+(.*?)$/,/^(.*?)\s+vs\.?\s+(.*?)\s+(\d+)\s*[-–—:]\s*(\d+)$/i];
export function parseResults(raw:string,sport:string,batches:PublishedBatch[]):ParseSummary{const fixtures=batches.filter(b=>b.sport===sport).flatMap(b=>b.items);const matched:FixtureResult[]=[],unmatched:string[]=[],ignored:string[]=[];const lines=raw.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
 for(const line of lines){let home='',away='',hs=NaN,as=NaN;let m=line.match(scorePatterns[0]);if(m){home=m[1].trim();hs=+m[2];as=+m[3];away=m[4].trim()}else{m=line.match(scorePatterns[1]);if(m){home=m[1].trim();away=m[2].trim();hs=+m[3];as=+m[4]}}
  if(!home||!away||!Number.isFinite(hs)||!Number.isFinite(as)){ignored.push(line);continue}
  const nh=norm(home),na=norm(away);const f=fixtures.find(x=>(norm(x.home)===nh&&norm(x.away)===na)||(norm(x.home)===na&&norm(x.away)===nh));if(!f){unmatched.push(line);continue}
  const reversed=norm(f.home)===na&&norm(f.away)===nh;const homeScore=reversed?as:hs,awayScore=reversed?hs:as;matched.push({key:fixtureKey(sport,f.home,f.away),sport,home:f.home,away:f.away,homeScore,awayScore,scoreLabel:`${homeScore}–${awayScore}`,updatedAt:new Date().toISOString()})
 }
 return {matched,unmatched,ignored}}
