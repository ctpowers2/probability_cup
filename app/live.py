"""
Live-match simulator for the demo.

Drives one match's clock in real time and recomputes the AI's win odds every
tick via the engine's own MatchModel.apply_live.

- Regulation (0-90'): goal timings sampled from Poisson(mu_a/mu_b)
- Extra time (91-120'): if level at 90', one additional ET goal sampled per side
  (lower mu since ET goals are rarer); if still level after 120', goes to penalties
- Penalties: Bradley-Terry shootout using each team's so_skill

The simulator is demo-only and never settles the real leaderboard.
"""

import threading
import time

import numpy as np

from src.models import MatchModel
from . import pool

_LOCK = threading.Lock()

# ET goals are ~40% as frequent per minute as regulation goals
_ET_GOAL_SCALE = 0.40
# Penalty rounds: first to N wins after minimum 5 kicks each side
_PEN_ROUNDS = 5


def _sample_goals(mu_a: float, mu_b: float, start: int = 1, end: int = 90) -> list[tuple[int, str]]:
    """Sample goals from Poisson(mu) and assign random minutes in [start, end]."""
    span = end - start + 1
    events: list[tuple[int, str]] = []
    for side, mu in (("a", mu_a), ("b", mu_b)):
        n = int(np.random.poisson(mu))
        for _ in range(n):
            events.append((int(np.random.randint(start, end + 1)), side))
    events.sort(key=lambda e: e[0])
    return events


def _sample_shootout(skill_a: float, skill_b: float) -> tuple[str, list[dict]]:
    """
    Simulate a full penalty shootout.
    Returns (winner 'a'|'b', list of kick events with {taker, scored, cumulative}).
    """
    kicks: list[dict] = []
    scores = {"a": 0, "b": 0}
    taken = {"a": 0, "b": 0}

    def shoot(side: str) -> bool:
        skill = skill_a if side == "a" else skill_b
        scored = np.random.random() < skill
        taken[side] += 1
        scores[side] += int(scored)
        kicks.append({"side": side, "taken": taken[side], "scored": scored,
                      "score_a": scores["a"], "score_b": scores["b"]})
        return scored

    # Standard 5 rounds alternating a/b
    order = ["a", "b"] * _PEN_ROUNDS
    for i, side in enumerate(order):
        shoot(side)
        ta, tb = taken["a"], taken["b"]
        sa, sb = scores["a"], scores["b"]
        # Early win: a can't be caught
        remaining_a = _PEN_ROUNDS - ta
        remaining_b = _PEN_ROUNDS - tb
        if sa > sb + remaining_b:
            return "a", kicks
        if sb > sa + remaining_a:
            return "b", kicks

    # Sudden death if still level
    while scores["a"] == scores["b"]:
        shoot("a")
        shoot("b")
        # Check after each pair: if a scored and b didn't, a wins
        if kicks[-2]["scored"] and not kicks[-1]["scored"]:
            return "a", kicks
        if kicks[-1]["scored"] and not kicks[-2]["scored"]:
            return "b", kicks

    winner = "a" if scores["a"] > scores["b"] else "b"
    return winner, kicks


