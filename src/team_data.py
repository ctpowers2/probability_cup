# Team statistics for 2026 World Cup.
# attack/defense: avg goals scored/conceded per game (recent international form)
# sot / sot_against: shots on target for/against per game
# fouls: avg fouls committed per game
# offsides: avg offsides per game
# corners: avg corners won per game
# yellows: avg yellow cards per game
# elo: FIFA-style Elo rating

TEAM_STATS: dict[str, dict] = {
    "ARG": {"attack": 2.10, "defense": 0.75, "sot": 5.8, "sot_against": 3.2, "fouls": 13.5, "offsides": 3.2, "corners": 5.8, "yellows": 1.8, "elo": 2140},
    "FRA": {"attack": 1.90, "defense": 0.70, "sot": 5.5, "sot_against": 3.0, "fouls": 14.0, "offsides": 2.5, "corners": 6.0, "yellows": 1.7, "elo": 2055},
    "ENG": {"attack": 1.80, "defense": 0.72, "sot": 5.8, "sot_against": 3.1, "fouls": 12.5, "offsides": 3.5, "corners": 5.5, "yellows": 1.5, "elo": 2012},
    "BRA": {"attack": 1.90, "defense": 0.80, "sot": 6.0, "sot_against": 3.2, "fouls": 14.5, "offsides": 2.8, "corners": 6.2, "yellows": 2.0, "elo": 2002},
    "ESP": {"attack": 1.85, "defense": 0.72, "sot": 5.5, "sot_against": 2.8, "fouls": 11.0, "offsides": 2.0, "corners": 5.8, "yellows": 1.6, "elo": 1998},
    "GER": {"attack": 1.75, "defense": 0.78, "sot": 5.2, "sot_against": 3.5, "fouls": 12.5, "offsides": 2.5, "corners": 5.5, "yellows": 1.5, "elo": 1962},
    "POR": {"attack": 2.00, "defense": 0.80, "sot": 5.8, "sot_against": 3.0, "fouls": 13.0, "offsides": 2.8, "corners": 5.5, "yellows": 1.8, "elo": 1960},
    "NED": {"attack": 1.70, "defense": 0.80, "sot": 5.0, "sot_against": 3.4, "fouls": 13.0, "offsides": 2.8, "corners": 5.5, "yellows": 1.7, "elo": 1942},
    "BEL": {"attack": 1.60, "defense": 0.85, "sot": 4.8, "sot_against": 3.5, "fouls": 13.5, "offsides": 2.5, "corners": 5.0, "yellows": 1.8, "elo": 1912},
    "URU": {"attack": 1.60, "defense": 0.78, "sot": 4.5, "sot_against": 3.2, "fouls": 15.5, "offsides": 2.2, "corners": 5.2, "yellows": 2.2, "elo": 1892},
    "MEX": {"attack": 1.45, "defense": 0.95, "sot": 4.5, "sot_against": 3.8, "fouls": 13.5, "offsides": 2.5, "corners": 5.0, "yellows": 1.8, "elo": 1852},
    "USA": {"attack": 1.50, "defense": 0.90, "sot": 4.5, "sot_against": 3.5, "fouls": 13.0, "offsides": 2.3, "corners": 5.0, "yellows": 1.6, "elo": 1848},
    "COL": {"attack": 1.55, "defense": 0.95, "sot": 4.8, "sot_against": 3.8, "fouls": 14.5, "offsides": 2.5, "corners": 5.2, "yellows": 2.0, "elo": 1842},
    "SUI": {"attack": 1.45, "defense": 0.82, "sot": 4.5, "sot_against": 3.5, "fouls": 13.5, "offsides": 2.0, "corners": 5.0, "yellows": 1.7, "elo": 1842},
    "JPN": {"attack": 1.50, "defense": 0.90, "sot": 4.5, "sot_against": 3.5, "fouls": 11.5, "offsides": 2.3, "corners": 4.8, "yellows": 1.4, "elo": 1838},
    "MAR": {"attack": 1.35, "defense": 0.72, "sot": 4.2, "sot_against": 3.0, "fouls": 14.0, "offsides": 2.0, "corners": 4.8, "yellows": 2.0, "elo": 1840},
    "SEN": {"attack": 1.40, "defense": 0.88, "sot": 4.2, "sot_against": 3.5, "fouls": 14.5, "offsides": 2.2, "corners": 4.8, "yellows": 1.9, "elo": 1822},
    "CRO": {"attack": 1.40, "defense": 0.85, "sot": 4.3, "sot_against": 3.5, "fouls": 14.0, "offsides": 2.5, "corners": 5.0, "yellows": 1.8, "elo": 1822},
    "TUR": {"attack": 1.40, "defense": 0.95, "sot": 4.3, "sot_against": 3.8, "fouls": 14.5, "offsides": 2.3, "corners": 5.0, "yellows": 2.0, "elo": 1818},
    "NOR": {"attack": 1.50, "defense": 1.00, "sot": 4.8, "sot_against": 4.0, "fouls": 12.5, "offsides": 3.5, "corners": 5.2, "yellows": 1.5, "elo": 1808},
    "CZE": {"attack": 1.35, "defense": 0.95, "sot": 4.2, "sot_against": 3.8, "fouls": 13.0, "offsides": 2.0, "corners": 4.8, "yellows": 1.7, "elo": 1792},
    "KOR": {"attack": 1.30, "defense": 0.98, "sot": 3.8, "sot_against": 3.8, "fouls": 12.5, "offsides": 2.0, "corners": 4.5, "yellows": 1.6, "elo": 1788},
    "AUT": {"attack": 1.45, "defense": 0.95, "sot": 4.5, "sot_against": 3.8, "fouls": 12.5, "offsides": 2.3, "corners": 5.0, "yellows": 1.7, "elo": 1785},
    "SWE": {"attack": 1.30, "defense": 0.92, "sot": 4.0, "sot_against": 3.8, "fouls": 13.0, "offsides": 2.0, "corners": 4.8, "yellows": 1.8, "elo": 1778},
    "AUS": {"attack": 1.25, "defense": 1.00, "sot": 3.8, "sot_against": 4.0, "fouls": 13.5, "offsides": 1.8, "corners": 4.8, "yellows": 1.8, "elo": 1762},
    "CAN": {"attack": 1.30, "defense": 1.00, "sot": 4.0, "sot_against": 4.0, "fouls": 13.5, "offsides": 2.5, "corners": 5.0, "yellows": 1.8, "elo": 1755},
    "SCO": {"attack": 1.25, "defense": 1.05, "sot": 4.0, "sot_against": 4.2, "fouls": 13.0, "offsides": 2.2, "corners": 5.0, "yellows": 1.7, "elo": 1745},
    "GHA": {"attack": 1.25, "defense": 1.08, "sot": 3.8, "sot_against": 4.0, "fouls": 14.0, "offsides": 2.0, "corners": 4.5, "yellows": 1.8, "elo": 1732},
    "IRN": {"attack": 1.10, "defense": 0.90, "sot": 3.5, "sot_against": 3.8, "fouls": 14.5, "offsides": 1.8, "corners": 4.2, "yellows": 2.0, "elo": 1725},
    "ALG": {"attack": 1.25, "defense": 1.05, "sot": 3.8, "sot_against": 3.8, "fouls": 14.0, "offsides": 2.0, "corners": 4.5, "yellows": 1.9, "elo": 1722},
    "TUN": {"attack": 1.10, "defense": 0.98, "sot": 3.5, "sot_against": 3.8, "fouls": 14.0, "offsides": 1.8, "corners": 4.5, "yellows": 1.9, "elo": 1715},
    "ECU": {"attack": 1.30, "defense": 1.08, "sot": 4.0, "sot_against": 4.0, "fouls": 14.0, "offsides": 2.2, "corners": 4.8, "yellows": 1.8, "elo": 1712},
    "PAR": {"attack": 1.10, "defense": 1.05, "sot": 3.5, "sot_against": 4.0, "fouls": 15.0, "offsides": 1.8, "corners": 4.5, "yellows": 2.0, "elo": 1700},
    "EGY": {"attack": 1.10, "defense": 0.98, "sot": 3.5, "sot_against": 3.8, "fouls": 14.0, "offsides": 1.8, "corners": 4.5, "yellows": 1.8, "elo": 1702},
    "BIH": {"attack": 1.10, "defense": 1.10, "sot": 3.5, "sot_against": 4.0, "fouls": 14.0, "offsides": 2.0, "corners": 4.5, "yellows": 1.9, "elo": 1690},
    "UZB": {"attack": 1.15, "defense": 1.05, "sot": 3.5, "sot_against": 3.8, "fouls": 13.0, "offsides": 2.0, "corners": 4.5, "yellows": 1.7, "elo": 1685},
    "IRQ": {"attack": 1.10, "defense": 1.15, "sot": 3.3, "sot_against": 4.2, "fouls": 14.5, "offsides": 1.8, "corners": 4.2, "yellows": 2.0, "elo": 1675},
    "CIV": {"attack": 1.25, "defense": 1.10, "sot": 3.8, "sot_against": 4.0, "fouls": 14.5, "offsides": 2.0, "corners": 4.8, "yellows": 2.0, "elo": 1682},
    "RSA": {"attack": 1.00, "defense": 1.15, "sot": 3.2, "sot_against": 4.2, "fouls": 14.0, "offsides": 1.8, "corners": 4.2, "yellows": 1.8, "elo": 1645},
    "QAT": {"attack": 1.05, "defense": 1.25, "sot": 3.2, "sot_against": 4.5, "fouls": 13.5, "offsides": 1.5, "corners": 4.5, "yellows": 1.7, "elo": 1638},
    "JOR": {"attack": 0.90, "defense": 1.20, "sot": 3.0, "sot_against": 4.5, "fouls": 14.0, "offsides": 1.5, "corners": 4.0, "yellows": 1.9, "elo": 1622},
    "KSA": {"attack": 1.05, "defense": 1.20, "sot": 3.2, "sot_against": 4.5, "fouls": 14.0, "offsides": 2.0, "corners": 4.5, "yellows": 2.0, "elo": 1625},
    "COD": {"attack": 0.95, "defense": 1.25, "sot": 3.0, "sot_against": 4.5, "fouls": 14.5, "offsides": 1.8, "corners": 4.0, "yellows": 2.0, "elo": 1615},
    "PAN": {"attack": 0.90, "defense": 1.10, "sot": 3.0, "sot_against": 4.0, "fouls": 14.5, "offsides": 1.5, "corners": 4.0, "yellows": 2.0, "elo": 1615},
    "CPV": {"attack": 0.95, "defense": 1.30, "sot": 3.0, "sot_against": 4.8, "fouls": 14.0, "offsides": 1.5, "corners": 4.0, "yellows": 1.8, "elo": 1585},
    "Haiti": {"attack": 0.75, "defense": 1.50, "sot": 2.5, "sot_against": 5.0, "fouls": 14.5, "offsides": 1.5, "corners": 3.5, "yellows": 2.2, "elo": 1532},
    "Curacao": {"attack": 0.80, "defense": 1.45, "sot": 2.8, "sot_against": 5.0, "fouls": 14.0, "offsides": 1.5, "corners": 3.8, "yellows": 2.0, "elo": 1505},
    "New Zealand": {"attack": 0.80, "defense": 1.40, "sot": 2.8, "sot_against": 5.0, "fouls": 13.0, "offsides": 1.5, "corners": 3.8, "yellows": 1.8, "elo": 1495},
}

