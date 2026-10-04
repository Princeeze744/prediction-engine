"""
QuantSport - 10 candidate market models (competition build).

Reads the collector data and writes public/research/models.json for the page /admin/models.

  RECORD  : odds_all.csv + fixtures.csv   (matches already played; prices captured ~1h before kick-off)
  TODAY   : prematch/oddsall_<date>.csv + prematch/fixtures_<date>.csv  (upcoming matches -> today's picks)

Every model is a fixed rule: a match condition (from the 1X2 / Over 2.5 prices) + one market selection.
Rules were found on 25-26 Sep and re-tested on 27-30 Sep. They are CANDIDATES, not proven edges.

Run from the v22 folder:   python tools\\build_models.py
"""
import json, os, re, glob, sys
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(os.environ.get('QS_DATA', Path.home() / 'Documents' / 'QuantSport_Data'))
OUT = Path(__file__).resolve().parent.parent / 'public' / 'research' / 'models.json'
SPLIT = '2026-09-26'   # rules were discovered on days <= SPLIT; later days are the unseen test

MODELS = [
 dict(id='M1', name='Away Favourite Wins a Half', sporty='Away Team to Win Either Half - Yes',
      why='Away favourites were under-priced this period; they usually win at least one half.',
      cond={'favS': 'awayFav'}, market='To Win Either Half', selection='Away'),
 dict(id='M2', name='Away Favourite Second-Half Goal', sporty='2nd Half - Away Team Over 0.5',
      why='In balanced-looking games with an away favourite, the away side tends to score after the break.',
      cond={'favS': 'awayFav', 'drawB': 'X3.3-3.7'}, market='Away Team Total Goals(2nd Half)', selection='Over 0.5'),
 dict(id='M3', name='Slow-Start Favourite: Half-Time Draw', sporty='1st Half - 1X2 - Draw',
      why='Strong favourites (1.25-1.45) often take time to break teams down; level at the break more than priced.',
      cond={'favB': 'fav1.25-1.45'}, market='First Half Winner', selection='Draw'),
 dict(id='M4', name='Goal-Rich First Half', sporty='1st Half - Over 1 (stake back on exactly 1 goal)',
      why='Senior games with a mid-range draw price produced more first-half goals than the price implied.',
      cond={'drawB': 'X3.3-3.7', 'cat': 'senior'}, market='Goals Over/Under First Half', selection='Over 1.0'),
 dict(id='M5', name='Home Scores Before the Break', sporty='1st Half - Home Team Over 0.5',
      why='League games priced for goals (Over 2.5 at 1.55-1.80): the home side scores early more than priced.',
      cond={'o25B': 'O2.5@1.55-1.80', 'comp': 'league'}, market='Home Team Total Goals(1st Half)', selection='Over 0.5'),
 dict(id='M6', name='Home Favourite Unbeaten at Half-Time', sporty='1st Half - Double Chance - Home or Draw',
      why='High hit-rate pick: home favourites in goal-priced games rarely trail at the break.',
      cond={'favS': 'homeFav', 'o25B': 'O2.5@1.55-1.80'}, market='Asian Handicap First Half', selection='Home +0.5'),
 dict(id='M7', name='Away Team Even Goals', sporty='Away Team Odd/Even - Even',
      why='In tighter league games the away side scores 0 or 2 more often than the even price implies.',
      cond={'o25B': 'O2.5@1.80-2.10', 'comp': 'league'}, market='Away Odd/Even', selection='Even'),
 dict(id='M8', name='Open Game Over 2.5', sporty='Over/Under - Over 2.5',
      why='Away favourite plus a short draw price: bookmakers price a cagey game, results were open.',
      cond={'favS': 'awayFav', 'drawB': 'X<3.3'}, market='Goals Over/Under', selection='Over 2.5'),
 dict(id='M9', name='Away Blank in First Half', sporty='1st Half - Away Team Under 0.5',
      why='High hit-rate pick: against clear home favourites (draw 4.3+), the away side rarely scores before the break.',
      cond={'favS': 'homeFav', 'drawB': 'X4.3+'}, market='Away Team Total Goals(1st Half)', selection='Under 0.5'),
 dict(id='M10', name='Away Favourite Scores in Both Halves', sporty='Away Team to Score in Both Halves - Yes',
      why='Higher-odds value pick from the same away-favourite pattern.',
      cond={'favS': 'awayFav'}, market='To Score In Both Halves By Teams', selection='Away'),
]

