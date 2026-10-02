import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

# Frozen candidate definitions recovered from Basketball Batch 001 research.
# These are empirical historical-neighbour consistency fingerprints, NOT calibrated probabilities.
CONFIG = {
    'B1': {'label':'Favourite 70+ points','features':'pFav_overround','k':40,'threshold':0.975,'status':'FORWARD TEST'},
    'B2': {'label':'Underdog margin <25','features':'pFav','k':75,'threshold':0.986667,'status':'FORWARD TEST'},
    'B3': {'label':'Total 140+ points','features':'pH_overround','k':50,'threshold':0.94,'status':'FORWARD TEST'},
    'B4': {'label':'Favourite 75+ points','features':'pFav_overround','k':50,'threshold':0.90,'status':'FORWARD TEST'},
    'B5': {'label':'Total 150+ points','features':'pH_overround','k':100,'threshold':0.77,'status':'FORWARD TEST'},
    'B6': {'label':'Total 160+ points','features':'logratio_overround','k':50,'threshold':0.74,'status':'FORWARD TEST'},
    'B7': {'label':'Underdog margin <20','features':'raw_odds','k':50,'threshold':0.96,'status':'FORWARD TEST'},
}

def enrich(df):
    d=df.copy()
    inv=np.column_stack([1/d.H.astype(float),1/d.A.astype(float)])
    over=inv.sum(axis=1); p=inv/over[:,None]
    d['pH'],d['pA'],d['overround']=p[:,0],p[:,1],over
    d['pFav']=np.maximum(d.pH,d.pA); d['home_fav']=d.H<=d.A
    fav=np.where(d.home_fav,d.hp,d.ap); dog=np.where(d.home_fav,d.ap,d.hp)
    favmargin=fav-dog
    d['B1_y']=(fav>=70).astype(int)
    d['B2_y']=(favmargin<25).astype(int)
    d['B3_y']=((d.hp+d.ap)>=140).astype(int)
    d['B4_y']=(fav>=75).astype(int)
    d['B5_y']=((d.hp+d.ap)>=150).astype(int)
    d['B6_y']=((d.hp+d.ap)>=160).astype(int)
    d['B7_y']=(favmargin<20).astype(int)
    return d

def _features(d, name):
    H=d.H.to_numpy(float); A=d.A.to_numpy(float)
    inv=np.column_stack([1/H,1/A]); over=inv.sum(axis=1); p=inv/over[:,None]
    pH=p[:,0]; pFav=np.maximum(p[:,0],p[:,1])
    if name=='pFav_overround': return np.column_stack([pFav,over])
    if name=='pFav': return pFav.reshape(-1,1)
    if name=='pH_overround': return np.column_stack([pH,over])
    if name=='logratio_overround': return np.column_stack([np.log(A/H),over])
    if name=='raw_odds': return np.column_stack([H,A])
    raise ValueError(name)

def _public_translation(code,row):
    home_fav=float(row.H)<=float(row.A)
    fav=row.home if home_fav else row.away
    dog=row.away if home_fav else row.home
    if code=='B1': return f'{fav} 70+ points', f'{fav} team total — Over 69.5', 'Favourite scores at least 70 points.'
    if code=='B4': return f'{fav} 75+ points', f'{fav} team total — Over 74.5', 'Favourite scores at least 75 points.'
    if code=='B3': return 'Game total 140+ points', 'Game total — Over 139.5', 'Both teams combine for at least 140 points.'
    if code=='B5': return 'Game total 150+ points', 'Game total — Over 149.5', 'Both teams combine for at least 150 points.'
    if code=='B6': return 'Game total 160+ points', 'Game total — Over 159.5', 'Both teams combine for at least 160 points.'
    if code=='B2': return f'{dog} +24.5', f'{dog} handicap +24.5', 'Underdog wins outright or loses by 24 points or fewer.'
    if code=='B7': return f'{dog} +19.5', f'{dog} handicap +19.5', 'Underdog wins outright or loses by 19 points or fewer.'
    return CONFIG[code]['label'],CONFIG[code]['label'],''

class BasketballScanner:
    def __init__(self,historical,k=50):
        self.raw_count=len(historical)
        h=historical.copy()
        h=h[(h.H>1)&(h.A>1)&h.hp.notna()&h.ap.notna()].copy()
        if 'is_3x3' in h.columns: h=h[~h.is_3x3.astype(str).str.lower().isin(['true','1'])]
        # Exclude administrative/forfeit-like 0-20 rows from model reference.
        h=h[~(((h.hp==0)&(h.ap==20))|((h.hp==20)&(h.ap==0)))]
        self.df=enrich(h.reset_index(drop=True)); self.k=k; self.models={}
        for code,cfg in CONFIG.items():
            kk=min(cfg['k'],len(self.df)); X=_features(self.df,cfg['features']); sc=StandardScaler().fit(X)
            nn=NearestNeighbors(n_neighbors=kk).fit(sc.transform(X)); self.models[code]=(sc,nn,kk)
    def scan(self,fixtures):
        out=[]
        for _,row in fixtures.iterrows():
            hits=[]
            one=pd.DataFrame([row])
            for code,cfg in CONFIG.items():
                sc,nn,kk=self.models[code]; inds=nn.kneighbors(sc.transform(_features(one,cfg['features'])),return_distance=False)[0]
                score=float(self.df.iloc[inds][code+'_y'].mean())
                if score+1e-12>=cfg['threshold']:
                    public,bookmaker,explanation=_public_translation(code,row)
                    hits.append({'code':code,'codes':[code],'option':cfg['label'],'public_selection':public,'bookmaker_market':bookmaker,'explanation':explanation,'score':score,'neighbour_hits':int(self.df.iloc[inds][code+'_y'].sum()),'k':kk,'threshold':cfg['threshold'],'tier':'PRIMARY','status':cfg['status']})
            hits.sort(key=lambda x:(x['score'],x['neighbour_hits']/x['k']),reverse=True)
            out.append({'home':row.home,'away':row.away,'H':row.H,'A':row.A,'options':hits,'recommended':hits[0]['option'] if hits else None,'strength':hits[0]['score'] if hits else None})
        return out
