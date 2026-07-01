"""
Online Bayesian updater for WC 2026 team attack/defense/SOT parameters,
plus an Elo forward pass from completed results.

Model: Dixon-Coles Poisson
    mu_goals_a = attack_a * defense_b / LEAGUE_GOALS
    mu_sot_a   = sot_a    * sot_against_b / LEAGUE_SOT

For each observed result we back-solve for effective attack/defense (from
goals) and effective SOT attack/defense (from shots on target).  Both are
updated via the same Bayesian conjugate formula:

    new_param = (N0 * prior + sum(effective)) / (N0 + n_games)

with N0 = 10 (prior weight in equivalent games).  Iterating 5 times is a
lightweight EM that lets parameters stabilise across multiple matches.

Elo is updated with a standard WC-weight formula (K=60) applied in
chronological order to every completed result.
"""

import copy
import math
import requests
from datetime import date, timedelta

from .team_data import TEAM_STATS
from .live_scores import _ESPN_TO_CODE

LEAGUE_GOALS: float = 1.35
LEAGUE_SOT: float = 4.20   # league-avg SOT per team per game (same as models.py)
N0: int = 10        # prior weight in equivalent games
N_ITER: int = 5     # EM iterations
ELO_K: float = 60.0  # WC match K-factor

_WC_START = date(2026, 6, 11)
_ESPN_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
)


# ------------------------------------------------------------------ #
# Data fetching                                                        #
# ------------------------------------------------------------------ #

def _parse_sot(comp: dict, code: str) -> int | None:
    """Extract shots-on-target for `code` from ESPN competition stats."""
    for c in comp.get("competitors", []):
        abbr = c["team"]["abbreviation"]
        if _ESPN_TO_CODE.get(abbr, abbr.upper()) != code:
            continue
        for stat in c.get("statistics", []):
            if stat.get("name") == "shotsOnTarget":
                try:
                    return int(stat["displayValue"])
                except (KeyError, ValueError, TypeError):
                    return None
    return None


def _fetch_day(d: date) -> list[dict]:
    """Return completed WC match results (goals + SOT) for a single date."""
    url = f"{_ESPN_SCOREBOARD}?dates={d.strftime('%Y%m%d')}"
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        events = r.json().get("events", [])
    except Exception:
        return []

    games: list[dict] = []
    for event in events:
        comp = event["competitions"][0]
        if comp["status"]["type"]["name"] not in ("STATUS_FINAL", "STATUS_FULL_TIME"):
            continue
        teams: dict[str, int] = {}
        for c in comp["competitors"]:
            abbr = c["team"]["abbreviation"]
            code = _ESPN_TO_CODE.get(abbr, abbr.upper())
            try:
                score = int(c.get("score", 0) or 0)
            except (ValueError, TypeError):
                score = 0
            teams[code] = score
        if len(teams) != 2:
            continue
        codes = list(teams.keys())
        ta, tb = codes[0], codes[1]
        ga, gb = teams[ta], teams[tb]
        sot_a = _parse_sot(comp, ta)
        sot_b = _parse_sot(comp, tb)
        games.append({
            "team_a": ta, "team_b": tb,
            "goals_a": ga, "goals_b": gb,
            "sot_a": sot_a, "sot_b": sot_b,
        })
    return games


def get_completed_results() -> list[dict]:
    """Fetch all completed WC 2026 match results from ESPN (June 11 → today)."""
    today = date.today()
    results: list[dict] = []
    d = _WC_START
    while d <= today:
        results.extend(_fetch_day(d))
        d += timedelta(days=1)
    # Deduplicate (same game can appear on multiple date queries near midnight)
    seen: set[tuple] = set()
    unique: list[dict] = []
    for g in results:
        key = (g["team_a"], g["team_b"])
        if key not in seen:
            seen.add(key)
            unique.append(g)
    return unique


# ------------------------------------------------------------------ #
# EM Bayesian update                                                   #
# ------------------------------------------------------------------ #

