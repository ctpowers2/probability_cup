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
from src.live_scores import get_live_states
from src.bayesian_updater import get_dynamic_stats
from src.odds_api import fetch_odds as fetch_bookmaker_odds

DATA_DIR = Path(__file__).parent / "data"
STORE_PATH = DATA_DIR / "pool.json"
_LOCK = threading.Lock()

# Knockout mode: no draws — a tie is decided in extra time / penalties, so every
# market is a two-way "who wins the tie". Set PC_KNOCKOUT=0 for group-stage 1X2.
KNOCKOUT = os.environ.get("PC_KNOCKOUT", "1") != "0"

# Outcomes, in fixed order — used for the Brier probability vector.
OUTCOMES = ("a", "b") if KNOCKOUT else ("a", "draw", "b")

# Live tournament API. Override the key with SPORTSPREDICT_API_KEY;
# set PC_USE_LIVE=0 to force the curated demo slate instead.
API_KEY = os.environ.get(
    "SPORTSPREDICT_API_KEY",
    "sp_live_d8b6fec43ffe8ae49b0c3af62076eb3a04365ff78736ee3463aa4ee6bf027321",
)
USE_LIVE = os.environ.get("PC_USE_LIVE", "1") != "0"
_SLATE_TTL = 300  # seconds — re-poll the live fixture list at most this often

# --------------------------------------------------------------------------- #
# Dynamic team stats cache                                                     #
# --------------------------------------------------------------------------- #
_STATS_TTL = 300  # refresh Bayesian+Elo update at most this often
_stats_cache: dict = {"stats": dict(TEAM_STATS), "ts": 0.0}
_stats_fetching = False

_ODDS_TTL = 300
_odds_cache: dict = {"odds": {}, "ts": 0.0}
_odds_fetching = False


def _refresh_odds_bg() -> None:
    global _odds_fetching
    try:
        _odds_cache["odds"] = fetch_bookmaker_odds()
    except Exception:
        pass
    finally:
        _odds_cache["ts"] = time.time()
        _odds_fetching = False


def _get_bookmaker_odds() -> dict:
    global _odds_fetching
    now = time.time()
    if (now - _odds_cache["ts"]) >= _ODDS_TTL and not _odds_fetching:
        _odds_fetching = True
        threading.Thread(target=_refresh_odds_bg, daemon=True).start()
    return _odds_cache["odds"]


def _refresh_stats_bg() -> None:
    """Refresh Bayesian+Elo stats in a background thread."""
    global _stats_fetching
    try:
        updated, _, _ = get_dynamic_stats()
        _stats_cache["stats"] = updated
    except Exception:
        pass
    finally:
        _stats_cache["ts"] = time.time()
        _stats_fetching = False


def _get_stats(code: str) -> dict:
    """Return team stats, using Bayesian+Elo-updated values when available."""
    global _stats_fetching
    now = time.time()
    if (now - _stats_cache["ts"]) >= _STATS_TTL and not _stats_fetching:
        _stats_fetching = True
        threading.Thread(target=_refresh_stats_bg, daemon=True).start()
    return _stats_cache["stats"].get(code) or get_stats(code)


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


# Of the ties still level after 90', the share settled in extra time (a goal)
# rather than going all the way to a shootout. The rest are decided on penalties.
ET_DECISIVE = 0.5


def shootout_edge(code_a: str, code_b: str) -> float:
    """P(A beats B in a shootout) from per-team shootout skill (Bradley–Terry)."""
    sa = _get_stats(code_a).get("so_skill", 0.5)
    sb = _get_stats(code_b).get("so_skill", 0.5)
    num = sa * (1 - sb)
    den = num + sb * (1 - sa)
    return num / den if den else 0.5


