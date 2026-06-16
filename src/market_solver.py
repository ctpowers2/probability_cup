"""
Parse natural-language market questions and return a probability 1-99.

Supported question patterns (all from observed World Cup 2026 markets):
  - Will {TEAM} win the match?
  - Will the match have {N}+ total goals?
  - Will both teams score AND the match have {N}+ total goals?
  - Will {TEAM} score in the [first|second] half?
  - Will {TEAM} score at least 1 goal?
  - Will {TEAM} score the first goal … and {TEAM} score in the second half?
  - Will both teams have at least 1 shot on target [in the second half]?
  - At halftime, will both teams have at least 1 shot on target?
  - Will {TEAM} have {N}+ shots on target [in the second half]?
  - Will {TEAM_A} have more shots on target than {TEAM_B} in the second half?
  - Will there be {N}+ total shots on target [in the second half]?
  - Will there be {N}+ total shots on target?
  - Will {TEAM_A} commit more fouls than {TEAM_B}?
  - Will {TEAM} be caught offside {N}+ times?
  - Will a penalty kick be awarded OR a red card be shown?
  - Will {TEAM_A} receive more cards than {TEAM_B}?
  - Will there be {N}+ total cards shown?
  - Will the second half have more goals than the first half?
  - [At halftime | In the second half], will {TEAM_A} have more corner kicks than {TEAM_B}?
  - Will {PLAYER} have at least 1 shot on target [in the second half]?
  - Will {PLAYER} score a goal (excluding own goals)?
  - Will {PLAYER} score or assist a goal?
"""

import re
from .models import MatchModel, prob_a_gt_b
from .team_data import CODE_TO_NAME, get_stats
from .player_data import DEFAULT_PLAYER, get_player_stats

# Probability clamp range (avoid Brier-score damage from extreme overconfidence)
P_MIN, P_MAX = 2, 98


def to_int_prob(p: float) -> int:
    return max(P_MIN, min(P_MAX, round(p * 100)))


# ------------------------------------------------------------------ #
# Team name extraction helpers                                         #
# ------------------------------------------------------------------ #

def _build_team_aliases(code_a: str, code_b: str) -> dict[str, str]:
    """Return a mapping of all known aliases → side ('a' or 'b') for this match."""
    aliases: dict[str, str] = {}
    for side, code in (("a", code_a), ("b", code_b)):
        # canonical full name
        full = CODE_TO_NAME.get(code, "")
        if full:
            aliases[full.lower()] = side
        # code itself
        aliases[code.lower()] = side
    return aliases


def _find_team_side(text: str, aliases: dict[str, str]) -> str | None:
    """Find which side ('a' or 'b') is mentioned first in text."""
    best_pos = len(text) + 1
    best_side = None
    for alias, side in aliases.items():
        idx = text.lower().find(alias)
        if idx != -1 and idx < best_pos:
            best_pos = idx
            best_side = side
    return best_side


def _find_both_teams(text: str, aliases: dict[str, str]) -> tuple[str | None, str | None]:
    """Return (first_mentioned_side, second_mentioned_side)."""
    positions: list[tuple[int, str]] = []
    for alias, side in aliases.items():
        idx = text.lower().find(alias)
        if idx != -1:
            positions.append((idx, side))
    positions.sort()
    sides = []
    for _, s in positions:
        if s not in sides:
            sides.append(s)
    first  = sides[0] if len(sides) > 0 else None
    second = sides[1] if len(sides) > 1 else None
    return first, second


# ------------------------------------------------------------------ #
# Player name extraction                                               #
# ------------------------------------------------------------------ #

def _extract_player_name(question: str) -> tuple[str, dict | None]:
    """
    Extract a player name from the question and return (raw_name, stats_or_None).
    Looks for a 2–3 word title-cased name after "Will ".
    """
    m = re.search(r'Will ([A-Z][\w\'-]+(?: [A-Z][\w\'-]+){1,2})\b', question)
    if m:
        raw = m.group(1)
        return raw, get_player_stats(raw)
    return "", None


