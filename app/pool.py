"""
Core logic for the "Beat the AI" World Cup pool.

Wraps the existing statistical engine (src/) without modifying it:
  - AI match odds come straight from MatchModel.p_win / p_draw
  - Human picks are stored in a flat JSON file (no DB — hackathon friendly)
  - Both humans and the AI are scored with the same multi-class Brier score,
    so the leaderboard is a genuine "can you out-predict the model?" contest.
"""

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

from src.api_client import SportsPredictClient, EVENT_ID
from src.team_data import get_stats, CODE_TO_NAME, TEAM_STATS, name_to_code
from src.models import MatchModel

DATA_DIR = Path(__file__).parent / "data"
STORE_PATH = DATA_DIR / "pool.json"
_LOCK = threading.Lock()

# Outcomes, in fixed order — used for the Brier probability vector.
OUTCOMES = ("a", "draw", "b")

# Live tournament API. Override the key with SPORTSPREDICT_API_KEY;
# set PC_USE_LIVE=0 to force the curated demo slate instead.
API_KEY = os.environ.get(
    "SPORTSPREDICT_API_KEY",
    "sp_live_d8b6fec43ffe8ae49b0c3af62076eb3a04365ff78736ee3463aa4ee6bf027321",
)
USE_LIVE = os.environ.get("PC_USE_LIVE", "1") != "0"
_SLATE_TTL = 300  # seconds — re-poll the live fixture list at most this often


# --------------------------------------------------------------------------- #
# Match slate                                                                  #
# --------------------------------------------------------------------------- #
# A curated slate of marquee fixtures. Stable IDs so picks and results survive
# restarts. This is the reliable demo default; it needs no network access —
# every probability below is computed locally by the model.
DEMO_FIXTURES = [
    ("m01", "ARG", "BRA", "Jun 12 · Group A"),
    ("m02", "FRA", "ENG", "Jun 12 · Group B"),
    ("m03", "ESP", "GER", "Jun 13 · Group C"),
    ("m04", "POR", "NED", "Jun 13 · Group D"),
    ("m05", "USA", "MEX", "Jun 14 · Group E"),
    ("m06", "BEL", "CRO", "Jun 14 · Group F"),
    ("m07", "MAR", "JPN", "Jun 15 · Group G"),
    ("m08", "URU", "COL", "Jun 15 · Group H"),
]


def ai_odds(code_a: str, code_b: str) -> dict:
    """Return normalized AI probabilities {a, draw, b} for a match."""
    model = MatchModel(get_stats(code_a), get_stats(code_b), code_a, code_b)
    p_a = model.p_win("a")
    p_b = model.p_win("b")
    p_d = model.p_draw()
    total = p_a + p_b + p_d or 1.0
    return {"a": p_a / total, "draw": p_d / total, "b": p_b / total}


def rationale(code_a: str, code_b: str, odds: dict) -> str:
    """
    A one-line, human-readable 'why' for the AI's odds, built from the same
    model internals that produced them. Explains the favorite in plain English.
    """
    model = MatchModel(get_stats(code_a), get_stats(code_b), code_a, code_b)
    fav = max(OUTCOMES, key=lambda o: odds[o])

    if fav == "draw":
        return (f"Evenly matched — expected goals {model.mu_goals_a:.1f}–{model.mu_goals_b:.1f}, "
                f"so a draw is the single most likely result.")

    # Orient everything toward the favored side.
    if fav == "a":
        fav_c, dog_c, mu_f, mu_d = code_a, code_b, model.mu_goals_a, model.mu_goals_b
    else:
        fav_c, dog_c, mu_f, mu_d = code_b, code_a, model.mu_goals_b, model.mu_goals_a

    fav_s, dog_s = get_stats(fav_c), get_stats(dog_c)
    reasons = []

    elo_gap = fav_s["elo"] - dog_s["elo"]
    if elo_gap >= 40:
        reasons.append(f"a {elo_gap:.0f}-point Elo edge")

    if fav_s["attack"] - dog_s["attack"] >= 0.25:
        reasons.append(f"the stronger attack ({fav_s['attack']:.1f} vs {dog_s['attack']:.1f} goals/game)")

    # Lower 'defense' = fewer goals conceded = better defense.
    if dog_s["defense"] - fav_s["defense"] >= 0.20:
        reasons.append(f"a tighter defense ({fav_s['defense']:.1f} vs {dog_s['defense']:.1f} conceded)")

    lead = f"{team_name(fav_c)} {odds[fav] * 100:.0f}%"
    xg = f"projected scoreline {mu_f:.1f}–{mu_d:.1f}"

    if reasons:
        joined = reasons[0] if len(reasons) == 1 else ", ".join(reasons[:-1]) + f" and {reasons[-1]}"
        return f"{lead} — {joined}; {xg}."
    return f"{lead} — marginally favored on form; {xg}."