HIGH_HIT = [
 dict(id='H1', group='HIGH HIT', name='Away Favourite +2 Start', sporty='Handicap 0:2 - Away (0:2)',
      why='The away side is the favourite and also gets a 2-goal head start: it only loses if the home team wins by 3 or more.',
      cond={'favS': 'awayFav', 'cat': 'senior'}, market='Handicap Result', selection='Away -2'),
 dict(id='H2', group='HIGH HIT', name='Home Team Under 3.5 Goals', sporty='Home Team Over/Under - Under 3.5',
      why='Slight home favourites (2.00-2.40) almost never score four.',
      cond={'favB': 'fav2.00-2.40', 'favS': 'homeFav'}, market='Total - Home', selection='Under 3.5'),
 dict(id='H3', group='HIGH HIT', name='Away Team Under 3.5 Goals', sporty='Away Team Over/Under - Under 3.5',
      why='Senior games with a draw price of 3.7-4.3: the away side rarely reaches four goals.',
      cond={'drawB': 'X3.7-4.3', 'cat': 'senior'}, market='Total - Away', selection='Under 3.5'),
 dict(id='H4', group='HIGH HIT', name='Home Will Not Win to Nil', sporty='Home Team to Win to Nil - No',
      why='When the away side is favourite, the home team rarely wins without conceding.',
      cond={'favS': 'awayFav', 'cat': 'senior'}, market='Win to Nil - Home', selection='No'),
 dict(id='H5', group='HIGH HIT', name='Second Half Under 3.5', sporty='2nd Half - Over/Under - Under 3.5',
      why='Home favourite in a balanced-price game: four second-half goals almost never happen.',
      cond={'favS': 'homeFav', 'drawB': 'X3.3-3.7'}, market='Goals Over/Under - Second Half', selection='Under 3.5'),
 dict(id='H6', group='HIGH HIT', name='At Least One Goal', sporty='Over/Under - Over 0.5',
      why='Slight home favourites: goalless games are rare.',
      cond={'favB': 'fav2.00-2.40', 'favS': 'homeFav'}, market='Goals Over/Under', selection='Over 0.5'),
 dict(id='H7', group='HIGH HIT', name='Away Under 1.5 in First Half', sporty='1st Half - Away Team Under 1.5',
      why='Even in games priced for goals, the away side rarely scores twice before the break.',
      cond={'o25B': 'O2.5@1.55-1.80'}, market='Away Team Total Goals(1st Half)', selection='Under 1.5'),
 dict(id='H8', group='HIGH HIT', name='Second-Half Goal', sporty='2nd Half - Over/Under - Over 0.5',
      why='Away favourite in a high-scoring game (Over 2.5 under 1.55): a second-half goal is close to certain.',
      cond={'favS': 'awayFav', 'o25B': 'O2.5@<1.55'}, market='Goals Over/Under - Second Half', selection='Over 0.5'),
 dict(id='H9', group='HIGH HIT', name='Not Both Teams Scoring in Both Halves', sporty='Both Teams to Score in Both Halves - No',
      why='Even in high-scoring league games, both teams scoring in each half is rare.',
      cond={'o25B': 'O2.5@<1.55', 'comp': 'league'}, market='Both Teams To Score in Both Halves', selection='No'),
 dict(id='H10', group='HIGH HIT', name='No Draw: Heavy Favourite, Goals Expected', sporty='Double Chance - Home or Away (12)',
      why='A heavy favourite (under 1.25) in a game priced for goals (Over 2.5 under 1.55) very rarely ends level.',
      cond={'favB': 'fav<1.25', 'o25B': 'O2.5@<1.55'}, market='Double Chance', selection='Home/Away'),
]
ACCA = [
 dict(id='A1', group='ACCA 1.20-1.50', name='Away Favourite Scores', sporty='Home Team Clean Sheet - No',
      why='When the away side is the favourite (senior game), it scores in almost nine games out of ten.',
      cond={'favS': 'awayFav', 'cat': 'senior'}, market='Clean Sheet - Home', selection='No'),
 dict(id='A2', group='ACCA 1.20-1.50', name='Home Favourite Not Behind at Half-Time', sporty='1st Half - Double Chance - Home or Draw',
      why='Home favourites in goal-priced games rarely trail at the break.',
      cond={'favS': 'homeFav', 'o25B': 'O2.5@1.55-1.80'}, market='Asian Handicap First Half', selection='Home +0.5'),
 dict(id='A3', group='ACCA 1.20-1.50', name='Underdog Will Not Score in Both Halves', sporty='Away Team to Score in Both Halves - No',
      why='Against a strong favourite (1.25-1.45) in league play, the away side rarely scores in each half.',
      cond={'favB': 'fav1.25-1.45', 'comp': 'league'}, market='Away team will score in both halves', selection='No'),
 dict(id='A4', group='ACCA 1.20-1.50', name='No First-Half GG', sporty='1st Half - GG/NG - No',
      why='One-sided games (draw 4.3+) priced for goals: both teams scoring before the break is uncommon.',
      cond={'drawB': 'X4.3+', 'o25B': 'O2.5@<1.55'}, market='Both Teams Score - First Half', selection='No'),
 dict(id='A5', group='ACCA 1.20-1.50', name='Away Favourite X2', sporty='Double Chance - Draw or Away',
      why='Away favourite in a tighter game (Over 2.5 at 1.80-2.10): rarely loses.',
      cond={'favS': 'awayFav', 'o25B': 'O2.5@1.80-2.10'}, market='Double Chance', selection='Draw/Away'),
 dict(id='A6', group='ACCA 1.20-1.50', name='Home Favourite 1X', sporty='Double Chance - Home or Draw',
      why='Home favourite with a draw price of 3.7-4.3: rarely loses.',
      cond={'favS': 'homeFav', 'drawB': 'X3.7-4.3'}, market='Asian Handicap', selection='Home +0.5'),
 dict(id='A7', group='ACCA 1.20-1.50', name='Away Favourite +1 Start', sporty='Handicap 0:1 - Away (0:1)',
      why='Away favourite with a one-goal head start in a tighter game.',
      cond={'favS': 'awayFav', 'o25B': 'O2.5@1.80-2.10'}, market='Handicap Result', selection='Away -1'),
 dict(id='A8', group='ACCA 1.20-1.50', name='Cup Game Over 1.5', sporty='Over/Under - Over 1.5',
      why='Cup ties with a home favourite produce at least two goals more often than priced.',
      cond={'favS': 'homeFav', 'comp': 'cup'}, market='Goals Over/Under', selection='Over 1.5'),
 dict(id='A9', group='ACCA 1.20-1.50', name='Home Team Scores', sporty='Away Team Clean Sheet - No',
      why='League games priced for goals (Over 2.5 at 1.55-1.80): the home side nearly always scores.',
      cond={'o25B': 'O2.5@1.55-1.80', 'comp': 'league'}, market='Clean Sheet - Away', selection='No'),
 dict(id='A10', group='ACCA 1.20-1.50', name='No First-Half GG (Home Favourite)', sporty='1st Half - GG/NG - No',
      why='Home favourite in a high-scoring game: both teams scoring before the break is still uncommon.',
      cond={'favS': 'homeFav', 'o25B': 'O2.5@<1.55'}, market='Both Teams Score - First Half', selection='No'),
]
for _m in MODELS:
    _m['group'] = 'VALUE'
# NEW (4 Oct): the next five, found by the same search (9,814 market/condition pairs, each checked on first days vs later unseen days).
NEW = [
 dict(id='S1', group='NEW', name='Home +2 Start in an Even Game', sporty='Handicap 2:0 - Home (2:0)',
      why='When neither side is a strong favourite (favourite at 1.70-2.00), the home team with a two-goal head start very rarely loses.',
      cond={'favB': 'fav1.70-2.00'}, market='Handicap Result', selection='Home +2'),
 dict(id='S2', group='NEW', name='Quiet First Half', sporty='1st Half - Over/Under - Under 2.5',
      why='Away favourite with a draw price of 3.7-4.3: three first-half goals are rare.',
      cond={'favS': 'awayFav', 'drawB': 'X3.7-4.3'}, market='Goals Over/Under First Half', selection='Under 2.5'),
 dict(id='S3', group='NEW', name='Home Favourite +1 at Half-Time', sporty='1st Half - Handicap 1:0 - Home (1:0)',
      why='Home favourite in a fairly open game: with a one-goal start it is almost never behind at the break.',
      cond={'favS': 'homeFav', 'o25B': 'O2.5@1.55-1.80'}, market='Handicap Result - First Half', selection='Home +1'),
 dict(id='S4', group='NEW', name='Away Team Under 2.5 Goals', sporty='Away Team Total - Under 2.5',
      why='League games with a very long draw price (4.3+): the away side scoring three is rarer than its price says.',
      cond={'drawB': 'X4.3+', 'comp': 'league'}, market='Total - Away', selection='Under 2.5'),
 dict(id='S5', group='NEW', name='Home Will Not Win Both Halves', sporty='Home To Win Both Halves - No',
      why='Even in high-scoring league games the home side seldom wins both halves.',
      cond={'o25B': 'O2.5@<1.55', 'comp': 'league'}, market='Home win both halves', selection='No'),
]
MODELS = HIGH_HIT + ACCA + MODELS + NEW


def ou(v, side, L):
    def one(l):
        r = 1.0 if v > l else 0.0 if v < l else 0.5
        return r if side == 'Over' else 1 - r
    if abs(L * 4 - round(L * 4)) < 1e-9 and abs(L * 2 - round(L * 2)) > 1e-9:
        return (one(L - 0.25) + one(L + 0.25)) / 2
    return one(L)


def res3(a, b):
    return 'Home' if a > b else 'Away' if b > a else 'Draw'


