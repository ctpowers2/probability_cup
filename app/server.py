"""
FastAPI backend for the "Beat the AI" World Cup pool.

Run:
    uvicorn app.server:app --reload
Then open http://127.0.0.1:8000
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import pool
from .live import SIM

app = FastAPI(title="Probability Cup — Beat the AI")

STATIC_DIR = Path(__file__).parent / "static"


class PickIn(BaseModel):
    user: str
    match_id: str
    pick: str  # "a" | "draw" | "b"
    conf: float | None = None  # optional confidence in [0.51, 0.99]


class ResultIn(BaseModel):
    match_id: str
    outcome: str  # "a" | "draw" | "b"


class LiveStartIn(BaseModel):
    match_id: str
    speed: float = 1.5  # match-minutes per real second


@app.get("/api/matches")
def api_matches():
    return {"matches": pool.build_matches(), "live": pool.is_live_slate(),
            "knockout": pool.KNOCKOUT}


@app.get("/api/picks/{user}")
def api_user_picks(user: str):
    return {"picks": pool.all_picks().get(user, {}), "results": pool.results_map()}


@app.post("/api/pick")
def api_pick(body: PickIn):
    try:
        pool.record_pick(body.user, body.match_id, body.pick, body.conf)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@app.get("/api/leaderboard")
def api_leaderboard():
    return pool.leaderboard()


@app.post("/api/result")
def api_result(body: ResultIn):
    """Demo control: settle a match so the leaderboard scores it."""
    try:
        pool.set_result(body.match_id, body.outcome)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@app.post("/api/results/clear")
def api_clear_results():
    pool.clear_results()
    return {"ok": True}


@app.get("/api/live")
def api_live_state():
    """The real match currently in play (from the live scoreboard), if any."""
    return pool.live_match_state()


@app.post("/api/sim/start")
def api_sim_start(body: LiveStartIn):
    """Kick off a DEMO simulation of a match. Does not affect the leaderboard."""
    try:
        SIM.start(body.match_id, body.speed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@app.post("/api/sim/stop")
def api_sim_stop():
    SIM.stop()
    return {"ok": True}


@app.get("/api/sim")
def api_sim_state():
    return SIM.state()


@app.get("/")
def landing():
    """Marketing landing page — the front door."""
    return FileResponse(STATIC_DIR / "landing.html")


@app.get("/play")
def play():
    """The interactive prediction pool."""
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")