def knockout_win_prob(p_a: float, p_b: float, p_d: float,
                      code_a: str, code_b: str) -> float:
    """
    P(A wins the tie): win in regulation, plus the draw mass resolved by
    extra time (share ET_DECISIVE, split by regulation strength) and by a
    penalty shootout (the rest, split by shootout skill).
    """
    reg = p_a + p_b or 1.0
    tie_a = ET_DECISIVE * (p_a / reg) + (1 - ET_DECISIVE) * shootout_edge(code_a, code_b)
    return p_a + p_d * tie_a


def ai_odds(code_a: str, code_b: str) -> dict:
    """
    Normalized AI probabilities for a match.
    Knockout: two-way {a, b} — the draw mass is resolved in extra time (by
    strength) and penalties (by each team's shootout skill). Group: {a, draw, b}.
    """
    model = MatchModel(_get_stats(code_a), _get_stats(code_b), code_a, code_b)
    p_a = model.p_win("a")
    p_b = model.p_win("b")
    p_d = model.p_draw()
    if KNOCKOUT:
        qa = knockout_win_prob(p_a, p_b, p_d, code_a, code_b)
        total = p_a + p_b + p_d or 1.0
        return {"a": qa / total, "b": (total - qa) / total}
    total = p_a + p_b + p_d or 1.0
    return {"a": p_a / total, "draw": p_d / total, "b": p_b / total}


def rationale(code_a: str, code_b: str, odds: dict) -> str:
    """
    A one-line, human-readable 'why' for the AI's odds, built from the same
    model internals that produced them. Explains the favorite in plain English.
    """
    model = MatchModel(_get_stats(code_a), _get_stats(code_b), code_a, code_b)
    fav = max(OUTCOMES, key=lambda o: odds[o])

    if fav == "draw":
        return (f"Evenly matched — expected goals {model.mu_goals_a:.1f}–{model.mu_goals_b:.1f}, "
                f"so a draw is the single most likely result.")

    # Orient everything toward the favored side.
    if fav == "a":
        fav_c, dog_c, mu_f, mu_d = code_a, code_b, model.mu_goals_a, model.mu_goals_b
    else:
        fav_c, dog_c, mu_f, mu_d = code_b, code_a, model.mu_goals_b, model.mu_goals_a

    fav_s, dog_s = _get_stats(fav_c), _get_stats(dog_c)
    reasons = []

    elo_gap = fav_s["elo"] - dog_s["elo"]
    if elo_gap >= 40:
        reasons.append(f"a {elo_gap:.0f}-point Elo edge")

    if fav_s["attack"] - dog_s["attack"] >= 0.25:
        reasons.append(f"the stronger attack ({fav_s['attack']:.1f} vs {dog_s['attack']:.1f} goals/game)")

    # Lower 'defense' = fewer goals conceded = better defense.
    if dog_s["defense"] - fav_s["defense"] >= 0.20:
        reasons.append(f"a tighter defense ({fav_s['defense']:.1f} vs {dog_s['defense']:.1f} conceded)")

    # In the knockouts, a shootout edge can be the deciding factor in a tight tie.
    if KNOCKOUT:
        sf, sd = fav_s.get("so_skill", 0.5), dog_s.get("so_skill", 0.5)
        if sf - sd >= 0.10:
            reasons.append(f"a stronger shootout record ({sf:.2f} vs {sd:.2f})")

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
    bm = _get_bookmaker_odds().get(frozenset({code_a, code_b}))
    crowd: dict | None = None
    if bm:
        # Re-orient so 'a'/'b' align with our match's code_a/code_b.
        if bm.get("code_a") == code_a:
            crowd = {"a": bm["a"], "b": bm["b"], "n_books": bm.get("n_books", 1)}
        else:
            crowd = {"a": bm["b"], "b": bm["a"], "n_books": bm.get("n_books", 1)}
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
        "crowd": crowd,
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


