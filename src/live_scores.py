"""
Live match state from ESPN public scoreboard API.
No API key required.
"""

import requests

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

# ESPN abbreviation → our team code
_ESPN_TO_CODE: dict[str, str] = {
    "ARG": "ARG", "FRA": "FRA", "ENG": "ENG", "BRA": "BRA",
    "ESP": "ESP", "GER": "GER", "POR": "POR", "NED": "NED",
    "BEL": "BEL", "URU": "URU", "MEX": "MEX", "USA": "USA",
    "COL": "COL", "SUI": "SUI", "JPN": "JPN", "MAR": "MAR",
    "SEN": "SEN", "CRO": "CRO", "TUR": "TUR", "NOR": "NOR",
    "CZE": "CZE", "KOR": "KOR", "AUT": "AUT", "SWE": "SWE",
    "AUS": "AUS", "CAN": "CAN", "SCO": "SCO", "GHA": "GHA",
    "IRN": "IRN", "ALG": "ALG", "TUN": "TUN", "ECU": "ECU",
    "PRY": "PAR", "PAR": "PAR", "EGY": "EGY", "BIH": "BIH",
    "UZB": "UZB", "IRQ": "IRQ", "CIV": "CIV", "RSA": "RSA",
    "QAT": "QAT", "JOR": "JOR", "KSA": "KSA", "COD": "COD",
    "PAN": "PAN", "CPV": "CPV", "HTI": "Haiti", "HAI": "Haiti",
    "CUW": "Curacao", "CUR": "Curacao", "NZL": "New Zealand",
}

_IN_PLAY_STATUSES = frozenset({
    "STATUS_IN_PROGRESS", "STATUS_FIRST_HALF",
    "STATUS_SECOND_HALF", "STATUS_HALFTIME",
})


def get_live_states() -> dict[frozenset, dict]:
    """
    Fetch current match states from ESPN.

    Returns a dict keyed by frozenset({code_x, code_y}) → state dict:
        {
            "scores": {code_x: int, code_y: int},
            "minute": int,
            "status": str,   # ESPN status name
            "in_play": bool,
            "halftime": bool,
        }

    Only in-play and recently completed matches are included.
    Scheduled matches are excluded.
    """
    try:
        resp = requests.get(ESPN_URL, timeout=8)
        resp.raise_for_status()
        events = resp.json().get("events", [])
    except Exception:
        return {}

    states: dict[frozenset, dict] = {}
    for event in events:
        comp = event["competitions"][0]
        status_name = comp["status"]["type"]["name"]

        if status_name == "STATUS_SCHEDULED":
            continue

        # Parse the two competitors
        teams: dict[str, int] = {}
        for c in comp["competitors"]:
            abbr = c["team"]["abbreviation"]
            code = _ESPN_TO_CODE.get(abbr)
            if code is None:
                # Try uppercased abbreviation as fallback
                code = abbr.upper()
            try:
                teams[code] = int(c.get("score", 0) or 0)
            except (ValueError, TypeError):
                teams[code] = 0

        if len(teams) != 2:
            continue

        # Parse minute from displayClock e.g. "70'" or "45+2'"
        clock_str = comp["status"].get("displayClock", "")
        try:
            minute = int(clock_str.rstrip("'").split("+")[0])
        except (ValueError, AttributeError):
            minute = 45 if comp["status"]["period"] == 1 else 90

        if status_name == "STATUS_HALFTIME":
            minute = 45
        elif status_name == "STATUS_FINAL":
            minute = 90

        codes = list(teams.keys())
        key = frozenset(codes)
        states[key] = {
            "scores": teams,
            "minute": minute,
            "status": status_name,
            "in_play": status_name in _IN_PLAY_STATUSES,
            "halftime": status_name == "STATUS_HALFTIME",
        }

    return states