def settle(m, s, hg, ag, h1, a1):
    """1 = win, 0 = lose, 0.5 = stake back."""
    h2, a2 = hg - h1, ag - a1
    if m == 'To Win Either Half':
        return float((h1 > a1 or h2 > a2) if s == 'Home' else (a1 > h1 or a2 > h2))
    if m == 'To Score In Both Halves By Teams':
        return float((h1 > 0 and h2 > 0) if s == 'Home' else (a1 > 0 and a2 > 0))
    if m == 'Clean Sheet - Home':
        return float((ag == 0) == (s == 'Yes'))
    if m == 'Clean Sheet - Away':
        return float((hg == 0) == (s == 'Yes'))
    if m == 'Away team will score in both halves':
        return float((a1 > 0 and a2 > 0) == (s == 'Yes'))
    if m == 'Both Teams Score - First Half':
        return float((h1 > 0 and a1 > 0) == (s == 'Yes'))
    if m == 'Asian Handicap':
        side, h = s.split(' '); d = (hg - ag) + float(h)
        r = 1.0 if d > 0 else 0.0 if d < 0 else 0.5
        return r if side == 'Home' else 1 - r
    if m == 'Handicap Result':
        side, h = s.split(' ')
        return float(res3(hg + int(float(h)), ag) == side)
    if m == 'Handicap Result - First Half':
        side, h = s.split(' ')
        return float(res3(h1 + int(float(h)), a1) == side)
    if m == 'Home win both halves':
        return float((h1 > a1 and h2 > a2) == (s == 'Yes'))
    if m == 'Double Chance':
        return float(res3(hg, ag) in s.split('/'))
    if m == 'Win to Nil - Home':
        return float((hg > ag and ag == 0) == (s == 'Yes'))
    if m == 'Both Teams To Score in Both Halves':
        return float((h1 > 0 and a1 > 0 and h2 > 0 and a2 > 0) == (s == 'Yes'))
    if m == 'First Half Winner':
        return float(res3(h1, a1) == s)
    if m == 'Odd/Even' or m.endswith('Odd/Even'):
        v = {'Odd/Even': hg + ag, 'Home Odd/Even': hg, 'Away Odd/Even': ag}[m]
        return float((v % 2 == 1) == (s == 'Odd'))
    if m == 'Asian Handicap First Half':
        side, h = s.split(' '); d = (h1 - a1) + float(h)
        r = 1.0 if d > 0 else 0.0 if d < 0 else 0.5
        return r if side == 'Home' else 1 - r
    mo = re.match(r'(Over|Under) (\d+(?:\.\d+)?)$', s)
    if mo:
        v = {'Goals Over/Under': hg + ag, 'Goals Over/Under First Half': h1 + a1, 'Away Team Total Goals(2nd Half)': a2,
             'Goals Over/Under - Second Half': h2 + a2, 'Total - Home': hg, 'Total - Away': ag,
             'Home Team Total Goals(1st Half)': h1, 'Away Team Total Goals(1st Half)': a1}[m]
        return ou(v, mo.group(1), float(mo.group(2)))
    raise ValueError(f'no settlement rule for {m} / {s}')


def features(odds, names):
    """Match conditions from median 1X2 and Over 2.5 prices."""
    def med(m, s):
        return odds[(odds.market == m) & (odds.selection == s)].groupby('fixture_id').odd.median()
    fx = pd.DataFrame({'H': med('Match Winner', 'Home'), 'X': med('Match Winner', 'Draw'), 'A': med('Match Winner', 'Away'),
                       'O25': med('Goals Over/Under', 'Over 2.5')}).dropna(subset=['H', 'X', 'A'])
    fx = fx.join(names)
    fav = fx[['H', 'A']].min(axis=1)
    fx['favB'] = pd.cut(fav, [1, 1.25, 1.45, 1.7, 2.0, 2.4, 99], labels=['fav<1.25', 'fav1.25-1.45', 'fav1.45-1.70', 'fav1.70-2.00', 'fav2.00-2.40', 'fav2.40+']).astype(str)
    fx['favS'] = np.where(fx.H <= fx.A, 'homeFav', 'awayFav')
    fx['drawB'] = pd.cut(fx.X, [1, 3.3, 3.7, 4.3, 99], labels=['X<3.3', 'X3.3-3.7', 'X3.7-4.3', 'X4.3+']).astype(str)
    fx['o25B'] = pd.cut(fx.O25, [1, 1.55, 1.8, 2.1, 99], labels=['O2.5@<1.55', 'O2.5@1.55-1.80', 'O2.5@1.80-2.10', 'O2.5@2.10+']).astype(str)
    home = fx.home.astype(str); lg = fx.league.astype(str)
    fx['cat'] = np.where(home.str.contains(r' W$| Women', regex=True), 'women', np.where(home.str.contains(r'U\d\d', regex=True), 'youth', 'senior'))
    fx['comp'] = np.where(lg.str.contains('Friendl', case=False), 'friendly',
                          np.where(lg.str.contains('Cup|Copa|Coupe|Pokal|Coppa|Taca|Shield|Trophy', case=False), 'cup', 'league'))
    return fx


def model_rows(model, odds, fx):
    m = fx
    for k, v in model['cond'].items():
        m = m[m[k] == v]
    sels = [model['selection']] + {'Home/Draw': ['Draw/Home'], 'Home/Away': ['Away/Home'], 'Draw/Away': ['Away/Draw']}.get(model['selection'], [])
    o = odds[(odds.market == model['market']) & odds.selection.isin(sels) & odds.fixture_id.isin(m.index) & (odds.odd >= 1.02)]
    p = o.groupby('fixture_id').odd.agg(typical='median', best='max')
    return m.join(p, how='inner')


def pnl(odd, r):
    return odd - 1 if r == 1 else -1.0 if r == 0 else 0.0


VOID_IDS = set()


def settle_leg(l, r):
    """Settle one ticket leg from a result row. Works without a half-time score when the market does not depend on it."""
    hg, ag = int(r.ft_home), int(r.ft_away)
    if pd.notna(r.ht_home) and pd.notna(r.ht_away):
        return settle(l['market'], l['selection'], hg, ag, int(r.ht_home), int(r.ht_away)), f'{int(r.ht_home)}-{int(r.ht_away)}'
    vs = {settle(l['market'], l['selection'], hg, ag, h1, a1) for h1 in range(hg + 1) for a1 in range(ag + 1)}
    return (vs.pop() if len(vs) == 1 else 0.5), ''


