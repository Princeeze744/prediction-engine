"""QuantSport - quick results refresh.
Fetches the scores of today's and yesterday's matches (2 API calls) and saves them to data/live_results.csv,
so tickets and picks can be marked Won/Lost on the same day, a couple of hours after each match ends.
Usage:  python tools/refresh_results.py      (needs APIFOOTBALL_KEY; uses QS_DATA like build_models.py)
"""
import csv, json, os, re, sys, urllib.request
from datetime import datetime, timedelta
from pathlib import Path

DATA = Path(os.environ.get('QS_DATA', Path.home() / 'Documents' / 'QuantSport_Data'))
KEY = re.sub(r'\s', '', os.environ.get('APIFOOTBALL_KEY', ''))
COLS = ['fixture_id', 'date', 'kickoff', 'status', 'league_id', 'league', 'country', 'season', 'round', 'home', 'away', 'home_id', 'away_id',
        'ft_home', 'ft_away', 'ht_home', 'ht_away', 'et_home', 'et_away', 'pen_home', 'pen_away', 'goals_home', 'goals_away']


def day_rows(day):
    req = urllib.request.Request(f'https://v3.football.api-sports.io/fixtures?date={day}&timezone=Africa/Lagos', headers={'x-apisports-key': KEY})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    if d.get('errors'):
        raise RuntimeError(f'API error: {d["errors"]}')
    for m in d.get('response', []):
        s = m['score']
        yield [m['fixture']['id'], day, m['fixture']['date'], m['fixture']['status']['short'], m['league']['id'], m['league']['name'], m['league']['country'],
               m['league']['season'], m['league']['round'], m['teams']['home']['name'], m['teams']['away']['name'], m['teams']['home']['id'], m['teams']['away']['id'],
               s['fulltime']['home'], s['fulltime']['away'], s['halftime']['home'], s['halftime']['away'], s['extratime']['home'], s['extratime']['away'],
               s['penalty']['home'], s['penalty']['away'], m['goals']['home'], m['goals']['away']]


def main():
    if not KEY:
        sys.exit('APIFOOTBALL_KEY is not set')
    now = datetime.now()
    rows = []
    for back in (0, 1):
        day = (now - timedelta(days=back)).strftime('%Y-%m-%d')
        got = list(day_rows(day)); rows += got
        print(f'  {day}: {len(got)} matches, {sum(1 for r in got if r[3] in ("FT", "AET", "PEN"))} finished')
    if not rows:
        sys.exit('No matches returned - keeping the previous file')
    DATA.mkdir(parents=True, exist_ok=True)
    with open(DATA / 'live_results.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(COLS); w.writerows(rows)
    print(f'Saved {len(rows)} rows to {DATA / "live_results.csv"}')


if __name__ == '__main__':
    main()
