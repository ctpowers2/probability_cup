"""
Online Bayesian updater for WC 2026 team attack/defense parameters.

Model: Dixon-Coles Poisson
    mu_goals_a = attack_a * defense_b / LEAGUE_GOALS

For each observed result (goals_a, goals_b) we back-solve for the team's
"effective" attack/defense performance that would have produced those goals
under the current parameter estimates.  We then update each team's posterior
via a Bayesian conjugate-like formula:

    new_attack = (N0 * prior_attack + sum(effective_attacks)) / (N0 + n_games)

with N0 = 10 (prior weight in equivalent games).  Iterating this 5 times
constitutes a lightweight EM loop that lets parameters stabilise across
multiple matches.
"""

import copy
import requests
from datetime import date, timedelta

from .team_data import TEAM_STATS
from .live_scores import _ESPN_TO_CODE

LEAGUE_GOALS: float = 1.35
N0: int = 10        # prior weight in equivalent games
N_ITER: int = 5     # EM iterations

_WC_START = date(2026, 6, 11)
_ESPN_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
)


# ------------------------------------------------------------------ #
# Data fetching                                                        #
# ------------------------------------------------------------------ #

def _fetch_day(d: date) -> list[dict]:
    """Return completed WC match results for a single date."""
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
        if len(teams) == 2:
            codes = list(teams.keys())
            games.append({
                "team_a": codes[0], "team_b": codes[1],
                "goals_a": teams[codes[0]], "goals_b": teams[codes[1]],
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
    Run iterative Bayesian EM update on attack/defense parameters.

    Parameters
    ----------
    results   : list of {"team_a", "team_b", "goals_a", "goals_b"}
    n0        : prior strength (equivalent games)
    n_iter    : number of EM iterations

    Returns
    -------
    Updated copy of TEAM_STATS with new attack/defense values.
    """
    stats: dict = copy.deepcopy(dict(TEAM_STATS))

    for iteration in range(n_iter):
        # Collect effective observations per team this iteration
        atk_obs: dict[str, list[float]] = {}
        def_obs: dict[str, list[float]] = {}

        for g in results:
            ta, tb = g["team_a"], g["team_b"]
            ga, gb = g["goals_a"], g["goals_b"]

            if ta not in stats or tb not in stats:
                continue

            atk_a = max(stats[ta]["attack"],  0.01)
            atk_b = max(stats[tb]["attack"],  0.01)
            def_a = max(stats[ta]["defense"], 0.01)
            def_b = max(stats[tb]["defense"], 0.01)

            # DC back-solve:
            #   mu_a = atk_a * def_b / L  =>  eff_atk_a = ga * L / def_b
            #   mu_b = atk_b * def_a / L  =>  eff_atk_b = gb * L / def_a
            #   mu_a = atk_a * def_b / L  =>  eff_def_b = ga * L / atk_a
            #   mu_b = atk_b * def_a / L  =>  eff_def_a = gb * L / atk_b
            eff_atk_a = ga * LEAGUE_GOALS / def_b
            eff_atk_b = gb * LEAGUE_GOALS / def_a
            eff_def_b = ga * LEAGUE_GOALS / atk_a
            eff_def_a = gb * LEAGUE_GOALS / atk_b

            atk_obs.setdefault(ta, []).append(eff_atk_a)
            atk_obs.setdefault(tb, []).append(eff_atk_b)
            def_obs.setdefault(tb, []).append(eff_def_b)
            def_obs.setdefault(ta, []).append(eff_def_a)

        # Bayesian posterior update (always use the ORIGINAL prior)
        for code in stats:
            prior_atk = TEAM_STATS[code]["attack"]
            prior_def = TEAM_STATS[code]["defense"]

            if code in atk_obs:
                obs = atk_obs[code]
                stats[code]["attack"] = (n0 * prior_atk + sum(obs)) / (n0 + len(obs))

            if code in def_obs:
                obs = def_obs[code]
                stats[code]["defense"] = (n0 * prior_def + sum(obs)) / (n0 + len(obs))

    return stats


# ------------------------------------------------------------------ #
# Public entry point                                                   #
# ------------------------------------------------------------------ #

def get_dynamic_stats() -> tuple[dict, int, float]:
    """
    Fetch completed WC results, run Bayesian EM.
    Returns (updated_stats, n_games, wc_goals_scale).

    wc_goals_scale = observed WC goals per team per game / LEAGUE_GOALS prior.
    Starts at 1.0 with no data; converges to the true WC scoring rate.
    """
    results = get_completed_results()
    n = len(results)
    if n == 0:
        return dict(TEAM_STATS), 0, 1.0
    total_goals = sum(g["goals_a"] + g["goals_b"] for g in results)
    wc_goals_per_team = total_goals / (2 * n)
    wc_goals_scale = wc_goals_per_team / LEAGUE_GOALS
    updated = compute_updated_stats(results)
    return updated, n, wc_goals_scale