# Default stats for unknown teams (mid-lower tier)
DEFAULT_STATS = {
    "attack": 1.10, "defense": 1.10, "sot": 3.5, "sot_against": 4.0,
    "fouls": 14.0, "offsides": 2.0, "corners": 4.5, "yellows": 1.8, "elo": 1650,
}

# Full name -> team code mapping (lowercase keys)
NAME_TO_CODE: dict[str, str] = {
    "argentina": "ARG", "france": "FRA", "england": "ENG", "brazil": "BRA",
    "spain": "ESP", "germany": "GER", "portugal": "POR", "netherlands": "NED",
    "belgium": "BEL", "uruguay": "URU", "mexico": "MEX", "united states": "USA",
    "usa": "USA", "colombia": "COL", "switzerland": "SUI", "japan": "JPN",
    "morocco": "MAR", "senegal": "SEN", "croatia": "CRO",
    "turkey": "TUR", "türkiye": "TUR", "turkiye": "TUR",
    "norway": "NOR", "czech republic": "CZE", "czechia": "CZE",
    "south korea": "KOR", "korea republic": "KOR", "austria": "AUT",
    "sweden": "SWE", "australia": "AUS", "canada": "CAN", "scotland": "SCO",
    "ghana": "GHA", "iran": "IRN", "algeria": "ALG", "tunisia": "TUN",
    "ecuador": "ECU", "paraguay": "PAR", "egypt": "EGY",
    "bosnia and herzegovina": "BIH", "bosnia": "BIH",
    "uzbekistan": "UZB", "iraq": "IRQ", "ivory coast": "CIV",
    "côte d'ivoire": "CIV", "cote d'ivoire": "CIV",
    "south africa": "RSA", "qatar": "QAT", "jordan": "JOR",
    "saudi arabia": "KSA", "dr congo": "COD", "congo dr": "COD",
    "panama": "PAN", "cape verde": "CPV", "haiti": "Haiti",
    "curacao": "Curacao", "curaçao": "Curacao",
    "new zealand": "New Zealand",
}