def _parse_kickoff_ts(iso: str) -> float | None:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return None


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
        match = _build_match(m["id"], a, b, _fmt_when(m.get("opening_time", "")))
        match["kickoff_ts"] = _parse_kickoff_ts(m.get("opening_time", ""))
        matches.append(match)
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
        # Persist team codes for every served match so it can still be shown
        # live / settled after it leaves the upcoming list at kickoff.
        _merge_meta({m["id"]: [m["team_a"], m["team_b"]] for m in matches})

    for m in _slate_cache["matches"]:
        _seen_teams[m["id"]] = (m["team_a"], m["team_b"])
    return _slate_cache["matches"]


def _merge_meta(pairs: dict) -> None:
    with _LOCK:
        state = _load()
        changed = False
        for mid, codes in pairs.items():
            if state["match_meta"].get(mid) != list(codes):
                state["match_meta"][mid] = list(codes)
                changed = True
        if changed:
            _save(state)


def _tracked_matches() -> dict:
    """Every match we know about: current slate + served/picked (persisted)."""
    get_slate()  # refresh _seen_teams for the current slate
    tracked = dict(_seen_teams)
    for mid, codes in _load()["match_meta"].items():
        tracked.setdefault(mid, tuple(codes))
    return tracked


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
# Real match tracking — live scores + settlement from the ESPN scoreboard      #
# --------------------------------------------------------------------------- #
_REAL_TTL = 60  # seconds — cache the ESPN scoreboard fetch
_real_cache = {"states": {}, "ts": 0.0}


def _real_states(force: bool = False) -> dict:
    now = time.time()
    if force or not _real_cache["states"] or (now - _real_cache["ts"]) >= _REAL_TTL:
        try:
            _real_cache["states"] = get_live_states() or _real_cache["states"]
        except Exception:
            pass
        _real_cache["ts"] = now
    return _real_cache["states"]


def _codes_for(match_id: str, meta: dict | None = None):
    """Team codes for a match, from memory / persisted meta / current slate."""
    if match_id in _seen_teams:
        return _seen_teams[match_id]
    meta = _load()["match_meta"] if meta is None else meta
    if match_id in meta:
        return tuple(meta[match_id])
    m = _index().get(match_id)
    return (m["team_a"], m["team_b"]) if m else None


def _settle_internal(match_id: str, outcome: str) -> None:
    """Record a real/auto result (no slate validation; trusted caller)."""
    with _LOCK:
        state = _load()
        if match_id not in state["results"]:
            state["results"][match_id] = outcome
            _save(state)


def sync_real_results() -> None:
    """Settle any tracked match that has actually finished (real ESPN result)."""
    states = _real_states()
    if not states:
        return
    results = _load()["results"]
    for mid, (a, b) in _tracked_matches().items():
        if mid in results:
            continue
        st = states.get(frozenset((a, b)))
        if not st or not st.get("final"):
            continue
        winner = st.get("winner")
        if not winner:
            sa, sb = st["scores"].get(a, 0), st["scores"].get(b, 0)
            if sa == sb:
                continue  # level, winner not yet reported (shootout pending)
            winner = a if sa > sb else b
        _settle_internal(mid, "a" if winner == a else "b")


def live_match_state() -> dict:
    """Real match currently in play (from ESPN) with live model odds, else inactive."""
    states = _real_states()
    if not states:
        return {"active": False}
    for mid, (a, b) in _tracked_matches().items():
        st = states.get(frozenset((a, b)))
        if not st or not st.get("in_play"):
            continue
        sa, sb = st["scores"].get(a, 0), st["scores"].get(b, 0)
        model = MatchModel(_get_stats(a), _get_stats(b), a, b)
        model.apply_live(sa, sb, st["minute"])
        p_a, p_b, p_d = model.p_win("a"), model.p_win("b"), model.p_draw()
        total = p_a + p_b + p_d or 1.0
        if KNOCKOUT:
            qa = knockout_win_prob(p_a, p_b, p_d, a, b)
            ai = {"a": round(qa / total * 100, 1), "b": round((total - qa) / total * 100, 1)}
        else:
            ai = {"a": round(p_a / total * 100, 1),
                  "draw": round(p_d / total * 100, 1),
                  "b": round(p_b / total * 100, 1)}
        return {
            "active": True, "mode": "live", "match_id": mid,
            "name_a": team_name(a), "name_b": team_name(b),
            "minute": st["minute"], "score_a": sa, "score_b": sb,
            "finished": False, "ai": ai, "goals": [],
        }
    return {"active": False}


