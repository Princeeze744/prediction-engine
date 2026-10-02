"""Tennis Research Engine 001. Not production/VIP. Clean singles only.
Architecture chosen on older uploaded period; thresholds are 90th-percentile OOF scores there;
newer uploaded period is a limited temporal holdout, already inspected, so future data is the true prospective test.
"""
import numpy as np,pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
CONFIG={
 'T1':{'label':'Favourite match winner','features':'raw','k':40,'threshold':0.875,'older_hit':'28/31','newer_hit':'11/14','status':'RESEARCH'},
 'T2':{'label':'Straight sets (2-0 either player)','features':'pFav','k':20,'threshold':0.95,'older_hit':'26/29','newer_hit':'9/11','status':'RESEARCH'},
 'T3':{'label':'Favourite 2-0','features':'pFav','k':100,'threshold':0.72,'older_hit':'38/46','newer_hit':'14/19','status':'RESEARCH'},
 'T4':{'label':'Favourite wins at least one set','features':'pFav','k':50,'threshold':0.92,'older_hit':'76/84','newer_hit':'33/39','status':'RESEARCH'},
}
def enrich(d):
 d=d.copy(); inv=np.c_[1/d.H,1/d.A]; p=inv/inv.sum(1)[:,None]; d['p1'],d['p2']=p[:,0],p[:,1]; d['pFav']=np.max(p,axis=1); d['fav1']=d.H<d.A
 fs=np.where(d.fav1,d.s1,d.s2); ds=np.where(d.fav1,d.s2,d.s1)
 d['T1_y']=np.where(d.fav1,d.s1>d.s2,d.s2>d.s1).astype(int); d['T2_y']=((d.s1+d.s2)==2).astype(int); d['T3_y']=((fs==2)&(ds==0)).astype(int); d['T4_y']=(fs>=1).astype(int)
 return d
def _x(d,f):
 if f=='raw': return np.log(d[['H','A']].to_numpy(float))
 if f=='pFav':
  inv=np.c_[1/d.H,1/d.A]; p=inv/inv.sum(1)[:,None]; return np.max(p,axis=1).reshape(-1,1)
 raise ValueError(f)
class TennisScanner:
 def __init__(self,historical):
  self.df=enrich(historical.reset_index(drop=True)); self.models={}
  for code,c in CONFIG.items():
   x=_x(self.df,c['features']); sc=StandardScaler().fit(x); kk=min(c['k'],len(self.df)); nn=NearestNeighbors(n_neighbors=kk).fit(sc.transform(x)); self.models[code]=(sc,nn,kk)
 def scan(self,fixtures):
  out=[]
  for _,r in fixtures.iterrows():
   hits=[]; one=pd.DataFrame([r]); fav=r.player1 if r.H<r.A else r.player2
   for code,c in CONFIG.items():
    sc,nn,k=self.models[code]; ii=nn.kneighbors(sc.transform(_x(one,c['features'])),return_distance=False)[0]; score=float(self.df.iloc[ii][code+'_y'].mean())
    if score+1e-12>=c['threshold']:
     if code=='T1': public=f'{fav} to win'; book='Match winner'
     elif code=='T2': public='Straight sets'; book='Total sets — Under 2.5'
     elif code=='T3': public=f'{fav} 2-0'; book='Correct set score — favourite 2-0'
     else: public=f'{fav} to win a set'; book=f'{fav} to win at least one set'
     hits.append({'code':code,'option':c['label'],'public_selection':public,'bookmaker_market':book,'score':score,'neighbour_hits':int(round(score*k)),'k':k,'tier':'TENNIS RESEARCH','status':'RESEARCH'})
   hits.sort(key=lambda z:z['score'],reverse=True); out.append({'home':r.player1,'away':r.player2,'H':r.H,'A':r.A,'options':hits})
  return out