def main():
    oa = DATA / 'odds_all.csv'
    if not oa.exists():
        oa = DATA / 'odds_all.csv.gz'          # compressed copy used by the cloud run
    if not oa.exists():
        sys.exit(f'odds_all.csv not found in {DATA} - run QS_Collect_AllMarkets.ps1 first')
    odds = pd.read_csv(oa).drop_duplicates(['fixture_id', 'bookmaker', 'market', 'selection'])
    odds = odds[pd.to_numeric(odds.odd, errors='coerce') > 1.0]
    fr = []
    if (DATA / 'live_results.csv').exists():          # same-day scores from refresh_results.py: freshest, so they come first
        lv = pd.read_csv(DATA / 'live_results.csv')
        fr.append(lv[lv.status.isin(['FT', 'AET', 'PEN'])])
        # matches that will not be played as scheduled: their picks are void (stake back), not pending for ever
        off = lv[lv.status.isin(['PST', 'CANC', 'ABD', 'AWD', 'WO']) & (lv.date.astype(str) < pd.Timestamp.now().strftime('%Y-%m-%d'))]
        VOID_IDS.update(int(i) for i in off.fixture_id)
    fr.append(pd.read_csv(DATA / 'fixtures.csv'))
    if (DATA / 'history.csv').exists():
        fr.append(pd.read_csv(DATA / 'history.csv'))
    fxt = pd.concat(fr).drop_duplicates('fixture_id').set_index('fixture_id')
    done = fxt[fxt.status.isin(['FT', 'AET', 'PEN'])].dropna(subset=['ft_home', 'ft_away', 'ht_home', 'ht_away'])
    fx = features(odds[odds.fixture_id.isin(done.index)], done[['date', 'league', 'country', 'home', 'away', 'ft_home', 'ft_away', 'ht_home', 'ht_away']])

    # ---- today's (upcoming) matches from the pre-match all-markets snapshot
    upcoming = None
    files = sorted(glob.glob(str(DATA / 'prematch' / 'oddsall_*.csv')))
    if files:
        day = Path(files[-1]).stem.replace('oddsall_', '')
        uo = pd.read_csv(files[-1]); uo = uo[pd.to_numeric(uo.odd, errors='coerce') > 1.0]
        uf = pd.read_csv(DATA / 'prematch' / f'fixtures_{day}.csv').drop_duplicates('fixture_id').set_index('fixture_id')
        uf = uf[uf.status == 'NS'] if 'status' in uf.columns else uf
        upcoming = (day, uo, features(uo[uo.fixture_id.isin(uf.index)], uf[['league', 'country', 'home', 'away', 'kickoff']]))

    out = []
    for md in MODELS:
        r = model_rows(md, odds, fx)
        rec = []
        for fid, x in r.iterrows():
            res = settle(md['market'], md['selection'], int(x.ft_home), int(x.ft_away), int(x.ht_home), int(x.ht_away))
            rec.append(dict(fid=int(fid), date=x.date, match=f'{x.home} - {x.away}', league=f'{x.country}: {x.league}', score=f'{int(x.ft_home)}-{int(x.ft_away)}',
                            ht=f'{int(x.ht_home)}-{int(x.ht_away)}', odds=round(float(x.typical), 2), best=round(float(x.best), 2),
                            status='WON' if res == 1 else 'LOST' if res == 0 else 'VOID', profit=round(pnl(x.typical, res), 2), profit_best=round(pnl(x.best, res), 2)))
        R = pd.DataFrame(rec)

        def summ(d):
            if d.empty:
                return dict(picks=0)
            s = d[d.status != 'VOID']
            return dict(picks=len(d), won=int((d.status == 'WON').sum()), lost=int((d.status == 'LOST').sum()), void=int((d.status == 'VOID').sum()),
                        hit=round((s.status == 'WON').mean() * 100, 1) if len(s) else None, avg_odds=round(d.odds.mean(), 2),
                        profit=round(d.profit.sum(), 2), roi=round(d.profit.mean() * 100, 1), roi_best=round(d.profit_best.mean() * 100, 1))
        daily = [dict(date=d, **summ(g)) for d, g in sorted(R.groupby('date'), reverse=True)] if not R.empty else []
        today = []
        if upcoming:
            day, uo, ufx = upcoming
            t = model_rows(md, uo, ufx)
            for fid, x in t.sort_values('kickoff').iterrows():
                today.append(dict(fid=int(fid), kickoff=str(x.kickoff), match=f'{x.home} - {x.away}', league=f'{x.country}: {x.league}', odds=round(float(x.typical), 2), best=round(float(x.best), 2)))
        out.append(dict(id=md['id'], group=md['group'], worst_day_hit=min([d['hit'] for d in daily if d.get('hit') is not None], default=None), name=md['name'], sporty=md['sporty'], why=md['why'], market=md['market'], selection=md['selection'],
                        rule=' and '.join(md['cond'].values()) + f"  ->  {md['market']} | {md['selection']}",
                        record=summ(R), found=summ(R[R.date <= SPLIT]) if not R.empty else {}, unseen=summ(R[R.date > SPLIT]) if not R.empty else {},
                        days_positive=int(sum(1 for d in daily if d['profit'] > 0)), days=len(daily), daily=daily,
                        today_date=upcoming[0] if upcoming else None, today=today,
                        picks=sorted(rec, key=lambda z: z['date'], reverse=True)))

    # ---------- accumulator tickets: mixed markets, one pick per match, built per day ----------
    by_id = {m['id']: m for m in out}

    def assemble(legs_by_model, order, size=None, target=None, min_legs=5, max_legs=12, per_model=2):
        """Round-robin across models so every ticket mixes markets. Returns list of tickets (lists of legs)."""
        queues = {k: list(v) for k, v in legs_by_model.items()}
        used, tickets = set(), []
        while True:
            t, count, prod, progressed = [], {}, 1.0, True
            while progressed:
                progressed = False
                for mid in order:
                    if count.get(mid, 0) >= per_model:
                        continue
                    q = queues.get(mid, [])
                    while q and q[0]['fid'] in used:
                        q.pop(0)
                    if not q:
                        continue
                    leg = q.pop(0); used.add(leg['fid']); t.append(leg); count[mid] = count.get(mid, 0) + 1; prod *= leg['odds']; progressed = True
                    done = (size and len(t) >= size) or (target and prod >= target and len(t) >= min_legs) or len(t) >= max_legs
                    if done:
                        break
                if (size and len(t) >= size) or (target and prod >= target and len(t) >= min_legs) or len(t) >= max_legs:
                    break
            ok = (size and len(t) == size) or (target and prod >= target and len(t) >= min_legs)
            if not ok:
                break
            tickets.append(t)
        return tickets

    def build_tickets(pool, lo, hi, size=None, target=None, min_legs=5, max_legs=12, per_model=2):
        ms = [by_id[i] for i in pool if i in by_id]
        order = [m['id'] for m in sorted(ms, key=lambda m: -(m['record'].get('hit') or 0))]
        tickets = []
        days = sorted({p['date'] for m in ms for p in m['picks']})
        for day in days:
            lbm = {m['id']: sorted([dict(p, model=m['id'], pick=m['sporty']) for p in m['picks'] if p['date'] == day and p['status'] != 'VOID' and lo <= p['odds'] <= hi],
                                   key=lambda z: z['fid']) for m in ms}
            for t in assemble(lbm, order, size, target, min_legs, max_legs, per_model):
                odds = float(np.prod([l['odds'] for l in t])); won = all(l['status'] == 'WON' for l in t)
                tickets.append(dict(date=day, odds=round(odds, 2), status='WON' if won else 'LOST', profit=round(odds - 1 if won else -1.0, 2),
                                    lost_legs=sum(l['status'] == 'LOST' for l in t), n_legs=len(t),
                                    legs=[dict(match=l['match'], pick=l['pick'], model=l['model'], odds=l['odds'], status=l['status'], score=l['score']) for l in t]))
        T = pd.DataFrame(tickets)

        def tsum(d):
            if d is None or len(d) == 0:
                return dict(tickets=0)
            return dict(tickets=len(d), won=int((d.status == 'WON').sum()), hit=round((d.status == 'WON').mean() * 100, 1), avg_odds=round(d.odds.mean(), 2),
                        profit=round(d.profit.sum(), 2), roi=round(d.profit.mean() * 100, 1), one_leg_short=int((d.lost_legs == 1).sum()), avg_legs=round(d.n_legs.mean(), 1))
        daily = [dict(date=d, **tsum(g)) for d, g in sorted(T.groupby('date'), reverse=True)] if len(T) else []
        lbm = {m['id']: sorted([dict(p, model=m['id'], pick=m['sporty']) for p in m['today'] if lo <= p['odds'] <= hi], key=lambda z: z['kickoff']) for m in ms}
        today = []
        for t in assemble(lbm, order, size, target, min_legs, max_legs, per_model):
            t = sorted(t, key=lambda z: z['kickoff'])
            today.append(dict(odds=round(float(np.prod([l['odds'] for l in t])), 2),
                              legs=[dict(kickoff=l['kickoff'], match=l['match'], league=l['league'], pick=l['pick'], model=l['model'], odds=l['odds']) for l in t]))
        return dict(size=size or 0, target=target, record=tsum(T), found=tsum(T[T.date <= SPLIT]) if len(T) else {}, unseen=tsum(T[T.date > SPLIT]) if len(T) else {},
                    daily=daily, today=today[:15], recent=sorted(tickets, key=lambda z: z['date'], reverse=True)[:60])

    SAFE = ['H1', 'H4', 'H6', 'H7', 'H8', 'H9', 'H10']                      # markets SportyBet offers on most matches
    POWER = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10']
    MIX = POWER + ['M1', 'M2', 'M4', 'M5', 'M7', 'M8', 'M9']
    plans = [('Safe 3', dict(pool=SAFE, lo=1.03, hi=1.25, size=3), 'Three mixed picks from the 90%+ models. Highest ticket win rate.'),
             ('Safe 5', dict(pool=SAFE, lo=1.03, hi=1.25, size=5), 'Five mixed picks from the 90%+ models: a 5-game ticket that still wins most of the time.'),
             ('Power 5', dict(pool=POWER, lo=1.18, hi=1.60, size=5), 'Five mixed picks, each priced 1.18-1.60.'),
             ('Mix 5 odds', dict(pool=POWER, lo=1.18, hi=1.65, target=5.0, min_legs=5, max_legs=10, per_model=3), 'Mixed markets, built until the ticket reaches 5 odds or more.'),
             ('Mix 10 odds', dict(pool=POWER + ['M1', 'M2', 'M9'], lo=1.18, hi=1.75, target=10.0, min_legs=6, max_legs=13, per_model=3), 'Mixed markets, built until the ticket reaches 10 odds or more. Big payout, wins less often.')]
    A_PLUS = POWER + ['M1', 'M2', 'M9']
    BIG = POWER + ['M1', 'M2', 'M4', 'M5', 'M7', 'M8', 'M9']
    plans += [('Mix 3 odds', dict(pool=POWER, lo=1.18, hi=1.50, target=3.0, min_legs=3, max_legs=7, per_model=2), 'Mixed markets, built until the ticket reaches 3 odds.'),
              ('Mix 20 odds', dict(pool=BIG, lo=1.20, hi=2.30, target=20.0, min_legs=6, max_legs=14, per_model=3), 'Mixed markets, built until the ticket reaches 20 odds. Rare wins, big payout.')]
    tickets = {}
    for label, kw, about in plans:
        tickets[label] = dict(build_tickets(**kw), group=label, about=about)

    # ---------- DAILY 10: 3 tickets @ 3 odds, 3 @ 5 odds, 3 @ 10 odds, 1 @ 20 odds; mixed markets; no match repeated ----------
    TIERS = [('3 odds', 3.0, 3, POWER, 1.18, 1.50, 3, 7, 1), ('5 odds', 5.0, 3, POWER, 1.18, 1.60, 4, 9, 2),
             ('10 odds', 10.0, 3, A_PLUS, 1.18, 1.80, 5, 11, 2), ('20 odds', 20.0, 1, BIG, 1.20, 2.30, 6, 14, 2)]

    def daily10(legs_of, sortkey):
        """legs_of(model_id) -> list of legs (dicts with fid, odds, pick). Returns 10 tickets; a match is used once across all tickets when possible."""
        used_all, result = set(), []
        for tier, target, count, pool, lo, hi, min_legs, max_legs, per_market in TIERS:
            order = [i for i in sorted(pool, key=lambda i: -(by_id[i]['record'].get('hit') or 0)) if i in by_id]
            for _ in range(count):
                def attempt(block):
                    t, fids, mk_count, prod, start = [], set(), {}, 1.0, len(result)
                    queues = {i: [l for l in sorted(legs_of(i), key=sortkey) if lo <= l['odds'] <= hi and l['fid'] not in block] for i in order}
                    rot = order[start % len(order):] + order[:start % len(order)]      # rotate so tickets start from different models
                    while len(t) < max_legs and not (prod >= target and len(t) >= min_legs):
                        cands = []
                        for i in rot:
                            q = [l for l in queues[i] if l['fid'] not in fids and mk_count.get(l['pick'], 0) < per_market]
                            if q:
                                cands.append((i, q[0]))
                        if not cands:
                            break
                        need = target / prod
                        closers = [c for c in cands if c[1]['odds'] >= need] if len(t) + 1 >= min_legs else []
                        i, leg = min(closers, key=lambda c: c[1]['odds']) if closers else cands[0]
                        t.append(dict(leg, model=i)); fids.add(leg['fid']); mk_count[leg['pick']] = mk_count.get(leg['pick'], 0) + 1; prod *= leg['odds']
                        rot = rot[rot.index(i) + 1:] + rot[:rot.index(i) + 1]
                    return t, prod
                t, prod = attempt(used_all)
                repeats = False
                if not (prod >= target and len(t) >= min_legs):
                    t2, prod2 = attempt(set())           # few matches today: allow a match already used in another ticket
                    if prod2 > prod:
                        t, prod, repeats = t2, prod2, True
                if len(t) < 2:
                    continue
                used_all |= {l['fid'] for l in t}
                result.append(dict(tier=tier, target=target, odds=round(prod, 2), reached=bool(prod >= target), repeats=repeats, legs=t))
        return result

    def leg_view(l):
        return {k: l.get(k) for k in ['fid', 'kickoff', 'match', 'league', 'pick', 'model', 'odds', 'market', 'selection', 'status', 'score', 'ht'] if l.get(k) is not None}

    # backtest of the exact Daily-10 method on each past day
    d10_bt = []
    for day in sorted({p['date'] for m in out for p in m['picks']}):
        tk = daily10(lambda i: [dict(p, pick=by_id[i]['sporty']) for p in by_id[i]['picks'] if p['date'] == day and p['status'] != 'VOID'], lambda z: z['fid'])
        for t in tk:
            won = all(l['status'] == 'WON' for l in t['legs'])
            d10_bt.append(dict(date=day, tier=t['tier'], odds=t['odds'], status='WON' if won else 'LOST', lost_legs=sum(l['status'] == 'LOST' for l in t['legs']), n_legs=len(t['legs'])))
    BT = pd.DataFrame(d10_bt)
    tier_bt = {}
    if len(BT):
        for tier, g in BT.groupby('tier'):
            pl = np.where(g.status == 'WON', g.odds - 1, -1.0)
            tier_bt[tier] = dict(tickets=len(g), won=int((g.status == 'WON').sum()), hit=round((g.status == 'WON').mean() * 100, 1), avg_odds=round(g.odds.mean(), 2),
                                 avg_legs=round(g.n_legs.mean(), 1), roi=round(pl.mean() * 100, 1), one_leg_short=int((g.lost_legs == 1).sum()))

    # today's Daily 10: frozen the first time it is built, so it cannot be changed after results are known
    ledger_dir = DATA / 'daily10'; ledger_dir.mkdir(parents=True, exist_ok=True)
    today_set = None
    if upcoming:
        day = upcoming[0]; lf = ledger_dir / f'{day}.json'
        if lf.exists() and '--rebuild' not in sys.argv:
            today_set = json.loads(lf.read_text(encoding='utf-8'))
        else:
            tk = daily10(lambda i: [dict(p, pick=by_id[i]['sporty'], market=by_id[i]['market'], selection=by_id[i]['selection']) for p in by_id[i]['today']], lambda z: (z['kickoff'], z['fid']))
            today_set = dict(date=day, created=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
                             tickets=[dict(no=n + 1, tier=t['tier'], target=t['target'], odds=t['odds'], reached=t['reached'], repeats=t['repeats'],
                                           legs=[leg_view(l) for l in sorted(t['legs'], key=lambda z: z['kickoff'])]) for n, t in enumerate(tk)])
            lf.write_text(json.dumps(today_set, indent=1, default=str), encoding='utf-8')

    # settle every frozen day from the results file
    res = fxt[fxt.status.isin(['FT', 'AET', 'PEN'])].dropna(subset=['ft_home', 'ft_away'])
    history = []
    for lf in sorted(ledger_dir.glob('*.json'), reverse=True)[:40]:
        d = json.loads(lf.read_text(encoding='utf-8'))
        for t in d['tickets']:
            for l in t['legs']:
                if l['fid'] in res.index:
                    r = res.loc[l['fid']]
                    v, ht_ = settle_leg(l, r)
                    l['status'] = 'WON' if v == 1 else 'LOST' if v == 0 else 'VOID'; l['score'] = f'{int(r.ft_home)}-{int(r.ft_away)}'; l['ht'] = ht_
                elif l['fid'] in VOID_IDS:
                    l['status'] = 'VOID'
                else:
                    l['status'] = 'PENDING'
            sts = [l['status'] for l in t['legs']]
            t['status'] = 'LOST' if 'LOST' in sts else 'PENDING' if 'PENDING' in sts else 'WON'
            t['lost_legs'] = sts.count('LOST')
        history.append(d)
    live = {}
    for d in history:
        for t in d['tickets']:
            if t['status'] == 'PENDING':
                continue
            a = live.setdefault(t['tier'], dict(tickets=0, won=0, profit=0.0))
            a['tickets'] += 1; a['won'] += t['status'] == 'WON'; a['profit'] += (t['odds'] - 1) if t['status'] == 'WON' else -1.0
    for a in live.values():
        a['hit'] = round(a['won'] / a['tickets'] * 100, 1); a['profit'] = round(a['profit'], 2)
    if today_set:
        today_set = next((d for d in history if d['date'] == today_set['date']), today_set)
    daily = dict(today=today_set, history=history, live=live, backtest=tier_bt,
                 tiers=[dict(tier=x[0], target=x[1], count=x[2]) for x in TIERS])

    # live scoreboard: how each model's picks have done inside the published VIP tickets
    bym = {}
    for d in history:
        for t in d['tickets']:
            for l in t['legs']:
                if l.get('status') in ('WON', 'LOST') and l.get('model') in by_id:
                    a = bym.setdefault(l['model'], dict(id=l['model'], name=by_id[l['model']]['name'], sporty=by_id[l['model']]['sporty'], picks=0, won=0))
                    a['picks'] += 1; a['won'] += l['status'] == 'WON'
    for a in bym.values():
        a['hit'] = round(a['won'] / a['picks'] * 100, 1)
    daily['by_model'] = sorted(bym.values(), key=lambda a: (-a['picks'], -a['hit']))

    # ---------- SPECIALS: one-market tickets from the five models with the best long-run record that have enough matches today ----------
    # Ranked on the whole record (and held up on unseen days), NOT on yesterday alone: tested, yesterday's form does not carry over.
    specials = dict(today=None, history=[], live={}, target=3.0)
    try:
        sdir = DATA / 'specials'; sdir.mkdir(parents=True, exist_ok=True)
        if upcoming:
            day = upcoming[0]; sf = sdir / f'{day}.json'
            if not sf.exists() or '--rebuild' in sys.argv:
                cands = []
                for m in out:
                    r_, u_ = m['record'], m['unseen']
                    if r_.get('picks', 0) < 90 or not r_.get('avg_odds') or r_['avg_odds'] < 1.15 or r_.get('hit') is None or u_.get('hit') is None:
                        continue
                    if min(r_['hit'], u_['hit']) < 78:                                    # specials are for options that come in often
                        continue
                    tp = [p for p in m['today'] if 1.12 <= p['odds'] <= 1.9]
                    if len(tp) < 4:
                        continue
                    edge = min(r_['hit'], u_['hit']) - 100 / r_['avg_odds']          # hit rate above the break-even rate, on the weaker of the two periods
                    cands.append((edge, m, tp))
                tks, seen_mk, n_models = [], set(), 0
                for edge, m, tp in sorted(cands, key=lambda z: -z[0]):
                    if (m['market'], m['selection']) in seen_mk or n_models >= 5:      # same bet under two model names counts once
                        continue
                    seen_mk.add((m['market'], m['selection'])); n_models += 1
                    tp = sorted(tp, key=lambda z: (z['kickoff'], z['fid'])); cur, prod, made = [], 1.0, 0
                    for p_ in tp:
                        cur.append(p_); prod *= p_['odds']
                        if prod >= specials['target'] and len(cur) >= 3:
                            tks.append((m, cur, prod)); cur, prod, made = [], 1.0, made + 1
                            if made >= 2:
                                break
                    if made == 0 and len(cur) >= 3:
                        tks.append((m, cur, prod))
                sset = dict(date=day, created=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
                            tickets=[dict(no=n + 1, model=m['id'], tier=m['name'], sporty=m['sporty'], target=specials['target'], odds=round(pr_, 2), reached=bool(pr_ >= specials['target']), repeats=False,
                                          record=dict(hit=m['record']['hit'], picks=m['record']['picks'], avg_odds=m['record']['avg_odds']),
                                          legs=[dict(fid=l['fid'], kickoff=l['kickoff'], match=l['match'], league=l['league'], pick=m['sporty'], model=m['id'], odds=l['odds'], market=m['market'], selection=m['selection']) for l in legs])
                                     for n, (m, legs, pr_) in enumerate(tks)])
                sf.write_text(json.dumps(sset, indent=1, default=str), encoding='utf-8')
        for sf in sorted(sdir.glob('*.json'), reverse=True)[:30]:
            d = json.loads(sf.read_text(encoding='utf-8'))
            for t in d['tickets']:
                for l in t['legs']:
                    if l['fid'] in res.index:
                        r = res.loc[l['fid']]; v, ht_ = settle_leg(l, r)
                        l['status'] = 'WON' if v == 1 else 'LOST' if v == 0 else 'VOID'; l['score'] = f'{int(r.ft_home)}-{int(r.ft_away)}'; l['ht'] = ht_
                    elif l['fid'] in VOID_IDS:
                        l['status'] = 'VOID'
                    else:
                        l['status'] = 'PENDING'
                sts = [l['status'] for l in t['legs']]
                t['status'] = 'LOST' if 'LOST' in sts else 'PENDING' if 'PENDING' in sts else 'WON'
                if t['status'] != 'PENDING':
                    a = specials['live'].setdefault(t['model'], dict(name=t['tier'], tickets=0, won=0)); a['tickets'] += 1; a['won'] += t['status'] == 'WON'
            specials['history'].append(d)
        if upcoming:
            specials['today'] = next((d for d in specials['history'] if d['date'] == upcoming[0]), None)
        if specials['today']:
            print(f"  SPECIALS for {specials['today']['date']}: " + ', '.join(f"{t['model']} {t['odds']} ({len(t['legs'])})" for t in specials['today']['tickets']))
    except Exception as e:
        specials['error'] = str(e)
        print('  SPECIALS skipped:', e)

    # ---------- FREE PICKS: the original v10.8 Core, run automatically on today's API fixtures (no pasting) ----------
    CATS = ['TOP FINGERPRINT', 'HOME 1+', 'AWAY 1+', 'OVER 1.5', 'OVER 2.5', 'UNDER 3.5', '1X', 'X2']
    CAT_OF = {'Home team to score 1+': 'HOME 1+', 'Away team to score 1+': 'AWAY 1+', 'Over 1.5': 'OVER 1.5', 'Over 2.5': 'OVER 2.5', 'Under 3.5': 'UNDER 3.5', '1X': '1X', 'X2': 'X2'}
    PRICE_OF = {'1X': ('Double Chance', ['Home/Draw', 'Draw/Home']), 'X2': ('Double Chance', ['Draw/Away', 'Away/Draw']),
                'Home team to score 1+': ('Total - Home', ['Over 0.5']), 'Away team to score 1+': ('Total - Away', ['Over 0.5']),
                'Over 1.5': ('Goals Over/Under', ['Over 1.5']), 'Over 2.5': ('Goals Over/Under', ['Over 2.5']), 'Under 3.5': ('Goals Over/Under', ['Under 3.5'])}

    def free_won(option, hg, ag):
        return {'1X': hg >= ag, 'X2': ag >= hg, 'Home team to score 1+': hg >= 1, 'Away team to score 1+': ag >= 1,
                'Over 1.5': hg + ag >= 2, 'Over 2.5': hg + ag >= 3, 'Under 3.5': hg + ag <= 3}[option]
    free = dict(cats=CATS, today=None, history=[], live={}, backtest={})
    try:
        core = Path(__file__).resolve().parent.parent / 'backend' / 'core'
        sys.path.insert(0, str(core))
        from engine import Scanner
        scanner = Scanner(pd.read_csv(core / 'historical.csv').rename(columns={'home_goals': 'hg', 'away_goals': 'ag'}))

        def scan(fxf, od):
            q = fxf.dropna(subset=['H', 'X', 'A']).reset_index().rename(columns={'X': 'D', 'index': 'fixture_id'})
            if 'fixture_id' not in q.columns:
                q = q.rename(columns={q.columns[0]: 'fixture_id'})
            if q.empty:
                return []
            price = {}
            for opt, (mk, sels) in PRICE_OF.items():
                price[opt] = od[(od.market == mk) & od.selection.isin(sels)].groupby('fixture_id').odd.median()
            items = []
            for row, r in zip(q.itertuples(), scanner.scan(q[['home', 'away', 'H', 'D', 'A']])):
                if not r['options']:
                    continue
                picks = [dict(option=o['option'], cat=CAT_OF[o['option']], consistency=round(o['score'] * 100), neighbours=f"{o['neighbour_hits']} / {o['k']}",
                              odds=(round(float(price[o['option']].get(row.fixture_id)), 2) if row.fixture_id in price[o['option']].index else None)) for o in r['options']]
                items.append(dict(fid=int(row.fixture_id), home=row.home, away=row.away, league=f"{getattr(row, 'country', '')}: {getattr(row, 'league', '')}",
                                  kickoff=str(getattr(row, 'kickoff', '')), odds=[round(float(row.H), 2), round(float(row.D), 2), round(float(row.A), 2)], picks=picks))
            return items

        # past record of the free picks on already-played matches (same engine, same thresholds)
        # (slow step: saved once and reused; it is only redone when new results have been collected)
        fdir = DATA / 'freepicks'; fdir.mkdir(parents=True, exist_ok=True)
        cache = fdir / '_record.cache'
        bt = None
        if cache.exists() and '--rebuild' not in sys.argv:
            try:
                c_ = json.loads(cache.read_text(encoding='utf-8'))
                bt = c_['bt'] if c_.get('n') == len(fx) else None
            except Exception:
                bt = None
        if bt is None:
            print(f'  FREE PICKS: checking the past record on {len(fx)} played matches - this takes a few minutes the first time, please wait...', flush=True)
            bt = {}
            for it, (_, x) in [(i, (i['fid'], fx.loc[i['fid']])) for i in scan(fx, odds)]:
                for n_, pk in enumerate(it['picks']):
                    w = bool(free_won(pk['option'], int(x.ft_home), int(x.ft_away)))
                    for c in ([pk['cat']] + (['TOP FINGERPRINT'] if n_ == 0 else [])):
                        a = bt.setdefault(c, dict(picks=0, won=0)); a['picks'] += 1; a['won'] += w
            for a in bt.values():
                a['hit'] = round(a['won'] / a['picks'] * 100, 1)
            cache.write_text(json.dumps(dict(n=len(fx), bt=bt)), encoding='utf-8')
        free['backtest'] = bt

        if upcoming:
            day, uo, ufx = upcoming
            ff = fdir / f'{day}.json'
            if not ff.exists() or '--rebuild' in sys.argv:
                ff.write_text(json.dumps(dict(date=day, created=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'), items=scan(ufx, uo)), indent=1, default=str), encoding='utf-8')
        done_ft = fxt[fxt.status.isin(['FT', 'AET', 'PEN'])].dropna(subset=['ft_home', 'ft_away'])
        for ff in sorted(fdir.glob('*.json'), reverse=True)[:30]:
            d = json.loads(ff.read_text(encoding='utf-8'))
            for it in d['items']:
                if it['fid'] in done_ft.index:
                    r = done_ft.loc[it['fid']]; it['score'] = f'{int(r.ft_home)}-{int(r.ft_away)}'
                    for pk in it['picks']:
                        pk['status'] = 'WON' if free_won(pk['option'], int(r.ft_home), int(r.ft_away)) else 'LOST'
                elif it['fid'] in VOID_IDS:
                    for pk in it['picks']:
                        pk['status'] = 'VOID'
            free['history'].append(d)
        for d in free['history']:
            for it in d['items']:
                for n_, pk in enumerate(it['picks']):
                    if pk.get('status') not in ('WON', 'LOST'):
                        continue
                    for c in ([pk['cat']] + (['TOP FINGERPRINT'] if n_ == 0 else [])):
                        a = free['live'].setdefault(c, dict(picks=0, won=0)); a['picks'] += 1; a['won'] += pk['status'] == 'WON'
        if upcoming:
            free['today'] = next((d for d in free['history'] if d['date'] == upcoming[0]), None)
    except Exception as e:      # the free feed must never stop the tickets from publishing
        free['error'] = str(e)
        print('  FREE PICKS skipped:', e)
    # ---------- NO DRAW SPOTLIGHT: Home or Away (12). "Sweet" = the strict rule (model H10), "Wide" = a looser rule with more matches ----------
    ND_TIERS = [('Sweet', 1.25, 1.55, 'Favourite under 1.25 and Over 2.5 under 1.55'), ('Wide', 1.45, 1.70, 'Favourite under 1.45 and Over 2.5 under 1.70')]
    nodraw = dict(tiers=[], today=None, history=[], live={})
    try:
        def nd_price(od):
            return od[(od.market == 'Double Chance') & od.selection.isin(['Home/Away', 'Away/Home']) & (od.odd >= 1.02)].groupby('fixture_id').odd.median()

        def nd_pick(f, od):
            f = f.join(nd_price(od).rename('p12'), how='inner')
            fav = f[['H', 'A']].min(axis=1); f = f.assign(fav=fav)
            f['tier'] = np.where((fav < 1.25) & (f.O25 < 1.55), 'Sweet', np.where((fav < 1.45) & (f.O25 < 1.70), 'Wide', ''))
            return f[f.tier != '']
        def med_of(od, mk, sels):
            return od[(od.market == mk) & od.selection.isin(sels)].groupby('fixture_id').odd.median()

        def nd_extras(od):
            return dict(o15=med_of(od, 'Goals Over/Under', ['Over 1.5']), h=med_of(od, 'Match Winner', ['Home']), a=med_of(od, 'Match Winner', ['Away']))
        past = nd_pick(fx, odds); past = past.assign(won=(past.ft_home != past.ft_away).astype(int))
        # companion picks on the same matches: Over 1.5 and Favourite to win (record on past matches)
        ex_ = nd_extras(odds)
        pe = past.assign(o15=ex_['o15'].reindex(past.index), fw=np.where(past.H <= past.A, past.H, past.A),
                         o15w=((past.ft_home + past.ft_away) >= 2).astype(int),
                         fww=np.where(past.H <= past.A, past.ft_home > past.ft_away, past.ft_away > past.ft_home).astype(int))
        nodraw['extras'] = {}
        for nm in ('Sweet', 'Wide'):
            s_ = pe if nm == 'Wide' else pe[pe.tier == 'Sweet']
            o_ = s_.dropna(subset=['o15'])
            nodraw['extras'][nm] = dict(over15=dict(picks=int(len(o_)), won=int(o_.o15w.sum()), hit=round(o_.o15w.mean() * 100, 1) if len(o_) else None, avg_odds=round(float(o_.o15.mean()), 2) if len(o_) else None),
                                        favwin=dict(picks=int(len(s_)), won=int(s_.fww.sum()), hit=round(s_.fww.mean() * 100, 1) if len(s_) else None, avg_odds=round(float(s_.fw.mean()), 2) if len(s_) else None))
        for nm, fa, o, rule in ND_TIERS:
            s_ = past if nm == 'Wide' else past[past.tier == 'Sweet']        # Wide includes the Sweet matches
            if len(s_):
                a_, b_ = s_[s_.date <= SPLIT], s_[s_.date > SPLIT]
                nodraw['tiers'].append(dict(tier=nm, rule=rule, picks=int(len(s_)), won=int(s_.won.sum()), hit=round(s_.won.mean() * 100, 1), avg_odds=round(float(s_.p12.mean()), 2),
                                            found=round(a_.won.mean() * 100, 1) if len(a_) else None, unseen=round(b_.won.mean() * 100, 1) if len(b_) else None,
                                            per_day=round(len(s_) / s_.date.nunique(), 1), worst_day=round(s_.groupby('date').won.mean().min() * 100, 1)))
        ndir = DATA / 'nodraw'; ndir.mkdir(parents=True, exist_ok=True)
        if upcoming:
            day, uo, ufx = upcoming
            nf = ndir / f'{day}.json'
            if not nf.exists() or '--rebuild' in sys.argv:
                t_ = nd_pick(ufx, uo).sort_values(['tier', 'fav'])
                ue = nd_extras(uo)
                its = [dict(fid=int(i), tier=r.tier, home=r.home, away=r.away, league=f'{r.country}: {r.league}', kickoff=str(r.kickoff), fav=round(float(r.fav), 2),
                            o25=round(float(r.O25), 2), odds=round(float(r.p12), 2), fav_side='Home' if r.H <= r.A else 'Away',
                            o15=(round(float(ue['o15'][i]), 2) if i in ue['o15'].index else None)) for i, r in t_.iterrows()]
                nf.write_text(json.dumps(dict(date=day, created=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'), items=its), indent=1), encoding='utf-8')
        done_nd = fxt[fxt.status.isin(['FT', 'AET', 'PEN'])].dropna(subset=['ft_home', 'ft_away'])
        for nf in sorted(ndir.glob('*.json'), reverse=True)[:30]:
            d = json.loads(nf.read_text(encoding='utf-8'))
            # days saved before the Over 1.5 / Favourite companions existed: fill them in from that day's saved pre-match prices and say so
            if any('fav_side' not in it for it in d['items']):
                pf = DATA / 'prematch' / f"oddsall_{d['date']}.csv"
                if pf.exists():
                    po = pd.read_csv(pf); po = po[pd.to_numeric(po.odd, errors='coerce') > 1.0]; pe_ = nd_extras(po)
                    for it in d['items']:
                        if 'fav_side' in it:
                            continue
                        h_, a_ = pe_['h'].get(it['fid']), pe_['a'].get(it['fid'])
                        if h_ is None or a_ is None:
                            continue
                        it['fav_side'] = 'Home' if h_ <= a_ else 'Away'
                        it['o15'] = round(float(pe_['o15'][it['fid']]), 2) if it['fid'] in pe_['o15'].index else None
                    d['companions_added'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
                    nf.write_text(json.dumps(d, indent=1), encoding='utf-8')
            for it in d['items']:
                if it['fid'] in done_nd.index:
                    r = done_nd.loc[it['fid']]; it['score'] = f'{int(r.ft_home)}-{int(r.ft_away)}'; it['status'] = 'WON' if r.ft_home != r.ft_away else 'LOST'
                    it['o15_status'] = 'WON' if r.ft_home + r.ft_away >= 2 else 'LOST'
                    if it.get('fav_side'):
                        it['fav_status'] = 'WON' if (r.ft_home > r.ft_away if it['fav_side'] == 'Home' else r.ft_away > r.ft_home) else 'LOST'
                    for t in ([it['tier']] + (['Wide'] if it['tier'] == 'Sweet' else [])):
                        a = nodraw['live'].setdefault(t, dict(picks=0, won=0)); a['picks'] += 1; a['won'] += it['status'] == 'WON'
                elif it['fid'] in VOID_IDS:
                    it['status'] = 'VOID'
            nodraw['history'].append(d)
        if upcoming:
            nodraw['today'] = next((d for d in nodraw['history'] if d['date'] == upcoming[0]), None)
        if nodraw['today']:
            n_s = sum(1 for i in nodraw['today']['items'] if i['tier'] == 'Sweet')
            print(f"  NO DRAW for {nodraw['today']['date']}: Sweet {n_s}, Wide {len(nodraw['today']['items'])} (Wide includes Sweet)")
        print('  NO DRAW past record: ' + ', '.join(f"{t['tier']} {t['hit']}% of {t['picks']} at avg odds {t['avg_odds']} (about {t['per_day']} a day)" for t in nodraw['tiers']))
    except Exception as e:
        nodraw['error'] = str(e)
        print('  NO DRAW spotlight skipped:', e)
    data = dict(specials=specials, nodraw=nodraw, free=free, daily10=daily, tickets=tickets, generated=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'), split=SPLIT,
                note='Candidates only. Selected as the best of 21,335 tested patterns over 6 days; some of this record is luck and will fade. '
                     'Flat 1-unit stakes at the typical (median) bookmaker price. Prices captured about 1 hour before kick-off.',
                models=out)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, default=str), encoding='utf-8')
    print(f'Wrote {OUT}')
    if free.get('today'):
        cc = {c: sum(1 for it in free['today']['items'] for n_, pk in enumerate(it['picks']) if pk['cat'] == c or (c == 'TOP FINGERPRINT' and n_ == 0)) for c in CATS}
        print(f"  FREE PICKS for {free['today']['date']}: {len(free['today']['items'])} matches | " + ', '.join(f'{c} {n_}' for c, n_ in cc.items()))
    print('  FREE PICKS past record: ' + ', '.join(f"{c} {v['hit']}% ({v['picks']})" for c, v in free['backtest'].items()))
    print('  DAILY 10 backtest (same method on past days): ' + ' | '.join(f"{k}: {v['won']}/{v['tickets']} won ({v['hit']}%), avg odds {v['avg_odds']}, {v['avg_legs']} picks" for k, v in tier_bt.items()))
    if today_set:
        print(f"  DAILY 10 for {today_set['date']} (frozen {today_set['created']}): " + ', '.join(f"#{t['no']} {t['tier']} -> {t['odds']} ({len(t['legs'])} picks{' REPEAT' if t['repeats'] else ''})" for t in today_set['tickets']))
    for g, t in tickets.items():
        r = t['record']
        print(f"  TICKETS [{g}]: {r.get('tickets')} tickets, won {r.get('hit')}%, avg odds {r.get('avg_odds')}, ROI {r.get('roi')}% (found {t['found'].get('hit')}% / unseen {t['unseen'].get('hit')}%), avg legs {r.get('avg_legs')}, one leg short {r.get('one_leg_short')}, today {len(t['today'])}")
    for m in out:
        r = m['record']
        print(f"  {m['id']:4s} {m['group']:9s} {m['name']:40s} picks={r.get('picks', 0):4d} hit={r.get('hit')}% odds={r.get('avg_odds')} ROI={r.get('roi')}% "
              f"hit found/unseen {m['found'].get('hit')}/{m['unseen'].get('hit')}% worst day {m['worst_day_hit']}% (ROI found {m['found'].get('roi')}% / unseen {m['unseen'].get('roi')}%) days+ {m['days_positive']}/{m['days']}  today={len(m['today'])}")


if __name__ == '__main__':
    main()
