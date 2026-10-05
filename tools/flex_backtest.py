"""QuantSport - FLEX backtest you can run and check yourself.

For one test day it builds an 18-pick ticket per option, the honest way:
  1. LEARN: using only the days BEFORE the test day, it measures how often the option won in each kind of match
     (strength of favourite, home/away favourite, draw price, goals price, league/cup, senior/youth/women).
  2. PICK: on the test day it takes the 18 matches from the kinds that won most often before, priced 1.90-2.40.
  3. CHECK: it prints every match with its odds, half-time and full-time score and Won/Lost, then the Flex result.

Usage (in the v22 folder, .venv active):
    $env:QS_DATA = "$PWD\\data"
    python tools\\flex_backtest.py --day 2026-09-28
    python tools\\flex_backtest.py --day 2026-09-28 --options hsh2,home,away --picks 18
"""
import argparse, os, sys, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_models as B

OPTIONS = {
    'hsh2': ('Highest Scoring Half - 2nd half', 'Highest Scoring Half', ['2nd Half'], lambda r: (r.ft_home + r.ft_away - r.ht_home - r.ht_away) > (r.ht_home + r.ht_away)),
    'home': ('Home to win (1)', 'Match Winner', ['Home'], lambda r: r.ft_home > r.ft_away),
    'away': ('Away to win (2)', 'Match Winner', ['Away'], lambda r: r.ft_away > r.ft_home),
    'win': ('Home win or Away win, whichever is priced about 2.00', '', [], None),
    'over25': ('Over 2.5', 'Goals Over/Under', ['Over 2.5'], lambda r: r.ft_home + r.ft_away >= 3),
    'gg': ('GG - both teams score', 'Both Teams Score', ['Yes'], lambda r: (r.ft_home >= 1) & (r.ft_away >= 1)),
}
FLEX = {11: 8.0, 12: 19.17, 13: 54.0, 14: 194.0, 15: 897.0, 16: 5691.59, 17: 55000.0}     # the payout table from the SportyBet slip (18 picks)
KINDS = ['favB', 'favS', 'drawB', 'o25B', 'comp', 'cat']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--day', required=True); ap.add_argument('--options', default='hsh2,home,away,win')
    ap.add_argument('--picks', type=int, default=18); ap.add_argument('--lo', type=float, default=1.90); ap.add_argument('--hi', type=float, default=2.40)
    a = ap.parse_args()
    D = B.DATA
    oa = D / 'odds_all.csv'
    oa = oa if oa.exists() else D / 'odds_all.csv.gz'
    odds = pd.read_csv(oa).drop_duplicates(['fixture_id', 'bookmaker', 'market', 'selection']); odds = odds[pd.to_numeric(odds.odd, errors='coerce') > 1.0]
    fr = [pd.read_csv(D / f) for f in ('fixtures.csv', 'history.csv') if (D / f).exists()]
    fxt = pd.concat(fr).drop_duplicates('fixture_id').set_index('fixture_id')
    done = fxt[fxt.status.isin(['FT', 'AET', 'PEN'])].dropna(subset=['ft_home', 'ft_away', 'ht_home', 'ht_away'])
    fx = B.features(odds[odds.fixture_id.isin(done.index)], done[['date', 'kickoff', 'league', 'country', 'home', 'away', 'ft_home', 'ft_away', 'ht_home', 'ht_away']])
    days = sorted(fx.date.unique())
    print(f'Data in {D}: {len(fx)} finished matches with prices, days {days[0]} to {days[-1]}')
    if a.day not in days:
        sys.exit(f'No matches for {a.day}. Days available: {", ".join(days)}')
    before = [d for d in days if d < a.day]
    if not before:
        sys.exit(f'{a.day} is the first day in the data, so there is nothing to learn from before it. Choose a later day.')
    print(f'TEST DAY {a.day}.  Learning only from: {", ".join(before)}\n')
    for key in a.options.split(','):
        name, mk, sels, won = OPTIONS[key]
        if key == 'win':            # home win and away win together: whichever side is priced around 2.00
            parts = []
            for k2 in ('home', 'away'):
                _, mk2, sels2, won2 = OPTIONS[k2]
                pr2 = odds[(odds.market == mk2) & odds.selection.isin(sels2)].groupby('fixture_id').odd.median().rename('price')
                g2 = fx.join(pr2, how='inner'); g2 = g2[(g2.price >= a.lo) & (g2.price <= a.hi)].copy(); g2['won'] = won2(g2).astype(int); g2['side'] = '1' if k2 == 'home' else '2'
                parts.append(g2)
            g = pd.concat(parts).sort_values('price'); g = g[~g.index.duplicated()]
        else:
            pr = odds[(odds.market == mk) & odds.selection.isin(sels)].groupby('fixture_id').odd.median().rename('price')
            g = fx.join(pr, how='inner'); g = g[(g.price >= a.lo) & (g.price <= a.hi)].copy(); g['won'] = won(g).astype(int); g['side'] = ''
        tr, te = g[g.date < a.day], g[g.date == a.day]
        print('=' * 110); print(f'{name}   (priced {a.lo:.2f}-{a.hi:.2f})')
        print(f'  Before the test day: {len(tr)} picks, {tr.won.mean() * 100:.1f}% won.   On the test day: {len(te)} matches to choose from.')
        if len(te) < a.picks or len(tr) < 100:
            print('  Not enough matches for an 18-pick ticket.\n'); continue
        # LEARN: score each kind of match on the earlier days (shrunk towards the overall rate so tiny groups cannot dominate)
        base = tr.won.mean(); score = pd.Series(0.0, index=te.index); used = []
        for k in KINDS:
            st = tr.groupby(k).won.agg(['sum', 'count']); rate = (st['sum'] + 20 * base) / (st['count'] + 20)
            score += te[k].map(rate).fillna(base).values - base
            b = rate.idxmax(); used.append(f'{b} {st.loc[b, "sum"] / st.loc[b, "count"] * 100:.0f}% of {int(st.loc[b, "count"])}')
        print('  Kinds of match that won most before: ' + ' | '.join(used))
        pick = te.assign(score=score).sort_values(['score', 'price'], ascending=[False, True]).head(a.picks).copy()
        pick['_k'] = pd.to_datetime(pick.kickoff, errors='coerce'); pick = pick.sort_values('_k')
        print(f'\n  {"Time":<7}{"Match":<52}{"Pick":<5}{"Odds":>5}  {"HT":>5} {"FT":>5}  Result')
        for _, r in pick.iterrows():
            kt = pd.to_datetime(r.kickoff, errors='coerce')
            print(f'  {(kt.strftime("%H:%M") if pd.notna(kt) else ""):<7}{(str(r.home) + " - " + str(r.away))[:50]:<52}{r.side:<5}{r.price:>5.2f}  {int(r.ht_home)}-{int(r.ht_away):<3} {int(r.ft_home)}-{int(r.ft_away):<3}  {"WON" if r.won else "lost"}')
        w = int(pick.won.sum()); n = len(pick)
        print(f'\n  RESULT: {w} of {n} won, {n - w} lost (cut {n - w}).  Average odds {pick.price.mean():.2f}.')
        if n == 18:
            print('  FLEX: ' + (f'needs 11. With {w} right the ticket pays about {FLEX.get(w, 262144):,.2f} odds at that cut level.' if w >= 11 else f'needs 11. With {w} right the ticket LOSES on every cut level.'))
        rest = te.drop(pick.index)
        print(f'  For comparison, the {len(rest)} matches NOT picked that day won {rest.won.mean() * 100:.1f}%; the 18 picked won {w / n * 100:.1f}%.\n')


if __name__ == '__main__':
    main()
