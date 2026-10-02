import math
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

# F1-F5 are the frozen settings recovered from the research notes.
# F6/F7 thresholds are explicitly marked candidate until the original 2,225-match
# experiment is reproduced exactly.
CONFIG={
 'F1': {'label':'Favourite avoids defeat','features':'HDA','threshold':0.94},
 'F2': {'label':'1X','features':'HDA','threshold':0.92},
 'F3': {'label':'Favourite scores 1+','features':'D','threshold':0.96},
 'F4': {'label':'Home scores 1+','features':'HD','threshold':0.94},
 'F5': {'label':'X2','features':'pH','threshold':0.80},
 'F6': {'label':'Over 1.5 goals','features':'HDA','threshold':0.90,'candidate':True},
 'F7': {'label':'Under 3.5 goals','features':'pHD','threshold':0.80,'candidate':True},
 'S1': {'label':'Over 2.5 goals','features':'pHD','threshold':0.76,'submodel':True},
}

def enrich(df):
    df=df.copy()
    inv=np.column_stack([1/df.H,1/df.D,1/df.A]); p=inv/inv.sum(axis=1,keepdims=True)
    df['pH'],df['pD'],df['pA']=p[:,0],p[:,1],p[:,2]
    df['fav_home']=df.H<=df.A
    df['F1_y']=np.where(df.fav_home,df.hg>=df.ag,df.ag>=df.hg).astype(int)
    df['F2_y']=(df.hg>=df.ag).astype(int)
    df['F3_y']=np.where(df.fav_home,df.hg>=1,df.ag>=1).astype(int)
    df['F4_y']=(df.hg>=1).astype(int)
    df['F5_y']=(df.ag>=df.hg).astype(int)
    df['F6_y']=((df.hg+df.ag)>=2).astype(int)
    df['F7_y']=((df.hg+df.ag)<=3).astype(int)
    df['S1_y']=((df.hg+df.ag)>=3).astype(int)
    return df

def _X(df,features):
    if features=='HDA': return np.log(df[['H','D','A']].to_numpy(float))
    if features=='HD': return np.log(df[['H','D']].to_numpy(float))
    if features=='D': return np.log(df[['D']].to_numpy(float))
    if features=='pH': return df[['pH']].to_numpy(float)
    if features=='pHD': return df[['pH','pD']].to_numpy(float)
    raise ValueError(features)

class Scanner:
    def __init__(self,historical,k=50):
        self.df=enrich(historical.reset_index(drop=True)); self.k=min(k,len(self.df)); self.models={}
        for code,cfg in CONFIG.items():
            X=_X(self.df,cfg['features']); sc=StandardScaler().fit(X); Xs=sc.transform(X)
            nn=NearestNeighbors(n_neighbors=self.k).fit(Xs)
            self.models[code]=(sc,nn)
    def scan(self,fixtures):
        q=fixtures.copy(); inv=np.column_stack([1/q.H,1/q.D,1/q.A]); p=inv/inv.sum(axis=1,keepdims=True)
        q['pH'],q['pD'],q['pA']=p[:,0],p[:,1],p[:,2]
        out=[]
        for i,row in q.iterrows():
            hits=[]
            for code,cfg in CONFIG.items():
                one=pd.DataFrame([row]); X=_X(one,cfg['features']); sc,nn=self.models[code]
                inds=nn.kneighbors(sc.transform(X),return_distance=False)[0]
                score=float(self.df.iloc[inds][code+'_y'].mean())
                if score+1e-12>=cfg['threshold']:
                    if code=='F1': option='1X' if row.H<=row.A else 'X2'
                    elif code=='F3': option='Home team to score 1+' if row.H<=row.A else 'Away team to score 1+'
                    else: option={'F2':'1X','F4':'Home team to score 1+','F5':'X2','F6':'Over 1.5','F7':'Under 3.5','S1':'Over 2.5'}[code]
                    hits.append({'code':code,'option':option,'score':score,'neighbour_hits':round(score*self.k),'k':self.k,'threshold':cfg['threshold'],'candidate_formula':cfg.get('candidate',False),'tier':'SUB-MODEL' if cfg.get('submodel') else 'PRIMARY'})
            # dedupe actual markets; keep strongest score, retaining codes
            ded={}
            for h in hits:
                o=h['option']
                if o not in ded: ded[o]={**h,'codes':[h['code']]}
                else:
                    ded[o]['codes'].append(h['code'])
                    if h['score']>ded[o]['score']:
                        codes=ded[o]['codes']; ded[o]={**h,'codes':codes}
            opts=sorted(ded.values(),key=lambda x:x['score'],reverse=True)
            out.append({'home':row.home,'away':row.away,'H':row.H,'D':row.D,'A':row.A,'options':opts,'recommended':opts[0]['option'] if opts else None,'strength':opts[0]['score'] if opts else None})
        return out
