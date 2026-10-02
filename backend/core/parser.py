import re
from dataclasses import dataclass, asdict

@dataclass
class Match:
    match_id: str | None
    home: str
    away: str
    home_goals: int | None
    away_goals: int | None
    H: float
    D: float
    A: float
    status: str
    raw: str

# Supports both the original Flashscore markdown export and the compact/plain-text
# format produced when Flashscore text is copied from a browser.
SCORE_MD_RE = re.compile(r'\[\*\*\s*(\d+)\s*-\s*(\d+)(?:aet)?\s*\*\*\]', re.I)
PENDING_MD_RE = re.compile(r'\[\*\*\s*-\s*\*\*\]')
ID_RE = re.compile(r'flashscore\.mobi/match/([^/?]+)', re.I)
ODD_MD_RE = re.compile(r'\[\s*\*{0,2}(\d+(?:\.\d+)?)\*{0,2}\s*\]\(')
ODD_PLAIN_RE = re.compile(r'\[\s*(\d+(?:\.\d+)?)\s*\|\s*(\d+(?:\.\d+)?)\s*\|\s*(\d+(?:\.\d+)?)\s*\]\s*$')
TIME_PREFIX = re.compile(r'^\s*(?:\d{1,2}:\d{2})?\s*', re.I)
LIVE_PREFIX = re.compile(r"^\s*(?:\d{1,3}(?:\+\d{1,2})?['’]|HT\b|LIVE\b)", re.I)
STATUS_WORD = re.compile(r'(?:Postponed|Cancelled|Canceled|Abandoned|Interrupted|Walkover|Awarded|Suspended|Delayed)', re.I)
LINK_SCORE = re.compile(r'\s*\[\*\*.*?\]\(https?://www\.flashscore\.mobi/match/.*$', re.I)
IMAGE = re.compile(r'\[image\]\([^)]*\)', re.I)
PLAIN_SCORE_END = re.compile(r'\s+(\d+)\s*-\s*(\d+)(?:\s*(?:AET|PEN))?\s*$', re.I)
PENDING_DASH_END = re.compile(r'\s+-\s*$')


def _plain_payload(line: str):
    """Return (prefix_without_odds, H,D,A) for compact copied rows."""
    m = ODD_PLAIN_RE.search(line)
    if not m:
        return None
    return line[:m.start()].rstrip(), tuple(float(x) for x in m.groups())


def _teams_markdown(line: str):
    s = IMAGE.sub('', line)
    s = TIME_PREFIX.sub('', s)
    s = LINK_SCORE.sub('', s)
    s = re.split(r'\[\*\*', s, 1)[0]
    parts = re.split(r'\s+-\s+', s.strip(), maxsplit=1)
    if len(parts) != 2:
        return None, None
    return parts[0].strip(), parts[1].strip()


def _teams_plain(prefix: str, status: str):
    s = TIME_PREFIX.sub('', prefix).strip()
    if status == 'completed':
        s = PLAIN_SCORE_END.sub('', s).strip()
    elif status == 'upcoming':
        s = PENDING_DASH_END.sub('', s).strip()
    parts = re.split(r'\s+-\s+', s, maxsplit=1)
    if len(parts) != 2:
        return None, None
    return parts[0].strip(), parts[1].strip()


def parse_text(text: str):
    matches, rejected = [], []
    for ln, line in enumerate(text.splitlines(), 1):
        raw = line.rstrip()
        if not raw.strip():
            continue

        mid_m = ID_RE.search(raw)
        mid = mid_m.group(1) if mid_m else None

        # Original markdown format.
        md_odds = [float(x) for x in ODD_MD_RE.findall(raw)]
        md_score = SCORE_MD_RE.search(raw)
        md_pending = PENDING_MD_RE.search(raw)
        if mid_m and len(md_odds) >= 3 and (md_score or md_pending):
            home, away = _teams_markdown(raw)
            if not home or not away:
                rejected.append({'line': ln, 'reason': 'teams_not_detected', 'raw': raw})
                continue
            if md_score:
                hg, ag = map(int, md_score.groups()); status = 'completed'
            else:
                hg = ag = None; status = 'upcoming'
            matches.append(Match(mid, home, away, hg, ag, *md_odds[:3], status, raw))
            continue

        # Plain copied format: Home - Away - [H | X | A] or Home - Away 2-1 [H | X | A]
        payload = _plain_payload(raw)
        if not payload:
            # Ignore headings/no-odds rows; report match-like rows missing odds.
            if re.search(r'\s+-\s+', raw) and not re.search(r'\bStandings\b', raw, re.I):
                rejected.append({'line': ln, 'reason': 'missing_H_X_A_odds', 'raw': raw})
            continue
        prefix, (H, D, A) = payload

        # Never treat obvious live/status rows as prospective fixtures.
        no_time = TIME_PREFIX.sub('', prefix).strip()
        if LIVE_PREFIX.search(no_time) or STATUS_WORD.search(prefix):
            rejected.append({'line': ln, 'reason': 'live_or_nonstandard_status', 'raw': raw})
            continue

        score = PLAIN_SCORE_END.search(prefix)
        if score:
            status = 'completed'; hg, ag = map(int, score.groups())
        elif PENDING_DASH_END.search(prefix):
            status = 'upcoming'; hg = ag = None
        else:
            rejected.append({'line': ln, 'reason': 'status_not_detected', 'raw': raw})
            continue

        home, away = _teams_plain(prefix, status)
        if not home or not away:
            rejected.append({'line': ln, 'reason': 'teams_not_detected', 'raw': raw})
            continue
        matches.append(Match(mid, home, away, hg, ag, H, D, A, status, raw))

    return matches, rejected


def to_dicts(matches):
    return [asdict(m) for m in matches]
