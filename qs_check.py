"""Compare the engine's ticket statuses with settle.py, using today's results.  Run from the v22 folder:
    python qs_check.py
"""
import csv
import json
from collections import Counter

from settle import settle_leg, settle_ticket

d = json.load(open("public/research/models.json", encoding="utf-8"))
R = {r["fixture_id"]: r for r in csv.DictReader(open("data/live_results.csv", encoding="utf-8"))}
today = d["daily10"]["today"]
mismatch, counts = 0, Counter()
for n, t in enumerate(today["tickets"], 1):
    res = []
    for l in t["legs"]:
        row = R.get(str(l["fid"]))
        mine = settle_leg(l["market"], str(l.get("selection") or l.get("pick", "")), row)
        engine = l.get("status", "PENDING")
        res.append(mine)
        counts[mine] += 1
        if mine != "PENDING" or engine != "PENDING":
            score = f"HT {row.get('ht_home')}-{row.get('ht_away')} FT {row.get('ft_home') or '-'}-{row.get('ft_away') or '-'}" if row else "no row"
            flag = "" if mine == engine else "   <-- DIFFERENT"
            mismatch += mine != engine
            print(f"T{n:<2} {l['match'][:34]:<34} {l['market'][:30]:<30} {str(l.get('selection'))[:14]:<14} "
                  f"{score:<16} settle.py={mine:<9} engine={engine}{flag}")
    print(f"T{n:<2} ticket: settle.py={settle_ticket(res)} · engine={t.get('status', 'PENDING')}")
print("\nLegs by settle.py:", dict(counts), f"· differences: {mismatch}")
