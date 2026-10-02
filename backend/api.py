from pathlib import Path
from dataclasses import asdict
import sys
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT=Path(__file__).parent
CORE=ROOT/'core'
sys.path.insert(0,str(CORE))
from parser import parse_text
from engine import Scanner
from basketball_parser import parse_basketball_text
from basketball_engine import BasketballScanner
from tennis_parser import parse_tennis_text
from tennis_engine import TennisScanner

app=FastAPI(title='QuantSport v10.8 Core API',version='10.8')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:3000','http://localhost:3001','http://127.0.0.1:3000','http://127.0.0.1:3001'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])

class ScanRequest(BaseModel):
    sport:str
    raw:str

football_hist=pd.read_csv(CORE/'historical.csv').rename(columns={'home_goals':'hg','away_goals':'ag'})
basket_hist=pd.read_csv(CORE/'basketball_historical.csv')
tennis_hist=pd.read_csv(CORE/'tennis_historical.csv')
football_scanner=Scanner(football_hist)
basket_scanner=BasketballScanner(basket_hist)
tennis_scanner=TennisScanner(tennis_hist)

def pick(option, top=False):
    public=option.get('public_selection') or option.get('option','')
    return {
        'market':public,
        'bookmakerMarket':option.get('bookmaker_market') or option.get('option',''),
        'consistency':round(float(option.get('score',0))*100),
        'neighbours':f"{option.get('neighbour_hits',0)} / {option.get('k',0)}",
        'tier':'HIGH MODEL' if top else ('SUB-MODEL' if option.get('tier')=='SUB-MODEL' else 'SUPPORTING'),
        'modelCode':option.get('code',''),
    }

def public_match(sport, r, idx, meta=None):
    opts=r.get('options',[])
    if not opts:return None
    top=pick(opts[0],True)
    support=[pick(o,False) for o in opts[1:]]
    odds=[str(r.get('H',''))]
    if sport=='football': odds += [str(r.get('D','')),str(r.get('A',''))]
    else: odds += [str(r.get('A',''))]
    return {'id':f'{sport}-{idx}-{abs(hash((r.get("home"),r.get("away"))))}', 'sport':sport,
            'league':(meta or {}).get('competition',''), 'time':(meta or {}).get('time',''),
            'home':r.get('home',''),'away':r.get('away',''),'odds':odds,'top':top,'support':support,
            'qualifiedMarkets':len(opts)}

@app.get('/health')
def health(): return {'ok':True,'engine':'v10.8 BOARD FINAL'}

@app.post('/scan')
def scan(req:ScanRequest):
    sport=req.sport.lower().strip(); raw=req.raw
    if not raw.strip(): raise HTTPException(400,'Paste fixture data first.')
    rejected=[]; parsed_count=0
    if sport=='football':
        matches,rejected=parse_text(raw); upcoming=[m for m in matches if m.status=='upcoming']; parsed_count=len(matches)
        if not upcoming:return {'sport':sport,'parsed':parsed_count,'upcoming':0,'qualified':0,'highModel':0,'supporting':0,'items':[],'rejected':rejected}
        df=pd.DataFrame([asdict(m) for m in upcoming])
        results=football_scanner.scan(df)
        metas=[{} for _ in results]
    elif sport=='basketball':
        matches,rejected=parse_basketball_text(raw); upcoming=[m for m in matches if m.status=='upcoming' and m.H and m.A and not m.is_3x3]; parsed_count=len(matches)
        if not upcoming:return {'sport':sport,'parsed':parsed_count,'upcoming':0,'qualified':0,'highModel':0,'supporting':0,'items':[],'rejected':rejected}
        df=pd.DataFrame([{'home':m.home,'away':m.away,'H':m.H,'A':m.A} for m in upcoming])
        results=basket_scanner.scan(df); metas=[{'competition':m.competition} for m in upcoming]
    elif sport=='tennis':
        matches,rejected=parse_tennis_text(raw); upcoming=[m for m in matches if m.status=='upcoming' and m.H and m.A]; parsed_count=len(matches)
        if not upcoming:return {'sport':sport,'parsed':parsed_count,'upcoming':0,'qualified':0,'highModel':0,'supporting':0,'items':[],'rejected':rejected}
        df=pd.DataFrame([{'player1':m.player1,'player2':m.player2,'H':m.H,'A':m.A} for m in upcoming])
        results=tennis_scanner.scan(df); metas=[{'competition':m.competition} for m in upcoming]
    else: raise HTTPException(400,'Unsupported sport')
    items=[]
    for i,(r,meta) in enumerate(zip(results,metas)):
        m=public_match(sport,r,i,meta)
        if m:items.append(m)
    return {'sport':sport,'engine':'v10.8 BOARD FINAL','parsed':parsed_count,'upcoming':len(upcoming),
            'qualified':len(items),'qualifiedMarkets':sum(1+len(x['support']) for x in items),
            'highModel':len(items),'supporting':sum(len(x['support']) for x in items),'items':items,'rejected':rejected[:100]}
