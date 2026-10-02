import hashlib
import re
from dataclasses import dataclass

@dataclass
class TennisMatch:
    match_id: str
    player1: str
    player2: str
    H: float | None
    A: float | None
    status: str
    competition: str
    s1: int | None = None
    s2: int | None = None

_BAD_STATUS = ('CANCELLED', 'RETIRED', 'ABANDONED', 'SUSPENDED', 'INTERRUPTED', 'POSTPONED', 'DELAYED', ' WALKOVER ', ' WO ')

def _plain(line: str) -> str:
    # Remove image markdown and turn markdown links into their visible labels.
    line = re.sub(r'\[image\]\([^)]*\)', '', line, flags=re.I)
    line = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', line)
    return line.replace('**', '').replace('\xa0', ' ').strip()

def _synthetic_id(comp: str, time_: str, p1: str, p2: str) -> str:
    key = f'{comp}|{time_}|{p1}|{p2}'.lower().encode('utf-8')
    return 'paste-' + hashlib.sha1(key).hexdigest()[:16]

def parse_tennis_text(text):
    """Parse Flashscore tennis from either copied markdown or rendered plain text.

    Singles only. Upcoming fixtures require two-way odds. Live/interrupted/cancelled
    rows are rejected. If a copied plain-text row has no Flashscore URL, a stable
    synthetic ID is created from competition/time/player names.
    """
    out, rejected, comp = [], [], ''
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        clean = _plain(line)

        # Markdown and rendered-copy section headings.
        if line.startswith('####'):
            comp = re.sub(r'^####\s*', '', clean).strip()
            continue
        upper_clean = clean.upper()
        if ('SINGLES:' in upper_clean or 'DOUBLES:' in upper_clean) and not re.match(r'^\d{1,2}:\d{2}', clean):
            comp = clean.lstrip('# ').strip()
            continue

        # Only fixture-looking rows continue.
        tm = re.match(r'^(\d{1,2}:\d{2})', clean)
        if not tm:
            continue
        time_ = tm.group(1)

        if 'DOUBLES' in comp.upper() or '/' in clean.split('[', 1)[0]:
            rejected.append({'raw': raw, 'reason': 'doubles'})
            continue
        up = f' {upper_clean} '
        if any(x in up for x in _BAD_STATUS) or re.search(r'\bSET\s*\d+\b', up):
            rejected.append({'raw': raw, 'reason': 'live/non-standard status'})
            continue

        # Odds: markdown form first, then rendered/plain bracket form.
        odds = [float(x) for x in re.findall(r'\[\s*\*{0,2}(\d+\.\d+)\*{0,2}\s*\]\(', line)]
        if len(odds) < 2:
            brackets = re.findall(r'\[([^\]]+)\]', clean)
            for b in reversed(brackets):
                nums = re.findall(r'(?<!\d)(\d+\.\d+)(?!\d)', b)
                if len(nums) >= 2:
                    odds = [float(nums[0]), float(nums[1])]
                    break
        if len(odds) < 2:
            rejected.append({'raw': raw, 'reason': 'missing 2-way odds'})
            continue

        # Final set score if present. A dash/blank score means upcoming.
        score = re.search(r'\[\*{0,2}(\d+)\s*-\s*(\d+)\*{0,2}\]', line)
        if not score:
            # In rendered text, score may be a bare 2-0/2-1 before odds.
            pre_odds = clean.rsplit('[', 1)[0]
            score = re.search(r'\s(\d+)\s*-\s*(\d+)\s*$', pre_odds)

        # Isolate names. Markdown source has the cleanest boundary; rendered copy
        # uses the last odds bracket as the boundary.
        md_name = re.search(r'^(?:\d{1,2}:\d{2})(.*?)(?:\s+\[\*\*(?:\d+\s*-\s*\d+|\s*-\s*)\*\*\])', line)
        if md_name:
            body = md_name.group(1).strip()
            body = _plain(body)
        else:
            body = clean[len(time_):].strip()
            # Remove trailing odds [ x.xx | y.yy ].
            body = re.sub(r'\s*\[\s*\[?\s*\d+\.\d+\s*\]?\s*\|\s*\[?\s*\d+\.\d+\s*\]?\s*\]\s*$', '', body).strip()
            # Remove blank upcoming score marker, or a completed set score.
            body = re.sub(r'\s*\[?\s*-\s*\]?\s*$', '', body).strip()
            body = re.sub(r'\s+\d+\s*-\s*\d+\s*$', '', body).strip()
        names = body.split(' - ', 1)
        if len(names) != 2 or not names[0].strip() or not names[1].strip():
            rejected.append({'raw': raw, 'reason': 'missing player names'})
            continue
        p1, p2 = names[0].strip(), names[1].strip()

        mid = re.search(r'flashscore\.mobi/match/([^/?]+)', line)
        match_id = mid.group(1) if mid else _synthetic_id(comp, time_, p1, p2)
        status = 'completed' if score else 'upcoming'
        s1 = s2 = None
        if score:
            s1, s2 = map(int, score.groups())
        out.append(TennisMatch(match_id, p1, p2, odds[0], odds[1], status, comp, s1, s2))
    return out, rejected
