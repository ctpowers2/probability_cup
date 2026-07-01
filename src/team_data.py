# Team statistics for 2026 World Cup.
# attack/defense: avg goals scored/conceded per game (recent international form)
# sot / sot_against: shots on target for/against per game
# fouls: avg fouls committed per game
# offsides: avg offsides per game
# corners: avg corners won per game
# yellows: avg yellow cards per game
# elo: FIFA-style Elo rating
# so_skill: penalty-shootout skill, ~0.5 = average (from historical shootout records)

TEAM_STATS: dict[str, dict] = {
    "ARG": {"attack": 2.27, "defense": 0.68, "sot": 5.8, "sot_against": 3.2, "fouls": 13.5, "offsides": 3.2, "corners": 5.8, "yellows": 1.8, "elo": 2148, "so_skill": 0.64},
    "FRA": {"attack": 2.26, "defense": 0.68, "sot": 5.5, "sot_against": 3.0, "fouls": 14.0, "offsides": 2.5, "corners": 6.0, "yellows": 1.7, "elo": 2134, "so_skill": 0.46},
    "ENG": {"attack": 1.83, "defense": 0.71, "sot": 5.8, "sot_against": 3.1, "fouls": 12.5, "offsides": 3.5, "corners": 5.5, "yellows": 1.5, "elo": 2038, "so_skill": 0.36},
    "BRA": {"attack": 1.94, "defense": 0.78, "sot": 6.0, "sot_against": 3.2, "fouls": 14.5, "offsides": 2.8, "corners": 6.2, "yellows": 2.0, "elo": 2031, "so_skill": 0.53},
    "ESP": {"attack": 2.04, "defense": 0.65, "sot": 5.5, "sot_against": 2.8, "fouls": 11.0, "offsides": 2.0, "corners": 5.8, "yellows": 1.6, "elo": 2144, "so_skill": 0.5},
    "GER": {"attack": 1.68, "defense": 0.81, "sot": 5.2, "sot_against": 3.5, "fouls": 12.5, "offsides": 2.5, "corners": 5.5, "yellows": 1.5, "elo": 1908, "so_skill": 0.73},
    "POR": {"attack": 2.04, "defense": 0.78, "sot": 5.8, "sot_against": 3.0, "fouls": 13.0, "offsides": 2.8, "corners": 5.5, "yellows": 1.8, "elo": 1990, "so_skill": 0.55},
    "NED": {"attack": 1.73, "defense": 0.78, "sot": 5.0, "sot_against": 3.4, "fouls": 13.0, "offsides": 2.8, "corners": 5.5, "yellows": 1.7, "elo": 1971, "so_skill": 0.33},
    "BEL": {"attack": 1.57, "defense": 0.87, "sot": 4.8, "sot_against": 3.5, "fouls": 13.5, "offsides": 2.5, "corners": 5.0, "yellows": 1.8, "elo": 1884, "so_skill": 0.5},
    "URU": {"attack": 1.54, "defense": 0.81, "sot": 4.5, "sot_against": 3.2, "fouls": 15.5, "offsides": 2.2, "corners": 5.2, "yellows": 2.2, "elo": 1841, "so_skill": 0.5},
    "MEX": {"attack": 1.54, "defense": 0.89, "sot": 4.5, "sot_against": 3.8, "fouls": 13.5, "offsides": 2.5, "corners": 5.0, "yellows": 1.8, "elo": 1943, "so_skill": 0.47},
    "USA": {"attack": 1.43, "defense": 0.94, "sot": 4.5, "sot_against": 3.5, "fouls": 13.0, "offsides": 2.3, "corners": 5.0, "yellows": 1.6, "elo": 1781, "so_skill": 0.5},
    "COL": {"attack": 1.73, "defense": 0.84, "sot": 4.8, "sot_against": 3.8, "fouls": 14.5, "offsides": 2.5, "corners": 5.2, "yellows": 2.0, "elo": 2004, "so_skill": 0.5},
    "SUI": {"attack": 1.52, "defense": 0.78, "sot": 4.5, "sot_against": 3.5, "fouls": 13.5, "offsides": 2.0, "corners": 5.0, "yellows": 1.7, "elo": 1914, "so_skill": 0.33},
    "JPN": {"attack": 1.55, "defense": 0.87, "sot": 4.5, "sot_against": 3.5, "fouls": 11.5, "offsides": 2.3, "corners": 4.8, "yellows": 1.4, "elo": 1888, "so_skill": 0.45},
    "MAR": {"attack": 1.39, "defense": 0.7, "sot": 4.2, "sot_against": 3.0, "fouls": 14.0, "offsides": 2.0, "corners": 4.8, "yellows": 2.0, "elo": 1886, "so_skill": 0.5},
    "SEN": {"attack": 1.47, "defense": 0.99, "sot": 4.2, "sot_against": 3.5, "fouls": 14.5, "offsides": 2.2, "corners": 4.8, "yellows": 1.9, "elo": 1842, "so_skill": 0.38},
    "CRO": {"attack": 1.48, "defense": 0.8, "sot": 4.3, "sot_against": 3.5, "fouls": 14.0, "offsides": 2.5, "corners": 5.0, "yellows": 1.8, "elo": 1905, "so_skill": 0.67},
    "TUR": {"attack": 1.43, "defense": 0.93, "sot": 4.3, "sot_against": 3.8, "fouls": 14.5, "offsides": 2.3, "corners": 5.0, "yellows": 2.0, "elo": 1852, "so_skill": 0.5},
    "NOR": {"attack": 1.95, "defense": 0.93, "sot": 4.8, "sot_against": 4.0, "fouls": 12.5, "offsides": 3.5, "corners": 5.2, "yellows": 1.5, "elo": 1934, "so_skill": 0.5},
    "CZE": {"attack": 1.24, "defense": 1.02, "sot": 4.2, "sot_against": 3.8, "fouls": 13.0, "offsides": 2.0, "corners": 4.8, "yellows": 1.7, "elo": 1680, "so_skill": 0.6},
    "KOR": {"attack": 1.24, "defense": 1.02, "sot": 3.8, "sot_against": 3.8, "fouls": 12.5, "offsides": 2.0, "corners": 4.5, "yellows": 1.6, "elo": 1723, "so_skill": 0.62},
    "AUT": {"attack": 1.68, "defense": 0.96, "sot": 4.5, "sot_against": 3.8, "fouls": 12.5, "offsides": 2.3, "corners": 5.0, "yellows": 1.7, "elo": 1836, "so_skill": 0.5},
    "SWE": {"attack": 1.26, "defense": 0.95, "sot": 4.0, "sot_against": 3.8, "fouls": 13.0, "offsides": 2.0, "corners": 4.8, "yellows": 1.8, "elo": 1731, "so_skill": 0.5},
    "AUS": {"attack": 1.28, "defense": 0.97, "sot": 3.8, "sot_against": 4.0, "fouls": 13.5, "offsides": 1.8, "corners": 4.8, "yellows": 1.8, "elo": 1800, "so_skill": 0.5},
    "CAN": {"attack": 1.31, "defense": 0.99, "sot": 4.0, "sot_against": 4.0, "fouls": 13.5, "offsides": 2.5, "corners": 5.0, "yellows": 1.8, "elo": 1764, "so_skill": 0.5},
    "SCO": {"attack": 1.25, "defense": 1.05, "sot": 4.0, "sot_against": 4.2, "fouls": 13.0, "offsides": 2.2, "corners": 5.0, "yellows": 1.7, "elo": 1745, "so_skill": 0.5},
    "GHA": {"attack": 1.11, "defense": 1.2, "sot": 3.8, "sot_against": 4.0, "fouls": 14.0, "offsides": 2.0, "corners": 4.5, "yellows": 1.8, "elo": 1575, "so_skill": 0.3},
    "IRN": {"attack": 1.13, "defense": 0.88, "sot": 3.5, "sot_against": 3.8, "fouls": 14.5, "offsides": 1.8, "corners": 4.2, "yellows": 2.0, "elo": 1764, "so_skill": 0.5},
    "ALG": {"attack": 1.15, "defense": 1.08, "sot": 3.8, "sot_against": 3.8, "fouls": 14.0, "offsides": 2.0, "corners": 4.5, "yellows": 1.9, "elo": 1785, "so_skill": 0.5},
    "TUN": {"attack": 0.98, "defense": 1.08, "sot": 3.5, "sot_against": 3.8, "fouls": 14.0, "offsides": 1.8, "corners": 4.5, "yellows": 1.9, "elo": 1562, "so_skill": 0.5},
    "ECU": {"attack": 1.44, "defense": 0.96, "sot": 4.0, "sot_against": 4.0, "fouls": 14.0, "offsides": 2.2, "corners": 4.8, "yellows": 1.8, "elo": 1871, "so_skill": 0.5},
    "PAR": {"attack": 1.19, "defense": 0.96, "sot": 3.5, "sot_against": 4.0, "fouls": 15.0, "offsides": 1.8, "corners": 4.5, "yellows": 2.0, "elo": 1823, "so_skill": 0.5},
    "EGY": {"attack": 1.13, "defense": 0.95, "sot": 3.5, "sot_against": 3.8, "fouls": 14.0, "offsides": 1.8, "corners": 4.5, "yellows": 1.8, "elo": 1742, "so_skill": 0.5},
    "BIH": {"attack": 1.05, "defense": 1.15, "sot": 3.5, "sot_against": 4.0, "fouls": 14.0, "offsides": 2.0, "corners": 4.5, "yellows": 1.9, "elo": 1622, "so_skill": 0.5},
    "UZB": {"attack": 1.11, "defense": 1.09, "sot": 3.5, "sot_against": 3.8, "fouls": 13.0, "offsides": 2.0, "corners": 4.5, "yellows": 1.7, "elo": 1631, "so_skill": 0.5},
    "IRQ": {"attack": 1.03, "defense": 1.48, "sot": 3.3, "sot_against": 4.2, "fouls": 14.5, "offsides": 1.8, "corners": 4.2, "yellows": 2.0, "elo": 1561, "so_skill": 0.5},
    "CIV": {"attack": 1.29, "defense": 1.07, "sot": 3.8, "sot_against": 4.0, "fouls": 14.5, "offsides": 2.0, "corners": 4.8, "yellows": 2.0, "elo": 1727, "so_skill": 0.5},
    "RSA": {"attack": 0.94, "defense": 1.22, "sot": 3.2, "sot_against": 4.2, "fouls": 14.0, "offsides": 1.8, "corners": 4.2, "yellows": 1.8, "elo": 1559, "so_skill": 0.5},
    "QAT": {"attack": 0.88, "defense": 1.45, "sot": 3.2, "sot_against": 4.5, "fouls": 13.5, "offsides": 1.5, "corners": 4.5, "yellows": 1.7, "elo": 1411, "so_skill": 0.5},
    "JOR": {"attack": 0.95, "defense": 1.33, "sot": 3.0, "sot_against": 4.5, "fouls": 14.0, "offsides": 1.5, "corners": 4.0, "yellows": 1.9, "elo": 1628, "so_skill": 0.5},
    "KSA": {"attack": 1.03, "defense": 1.22, "sot": 3.2, "sot_against": 4.5, "fouls": 14.0, "offsides": 2.0, "corners": 4.5, "yellows": 2.0, "elo": 1596, "so_skill": 0.5},
    "COD": {"attack": 1.01, "defense": 1.17, "sot": 3.0, "sot_against": 4.5, "fouls": 14.5, "offsides": 1.8, "corners": 4.0, "yellows": 2.0, "elo": 1712, "so_skill": 0.5},
    "PAN": {"attack": 0.93, "defense": 1.07, "sot": 3.0, "sot_against": 4.0, "fouls": 14.5, "offsides": 1.5, "corners": 4.0, "yellows": 2.0, "elo": 1658, "so_skill": 0.5},
    "CPV": {"attack": 0.97, "defense": 1.27, "sot": 3.0, "sot_against": 4.8, "fouls": 14.0, "offsides": 1.5, "corners": 4.0, "yellows": 1.8, "elo": 1622, "so_skill": 0.5},
    "Haiti": {"attack": 0.74, "defense": 1.52, "sot": 2.5, "sot_against": 5.0, "fouls": 14.5, "offsides": 1.5, "corners": 3.5, "yellows": 2.2, "elo": 1517, "so_skill": 0.5},
    "Curacao": {"attack": 0.76, "defense": 1.52, "sot": 2.8, "sot_against": 5.0, "fouls": 14.0, "offsides": 1.5, "corners": 3.8, "yellows": 2.0, "elo": 1438, "so_skill": 0.5},
    "New Zealand": {"attack": 0.82, "defense": 1.36, "sot": 2.8, "sot_against": 5.0, "fouls": 13.0, "offsides": 1.5, "corners": 3.8, "yellows": 1.8, "elo": 1534, "so_skill": 0.5},
}

# Default stats for unknown teams (mid-lower tier)
DEFAULT_STATS = {
    "attack": 1.10, "defense": 1.10, "sot": 3.5, "sot_against": 4.0,
    "fouls": 14.0, "offsides": 2.0, "corners": 4.5, "yellows": 1.8, "elo": 1650,
    "so_skill": 0.50,
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