class LiveSim:
    """In-memory singleton holding at most one live match."""

    def __init__(self):
        self._reset()

    def _reset(self):
        self.match_id: str | None = None
        self.start_ts: float = 0.0
        self.speed: float = 1.5
        self.reg_goals: list[tuple[int, str]] = []
        self.et_goals: list[tuple[int, str]] = []
        self.pen_winner: str | None = None
        self.pen_kicks: list[dict] = []
        self.settled: bool = False
        self._stats_a: dict = {}
        self._stats_b: dict = {}

    def start(self, match_id: str, speed: float = 1.5) -> None:
        m = pool.get_match(match_id)
        if not m:
            raise ValueError(f"Unknown match: {match_id!r}")

        # Read directly from the shared stats cache so we use the exact same
        # values that produced the card's AI odds — no race with background threads.
        cached = pool._stats_cache.get("stats") or {}
        from src.team_data import get_stats as _static
        stats_a = cached.get(m["team_a"]) or _static(m["team_a"])
        stats_b = cached.get(m["team_b"]) or _static(m["team_b"])
        model = MatchModel(stats_a, stats_b, m["team_a"], m["team_b"])

        reg_goals = _sample_goals(model.mu_goals_a, model.mu_goals_b, 1, 90)
        sa_reg = sum(1 for _, s in reg_goals if s == "a")
        sb_reg = sum(1 for _, s in reg_goals if s == "b")

        et_goals: list[tuple[int, str]] = []
        pen_winner: str | None = None
        pen_kicks: list[dict] = []

        if pool.KNOCKOUT and sa_reg == sb_reg:
            # Extra time: lower-rate goals in 91-120'
            et_mu_a = model.mu_goals_a * _ET_GOAL_SCALE * (30 / 90)
            et_mu_b = model.mu_goals_b * _ET_GOAL_SCALE * (30 / 90)
            et_goals = _sample_goals(et_mu_a, et_mu_b, 91, 120)
            sa_et = sa_reg + sum(1 for _, s in et_goals if s == "a")
            sb_et = sb_reg + sum(1 for _, s in et_goals if s == "b")

            if sa_et == sb_et:
                skill_a = stats_a.get("so_skill", 0.5)
                skill_b = stats_b.get("so_skill", 0.5)
                pen_winner, pen_kicks = _sample_shootout(skill_a, skill_b)

        with _LOCK:
            self._reset()
            self.match_id = match_id
            self.start_ts = time.time()
            self.speed = max(0.2, speed)
            self.reg_goals = reg_goals
            self.et_goals = et_goals
            self.pen_winner = pen_winner
            self.pen_kicks = pen_kicks
            self._stats_a = stats_a
            self._stats_b = stats_b

    def stop(self) -> None:
        with _LOCK:
            self._reset()

    def _clock(self) -> tuple[int, int, int, str]:
        """Return (minute, score_a, score_b, phase) where phase is 'reg'|'et'|'pen'."""
        elapsed_min = (time.time() - self.start_ts) * self.speed

        if elapsed_min <= 90:
            minute = min(90, int(elapsed_min))
            sa = sum(1 for mm, s in self.reg_goals if mm <= minute and s == "a")
            sb = sum(1 for mm, s in self.reg_goals if mm <= minute and s == "b")
            return minute, sa, sb, "reg"

        # Extra time phase (only reached if level at 90')
        if self.et_goals is not None and len(self.et_goals) >= 0 and (
                self.pen_winner is not None or self.et_goals):
            et_elapsed = elapsed_min - 90
            if et_elapsed <= 30:
                minute = 90 + min(30, int(et_elapsed))
                sa = sum(1 for mm, s in self.reg_goals if s == "a")
                sb = sum(1 for mm, s in self.reg_goals if s == "b")
                sa += sum(1 for mm, s in self.et_goals if mm <= minute and s == "a")
                sb += sum(1 for mm, s in self.et_goals if mm <= minute and s == "b")
                return minute, sa, sb, "et"

            # Penalties phase
            sa = sum(1 for _, s in self.reg_goals if s == "a") + \
                 sum(1 for _, s in self.et_goals if s == "a")
            sb = sum(1 for _, s in self.reg_goals if s == "b") + \
                 sum(1 for _, s in self.et_goals if s == "b")
            return 120, sa, sb, "pen"

        # Regulation-only path (no ET needed)
        sa = sum(1 for _, s in self.reg_goals if s == "a")
        sb = sum(1 for _, s in self.reg_goals if s == "b")
        return 90, sa, sb, "reg"

    def state(self) -> dict:
        if not self.match_id:
            return {"active": False}

        m = pool.get_match(self.match_id)
        minute, sa, sb, phase = self._clock()

        model = MatchModel(self._stats_a, self._stats_b, m["team_a"], m["team_b"])

        if phase == "pen":
            # Shootout in progress or complete — odds are the pen winner probability
            pen_elapsed = (time.time() - self.start_ts) * self.speed - 120
            n_kicks_shown = min(len(self.pen_kicks), max(0, int(pen_elapsed * 2)))
            kicks_so_far = self.pen_kicks[:n_kicks_shown]
            pen_done = n_kicks_shown >= len(self.pen_kicks)

            if pen_done and self.pen_winner:
                odds = {"a": 1.0 if self.pen_winner == "a" else 0.0,
                        "b": 0.0 if self.pen_winner == "a" else 1.0}
                finished = True
            else:
                # During shootout show running advantage based on kicks so far
                sa_pen = sum(1 for k in kicks_so_far if k["side"] == "a" and k["scored"])
                sb_pen = sum(1 for k in kicks_so_far if k["side"] == "b" and k["scored"])
                # Rough prob: give slight edge to whoever is ahead in penalties
                raw = 0.5 + (sa_pen - sb_pen) * 0.08
                raw = max(0.05, min(0.95, raw))
                odds = {"a": raw, "b": 1 - raw}
                finished = False

            goals_all = [{"minute": mm, "side": s,
                          "team": m["name_a"] if s == "a" else m["name_b"]}
                         for mm, s in self.reg_goals + self.et_goals]

            pen_summary = ""
            if kicks_so_far:
                sa_p = sum(1 for k in kicks_so_far if k["side"] == "a" and k["scored"])
                sb_p = sum(1 for k in kicks_so_far if k["side"] == "b" and k["scored"])
                pen_summary = f"{sa_p}–{sb_p} on penalties"

            return {
                "active": True, "mode": "sim", "match_id": self.match_id,
                "name_a": m["name_a"], "name_b": m["name_b"],
                "minute": 120, "score_a": sa, "score_b": sb,
                "phase": "pen", "pen_summary": pen_summary,
                "finished": finished,
                "ai": {k: round(v * 100, 1) for k, v in odds.items()},
                "goals": goals_all,
            }

        # Regulation or ET: use live model
        model.apply_live(sa, sb, minute)
        p_a, p_b, p_d = model.p_win("a"), model.p_win("b"), model.p_draw()
        total = p_a + p_b + p_d or 1.0
        if pool.KNOCKOUT:
            qa = pool.knockout_win_prob(p_a, p_b, p_d, m["team_a"], m["team_b"])
            odds = {"a": qa / total, "b": (total - qa) / total}
        else:
            odds = {"a": p_a / total, "draw": p_d / total, "b": p_b / total}

        finished = (phase == "reg" and minute >= 90 and not self.et_goals and self.pen_winner is None) or \
                   (phase == "et" and minute >= 120 and self.pen_winner is None and
                    sum(1 for _, s in self.et_goals if s == "a") !=
                    sum(1 for _, s in self.et_goals if s == "b"))

        goals_shown = self.reg_goals if phase == "reg" else self.reg_goals + [
            g for g in self.et_goals if g[0] <= minute]
        recent = [{"minute": mm, "side": s,
                   "team": m["name_a"] if s == "a" else m["name_b"]}
                  for mm, s in goals_shown if mm <= minute]

        return {
            "active": True, "mode": "sim", "match_id": self.match_id,
            "name_a": m["name_a"], "name_b": m["name_b"],
            "minute": minute, "score_a": sa, "score_b": sb,
            "phase": phase,
            "finished": finished,
            "ai": {k: round(v * 100, 1) for k, v in odds.items()},
            "goals": recent,
        }


SIM = LiveSim()
