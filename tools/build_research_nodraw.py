"""
QuantSport Research Lab - No-Draw (12) signal builder.

Reads your collector data (Documents/QuantSport_Data) and writes
public/research/nodraw.json, which the website page /admin/research displays.

Two kinds of picks:
  BACKTEST  - predictions downloaded AFTER the matches (predictions.csv). Not proof.
  LIVE      - predictions captured BEFORE kick-off by QS_PreMatch_Snapshot.ps1 (prematch folder). This is the real test.

Signal: API-Football gives its placeholder prediction (33/33/33 or 35/35/30)  ->  paper-bet "12" (home or away, no draw)
at the best available Double Chance Home/Away price. Settled on the 90-minute score.

Run from the v22 folder (with the .venv active):
  python tools\\build_research_nodraw.py
"""
import json, os, sys, glob
from pathlib import Path
import pandas as pd

DATA = Path(os.environ.get('QS_DATA', Path.home() / 'Documents' / 'QuantSport_Data'))
OUT = Path(__file__).resolve().parent.parent / 'public' / 'research' / 'nodraw.json'
DONE = {'FT', 'AET', 'PEN'}


def is_placeholder(h, d, a):
    h, d, a = str(h).strip(), str(d).strip(), str(a).strip()
    return (h, d, a) in {('33%', '33%', '33%'), ('35%', '35%', '30%')}


def best_12(odds):
    if odds is None or odds.empty:
        return pd.Series(dtype=float)
    o = odds[(odds['market'] == 'Double Chance') & (odds['selection'].isin(['Home/Away', 'Away/Home']))].copy()
    o['odd'] = pd.to_numeric(o['odd'], errors='coerce')
    o = o[o['odd'] > 1.0]
    return o.groupby('fixture_id')['odd'].max()


def load_results():
    frames = []
    for f in [DATA / 'fixtures.csv', DATA / 'history.csv']:
        if f.exists():
            frames.append(pd.read_csv(f, usecols=lambda c: c in {'fixture_id', 'date', 'status', 'league', 'country', 'home', 'away', 'ft_home', 'ft_away', 'kickoff'}))
    if not frames:
        sys.exit(f'No fixtures.csv/history.csv found in {DATA}')
    r = pd.concat(frames).drop_duplicates('fixture_id', keep='first').set_index('fixture_id')
    return r


def settle(row):
    if row.get('status') not in DONE or pd.isna(row.get('ft_home')) or pd.isna(row.get('ft_away')):
        return 'PENDING', None
    hg, ag = int(row['ft_home']), int(row['ft_away'])
    return ('WON' if hg != ag else 'LOST'), f'{hg}-{ag}'


def main():
    res = load_results()
    picks = []

    # ---------- BACKTEST (predictions fetched after the matches) ----------
    pf = DATA / 'predictions.csv'
    if pf.exists() and (DATA / 'odds.csv').exists():
        p = pd.read_csv(pf).drop_duplicates('fixture_id')
        b12 = best_12(pd.read_csv(DATA / 'odds.csv'))
        for r in p.itertuples():
            if not is_placeholder(r.pct_home, r.pct_draw, r.pct_away) or r.fixture_id not in b12.index or r.fixture_id not in res.index:
                continue
            f = res.loc[r.fixture_id]
            status, score = settle(f)
            picks.append(dict(source='BACKTEST', fixture_id=int(r.fixture_id), date=str(f['date']), league=f"{f.get('country', '')}: {f.get('league', '')}",
                              home=f['home'], away=f['away'], api=f'{r.pct_home}/{r.pct_draw}/{r.pct_away}', odds=round(float(b12[r.fixture_id]), 2),
                              status=status, score=score))

    # ---------- LIVE (predictions captured before kick-off) ----------
    pre = DATA / 'prematch'
    for pfile in sorted(glob.glob(str(pre / 'predictions_*.csv'))):
        day = Path(pfile).stem.replace('predictions_', '')
        p = pd.read_csv(pfile)
        fxf, odf = pre / f'fixtures_{day}.csv', pre / f'odds_{day}.csv'
        if not fxf.exists() or not odf.exists() or p.empty:
            continue
        fx = pd.read_csv(fxf).set_index('fixture_id')
        b12 = best_12(pd.read_csv(odf))
        for r in p.itertuples():
            if not is_placeholder(r.pct_home, r.pct_draw, r.pct_away) or r.fixture_id not in fx.index or r.fixture_id not in b12.index:
                continue
            f = fx.loc[r.fixture_id]
            ko = pd.to_datetime(f['kickoff'], errors='coerce')
            snap = pd.to_datetime(r.snapshot, errors='coerce')
            if pd.notna(ko) and pd.notna(snap) and (ko.tz_localize(None) if ko.tzinfo else ko) <= snap:
                continue  # captured after kick-off -> not a valid pre-match pick
            if r.fixture_id in res.index:
                status, score = settle(res.loc[r.fixture_id])
            else:
                status, score = 'PENDING', None
            picks.append(dict(source='LIVE', fixture_id=int(r.fixture_id), date=day, league=f"{f.get('country', '')}: {f.get('league', '')}",
                              home=f['home'], away=f['away'], api=f'{r.pct_home}/{r.pct_draw}/{r.pct_away}', odds=round(float(b12[r.fixture_id]), 2),
                              kickoff=str(f['kickoff']), snapshot=str(r.snapshot), status=status, score=score))

    # live pick wins over backtest duplicate of same fixture
    seen, out = set(), []
    for pk in sorted(picks, key=lambda x: 0 if x['source'] == 'LIVE' else 1):
        if pk['fixture_id'] in seen:
            continue
        seen.add(pk['fixture_id']); pk['profit'] = None if pk['status'] == 'PENDING' else round(pk['odds'] - 1 if pk['status'] == 'WON' else -1.0, 2)
        out.append(pk)
    out.sort(key=lambda x: (x['date'], x.get('kickoff', ''), x['home']), reverse=True)

    def summary(rows):
        s = [x for x in rows if x['status'] != 'PENDING']
        won = sum(x['status'] == 'WON' for x in s)
        profit = round(sum(x['profit'] for x in s), 2)
        return dict(picks=len(rows), settled=len(s), won=won, lost=len(s) - won, pending=len(rows) - len(s),
                    hit=round(won / len(s) * 100, 1) if s else None, profit=profit, roi=round(profit / len(s) * 100, 1) if s else None,
                    avg_odds=round(sum(x['odds'] for x in rows) / len(rows), 2) if rows else None)

    days = {}
    for x in out:
        days.setdefault((x['date'], x['source']), []).append(x)
    daily = [dict(date=d, source=s, **summary(v)) for (d, s), v in sorted(days.items(), reverse=True)]
    data = dict(generated=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'), signal='API placeholder (33/33/33 or 35/35/30) -> No Draw (12)',
                rules='Best Double Chance Home/Away price across 7 bookmakers. Settled on 90-minute score. 1 unit per pick. LIVE = captured before kick-off.',
                summary={'LIVE': summary([x for x in out if x['source'] == 'LIVE']), 'BACKTEST': summary([x for x in out if x['source'] == 'BACKTEST'])},
                daily=daily, picks=out)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, default=str), encoding='utf-8')
    print(f"Wrote {OUT}")
    for k, v in data['summary'].items():
        print(f"  {k:8s} picks={v['picks']} settled={v['settled']} won={v['won']} hit={v['hit']}% profit={v['profit']}u ROI={v['roi']}%")


if __name__ == '__main__':
    main()
