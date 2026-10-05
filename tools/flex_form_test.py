"""QuantSport - FLEX test using TEAM FORM (not just odds). Run it yourself and check the scores.

For every team it works out, from that team's last 10 matches BEFORE each game: how often the 2nd half outscored the 1st,
goals for/against in each half, win and draw rate. A model learns from all earlier days which form predicts the result,
then picks the 18 strongest matches on each test day. Nothing from a test day is used to choose that day's picks.

Usage (v22 folder, .venv active):
    $env:QS_DATA = "$PWD\\data"
    python tools\\flex_form_test.py                      # summary over every test day
    python tools\\flex_form_test.py --show 2026-09-28     # also list the 18 picks and scores for one day
"""
import argparse, os, sys, warnings
warnings.filterwarnings('ignore')
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
DATA = Path(os.environ.get('QS_DATA', Path.home() / 'Documents' / 'QuantSport_Data'))
NAMES = {'hsh2': 'Highest Scoring Half - 2nd half', 'hw': 'Home to win', 'aw': 'Away to win'}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--show', default=''); ap.add_argument('--picks', type=int, default=18); a = ap.parse_args()
    fr = [pd.read_csv(DATA / f) for f in ('history.csv', 'fixtures.csv', 'live_results.csv') if (DATA / f).exists()]
    m = pd.concat(fr).drop_duplicates('fixture_id'); m = m[m.status.isin(['FT', 'AET', 'PEN'])].dropna(subset=['ft_home', 'ft_away', 'ht_home', 'ht_away', 'home_id', 'away_id'])
    m['kt'] = pd.to_datetime(m.kickoff, errors='coerce', utc=True); m = m.sort_values(['date', 'kt', 'fixture_id']).reset_index(drop=True)
    m['g1'] = m.ht_home + m.ht_away; m['g2'] = m.ft_home + m.ft_away - m.g1
    m['hsh2'] = (m.g2 > m.g1).astype(int); m['hw'] = (m.ft_home > m.ft_away).astype(int); m['aw'] = (m.ft_away > m.ft_home).astype(int)

    def side(s):
        o = 'away' if s == 'home' else 'home'
        d = pd.DataFrame({'fixture_id': m.fixture_id, 'team': m[s + '_id'], 'home': int(s == 'home'), 'hsh2': m.hsh2, 'hsh1': (m.g1 > m.g2).astype(int), 'g1': m.g1, 'g2': m.g2,
                          'gf': m['ft_' + s], 'ga': m['ft_' + o], 'gf2': m['ft_' + s] - m['ht_' + s], 'ga2': m['ft_' + o] - m['ht_' + o], 'gf1': m['ht_' + s], 'ga1': m['ht_' + o],
                          'win': (m['ft_' + s] > m['ft_' + o]).astype(int), 'draw': (m.ft_home == m.ft_away).astype(int)})
        d['ord'] = np.arange(len(d)); return d
    L = pd.concat([side('home'), side('away')]).sort_values(['team', 'ord'])
    cols = ['hsh2', 'hsh1', 'g1', 'g2', 'gf', 'ga', 'gf2', 'ga2', 'gf1', 'ga1', 'win', 'draw']; g = L.groupby('team')
    for c in cols:
        L['r_' + c] = g[c].transform(lambda x: x.shift(1).rolling(10, min_periods=5).mean())          # shift(1): only matches BEFORE this one
    L['n'] = g.cumcount(); feat = ['r_' + c for c in cols]
    X = m.set_index('fixture_id').join(L[L.home == 1].set_index('fixture_id')[feat + ['n']].add_prefix('h_')).join(L[L.home == 0].set_index('fixture_id')[feat + ['n']].add_prefix('a_'))
    X = X.sort_values(['league_id', 'date'])
    for c in ['hsh2', 'hw', 'aw', 'g1', 'g2']:
        X['lg_' + c] = (X.groupby('league_id')[c].cumsum() - X[c] + X[c].mean() * 15) / (X.groupby('league_id').cumcount() + 15)
    X = X.sort_values(['date', 'kt']); X = X[(X.h_n >= 5) & (X.a_n >= 5)].dropna(subset=['h_r_hsh2', 'a_r_hsh2'])
    F = [c for c in X.columns if c.startswith(('h_r_', 'a_r_', 'lg_'))]; days = sorted(X.date.unique())
    print(f'{len(m)} finished matches from {m.date.min()} to {m.date.max()}; {len(X)} where both teams have at least 5 earlier matches.')
    if len(days) < 60:
        sys.exit('Not enough history in the data folder for this test (history.csv is needed).')
    start = 45
    print(f'Learning starts with the first {start} days; tested day by day on the {len(days) - start} days after that. 11 of {a.picks} needed.\n')
    for t in ['hsh2', 'hw', 'aw']:
        res, mdl = [], None
        for i, d in enumerate(days):
            if i < start:
                continue
            if mdl is None or (i - start) % 7 == 0:
                tr = X[X.date < d]
                mdl = (make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=500)).fit(tr[F], tr[t]),
                       HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=150, min_samples_leaf=80, random_state=1).fit(tr[F], tr[t]))
            te = X[X.date == d]
            if len(te) < a.picks + 10:
                continue
            te = te.assign(p=(mdl[0].predict_proba(te[F])[:, 1] + mdl[1].predict_proba(te[F])[:, 1]) / 2).sort_values('p', ascending=False)
            top = te.head(a.picks); res.append((d, int(top[t].sum()), te.iloc[a.picks:][t].mean(), len(te)))
            if d == a.show:
                print(f'--- {NAMES[t]}: the {a.picks} picks for {d} ---')
                for _, r in top.assign(k=top.kt).sort_values('k').iterrows():
                    print(f'  {(str(r.home) + " - " + str(r.away))[:52]:<54} HT {int(r.ht_home)}-{int(r.ht_away)}  FT {int(r.ft_home)}-{int(r.ft_away)}  {"WON" if r[t] else "lost"}')
                print(f'  => {int(top[t].sum())} of {a.picks} won\n')
        R = pd.DataFrame(res, columns=['date', 'won', 'rest', 'n'])
        print(f'{NAMES[t]}: {len(R)} test days')
        print(f'   the {a.picks} picked won {R.won.sum() / (a.picks * len(R)) * 100:.1f}%   |   the matches NOT picked won {R.rest.mean() * 100:.1f}%')
        print(f'   days with 11+: {int((R.won >= 11).sum())} of {len(R)}   12+: {int((R.won >= 12).sum())}   13+: {int((R.won >= 13).sum())}')
        print('   wins per day: ' + ' '.join(str(v) for v in R.won) + '\n')
    print('NOTE: "Home to win" and "Away to win" picks here are mostly strong favourites at low odds (about 1.2-1.5), NOT 2-odds picks.\n'
          '      Only the Highest Scoring Half line is a like-for-like Flex test, because almost every match is priced near 2.00 for it.')


if __name__ == '__main__':
    main()