# --------------------------------------------------------------------------- #
# Persistence                                                                  #
# --------------------------------------------------------------------------- #
def _load() -> dict:
    if STORE_PATH.exists():
        with open(STORE_PATH) as f:
            state = json.load(f)
    else:
        state = {}
    state.setdefault("picks", {})
    state.setdefault("results", {})
    state.setdefault("match_meta", {})  # match_id -> [team_a, team_b], for settling
    return state


def _save(state: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    tmp = STORE_PATH.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STORE_PATH)


class PickLockedError(Exception):
    pass


def record_pick(user: str, match_id: str, pick: str, conf: float | None = None) -> None:
    """Store (or overwrite) a user's pick for a match.

    pick ∈ OUTCOMES; conf is optional confidence in [0.51, 0.99].
    Stored as {"pick": "a", "conf": 0.75} or plain "a" for full confidence.
    Raises PickLockedError if kickoff has already passed.
    """
    user = user.strip()
    if not user:
        raise ValueError("Name required")
    if pick not in OUTCOMES:
        raise ValueError(f"Invalid pick: {pick!r}")
    match = _index().get(match_id)
    if match is None:
        raise ValueError(f"Unknown match: {match_id!r}")
    kickoff_ts = match.get("kickoff_ts")
    if kickoff_ts is not None and time.time() >= kickoff_ts:
        raise PickLockedError("Picks are locked — this match has already kicked off")
    if conf is None:
        entry = pick
    else:
        conf = max(0.51, min(0.99, float(conf)))
        entry = {"pick": pick, "conf": conf}
    with _LOCK:
        state = _load()
        state["picks"].setdefault(user, {})[match_id] = entry
        state["match_meta"][match_id] = [match["team_a"], match["team_b"]]
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


def _pick_to_vec(entry) -> dict:
    """Convert a stored pick entry (str or {pick, conf}) to a probability vector."""
    if isinstance(entry, dict):
        chosen, conf = entry["pick"], entry["conf"]
    else:
        chosen, conf = entry, 1.0
    others = [o for o in OUTCOMES if o != chosen]
    rest = (1.0 - conf) / len(others) if others else 0.0
    return {o: (conf if o == chosen else rest) for o in OUTCOMES}


def _pick_choice(entry) -> str:
    """The chosen outcome from a stored pick entry."""
    return entry["pick"] if isinstance(entry, dict) else entry


def _match_label(mid: str, meta: dict) -> str:
    codes = meta.get(mid)
    if not codes:
        return mid
    return f"{team_name(codes[0])} vs {team_name(codes[1])}"


