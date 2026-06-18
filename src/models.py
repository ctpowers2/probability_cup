"""
Statistical models for World Cup match prediction.

Core model: Dixon-Coles Poisson model for goals.
All other stats (SOT, fouls, offsides, corners, cards) use independent
Poisson distributions calibrated from team-level averages.
"""

import math
from scipy.stats import poisson

# Tournament-wide league averages (per team per game)
LEAGUE = {
    "goals":   1.35,
    "sot":     4.20,
    "fouls":   14.0,
    "offsides": 2.10,
    "corners":  5.00,
    "yellows":  1.85,
}

# Red card & penalty base rates per game (match-level, not per team)
BASE_RED_CARD_RATE   = 0.06
BASE_PENALTY_RATE    = 0.30

# WC tournament play is more conservative — fewer offsides than league priors.
# Calibrated from WC 2026 observed data (3/3 high-confidence offside predictions
# were too high before this correction).
WC_OFFSIDES_SCALE = 0.60

# Half-time proportion of full-game stats
H1_FRAC = {"goals": 0.45, "sot": 0.48, "corners": 0.48, "fouls": 0.50, "offsides": 0.50, "yellows": 0.50}
H2_FRAC = {k: 1.0 - v for k, v in H1_FRAC.items()}


def _dc_expected(home_atk: float, home_def: float,
                 away_atk: float, away_def: float,
                 league_avg: float) -> tuple[float, float]:
    """
    Dixon-Coles: expected stat for home (A) and away (B).

    home_atk / away_atk = avg stat scored per game (higher = stronger attack).
    home_def / away_def = avg stat conceded per game (lower = stronger defense).

    mu_A = (atk_A / league) * (def_B / league) * league  =  atk_A * def_B / league
    """
    mu_a = home_atk * away_def / league_avg
    mu_b = away_atk * home_def / league_avg
    return max(mu_a, 0.01), max(mu_b, 0.01)


