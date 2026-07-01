"""
Fetch live Kalshi prediction market probabilities for WC 2026 matches.

Uses the public elections API — no auth required.
Returns mid-market probabilities (avg of yes_bid and yes_ask) for each
team-advances market, keyed by frozenset({team_a_code, team_b_code}).
"""

import requests
from .team_data import TEAM_STATS

_API = "https://api.elections.kalshi.com/trade-api/v2/markets"
_TICKER_PREFIX = "KXWCADVANCE"
_TIMEOUT = 6


def _mid(bid: float, ask: float) -> float | None:
    """Mid-market price from bid/ask in dollars (0–1 scale)."""
    if bid == 0 and ask == 0:
        return None
    if ask == 0:
        return bid
    if bid == 0:
        return ask
    return (bid + ask) / 2


def _ticker_to_code(ticker: str) -> str | None:
    """
    Extract the team code from a KXWCADVANCE ticker.
    Format: KXWCADVANCE-26MMDDTEAM1TEAM2-TEAMX
    The side code after the last '-' is the team being bet on.
    """
    parts = ticker.split("-")
    if len(parts) < 3:
        return None
    code = parts[-1].upper()
    return code if code in TEAM_STATS else None


def _parse_opponent_code(ticker: str, side_code: str) -> str | None:
    """
    Extract the opposing team code from the middle segment of a ticker.
    e.g. KXWCADVANCE-26JUL01USABIH-USA -> middle = 26JUL01USABIH
    Strip the date prefix (digits + 3-char month), then the side code,
    leaving the opponent.
    """
    parts = ticker.split("-")
    if len(parts) < 3:
        return None
    middle = parts[1]  # e.g. "26JUL01USABIH"
    # Remove leading date digits+month (e.g. "26JUL01" = 7 chars)
    i = 0
    while i < len(middle) and (middle[i].isdigit() or (i >= 2 and middle[i].isalpha() and i < 7)):
        i += 1
    # Skip 6-char date block: 2 digits + 3 char month + 2 digits
    stripped = middle[7:] if len(middle) > 7 else middle
    # stripped should be the two team codes concatenated, e.g. "USABIH"
    # remove the side code to get the opponent
    stripped_upper = stripped.upper()
    side_upper = side_code.upper()
    if stripped_upper.startswith(side_upper):
        opp = stripped_upper[len(side_upper):]
    elif stripped_upper.endswith(side_upper):
        opp = stripped_upper[: -len(side_upper)]
    else:
        return None
    return opp if opp in TEAM_STATS else None


def fetch_kalshi_odds() -> dict[frozenset, dict]:
    """
    Fetch all KXWCADVANCE markets and return a dict keyed by
    frozenset({code_a, code_b}) → {"a": prob_a, "b": prob_b, "volume": float}.

    Returns empty dict on any network error.
    Mid-market probability is None for markets with no liquidity;
    callers should treat None as unavailable.
    """
    results: dict[frozenset, dict] = {}
    cursor = None

    while True:
        params: dict = {"ticker": _TICKER_PREFIX, "limit": 100}
        if cursor:
            params["cursor"] = cursor
        try:
            r = requests.get(_API, params=params, timeout=_TIMEOUT)
            r.raise_for_status()
            data = r.json()
        except Exception:
            break

        for m in data.get("markets", []):
            ticker: str = m.get("ticker", "")
            if not ticker.startswith(_TICKER_PREFIX):
                continue

            side_code = _ticker_to_code(ticker)
            if not side_code:
                continue
            opp_code = _parse_opponent_code(ticker, side_code)
            if not opp_code:
                continue

            yes_bid = float(m.get("yes_bid_dollars") or 0)
            yes_ask = float(m.get("yes_ask_dollars") or 0)
            prob = _mid(yes_bid, yes_ask)
            volume = float(m.get("volume_fp") or 0)

            key = frozenset({side_code, opp_code})
            if key not in results:
                results[key] = {"a": None, "b": None, "volume": 0.0,
                                "code_a": side_code, "code_b": opp_code}

            entry = results[key]
            # Assign probability to the correct side
            if side_code == entry["code_a"]:
                entry["a"] = prob
            else:
                entry["b"] = prob
            entry["volume"] = max(entry["volume"], volume)

        cursor = data.get("cursor")
        if not cursor:
            break

    # Normalize: ensure both sides sum to ~1 when both are present
    cleaned: dict[frozenset, dict] = {}
    for key, entry in results.items():
        pa, pb = entry["a"], entry["b"]
        if pa is not None and pb is not None and (pa + pb) > 0:
            total = pa + pb
            entry["a"] = round(pa / total * 100, 1)
            entry["b"] = round(pb / total * 100, 1)
        elif pa is not None:
            entry["a"] = round(pa * 100, 1)
            entry["b"] = round((1 - pa) * 100, 1)
        elif pb is not None:
            entry["b"] = round(pb * 100, 1)
            entry["a"] = round((1 - pb) * 100, 1)
        else:
            continue  # no price data, skip
        cleaned[key] = entry

    return cleaned
