"""
Fetch live bookmaker odds for WC 2026 matches from The Odds API.
https://the-odds-api.com  — free tier: 500 requests/month

Set ODDS_API_KEY env var with your API key.
Returns probabilities keyed by frozenset({team_a_code, team_b_code}).
"""

import os
import requests

from .team_data import NAME_TO_CODE

_API = "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds"
_TIMEOUT = 8

# Bookmakers tried in priority order; first one with h2h prices wins
_BOOKS = ["draftkings", "fanduel", "betmgm", "williamhill_us", "betway", "pinnacle"]


def _name_to_code(name: str) -> str | None:
    return NAME_TO_CODE.get(name.lower().strip())


def fetch_odds() -> dict[frozenset, dict]:
    """
    Fetch h2h (moneyline) decimal odds for all upcoming WC 2026 matches.

    Returns:
        {frozenset({code_home, code_away}): {
            "a": float,      # vig-removed % for code_a (home)
            "b": float,      # vig-removed % for code_b (away)
            "code_a": str,   # home team code
            "code_b": str,   # away team code
            "book": str,     # bookmaker key used
        }}

    Returns empty dict if ODDS_API_KEY is not set or on any network error.
    """
    api_key = os.environ.get("ODDS_API_KEY", "")
    if not api_key:
        return {}

    params = {
        "apiKey": api_key,
        "regions": "us,uk,eu",
        "markets": "h2h",
        "oddsFormat": "decimal",
        "bookmakers": ",".join(_BOOKS),
    }
    try:
        r = requests.get(_API, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        events = r.json()
    except Exception:
        return {}

    results: dict[frozenset, dict] = {}

    for event in events:
        home_name = event.get("home_team", "")
        away_name = event.get("away_team", "")
        code_home = _name_to_code(home_name)
        code_away = _name_to_code(away_name)
        if not code_home or not code_away:
            continue

        key = frozenset({code_home, code_away})
        if key in results:
            continue

        # Walk bookmakers in priority order; take first with valid h2h prices
        home_p: float | None = None
        away_p: float | None = None
        book_used = ""

        for bm in event.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                prices = {o["name"]: float(o["price"]) for o in market.get("outcomes", [])}
                hp = prices.get(home_name)
                ap = prices.get(away_name)
                if hp and hp > 1.0 and ap and ap > 1.0:
                    home_p = 1.0 / hp
                    away_p = 1.0 / ap
                    book_used = bm.get("key", "")
                break
            if home_p is not None:
                break

        if home_p is None or away_p is None:
            continue

        # Remove vig by normalizing to 100%
        total = home_p + away_p
        results[key] = {
            "a": round(home_p / total * 100, 1),
            "b": round(away_p / total * 100, 1),
            "code_a": code_home,
            "code_b": code_away,
            "book": book_used,
        }

    return results