class MatchModel:
    """
    Full statistical model for a single match.
    team_a_stats / team_b_stats: dicts from team_data.TEAM_STATS
    wc_goals_scale: observed WC goals per team / league prior (default 1.0)
    """

    def __init__(self, team_a_stats: dict, team_b_stats: dict,
                 team_a_code: str = "", team_b_code: str = "",
                 wc_goals_scale: float = 1.0):
        self.a = team_a_stats
        self.b = team_b_stats
        self.a_code = team_a_code
        self.b_code = team_b_code
        self.wc_goals_scale = wc_goals_scale
        self._build()

    # ------------------------------------------------------------------ #
    # Setup                                                                #
    # ------------------------------------------------------------------ #

    def _build(self):
        a, b = self.a, self.b

        # Goals (main Poisson means), scaled to observed WC goals rate
        raw_goals_a, raw_goals_b = _dc_expected(
            a["attack"], a["defense"], b["attack"], b["defense"], LEAGUE["goals"]
        )
        self.mu_goals_a = raw_goals_a * self.wc_goals_scale
        self.mu_goals_b = raw_goals_b * self.wc_goals_scale

        # Shots on target
        self.mu_sot_a, self.mu_sot_b = _dc_expected(
            a["sot"], a["sot_against"], b["sot"], b["sot_against"], LEAGUE["sot"]
        )

        # Fouls — independent (DC adjustment hurt performance: game-state effects
        # dominate and DC overcorrects when opponent attack is far from average)
        self.mu_fouls_a = a["fouls"]
        self.mu_fouls_b = b["fouls"]

        # Offsides — DC-style but scaled down for WC tournament play.
        # WC teams run more conservative lines → fewer offsides than league priors.
        self.mu_offsides_a = a["offsides"] * b["attack"] / LEAGUE["goals"] * WC_OFFSIDES_SCALE
        self.mu_offsides_b = b["offsides"] * a["attack"] / LEAGUE["goals"] * WC_OFFSIDES_SCALE

        # Corners (independent)
        self.mu_corners_a = a["corners"]
        self.mu_corners_b = b["corners"]

        # Yellow cards (independent)
        self.mu_yellows_a = a["yellows"]
        self.mu_yellows_b = b["yellows"]

        # Red cards: scale with foul intensity
        foul_factor = (self.mu_fouls_a + self.mu_fouls_b) / (2 * LEAGUE["fouls"])
        self.prob_red_card = 1 - (1 - BASE_RED_CARD_RATE * foul_factor) ** 2
        self.prob_penalty   = BASE_PENALTY_RATE
        self.prob_pen_or_red = 1 - (1 - self.prob_penalty) * (1 - self.prob_red_card)

        # Half-split expectations
        for stat in ("goals", "sot", "corners", "fouls", "offsides", "yellows"):
            for side, mu_attr in (("a", f"mu_{stat}_a"), ("b", f"mu_{stat}_b")):
                base = getattr(self, mu_attr)
                setattr(self, f"h1_{stat}_{side}", base * H1_FRAC[stat])
                setattr(self, f"h2_{stat}_{side}", base * H2_FRAC[stat])

    # ------------------------------------------------------------------ #
    # Probability helpers                                                   #
    # ------------------------------------------------------------------ #

    def mu(self, stat: str, side: str, half: str = "full") -> float:
        """Return the Poisson mean for (stat, side, half)."""
        if half == "full":
            return getattr(self, f"mu_{stat}_{side}")
        return getattr(self, f"{half}_{stat}_{side}")

    def p_a_gt_b(self, stat: str, half: str = "full", max_k: int = 35) -> float:
        """P(stat_a > stat_b)"""
        lam_a = self.mu(stat, "a", half)
        lam_b = self.mu(stat, "b", half)
        return _prob_a_gt_b(lam_a, lam_b, max_k)

    # ------------------------------------------------------------------ #
    # Live match adjustment                                                #
    # ------------------------------------------------------------------ #

    def apply_live(self, score_a: int, score_b: int, minute: int) -> None:
        """
        Scale all Poisson means for remaining time and store the current score.
        Modifies in-place — call once after construction.
        """
        self.live = True
        self.score_a = score_a
        self.score_b = score_b
        self.minute = max(0, min(90, minute))

        full_r = max(0.0, (90 - self.minute) / 90)

        for stat in ("goals", "sot", "corners", "fouls", "offsides", "yellows"):
            for side in ("a", "b"):
                attr = f"mu_{stat}_{side}"
                setattr(self, attr, getattr(self, attr) * full_r)

        h1_r = max(0.0, (45 - self.minute) / 45) if self.minute <= 45 else 0.0
        h2_r = 1.0 if self.minute <= 45 else max(0.0, (90 - self.minute) / 45)

        for stat in ("goals", "sot", "corners", "fouls", "offsides", "yellows"):
            for side in ("a", "b"):
                setattr(self, f"h1_{stat}_{side}",
                        getattr(self, f"h1_{stat}_{side}") * h1_r)
                setattr(self, f"h2_{stat}_{side}",
                        getattr(self, f"h2_{stat}_{side}") * h2_r)

        foul_factor = (self.mu_fouls_a + self.mu_fouls_b) / (2 * LEAGUE["fouls"])
        self.prob_red_card = 1 - (1 - BASE_RED_CARD_RATE * foul_factor) ** 2
        self.prob_pen_or_red = 1 - (1 - self.prob_penalty) * (1 - self.prob_red_card)

    # ------------------------------------------------------------------ #
    # Probability helpers (live-aware)                                     #
    # ------------------------------------------------------------------ #

    def p_win(self, side: str, max_g: int = 12) -> float:
        """P(side wins). Live-aware: conditions on current score + remaining lambdas."""
        mu_win, mu_lose = (
            (self.mu_goals_a, self.mu_goals_b) if side == "a"
            else (self.mu_goals_b, self.mu_goals_a)
        )
        lead = 0
        if getattr(self, "live", False):
            lead = (self.score_a - self.score_b) if side == "a" else (self.score_b - self.score_a)
        p = 0.0
        for g_win in range(max_g + 1):
            for g_lose in range(max_g + 1):
                if lead + g_win - g_lose > 0:
                    p += poisson.pmf(g_win, mu_win) * poisson.pmf(g_lose, mu_lose)
        return float(p)

    def p_draw(self, max_g: int = 10) -> float:
        """P(draw at FT). Live-aware: conditions on current score."""
        sa = getattr(self, "score_a", 0)
        sb = getattr(self, "score_b", 0)
        p = 0.0
        for da in range(max_g + 1):
            db = da - (sb - sa)  # need sa+da = sb+db
            if 0 <= db <= max_g:
                p += float(poisson.pmf(da, self.mu_goals_a)) * float(poisson.pmf(db, self.mu_goals_b))
        return float(p)

    def p_btts(self) -> float:
        """P(both teams score >= 1). Live-aware."""
        if getattr(self, "live", False):
            a_done = self.score_a >= 1
            b_done = self.score_b >= 1
            if a_done and b_done:
                return 1.0
            p_a = 1.0 if a_done else float(1 - poisson.pmf(0, self.mu_goals_a))
            p_b = 1.0 if b_done else float(1 - poisson.pmf(0, self.mu_goals_b))
            return p_a * p_b
        return float((1 - poisson.pmf(0, self.mu_goals_a)) *
                     (1 - poisson.pmf(0, self.mu_goals_b)))

    def p_ge(self, stat: str, side: str, n: int, half: str = "full") -> float:
        """P(stat_side >= n). Live-aware for full-match goals."""
        if getattr(self, "live", False) and stat == "goals" and half == "full":
            current = self.score_a if side == "a" else self.score_b
            if current >= n:
                return 1.0
            n = n - current
        lam = self.mu(stat, side, half)
        return float(1 - poisson.cdf(n - 1, lam))

    def p_total_ge(self, stat: str, n: int, half: str = "full") -> float:
        """P(stat_a + stat_b >= n). Live-aware for full-match goals."""
        if getattr(self, "live", False) and stat == "goals" and half == "full":
            current = self.score_a + self.score_b
            if current >= n:
                return 1.0
            n = n - current
        lam = self.mu(stat, "a", half) + self.mu(stat, "b", half)
        return float(1 - poisson.cdf(n - 1, lam))

    def p_btts_and_goals_ge(self, n: int) -> float:
        """P(both teams score AND total goals >= n)."""
        p = 0.0
        lam_a, lam_b = self.mu_goals_a, self.mu_goals_b
        for ga in range(20):
            if ga == 0:
                continue
            for gb in range(20):
                if gb == 0:
                    continue
                if ga + gb >= n:
                    p += poisson.pmf(ga, lam_a) * poisson.pmf(gb, lam_b)
        return float(p)

    def p_score_first_and_other_scores_2h(self, first_side: str, other_side: str) -> float:
        """
        P(first_side scores first goal AND other_side scores in 2H).
        Approximate: treat as independent (first-scorer * scores-in-2H).
        """
        mu_a = self.mu_goals_a
        mu_b = self.mu_goals_b
        p_any_goal = 1 - math.exp(-(mu_a + mu_b))
        if mu_a + mu_b < 1e-9:
            return 0.0
        mu_first = mu_a if first_side == "a" else mu_b
        p_first = (mu_first / (mu_a + mu_b)) * p_any_goal
        other_mu_2h = self.h2_goals_b if other_side == "b" else self.h2_goals_a
        p_other_2h = float(1 - poisson.pmf(0, other_mu_2h))
        return float(p_first * p_other_2h)

    def p_h2_more_goals_than_h1(self) -> float:
        """P(goals in 2H > goals in 1H)."""
        lam_1h = self.mu_goals_a * H1_FRAC["goals"] + self.mu_goals_b * H1_FRAC["goals"]
        lam_2h = self.mu_goals_a * H2_FRAC["goals"] + self.mu_goals_b * H2_FRAC["goals"]
        return _prob_a_gt_b(lam_2h, lam_1h)

    def p_both_sot_ge1(self, half: str = "full") -> float:
        """P(both teams have >= 1 SOT) in the given half."""
        pa = float(1 - poisson.pmf(0, self.mu("sot", "a", half)))
        pb = float(1 - poisson.pmf(0, self.mu("sot", "b", half)))
        return pa * pb

    def p_total_le(self, stat: str, n: int, half: str = "full") -> float:
        """P(stat_a + stat_b <= n)."""
        lam = self.mu(stat, "a", half) + self.mu(stat, "b", half)
        return float(poisson.cdf(n, lam))

    def p_ge_team(self, stat: str, side: str, n: int, half: str = "full") -> float:
        """Alias for p_ge — kept for clarity in solver."""
        return self.p_ge(stat, side, n, half)

    def p_total_cards_ge(self, n: int) -> float:
        """P(total yellow cards >= n)."""
        lam = self.mu_yellows_a + self.mu_yellows_b
        return float(1 - poisson.cdf(n - 1, lam))

    def p_cards_a_gt_b(self) -> float:
        """P(team A receives more yellow cards than team B)."""
        return _prob_a_gt_b(self.mu_yellows_a, self.mu_yellows_b)

    # ------------------------------------------------------------------ #
    # Player helpers                                                        #
    # ------------------------------------------------------------------ #

    def p_player_sot(self, sot_per_game: float, half: str = "full") -> float:
        """P(player has >= 1 SOT) in given half."""
        frac = H2_FRAC["sot"] if half == "h2" else (H1_FRAC["sot"] if half == "h1" else 1.0)
        lam = sot_per_game * frac
        return float(1 - poisson.pmf(0, lam))

    def p_player_goal(self, goal_per_game: float) -> float:
        """P(player scores >= 1 goal in the match)."""
        return float(1 - poisson.pmf(0, goal_per_game))

    def p_player_goal_or_assist(self, goal_per_game: float, assist_per_game: float) -> float:
        """P(player scores OR assists) — complement of P(no goal AND no assist)."""
        p_neither = poisson.pmf(0, goal_per_game) * poisson.pmf(0, assist_per_game)
        return float(1 - p_neither)


# ------------------------------------------------------------------ #
# Utility                                                              #
# ------------------------------------------------------------------ #

def prob_a_gt_b(lam_a: float, lam_b: float, max_k: int = 35) -> float:
    """P(A > B) strictly, for A ~ Pois(lam_a), B ~ Pois(lam_b)."""
    p = 0.0
    for b_val in range(max_k + 1):
        p_b = float(poisson.pmf(b_val, lam_b))
        if p_b < 1e-10:
            continue
        p += p_b * float(1 - poisson.cdf(b_val, lam_a))
    return p


# Keep old name as alias for internal use
_prob_a_gt_b = prob_a_gt_b
