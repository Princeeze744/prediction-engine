"""Independently re-settle PAST days (daily10.history) and compare with what the engine/website shows.
Run from the v22 folder:   python qs_verify.py
"""
import csv
import json

from settle import settle_leg, settle_ticket

d = json.load(open("public/research/models.json", encoding="utf-8"))
R = {r["fixture_id"]: r for r in csv.DictReader(open("data/live_results.csv", encoding="utf-8"))}
for day in d["daily10"]["history"]:
    print(f"\n===== {day['date']} =====")
    agree = disagree = missing = 0
    for n, t in enumerate(day["tickets"], 1):
        mine = []
        for l in t["legs"]:
            row = R.get(str(l["fid"]))
            m = settle_leg(l["market"], str(l.get("selection") or l.get("pick", "")), row)
            e = l.get("status", "PENDING")
            mine.append(m)
            if row is None:
                missing += 1
            if m == e:
                agree += 1
                continue
            disagree += 1
            sc = (f"HT {row.get('ht_home') or '?'}-{row.get('ht_away') or '?'} "
                  f"FT {row.get('ft_home') or '?'}-{row.get('ft_away') or '?'} [{row.get('status')}]") if row else "NO SCORE ROW"
            print(f"  T{n:<2} {l['match'][:32]:<32} {l['market'][:30]:<30} {str(l.get('selection'))[:12]:<12} "
                  f"{sc:<26} settle.py={m:<9} engine={e}")
        tm, te = settle_ticket(mine), t.get("status", "PENDING")
        print(f"  T{n:<2} TICKET  settle.py={tm:<10} engine={te}{'' if tm == te or (tm.startswith('WON') and te == 'WON') else '   <-- CHECK'}")
    print(f"  legs agreeing: {agree} · differing: {disagree} · legs with no score row: {missing}")