# ------------------------------------------------------------------ #
# Main solver                                                          #
# ------------------------------------------------------------------ #

def solve(question: str, team_a_code: str, team_b_code: str, model: MatchModel) -> int:
    """
    Solve a market question and return an integer probability 1-99.

    team_a_code / team_b_code: e.g. "IRQ", "NOR" (first/second in match name).
    model: MatchModel built from those two teams' stats.
    """
    q = question.strip()
    ql = q.lower()

    aliases = _build_team_aliases(team_a_code, team_b_code)

    # ---------------------------------------------------------------- #
    # 1. Match winner                                                   #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) win the match', ql)
    if m:
        side = _find_team_side(m.group(1), aliases)
        if side:
            return to_int_prob(model.p_win(side))
        return to_int_prob(0.40)

    # ---------------------------------------------------------------- #
    # 2. Total goals >= N                                               #
    # ---------------------------------------------------------------- #
    m = re.search(r'match have (\d+) or more total goals', ql)
    if m:
        n = int(m.group(1))
        return to_int_prob(model.p_total_ge("goals", n))

    # ---------------------------------------------------------------- #
    # 3. BTTS + goals >= N                                              #
    # ---------------------------------------------------------------- #
    m = re.search(r'both teams score and.+?(\d+) or more total goals', ql)
    if m:
        n = int(m.group(1))
        return to_int_prob(model.p_btts_and_goals_ge(n))

    # ---------------------------------------------------------------- #
    # 4. Team scores in first / second half                             #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) score in the (first|second) half', ql)
    if m:
        side = _find_team_side(m.group(1), aliases)
        half = "h1" if m.group(2) == "first" else "h2"
        if side:
            return to_int_prob(model.p_ge("goals", side, 1, half))
        return to_int_prob(0.45)

    # ---------------------------------------------------------------- #
    # 5. Team scores at least 1 goal (full match)                       #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) score at least 1 goal', ql)
    if m:
        side = _find_team_side(m.group(1), aliases)
        if side:
            return to_int_prob(model.p_ge("goals", side, 1))
        return to_int_prob(0.55)

    # ---------------------------------------------------------------- #
    # 6. First goal scorer + other scores in 2H                        #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) score the first goal.+?and (.+?) score in the second half', ql)
    if m:
        first_side  = _find_team_side(m.group(1), aliases)
        other_side  = _find_team_side(m.group(2), aliases)
        if first_side and other_side:
            return to_int_prob(model.p_score_first_and_other_scores_2h(first_side, other_side))
        return to_int_prob(0.20)

    # ---------------------------------------------------------------- #
    # 7. Both teams >= 1 SOT (second half or full match)               #
    # ---------------------------------------------------------------- #
    if re.search(r'both teams have at least 1 shot on target in the second half', ql):
        return to_int_prob(model.p_both_sot_ge1("h2"))

    if re.search(r'at halftime.+?both teams have at least 1 shot on target', ql):
        return to_int_prob(model.p_both_sot_ge1("h1"))

    if re.search(r'both teams have at least 1 shot on target', ql):
        return to_int_prob(model.p_both_sot_ge1("full"))

    # ---------------------------------------------------------------- #
    # 8. Team has N+ SOT (possibly in 2H)                               #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) have (\d+) or more shots on target(?: in the second half)?', ql)
    if m:
        side = _find_team_side(m.group(1), aliases)
        n    = int(m.group(2))
        half = "h2" if "second half" in ql else "full"
        if side:
            return to_int_prob(model.p_ge("sot", side, n, half))
        return to_int_prob(0.50)

    # ---------------------------------------------------------------- #
    # 9. Team A more SOT than Team B in 2H                              #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) have more shots on target than (.+?) in the second half', ql)
    if m:
        first_side, second_side = _find_both_teams(m.group(0), aliases)
        if first_side and second_side:
            p = prob_a_gt_b(model.mu("sot", first_side, "h2"),
                            model.mu("sot", second_side, "h2"))
            return to_int_prob(p)
        return to_int_prob(0.50)

    # ---------------------------------------------------------------- #
    # 10. Total SOT >= N (possibly in 2H)                               #
    # ---------------------------------------------------------------- #
    m = re.search(r'(\d+) or more total shots on target(?: in the second half)?', ql)
    if m:
        n    = int(m.group(1))
        half = "h2" if "second half" in ql else "full"
        return to_int_prob(model.p_total_ge("sot", n, half))

    m = re.search(r'there be (\d+) or more total shots on target', ql)
    if m:
        n = int(m.group(1))
        return to_int_prob(model.p_total_ge("sot", n))

    # ---------------------------------------------------------------- #
    # 11. Fouls: team A > team B                                        #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) commit more fouls than (.+?)[\?$]', ql)
    if m:
        first_side, second_side = _find_both_teams(m.group(0), aliases)
        if first_side and second_side:
            p = prob_a_gt_b(model.mu("fouls", first_side),
                            model.mu("fouls", second_side))
            return to_int_prob(p)
        return to_int_prob(0.50)

    # ---------------------------------------------------------------- #
    # 12. Offsides >= N                                                 #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) be caught offside (\d+) or more times', ql)
    if m:
        side = _find_team_side(m.group(1), aliases)
        n    = int(m.group(2))
        if side:
            return to_int_prob(model.p_ge("offsides", side, n))
        return to_int_prob(0.40)

    # ---------------------------------------------------------------- #
    # 13. Penalty OR red card                                           #
    # ---------------------------------------------------------------- #
    if re.search(r'penalty kick.*?or.*?red card|red card.*?or.*?penalty', ql):
        return to_int_prob(model.prob_pen_or_red)

    # ---------------------------------------------------------------- #
    # 14. Cards: team A > team B                                        #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) receive more cards than (.+?)[\?$]', ql)
    if m:
        first_side, second_side = _find_both_teams(m.group(0), aliases)
        if first_side and second_side:
            p = prob_a_gt_b(model.mu("yellows", first_side),
                            model.mu("yellows", second_side))
            return to_int_prob(p)
        return to_int_prob(0.50)

    # ---------------------------------------------------------------- #
    # 15. Total cards >= N                                              #
    # ---------------------------------------------------------------- #
    m = re.search(r'(\d+) or more total cards', ql)
    if m:
        n = int(m.group(1))
        return to_int_prob(model.p_total_cards_ge(n))

    # ---------------------------------------------------------------- #
    # 16. Second half more goals than first half                        #
    # ---------------------------------------------------------------- #
    if re.search(r'second half have more goals than the first half', ql):
        return to_int_prob(model.p_h2_more_goals_than_h1())

    # ---------------------------------------------------------------- #
    # 17. Corners: team A > team B (HT or 2H)                          #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) have more corner kicks than (.+?)[\?$]', ql)
    if m:
        first_side, second_side = _find_both_teams(m.group(0), aliases)
        half = "h1" if "halftime" in ql else ("h2" if "second half" in ql else "full")
        if first_side and second_side:
            p = prob_a_gt_b(model.mu("corners", first_side, half),
                            model.mu("corners", second_side, half))
            return to_int_prob(p)
        return to_int_prob(0.50)

    # ---------------------------------------------------------------- #
    # 18. Player: >= 1 SOT (possibly in 2H)                            #
    # ---------------------------------------------------------------- #
    if re.search(r'have at least 1 shot on target', ql):
        _, pstats = _extract_player_name(q)
        half = "h2" if "second half" in ql else "full"
        stats = pstats or DEFAULT_PLAYER
        return to_int_prob(model.p_player_sot(stats["sot_per_game"], half))

    # ---------------------------------------------------------------- #
    # 19. Player: score a goal (excluding own goals)                    #
    # ---------------------------------------------------------------- #
    if re.search(r'score a goal|score or assist', ql):
        _, pstats = _extract_player_name(q)
        stats = pstats or DEFAULT_PLAYER
        if "score or assist" in ql:
            return to_int_prob(model.p_player_goal_or_assist(
                stats["goal_per_game"], stats["assist_per_game"]
            ))
        return to_int_prob(model.p_player_goal(stats["goal_per_game"]))

    # ---------------------------------------------------------------- #
    # 20. Total goals <= N ("2 or fewer total goals")                   #
    # ---------------------------------------------------------------- #
    m = re.search(r'match have (\d+) or fewer total goals', ql)
    if m:
        n = int(m.group(1))
        return to_int_prob(model.p_total_le("goals", n))

    # ---------------------------------------------------------------- #
    # 21. 2H total goals >= N                                           #
    # ---------------------------------------------------------------- #
    m = re.search(r'second half have (\d+) or more total goals', ql)
    if m:
        n = int(m.group(1))
        return to_int_prob(model.p_total_ge("goals", n, "h2"))

    # ---------------------------------------------------------------- #
    # 22. 2H more total goals than 1H (with "total" variant)           #
    # ---------------------------------------------------------------- #
    if re.search(r'second half have more total goals than the first half', ql):
        return to_int_prob(model.p_h2_more_goals_than_h1())

    # ---------------------------------------------------------------- #
    # 23. At halftime, will match be tied?                              #
    # ---------------------------------------------------------------- #
    if re.search(r'at halftime.*?match be tied|halftime.*?tied', ql):
        return to_int_prob(model.p_draw(max_g=8))  # reuse draw logic on HT goals

    # ---------------------------------------------------------------- #
    # 24. At halftime, will {TEAM} be winning?                         #
    # ---------------------------------------------------------------- #
    m = re.search(r'at halftime.*?will (.+?) be winning', ql)
    if not m:
        m = re.search(r'will (.+?) be winning at halftime', ql)
    if m:
        side = _find_team_side(m.group(1), aliases)
        if side:
            p = prob_a_gt_b(model.mu("goals", side, "h1"),
                            model.mu("goals", "b" if side == "a" else "a", "h1"))
            return to_int_prob(p)
        return to_int_prob(0.40)

    # ---------------------------------------------------------------- #
    # 25. Team corners >= N                                             #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) have (\d+) or more corner kicks', ql)
    if not m:
        m = re.search(r'will (.+?) finish with (\d+) or more corner kicks', ql)
    if m:
        side = _find_team_side(m.group(1), aliases)
        n    = int(m.group(2))
        if side:
            return to_int_prob(model.p_ge("corners", side, n))
        return to_int_prob(0.50)

    # ---------------------------------------------------------------- #
    # 25b. Team >= N corner kicks in first or second half              #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) have at least (\d+) corner kicks? in the (first|second) half', ql)
    if m:
        side = _find_team_side(m.group(1), aliases)
        n    = int(m.group(2))
        half = "h1" if m.group(3) == "first" else "h2"
        if side:
            return to_int_prob(model.p_ge("corners", side, n, half))
        return to_int_prob(0.50)

    # ---------------------------------------------------------------- #
    # 26. Total corners >= N (full match or second half)                #
    # ---------------------------------------------------------------- #
    m = re.search(r'(\d+) or more total corner kicks in the second half', ql)
    if m:
        n = int(m.group(1))
        return to_int_prob(model.p_total_ge("corners", n, "h2"))

    m = re.search(r'there be (\d+) or more total corner kicks', ql)
    if m:
        n = int(m.group(1))
        return to_int_prob(model.p_total_ge("corners", n))

    # ---------------------------------------------------------------- #
    # 27. Corners: team A > team B ("finish with" / "In the 2H" order) #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) finish with more corner kicks than (.+?)[\?$]', ql)
    if not m:
        m = re.search(r'in the second half.*?will (.+?) have more corner kicks than (.+?)[\?$]', ql)
    if m:
        first_side, second_side = _find_both_teams(m.group(0), aliases)
        half = "h2" if "second half" in ql else "full"
        if first_side and second_side:
            p = prob_a_gt_b(model.mu("corners", first_side, half),
                            model.mu("corners", second_side, half))
            return to_int_prob(p)
        return to_int_prob(0.50)

    # ---------------------------------------------------------------- #
    # 28. SOT comparison 2H with alternative word order                 #
    # ---------------------------------------------------------------- #
    m = re.search(r'in the second half.*?will (.+?) have more shots on target than (.+?)[\?$]', ql)
    if m:
        first_side, second_side = _find_both_teams(m.group(0), aliases)
        if first_side and second_side:
            p = prob_a_gt_b(model.mu("sot", first_side, "h2"),
                            model.mu("sot", second_side, "h2"))
            return to_int_prob(p)
        return to_int_prob(0.50)

    # ---------------------------------------------------------------- #
    # 29. Goals comparison in second half                               #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) score more goals than (.+?) in the second half', ql)
    if m:
        first_side, second_side = _find_both_teams(m.group(0), aliases)
        if first_side and second_side:
            p = prob_a_gt_b(model.mu("goals", first_side, "h2"),
                            model.mu("goals", second_side, "h2"))
            return to_int_prob(p)
        return to_int_prob(0.50)

    # ---------------------------------------------------------------- #
    # 30. Penalty only (no red card mention)                            #
    # ---------------------------------------------------------------- #
    if re.search(r'penalty kick be awarded', ql):
        return to_int_prob(model.prob_penalty)

    # ---------------------------------------------------------------- #
    # 31. Team receives at least 1 card in second half                  #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) receive at least 1 card in the second half', ql)
    if m:
        side = _find_team_side(m.group(1), aliases)
        if side:
            return to_int_prob(model.p_ge("yellows", side, 1, "h2"))
        return to_int_prob(0.50)

    # ---------------------------------------------------------------- #
    # 32. Team goals >= N (e.g. "score 3 or more total goals")          #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) score (\d+) or more (?:total )?goals', ql)
    if m:
        side = _find_team_side(m.group(1), aliases)
        n    = int(m.group(2))
        if side:
            return to_int_prob(model.p_ge("goals", side, n))
        return to_int_prob(0.30)

    # ---------------------------------------------------------------- #
    # 33. First goal of the second half                                 #
    # ---------------------------------------------------------------- #
    m = re.search(r'will (.+?) score the first goal of the second half', ql)
    if m:
        side = _find_team_side(m.group(1), aliases)
        if side:
            mu_a2 = model.mu("goals", "a", "h2")
            mu_b2 = model.mu("goals", "b", "h2")
            total = mu_a2 + mu_b2
            if total < 1e-9:
                return to_int_prob(0.10)
            import math
            p_any = 1 - math.exp(-total)
            mu_side = mu_a2 if side == "a" else mu_b2
            return to_int_prob((mu_side / total) * p_any)
        return to_int_prob(0.30)

    # ---------------------------------------------------------------- #
    # Fallback: return 50 (maximum entropy)                             #
    # ---------------------------------------------------------------- #
    return 50


# ------------------------------------------------------------------ #
# Convenience: build model + solve in one call                         #
# ------------------------------------------------------------------ #

def predict_market(question: str, team_a_code: str, team_b_code: str) -> int:
    """Build a MatchModel from team codes and solve the market question."""
    stats_a = get_stats(team_a_code)
    stats_b = get_stats(team_b_code)
    model = MatchModel(stats_a, stats_b, team_a_code, team_b_code)
    return solve(question, team_a_code, team_b_code, model)
