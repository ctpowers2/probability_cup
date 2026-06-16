# Player statistics for known World Cup 2026 participants.
# sot_per_game: avg shots on target per 90 min
# goal_per_game: avg goals per 90 min
# assist_per_game: avg assists per 90 min
# team: team code

PLAYER_STATS: dict[str, dict] = {
    # Argentina
    "lionel messi":         {"team": "ARG", "sot_per_game": 1.4, "goal_per_game": 0.65, "assist_per_game": 0.45},
    "lautaro martinez":     {"team": "ARG", "sot_per_game": 1.5, "goal_per_game": 0.60, "assist_per_game": 0.20},
    "rodrigo de paul":      {"team": "ARG", "sot_per_game": 0.6, "goal_per_game": 0.15, "assist_per_game": 0.25},
    "julian alvarez":       {"team": "ARG", "sot_per_game": 1.2, "goal_per_game": 0.50, "assist_per_game": 0.25},

    # France
    "kylian mbappe":        {"team": "FRA", "sot_per_game": 1.8, "goal_per_game": 0.80, "assist_per_game": 0.30},
    "antoine griezmann":    {"team": "FRA", "sot_per_game": 1.2, "goal_per_game": 0.40, "assist_per_game": 0.35},
    "ousmane dembele":      {"team": "FRA", "sot_per_game": 1.3, "goal_per_game": 0.30, "assist_per_game": 0.40},

    # England
    "harry kane":           {"team": "ENG", "sot_per_game": 1.8, "goal_per_game": 0.70, "assist_per_game": 0.25},
    "jude bellingham":      {"team": "ENG", "sot_per_game": 1.2, "goal_per_game": 0.40, "assist_per_game": 0.35},
    "bukayo saka":          {"team": "ENG", "sot_per_game": 1.3, "goal_per_game": 0.35, "assist_per_game": 0.40},
    "phil foden":           {"team": "ENG", "sot_per_game": 1.2, "goal_per_game": 0.35, "assist_per_game": 0.35},

    # Brazil
    "vinicius junior":      {"team": "BRA", "sot_per_game": 1.7, "goal_per_game": 0.55, "assist_per_game": 0.35},
    "rodrygo":              {"team": "BRA", "sot_per_game": 1.3, "goal_per_game": 0.40, "assist_per_game": 0.30},
    "raphinha":             {"team": "BRA", "sot_per_game": 1.4, "goal_per_game": 0.40, "assist_per_game": 0.35},

    # Spain
    "pedri":                {"team": "ESP", "sot_per_game": 0.8, "goal_per_game": 0.20, "assist_per_game": 0.30},
    "ferran torres":        {"team": "ESP", "sot_per_game": 1.2, "goal_per_game": 0.40, "assist_per_game": 0.25},
    "alvaro morata":        {"team": "ESP", "sot_per_game": 1.3, "goal_per_game": 0.45, "assist_per_game": 0.20},

    # Germany
    "florian wirtz":        {"team": "GER", "sot_per_game": 1.2, "goal_per_game": 0.38, "assist_per_game": 0.40},
    "kai havertz":          {"team": "GER", "sot_per_game": 1.1, "goal_per_game": 0.35, "assist_per_game": 0.25},
    "jamal musiala":        {"team": "GER", "sot_per_game": 1.4, "goal_per_game": 0.38, "assist_per_game": 0.35},

    # Portugal
    "cristiano ronaldo":    {"team": "POR", "sot_per_game": 2.0, "goal_per_game": 0.80, "assist_per_game": 0.20},
    "bruno fernandes":      {"team": "POR", "sot_per_game": 1.5, "goal_per_game": 0.45, "assist_per_game": 0.45},
    "rafael leao":          {"team": "POR", "sot_per_game": 1.3, "goal_per_game": 0.35, "assist_per_game": 0.35},

    # Netherlands
    "cody gakpo":           {"team": "NED", "sot_per_game": 1.3, "goal_per_game": 0.40, "assist_per_game": 0.28},
    "xavi simons":          {"team": "NED", "sot_per_game": 1.1, "goal_per_game": 0.32, "assist_per_game": 0.32},

    # Belgium
    "romelu lukaku":        {"team": "BEL", "sot_per_game": 1.6, "goal_per_game": 0.55, "assist_per_game": 0.20},
    "kevin de bruyne":      {"team": "BEL", "sot_per_game": 1.1, "goal_per_game": 0.25, "assist_per_game": 0.55},

    # Colombia
    "james rodriguez":      {"team": "COL", "sot_per_game": 0.9, "goal_per_game": 0.22, "assist_per_game": 0.45},
    "luis diaz":            {"team": "COL", "sot_per_game": 1.4, "goal_per_game": 0.40, "assist_per_game": 0.30},
    "radamel falcao":       {"team": "COL", "sot_per_game": 1.2, "goal_per_game": 0.45, "assist_per_game": 0.15},

    # Morocco
    "hakim ziyech":         {"team": "MAR", "sot_per_game": 1.2, "goal_per_game": 0.30, "assist_per_game": 0.40},
    "youssef en-nesyri":    {"team": "MAR", "sot_per_game": 1.4, "goal_per_game": 0.50, "assist_per_game": 0.15},

    # Senegal
    "sadio mane":           {"team": "SEN", "sot_per_game": 1.5, "goal_per_game": 0.55, "assist_per_game": 0.28},

    # Croatia
    "luka modric":          {"team": "CRO", "sot_per_game": 0.7, "goal_per_game": 0.15, "assist_per_game": 0.35},
    "ivan perisic":         {"team": "CRO", "sot_per_game": 1.0, "goal_per_game": 0.28, "assist_per_game": 0.28},
    "luka sucic":           {"team": "CRO", "sot_per_game": 0.9, "goal_per_game": 0.22, "assist_per_game": 0.28},

    # Norway
    "erling haaland":       {"team": "NOR", "sot_per_game": 2.2, "goal_per_game": 0.90, "assist_per_game": 0.18},
    "martin odegaard":      {"team": "NOR", "sot_per_game": 1.0, "goal_per_game": 0.28, "assist_per_game": 0.42},

    # Uruguay
    "darwin nunez":         {"team": "URU", "sot_per_game": 1.7, "goal_per_game": 0.55, "assist_per_game": 0.20},
    "federico valverde":    {"team": "URU", "sot_per_game": 1.0, "goal_per_game": 0.28, "assist_per_game": 0.32},

    # Mexico
    "hirving lozano":       {"team": "MEX", "sot_per_game": 1.2, "goal_per_game": 0.35, "assist_per_game": 0.28},
    "raul jimenez":         {"team": "MEX", "sot_per_game": 1.4, "goal_per_game": 0.48, "assist_per_game": 0.18},

    # USA
    "christian pulisic":    {"team": "USA", "sot_per_game": 1.3, "goal_per_game": 0.38, "assist_per_game": 0.35},
    "giovanni reyna":       {"team": "USA", "sot_per_game": 0.9, "goal_per_game": 0.22, "assist_per_game": 0.32},

    # Japan
    "takumi minamino":      {"team": "JPN", "sot_per_game": 1.1, "goal_per_game": 0.35, "assist_per_game": 0.25},
    "ritsu doan":           {"team": "JPN", "sot_per_game": 1.0, "goal_per_game": 0.30, "assist_per_game": 0.28},
    "kaoru mitoma":         {"team": "JPN", "sot_per_game": 1.2, "goal_per_game": 0.32, "assist_per_game": 0.30},

    # Algeria
    "riyad mahrez":         {"team": "ALG", "sot_per_game": 1.3, "goal_per_game": 0.38, "assist_per_game": 0.40},
    "islam slimani":        {"team": "ALG", "sot_per_game": 1.1, "goal_per_game": 0.38, "assist_per_game": 0.15},

    # Saudi Arabia
    "salem al-dawsari":     {"team": "KSA", "sot_per_game": 1.1, "goal_per_game": 0.35, "assist_per_game": 0.30},

    # Iraq
    "mohanad ali":          {"team": "IRQ", "sot_per_game": 0.9, "goal_per_game": 0.30, "assist_per_game": 0.18},

    # Czech Republic
    "patrik schick":        {"team": "CZE", "sot_per_game": 1.4, "goal_per_game": 0.50, "assist_per_game": 0.15},

    # Switzerland
    "granit xhaka":         {"team": "SUI", "sot_per_game": 0.7, "goal_per_game": 0.15, "assist_per_game": 0.30},
    "breel embolo":         {"team": "SUI", "sot_per_game": 1.2, "goal_per_game": 0.40, "assist_per_game": 0.18},

    # Canada
    "alphonso davies":      {"team": "CAN", "sot_per_game": 1.0, "goal_per_game": 0.28, "assist_per_game": 0.35},
    "jonathan david":       {"team": "CAN", "sot_per_game": 1.5, "goal_per_game": 0.55, "assist_per_game": 0.18},

    # Ecuador
    "enner valencia":       {"team": "ECU", "sot_per_game": 1.3, "goal_per_game": 0.45, "assist_per_game": 0.18},

    # Ghana
    "jordan ayew":          {"team": "GHA", "sot_per_game": 0.9, "goal_per_game": 0.25, "assist_per_game": 0.22},

    # Tunisia
    "wahbi khazri":         {"team": "TUN", "sot_per_game": 0.9, "goal_per_game": 0.28, "assist_per_game": 0.25},

    # South Korea
    "son heung-min":        {"team": "KOR", "sot_per_game": 1.4, "goal_per_game": 0.48, "assist_per_game": 0.30},

    # Iran
    "sardar azmoun":        {"team": "IRN", "sot_per_game": 1.3, "goal_per_game": 0.42, "assist_per_game": 0.22},
    "mehdi taremi":         {"team": "IRN", "sot_per_game": 1.4, "goal_per_game": 0.45, "assist_per_game": 0.22},
}

# Default profile for unknown players on unknown/weak teams
DEFAULT_PLAYER = {"sot_per_game": 0.6, "goal_per_game": 0.18, "assist_per_game": 0.15}


def _normalize(name: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    return " ".join(ascii_only.lower().split())


# Pre-built accent-stripped index for fast lookup
_NORMALIZED_INDEX: dict[str, str] = {_normalize(k): k for k in PLAYER_STATS}


def get_player_stats(name: str) -> dict | None:
    """Return player stats by name (case-insensitive, accent-insensitive)."""
    key = _normalize(name)
    canonical = _NORMALIZED_INDEX.get(key)
    if canonical:
        return PLAYER_STATS[canonical]
    # Partial match fallback: accept if normalized key is a substring
    for nk, canonical in _NORMALIZED_INDEX.items():
        if key in nk or nk in key:
            return PLAYER_STATS[canonical]
    return None