def compute_updated_stats(
    results: list[dict],
    n0: int = N0,
    n_iter: int = N_ITER,
) -> dict:
    """
    Run iterative Bayesian EM update on attack/defense and SOT parameters.

    Parameters
    ----------
    results   : list of {"team_a", "team_b", "goals_a", "goals_b",
                          "sot_a": int|None, "sot_b": int|None}
    n0        : prior strength (equivalent games)
    n_iter    : number of EM iterations

    Returns
    -------
    Updated copy of TEAM_STATS with new attack/defense/sot/sot_against values.
    """
    stats: dict = copy.deepcopy(dict(TEAM_STATS))

    for _ in range(n_iter):
        atk_obs:     dict[str, list[float]] = {}
        def_obs:     dict[str, list[float]] = {}
        sot_obs:     dict[str, list[float]] = {}
        sotag_obs:   dict[str, list[float]] = {}

        for g in results:
            ta, tb = g["team_a"], g["team_b"]
            ga, gb = g["goals_a"], g["goals_b"]

            if ta not in stats or tb not in stats:
                continue

            atk_a = max(stats[ta]["attack"],  0.01)
            atk_b = max(stats[tb]["attack"],  0.01)
            def_a = max(stats[ta]["defense"], 0.01)
            def_b = max(stats[tb]["defense"], 0.01)

            # Goals back-solve (Dixon-Coles):
            atk_obs.setdefault(ta, []).append(ga * LEAGUE_GOALS / def_b)
            atk_obs.setdefault(tb, []).append(gb * LEAGUE_GOALS / def_a)
            def_obs.setdefault(tb, []).append(ga * LEAGUE_GOALS / atk_a)
            def_obs.setdefault(ta, []).append(gb * LEAGUE_GOALS / atk_b)

            # SOT back-solve (same structure, skip if ESPN didn't return stats)
            sa, sb = g.get("sot_a"), g.get("sot_b")
            if sa is not None and sb is not None:
                sot_a_p = max(stats[ta]["sot"],        0.01)
                sot_b_p = max(stats[tb]["sot"],        0.01)
                sag_a   = max(stats[ta]["sot_against"], 0.01)
                sag_b   = max(stats[tb]["sot_against"], 0.01)

                sot_obs.setdefault(ta,  []).append(sa * LEAGUE_SOT / sag_b)
                sot_obs.setdefault(tb,  []).append(sb * LEAGUE_SOT / sag_a)
                sotag_obs.setdefault(tb, []).append(sa * LEAGUE_SOT / sot_a_p)
                sotag_obs.setdefault(ta, []).append(sb * LEAGUE_SOT / sot_b_p)

        # Bayesian posterior update (always shrink toward ORIGINAL prior)
        for code in stats:
            prior = TEAM_STATS[code]

            if code in atk_obs:
                obs = atk_obs[code]
                stats[code]["attack"] = (n0 * prior["attack"] + sum(obs)) / (n0 + len(obs))

            if code in def_obs:
                obs = def_obs[code]
                stats[code]["defense"] = (n0 * prior["defense"] + sum(obs)) / (n0 + len(obs))

            if code in sot_obs:
                obs = sot_obs[code]
                stats[code]["sot"] = (n0 * prior["sot"] + sum(obs)) / (n0 + len(obs))

            if code in sotag_obs:
                obs = sotag_obs[code]
                stats[code]["sot_against"] = (n0 * prior["sot_against"] + sum(obs)) / (n0 + len(obs))

    return stats


# ------------------------------------------------------------------ #
# Elo update                                                           #
# ------------------------------------------------------------------ #

def _elo_expected(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + math.pow(10, (rb - ra) / 400.0))


def compute_updated_elo(results: list[dict], stats: dict) -> dict:
    """
    Forward-pass Elo update on completed WC results (K=60).
    Mutates and returns `stats` in-place.
    """
    for g in results:
        ta, tb = g["team_a"], g["team_b"]
        if ta not in stats or tb not in stats:
            continue
        ra, rb = stats[ta]["elo"], stats[tb]["elo"]
        ga, gb = g["goals_a"], g["goals_b"]
        score_a = 0.5 if ga == gb else (1.0 if ga > gb else 0.0)
        exp_a = _elo_expected(ra, rb)
        delta = ELO_K * (score_a - exp_a)
        stats[ta]["elo"] = ra + delta
        stats[tb]["elo"] = rb - delta
    return stats


# ------------------------------------------------------------------ #
# Public entry point                                                   #
# ------------------------------------------------------------------ #

def get_dynamic_stats() -> tuple[dict, int, float]:
    """
    Fetch completed WC results, run Bayesian EM on attack/defense/SOT,
    then forward-pass Elo updates from results.
    Returns (updated_stats, n_games, wc_goals_scale).
    """
    results = get_completed_results()
    n = len(results)
    if n == 0:
        return dict(TEAM_STATS), 0, 1.0
    total_goals = sum(g["goals_a"] + g["goals_b"] for g in results)
    wc_goals_per_team = total_goals / (2 * n)
    wc_goals_scale = wc_goals_per_team / LEAGUE_GOALS
    updated = compute_updated_stats(results)
    updated = compute_updated_elo(results, updated)
    return updated, n, wc_goals_scale
