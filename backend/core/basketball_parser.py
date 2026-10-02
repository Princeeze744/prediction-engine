import re, hashlib
from dataclasses import dataclass
@dataclass
class BasketballMatch:
    match_id:str|None; home:str; away:str; home_points:int|None; away_points:int|None; H:float|None; A:float|None; status:str; competition:str; gender:str; is_3x3:bool; overtime:bool; raw:str
ID_RE=re.compile(r'flashscore\.mobi/match/([^/?\s]+)',re.I)
SCORE_MD=re.compile(r'\[\*\*\s*(\d+)\s*-\s*(\d+)\s*(ot)?\s*\*\*\]',re.I)
SCORE_PLAIN=re.compile(r'(?<![\d.])(\d{1,3})\s*-\s*(\d{1,3})(?:\s*(OT|AOT))?(?![\d.])',re.I)
ODD_MD=re.compile(r'\[\s*\*{0,2}(\d+(?:\.\d+)?)\*{0,2}\s*\]\(')
ODD_PLAIN=re.compile(r'\[\s*(\d+(?:\.\d+)?)\s*\|\s*(\d+(?:\.\d+)?)\s*\]')
BAD=re.compile(r'(?i)(?:^|\b)(Postponed|Cancelled|Canceled|Abandoned|Interrupted|Suspended|Delayed)(?=\b|[A-Z])')
LIVE=re.compile(r'^\s*(?:\d+(?:st|nd|rd|th)\s+Quarter|Q[1-4]\b|Half\s*Time|HT\b|OT\b)',re.I)
TIME=re.compile(r'^\s*\d{1,2}:\d{2}\s*')
def _odds(s):
    m=ODD_PLAIN.search(s)
    if m:return float(m.group(1)),float(m.group(2))
    a=[float(x) for x in ODD_MD.findall(s)]; return (a[0],a[1]) if len(a)>=2 else (None,None)
def _score(s):
    m=SCORE_MD.search(s)
    if m:return int(m.group(1)),int(m.group(2)),bool(m.group(3))
    z=ODD_PLAIN.sub('',s); m=SCORE_PLAIN.search(z)
    return (int(m.group(1)),int(m.group(2)),bool(m.group(3))) if m else None
def _teams(s,score):
    z=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',s).replace('**',''); z=TIME.sub('',z); z=ODD_PLAIN.sub('',z)
    z=re.sub(r'\[\s*\d+(?:\.\d+)?\s*\]\([^)]*\)','',z)
    if score:z=re.sub(rf'\b{score[0]}\s*-\s*{score[1]}(?:\s*(?:OT|AOT))?\b','',z,flags=re.I)
    z=re.sub(r'\[\s*-\s*\]','',z).strip(' -'); p=re.split(r'\s+-\s+',z,maxsplit=1)
    if len(p)!=2:return None,None
    return p[0].strip(),p[1].strip(' -')
def parse_basketball_text(text):
    comp='Unknown'; out=[]; rejected=[]
    for ln,line in enumerate(text.splitlines(),1):
        raw=line.rstrip(); st=raw.strip()
        if not st:continue
        if st.startswith('#### '):comp=st[5:].strip();continue
        # Headings usually contain ':' and no time/odds/score.
        if ':' in st and not TIME.search(st) and not ODD_PLAIN.search(st) and not ID_RE.search(st):comp=st;continue
        # Flashscore browser copies can concatenate status and team, e.g. 'PostponedBuducnost'.
        status_probe=TIME.sub('',raw).lstrip()
        if BAD.search(status_probe):rejected.append({'line':ln,'reason':'nonstandard_status','raw':raw});continue
        if LIVE.search(raw):rejected.append({'line':ln,'reason':'live','raw':raw});continue
        H,A=_odds(raw); sc=_score(raw); has_time=bool(TIME.search(raw))
        if sc:status='completed';hp,ap,ot=sc
        elif has_time and H is not None and A is not None:status='upcoming';hp=ap=None;ot=False
        else:
            if ' - ' in raw:rejected.append({'line':ln,'reason':'missing_odds_or_status','raw':raw})
            continue
        home,away=_teams(raw,sc)
        if not home or not away:rejected.append({'line':ln,'reason':'teams_not_detected','raw':raw});continue
        m=ID_RE.search(raw); mid=m.group(1) if m else 'plain-'+hashlib.sha1(f'{comp}|{home}|{away}|{raw}'.encode()).hexdigest()[:16]
        low=(comp+' '+raw).lower(); is3='3x3' in low or '3 x 3' in low; gender='Women' if ('women' in low or re.search(r'\bW\b',raw)) else 'Men/Other'
        out.append(BasketballMatch(mid,home,away,hp,ap,H,A,status,comp,gender,is3,ot,raw))
    return out,rejected
