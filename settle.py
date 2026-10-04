"""QuantSport settlement - every market on the tickets, settled from the results row.

settle_leg(market, selection, row) -> WON | LOST | VOID | HALF_WON | HALF_LOST | PENDING
  row: dict from data/live_results.csv (status, ht_home, ht_away, ft_home, ft_away)
  Half-time markets settle as soon as half-time is known (HT, 2H, FT...). Full-time markets need FT/AET/PEN
  and use the 90-minute score (ft_*), the standard for these markets. Cancelled/abandoned -> VOID.
Selections follow API-Football style values, e.g. "Home -0.75", "Over 2.5", "Home/Draw", "Yes", "Away".
"""
from __future__ import annotations

import re

HT_KNOWN = {"HT", "2H", "ET", "BT", "P", "FT", "AET", "PEN"}
FT_KNOWN = {"FT", "AET", "PEN"}
VOID_STATUS = {"PST", "CANC", "ABD", "AWD", "WO"}


def _num(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def _scores(row, part):
    h, a = _num(row.get(f"{part}_home")), _num(row.get(f"{part}_away"))
    return (h, a) if h is not None and a is not None else None


def _line(sel):
    m = re.search(r"([+-]?\d+(?:\.\d+)?)\s*$", sel.strip())
    return float(m.group(1)) if m else None


def _ah(margin, line):
    """Asian handicap for the picked side. margin = picked goals - other goals. Quarter lines split in two."""
    parts = [line - 0.25, line + 0.25] if abs(line * 4) % 2 == 1 else [line]
    res = []
    for p in parts:
        v = margin + p
        res.append(1 if v > 0 else 0 if v == 0 else -1)
    if len(res) == 1:
        return {1: "WON", 0: "VOID", -1: "LOST"}[res[0]]
    s = sorted(res)
    return {(1, 1): "WON", (-1, -1): "LOST", (0, 1): "HALF_WON", (-1, 0): "HALF_LOST"}.get(tuple(s), "VOID")


def _ou(total, sel):
    line = _line(sel)
    if line is None:
        return "PENDING"
    over = sel.lower().startswith("over")
    parts = [line - 0.25, line + 0.25] if abs(line * 4) % 2 == 1 else [line]
    res = [(1 if (total > p if over else total < p) else 0 if total == p else -1) for p in parts]
    if len(res) == 1:
        return {1: "WON", 0: "VOID", -1: "LOST"}[res[0]]
    return {(1, 1): "WON", (-1, -1): "LOST", (0, 1): "HALF_WON", (-1, 0): "HALF_LOST"}.get(tuple(sorted(res)), "VOID")


def _yes(sel):
    return sel.strip().lower() in ("yes", "y", "gg")


def settle_leg(market: str, selection: str, row: dict | None) -> str:
    if not row:
        return "PENDING"
    status = (row.get("status") or "").upper()
    if status in VOID_STATUS:
        return "VOID"
    m, sel = market.strip().lower(), selection.strip()
    first_half = "first half" in m or "1st half" in m
    second_half = "2nd half" in m or "second half" in m
    needs_ht = first_half or second_half or "either half" in m
    if first_half:
        if status not in HT_KNOWN:
            return "PENDING"
        sc = _scores(row, "ht")
    else:
        if status not in FT_KNOWN:
            return "PENDING"
        sc = _scores(row, "ft")
        if needs_ht and _scores(row, "ht") is None:
            return "PENDING"
    if sc is None:
        return "PENDING"
    h, a = sc
    if second_half:
        ht = _scores(row, "ht")
        h, a = h - ht[0], a - ht[1]
    side_home = sel.lower().startswith("home")

    if m.startswith("both teams score"):
        btts = h > 0 and a > 0
        return "WON" if btts == _yes(sel) else "LOST"
    if m.startswith("asian handicap"):
        line = _line(sel)
        if line is None:
            return "PENDING"
        return _ah((h - a) if side_home else (a - h), line)
    if m.startswith("handicap result"):                       # European 3-way: handicap applied to HOME
        line = _line(sel) or 0.0
        diff = h + line - a
        pick = sel.lower().split()[0]
        out = "home" if diff > 0 else "draw" if diff == 0 else "away"
        return "WON" if pick == out else "LOST"
    if m.startswith("to win either half"):
        ht = _scores(row, "ht")
        fh, fa = ft = _scores(row, "ft")
        h1, a1, h2, a2 = ht[0], ht[1], fh - ht[0], fa - ht[1]
        won = (h1 > a1 or h2 > a2) if side_home else (a1 > h1 or a2 > h2)
        return "WON" if won else "LOST"
    if m.startswith("clean sheet - home"):
        return "WON" if (a == 0) == _yes(sel) else "LOST"
    if m.startswith("clean sheet - away"):
        return "WON" if (h == 0) == _yes(sel) else "LOST"
    if m.startswith("double chance"):
        res = "home" if h > a else "draw" if h == a else "away"
        opts = [x.strip().lower() for x in re.split(r"[/]", sel)]
        alias = {"1": "home", "x": "draw", "2": "away"}
        return "WON" if res in [alias.get(o, o) for o in opts] else "LOST"
    if "score in both halves" in m:                           # "Home/Away team will score in both halves"
        ht, ft = _scores(row, "ht"), _scores(row, "ft")
        if ht is None or ft is None:
            return "PENDING"
        k = 0 if m.startswith("home") else 1
        both = ht[k] > 0 and (ft[k] - ht[k]) > 0
        return "WON" if both == _yes(sel) else "LOST"
    if "odd/even" in m:                                        # "Odd/Even", "Home Odd/Even", "Away Odd/Even"
        goals = h if m.startswith("home") else a if m.startswith("away") else h + a
        return "WON" if ("even" if goals % 2 == 0 else "odd") == sel.strip().lower() else "LOST"
    if "team total goals" in m or "total - home" in m or "total - away" in m:
        team = h if m.startswith("home") or "home" in m.split("team")[0] else a
        return _ou(team, sel)
    if "over/under" in m:
        return _ou(h + a, sel)
    return "PENDING"                                            # unknown market: never guess


def settle_ticket(leg_results: list[str]) -> str:
    """Accumulator: any LOST -> LOST; all decided -> WON (VOID legs drop out, half results noted)."""
    if any(r == "LOST" for r in leg_results):
        return "LOST"
    if any(r == "PENDING" for r in leg_results):
        return "PENDING"
    if all(r == "VOID" for r in leg_results):
        return "VOID"
    if any(r in ("HALF_WON", "HALF_LOST") for r in leg_results):
        return "WON (reduced)" if not any(r == "HALF_LOST" for r in leg_results) else "PARTIAL"
    return "WON"