def leaderboard() -> dict:
    """
    Score every human and the AI on the same resolved matches with Brier score.
    Returns {players: [...], resolved_count: int}. Players sorted by avg Brier.
    Each player row includes a 'breakdown' list of per-match score details.
    """
    sync_real_results()  # pull in any real match results before scoring
    state = _load()
    results = state["results"]
    picks = state["picks"]
    meta = state["match_meta"]

    rows = []

    # Human players
    for user, user_picks in picks.items():
        scored = [(mid, p) for mid, p in user_picks.items() if mid in results]
        if not scored:
            rows.append({"name": user, "is_ai": False, "picks": 0,
                         "avg_brier": None, "correct": 0, "total": 0, "breakdown": []})
            continue
        breakdown = []
        brier_vals = []
        for mid, p in scored:
            outcome = results[mid]
            b = _brier(_pick_to_vec(p), outcome)
            brier_vals.append(b)
            chosen = _pick_choice(p)
            conf = p["conf"] if isinstance(p, dict) else 1.0
            codes = meta.get(mid, [None, None])
            outcome_name = team_name(codes[0] if outcome == "a" else codes[1]) if codes[0] else outcome
            breakdown.append({
                "match": _match_label(mid, meta),
                "pick": team_name(codes[0] if chosen == "a" else codes[1]) if codes[0] else chosen,
                "conf": round(conf * 100),
                "correct": chosen == outcome,
                "score": round((1 - b / 2) * 100),
            })
        correct = sum(1 for b in breakdown if b["correct"])
        rows.append({
            "name": user, "is_ai": False, "picks": len(scored),
            "avg_brier": round(sum(brier_vals) / len(brier_vals), 4),
            "correct": correct, "total": len(scored),
            "breakdown": sorted(breakdown, key=lambda x: x["match"]),
        })

    # The AI, scored on every resolved match using its full probability vector
    ai_scored = []
    ai_breakdown = []
    for mid, outcome in results.items():
        codes = _codes_for(mid, meta)
        if not codes:
            continue
        odds = ai_odds(*codes)
        b = _brier(odds, outcome)
        correct = max(OUTCOMES, key=lambda o: odds[o]) == outcome
        ai_scored.append((b, correct))
        ai_breakdown.append({
            "match": _match_label(mid, meta),
            "pick": f"{team_name(codes[0])} {round(odds['a']*100)}% / {team_name(codes[1])} {round(odds['b']*100)}%",
            "conf": None,
            "correct": correct,
            "score": round((1 - b / 2) * 100),
        })
    if ai_scored:
        rows.append({
            "name": "🤖 The AI", "is_ai": True, "picks": len(ai_scored),
            "avg_brier": round(sum(b for b, _ in ai_scored) / len(ai_scored), 4),
            "correct": sum(1 for _, c in ai_scored if c), "total": len(ai_scored),
            "breakdown": sorted(ai_breakdown, key=lambda x: x["match"]),
        })

    # Public line (bookmaker odds), scored on every resolved match
    bm_odds_snapshot = _get_bookmaker_odds()
    bm_scored = []
    bm_breakdown = []
    for mid, outcome in results.items():
        codes = _codes_for(mid, meta)
        if not codes:
            continue
        bm = bm_odds_snapshot.get(frozenset(codes))
        if not bm:
            continue
        if bm.get("code_a") == codes[0]:
            bm_probs = {"a": bm["a"] / 100, "b": bm["b"] / 100}
        else:
            bm_probs = {"a": bm["b"] / 100, "b": bm["a"] / 100}
        b = _brier(bm_probs, outcome)
        correct = max(bm_probs, key=bm_probs.get) == outcome
        bm_scored.append((b, correct))
        bm_breakdown.append({
            "match": _match_label(mid, meta),
            "pick": f"{team_name(codes[0])} {round(bm_probs['a']*100)}% / {team_name(codes[1])} {round(bm_probs['b']*100)}%",
            "conf": None,
            "correct": correct,
            "score": round((1 - b / 2) * 100),
        })
    if bm_scored:
        rows.append({
            "name": "📊 Public line", "is_ai": True, "picks": len(bm_scored),
            "avg_brier": round(sum(b for b, _ in bm_scored) / len(bm_scored), 4),
            "correct": sum(1 for _, c in bm_scored if c), "total": len(bm_scored),
            "breakdown": sorted(bm_breakdown, key=lambda x: x["match"]),
        })

    # Sort: scored players by avg Brier (asc); unscored players last.
    rows.sort(key=lambda r: (r["avg_brier"] is None, r["avg_brier"] or 0))
    return {"players": rows, "resolved_count": len(results)}


def all_picks() -> dict:
    """Raw picks per user (for showing a user their own selections)."""
    return _load()["picks"]


def results_map() -> dict:
    return _load()["results"]