def team_name(code: str) -> str:
    return CODE_TO_NAME.get(code, code)


def _build_match(mid: str, code_a: str, code_b: str, when: str) -> dict:
    """Assemble one match dict with locally-computed AI odds + rationale."""
    odds = ai_odds(code_a, code_b)
    return {
        "id": mid,
        "team_a": code_a,
        "team_b": code_b,
        "name_a": team_name(code_a),
        "name_b": team_name(code_b),
        "when": when,
        "ai": {k: round(v * 100, 1) for k, v in odds.items()},
        "ai_favorite": max(OUTCOMES, key=lambda o: odds[o]),
        "ai_rationale": rationale(code_a, code_b, odds),
    }


def _demo_matches() -> list[dict]:
    return [_build_match(mid, a, b, when) for mid, a, b, when in DEMO_FIXTURES]


def _resolve_code(part: str) -> str:
    """Map an API team token ('NOR' or 'Norway') to a TEAM_STATS code."""
    part = part.strip()
    if part in TEAM_STATS:
        return part
    return name_to_code(part) or part


def _fmt_when(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %d · %H:%M UTC")
    except Exception:
        return "Upcoming"


def fetch_live_matches() -> list[dict]:
    """Pull the real upcoming fixtures from the tournament API (may raise)."""
    client = SportsPredictClient(API_KEY)
    raw = client.list_matches(EVENT_ID) or []
    raw = sorted(raw, key=lambda m: m.get("opening_time", ""))
    matches = []
    for m in raw:
        parts = [p.strip() for p in m.get("name", "").split(" vs ")]
        if len(parts) != 2:
            continue
        a, b = _resolve_code(parts[0]), _resolve_code(parts[1])
        matches.append(_build_match(m["id"], a, b, _fmt_when(m.get("opening_time", ""))))
    return matches


# Remembers team codes for every match we've served, so the leaderboard can
# still score the AI on a settled match even if it later rotates out of the API.
_seen_teams: dict[str, tuple[str, str]] = {}
_slate_cache = {"matches": None, "ts": 0.0, "live": False}


def get_slate(force: bool = False) -> list[dict]:
    """Cached match slate: real fixtures when available, else the demo set."""
    now = time.time()
    fresh = _slate_cache["matches"] is not None and (now - _slate_cache["ts"]) < _SLATE_TTL
    if not (fresh and not force):
        matches, live = None, False
        if USE_LIVE:
            try:
                fetched = fetch_live_matches()
                if fetched:
                    matches, live = fetched, True
            except Exception:
                matches = None
        if not matches:
            matches = _demo_matches()
        _slate_cache.update(matches=matches, ts=now, live=live)

    for m in _slate_cache["matches"]:
        _seen_teams[m["id"]] = (m["team_a"], m["team_b"])
    return _slate_cache["matches"]


def build_matches() -> list[dict]:
    """The match slate with AI odds attached (live fixtures or demo fallback)."""
    return get_slate()


def is_live_slate() -> bool:
    get_slate()
    return _slate_cache["live"]


def _index() -> dict[str, dict]:
    return {m["id"]: m for m in get_slate()}


def get_match(match_id: str) -> dict | None:
    return _index().get(match_id)


# --------------------------------------------------------------------------- #
# Persistence                                                                  #
# --------------------------------------------------------------------------- #
def _load() -> dict:
    if STORE_PATH.exists():
        with open(STORE_PATH) as f:
            return json.load(f)
    return {"picks": {}, "results": {}}


def _save(state: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    tmp = STORE_PATH.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STORE_PATH)


def record_pick(user: str, match_id: str, pick: str) -> None:
    """Store (or overwrite) a user's pick for a match. pick ∈ {a, draw, b}."""
    user = user.strip()
    if not user:
        raise ValueError("Name required")
    if pick not in OUTCOMES:
        raise ValueError(f"Invalid pick: {pick!r}")
    if match_id not in _index():
        raise ValueError(f"Unknown match: {match_id!r}")
    with _LOCK:
        state = _load()
        state["picks"].setdefault(user, {})[match_id] = pick
        _save(state)


def set_result(match_id: str, outcome: str) -> None:
    """Settle a match. outcome ∈ {a, draw, b}. Used by the demo control."""
    if outcome not in OUTCOMES:
        raise ValueError(f"Invalid outcome: {outcome!r}")
    if match_id not in _index():
        raise ValueError(f"Unknown match: {match_id!r}")
    with _LOCK:
        state = _load()
        state["results"][match_id] = outcome
        _save(state)


def clear_results() -> None:
    with _LOCK:
        state = _load()
        state["results"] = {}
        _save(state)


# --------------------------------------------------------------------------- #
# Scoring                                                                      #
# --------------------------------------------------------------------------- #
def _brier(prob_vec: dict, outcome: str) -> float:
    """Multi-class Brier score: sum over outcomes of (p - actual)^2. Lower = better."""
    return sum((prob_vec[o] - (1.0 if o == outcome else 0.0)) ** 2 for o in OUTCOMES)


def _onehot(pick: str) -> dict:
    return {o: (1.0 if o == pick else 0.0) for o in OUTCOMES}


def leaderboard() -> dict:
    """
    Score every human and the AI on the same resolved matches with Brier score.
    Returns {players: [...], resolved_count: int}. Players sorted by avg Brier.
    """
    state = _load()
    results = state["results"]
    picks = state["picks"]

    rows = []

    # Human players
    for user, user_picks in picks.items():
        scored = [(mid, p) for mid, p in user_picks.items() if mid in results]
        if not scored:
            rows.append({"name": user, "is_ai": False, "picks": 0,
                         "avg_brier": None, "correct": 0, "total": 0})
            continue
        briers = [_brier(_onehot(p), results[mid]) for mid, p in scored]
        correct = sum(1 for mid, p in scored if p == results[mid])
        rows.append({
            "name": user, "is_ai": False, "picks": len(scored),
            "avg_brier": round(sum(briers) / len(briers), 4),
            "correct": correct, "total": len(scored),
        })

    # The AI, scored on every resolved match using its full probability vector
    index = _index()
    ai_scored = []
    for mid, outcome in results.items():
        codes = _seen_teams.get(mid) or (
            (index[mid]["team_a"], index[mid]["team_b"]) if mid in index else None
        )
        if not codes:
            continue
        odds = ai_odds(*codes)
        ai_scored.append((_brier(odds, outcome),
                          max(OUTCOMES, key=lambda o: odds[o]) == outcome))
    if ai_scored:
        rows.append({
            "name": "🤖 The AI", "is_ai": True, "picks": len(ai_scored),
            "avg_brier": round(sum(b for b, _ in ai_scored) / len(ai_scored), 4),
            "correct": sum(1 for _, c in ai_scored if c), "total": len(ai_scored),
        })

    # Sort: scored players by avg Brier (asc); unscored players last.
    rows.sort(key=lambda r: (r["avg_brier"] is None, r["avg_brier"] or 0))
    return {"players": rows, "resolved_count": len(results)}


def all_picks() -> dict:
    """Raw picks per user (for showing a user their own selections)."""
    return _load()["picks"]


def results_map() -> dict:
    return _load()["results"]
