"""
Live-match simulator for the demo finale.

Drives one match's clock in real time and recomputes the AI's win odds every
tick via the engine's own `MatchModel.apply_live`. Goal timings are sampled once
at kickoff from the model's expected goals (Poisson), so every run is different
but realistic. When the clock hits 90', the final result is auto-settled into
the pool so the leaderboard scores everyone — the model and the humans — live.

No external feed required: this is self-contained and demo-reliable.
"""

import threading
import time

import numpy as np

from src.team_data import get_stats
from src.models import MatchModel

from . import pool

_LOCK = threading.Lock()


def _sample_goals(mu_a: float, mu_b: float) -> list[tuple[int, str]]:
    """Sample goal count per side (Poisson) and assign each a random minute."""
    events: list[tuple[int, str]] = []
    for side, mu in (("a", mu_a), ("b", mu_b)):
        n = int(np.random.poisson(mu))
        for _ in range(n):
            events.append((int(np.random.randint(1, 91)), side))
    events.sort(key=lambda e: e[0])
    return events


class LiveSim:
    """In-memory singleton holding at most one live match."""

    def __init__(self):
        self.match_id: str | None = None
        self.start_ts: float = 0.0
        self.speed: float = 1.5        # match-minutes per real second (~60s match)
        self.goals: list[tuple[int, str]] = []
        self.settled: bool = False

    def start(self, match_id: str, speed: float = 1.5) -> None:
        m = pool.get_match(match_id)
        if not m:
            raise ValueError(f"Unknown match: {match_id!r}")
        model = MatchModel(get_stats(m["team_a"]), get_stats(m["team_b"]),
                           m["team_a"], m["team_b"])
        with _LOCK:
            self.match_id = match_id
            self.start_ts = time.time()
            self.speed = max(0.2, speed)
            self.goals = _sample_goals(model.mu_goals_a, model.mu_goals_b)
            self.settled = False

    def stop(self) -> None:
        with _LOCK:
            self.match_id = None
            self.goals = []
            self.settled = False

    def _clock(self) -> tuple[int, int, int]:
        """Current (minute, score_a, score_b) from real elapsed time."""
        minute = min(90, int((time.time() - self.start_ts) * self.speed))
        sa = sum(1 for mm, s in self.goals if mm <= minute and s == "a")
        sb = sum(1 for mm, s in self.goals if mm <= minute and s == "b")
        return minute, sa, sb

    def state(self) -> dict:
        if not self.match_id:
            return {"active": False}

        m = pool.get_match(self.match_id)
        minute, sa, sb = self._clock()

        model = MatchModel(get_stats(m["team_a"]), get_stats(m["team_b"]),
                           m["team_a"], m["team_b"])
        model.apply_live(sa, sb, minute)
        p_a, p_b, p_d = model.p_win("a"), model.p_win("b"), model.p_draw()
        total = p_a + p_b + p_d or 1.0
        odds = {"a": p_a / total, "draw": p_d / total, "b": p_b / total}

        finished = minute >= 90
        # Auto-settle the final result into the pool exactly once.
        if finished and not self.settled:
            outcome = "a" if sa > sb else "b" if sb > sa else "draw"
            pool.set_result(self.match_id, outcome)
            with _LOCK:
                self.settled = True

        # Recent goals for a live event ticker.
        recent = [{"minute": mm, "side": s,
                   "team": m["name_a"] if s == "a" else m["name_b"]}
                  for mm, s in self.goals if mm <= minute]

        return {
            "active": True,
            "match_id": self.match_id,
            "name_a": m["name_a"], "name_b": m["name_b"],
            "minute": minute, "score_a": sa, "score_b": sb,
            "finished": finished,
            "ai": {k: round(v * 100, 1) for k, v in odds.items()},
            "goals": recent,
        }


SIM = LiveSim()
