"""
Generate a team-specific expert tip comparing AI vs bookmaker odds for a match.

Uses Groq (free tier) for fast, low-cost inference. Returns a short HTML string
(plain text with optional <b> tags) explaining the discrepancy in terms of the
actual team stats, Elo gap, and odds gap.

Returns None if GROQ_API_KEY is not set or on any error.
"""

import os

from .team_data import CODE_TO_NAME, DEFAULT_STATS, TEAM_STATS

_MODEL = "llama-3.1-8b-instant"
_MAX_TOKENS = 160


def _stat(stats: dict, key: str, default=None):
    return stats.get(key, DEFAULT_STATS.get(key, default))


def generate_tip(
    code_a: str,
    code_b: str,
    stats_a: dict,
    stats_b: dict,
    ai_a: float,
    ai_b: float,
    pub_a: float | None,
    pub_b: float | None,
) -> str | None:
    """
    Generate a 1-2 sentence expert insight for this matchup.

    Parameters
    ----------
    code_a/b   : team codes
    stats_a/b  : dynamic stat dicts (attack, defense, elo, sot, so_skill, ...)
    ai_a/b     : AI win probabilities (0-100)
    pub_a/b    : bookmaker win probabilities (0-100), or None if unavailable
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        import sys
        print("[tip] GROQ_API_KEY not set — skipping tip generation", file=sys.stderr)
        return None

    try:
        from groq import Groq
    except ImportError:
        return None

    name_a = CODE_TO_NAME.get(code_a, code_a)
    name_b = CODE_TO_NAME.get(code_b, code_b)

    elo_a = round(_stat(stats_a, "elo", 1700))
    elo_b = round(_stat(stats_b, "elo", 1700))
    elo_gap = elo_a - elo_b

    atk_a = round(_stat(stats_a, "attack", 1.3), 2)
    atk_b = round(_stat(stats_b, "attack", 1.3), 2)
    def_a = round(_stat(stats_a, "defense", 1.0), 2)
    def_b = round(_stat(stats_b, "defense", 1.0), 2)
    so_a  = round(_stat(stats_a, "so_skill", 0.5), 2)
    so_b  = round(_stat(stats_b, "so_skill", 0.5), 2)

    market_line = (
        f"Bookmaker line: {name_a} {pub_a:.1f}% / {name_b} {pub_b:.1f}%."
        if pub_a is not None else "No bookmaker line available."
    )
    ai_gap = round(ai_a - (pub_a or ai_a), 1)

    prompt = f"""You are a sharp football analyst writing a one-sentence insight for a World Cup 2026 prediction app.

Match: {name_a} vs {name_b} (knockout round, no draws)

Stats:
- Elo: {name_a} {elo_a} / {name_b} {elo_b} (gap: {elo_gap:+d})
- Attack (goals/game): {name_a} {atk_a} / {name_b} {atk_b}
- Defense (conceded/game, lower=better): {name_a} {def_a} / {name_b} {def_b}
- Penalty shootout skill (0-1): {name_a} {so_a} / {name_b} {so_b}

AI model: {name_a} {ai_a:.1f}% / {name_b} {ai_b:.1f}%
{market_line}
AI vs market gap on {name_a}: {ai_gap:+.1f}pp

Write exactly 1-2 sentences (max 45 words) explaining what drives the AI's view and why it differs from (or agrees with) the market. Be specific about which stats matter most for this matchup. Use plain text with optional <b>team name</b> tags. No em-dashes."""

    try:
        client = Groq(api_key=api_key)
        msg = client.chat.completions.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.choices[0].message.content.strip()
    except Exception as e:
        import sys
        print(f"[tip] Groq error for {code_a} vs {code_b}: {e}", file=sys.stderr)
        return None