# Code -> canonical full name
CODE_TO_NAME: dict[str, str] = {
    "ARG": "Argentina", "FRA": "France", "ENG": "England", "BRA": "Brazil",
    "ESP": "Spain", "GER": "Germany", "POR": "Portugal", "NED": "Netherlands",
    "BEL": "Belgium", "URU": "Uruguay", "MEX": "Mexico", "USA": "United States",
    "COL": "Colombia", "SUI": "Switzerland", "JPN": "Japan", "MAR": "Morocco",
    "SEN": "Senegal", "CRO": "Croatia", "TUR": "Türkiye", "NOR": "Norway",
    "CZE": "Czech Republic", "KOR": "South Korea", "AUT": "Austria",
    "SWE": "Sweden", "AUS": "Australia", "CAN": "Canada", "SCO": "Scotland",
    "GHA": "Ghana", "IRN": "Iran", "ALG": "Algeria", "TUN": "Tunisia",
    "ECU": "Ecuador", "PAR": "Paraguay", "EGY": "Egypt", "BIH": "Bosnia",
    "UZB": "Uzbekistan", "IRQ": "Iraq", "CIV": "Ivory Coast", "RSA": "South Africa",
    "QAT": "Qatar", "JOR": "Jordan", "KSA": "Saudi Arabia", "COD": "DR Congo",
    "PAN": "Panama", "CPV": "Cape Verde", "Haiti": "Haiti",
    "Curacao": "Curaçao", "New Zealand": "New Zealand",
}


def get_stats(code: str) -> dict:
    """Return team stats by code; fall back to DEFAULT_STATS if unknown."""
    return TEAM_STATS.get(code, DEFAULT_STATS)


def name_to_code(name: str) -> str | None:
    """Convert a full team name (case-insensitive) to its 3-letter code."""
    return NAME_TO_CODE.get(name.lower().strip())
