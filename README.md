# ⚡ Probability Cup

A **"who will win" World Cup prediction pool** where people pick match winners and a
statistical AI posts the odds — then everyone (humans *and* the model) is scored on the
same proper scoring rule. The hook: **can you beat the machine, and the bookmakers?**

Live: **https://probability-cup.onrender.com**

---

## What it does

Probability Cup has two parts that share one statistical engine:

1. **The pool** (`app/`) — a web app where you pick winners of upcoming World Cup fixtures
   (with a confidence slider), the AI posts win probabilities next to the **real bookmaker
   line**, and a leaderboard scores humans against the model as results come in.
2. **The prediction bot** (`src/main.py`) — a headless agent that prices every open market
   on the [SportsPredict](https://sportspredict.com) tournament platform and submits its
   probabilities automatically (runs on a schedule via GitHub Actions).

Both are powered by the same model in `src/`.

---

## The model

- **Goals:** a **Dixon–Coles Poisson** model. Each team has an attack and defense rating
  (goals scored / conceded per game, recent international form); expected goals for a match
  come from combining the two sides' ratings against the tournament average.
- **Other markets:** shots on target, fouls, offsides, corners and cards use independent
  Poisson distributions from team-level averages.
- **Live-aware:** `MatchModel.apply_live(score, minute)` rescales the remaining expected
  goals for the time left, so in-play odds condition on the current score and clock.
- **Self-calibrating:** `bayesian_updater.py` nudges the priors from completed World Cup
  results as the tournament unfolds.
- **48 national teams** are rated in `src/team_data.py` — attack, defense, shots, fouls,
  offsides, corners, cards, **Elo**, and **penalty-shootout skill** (`so_skill`).

### Knockout rounds

During the knockouts there are no draws — every tie has a winner. The pool runs in
**knockout mode**: each market is two-way (`team A` / `team B`), and the draw probability is
resolved with a proper **extra time + penalties** model:

```
P(A wins the tie) = P(win in 90')
                  + P(draw) × [ extra-time share × (regulation strength)
                              + penalty share    × (shootout skill) ]
```

Shootout skill (`so_skill`) comes from historical shootout records, shrunk toward average
with `(1.5 + W) / (3 + W + L)`, so Germany and Croatia get a real edge in a tight tie while
England and the Netherlands are dragged down. Set `PC_KNOCKOUT=0` for the three-way
group-stage market.

---

## Beat the AI (and the bookmakers)

- **Pick with confidence.** Choose a winner and set how sure you are with a slider.
- **Proper scoring rule.** Every pick is graded by a quadratic score,
  `(p_winner² − p_loser²) × 50`, ranging from **−50** (all-in on the loser) to **+50**
  (all-in on the winner). A correct pick earns points, a wrong one loses them, and slamming
  confidence to the max is penalised when you're wrong — so honest, calibrated picks win.
  The AI is scored the same way on its probability vector.
- **AI vs. the public line.** Each match shows the model's odds beside the **real bookmaker
  line** (averaged across sportsbooks via [The Odds API](https://the-odds-api.com)), so you
  can see where the AI disagrees with the market.
- **Expert tips.** A fast LLM ([Groq](https://groq.com), free tier) writes a short,
  team-specific note explaining each AI-vs-bookmaker discrepancy in terms of the actual
  stats and Elo gap.
- **Real results, automatic settlement.** The leaderboard settles from actual outcomes
  pulled from the public **ESPN scoreboard** (`src/live_scores.py`) — including extra-time
  and penalty winners — and shows a per-match score breakdown.
- **Live panel + pick locking.** The match actually in play is shown with the model's odds
  updating in real time; picks lock at kickoff, with a countdown badge beforehand.
- A **"Simulate (demo)"** button replays a fictional match for demos when nothing is live.
  It's clearly labelled and **never affects the leaderboard**.

---

## Running locally

```bash
pip install -r requirements.txt
uvicorn app.server:app --reload      # → http://127.0.0.1:8000
```

- `/` — marketing landing page
- `/play` — the interactive pool

The prediction bot (optional; needs a valid API key):

```bash
python -m src.main --dry-run         # print predictions without submitting
```

### Configuration (environment variables)

| Variable | Default | Meaning |
|----------|---------|---------|
| `SPORTSPREDICT_API_KEY` | *(bundled fallback)* | Tournament API key for real fixtures |
| `ODDS_API_KEY` | *(unset)* | The Odds API key for real bookmaker lines (optional) |
| `GROQ_API_KEY` | *(unset)* | Groq key for LLM expert tips (optional) |
| `PC_USE_LIVE` | `1` | `0` forces the curated demo fixture slate |
| `PC_KNOCKOUT` | `1` | `0` switches markets back to three-way (group stage) |

Public lines and expert tips degrade gracefully — if a key isn't set, the app just omits
that feature.

---

## Project layout

```
src/                     the statistical engine (no web framework)
  models.py              Dixon–Coles + Poisson match model
  team_data.py           per-team ratings for 48 nations
  market_solver.py       natural-language market → probability
  bayesian_updater.py    recalibrate priors from completed results
  live_scores.py         real live scores + winners from ESPN
  odds_api.py            real bookmaker lines from The Odds API
  tip.py                 LLM expert tips (Groq) comparing AI vs the line
  api_client.py          SportsPredict tournament API client
  main.py                the prediction bot

app/                     the web pool (FastAPI)
  server.py              API routes
  pool.py                fixtures, AI odds, knockout tie-break, real settlement, scoring
  live.py                demo match simulator
  static/landing.html    landing page   (served at /)
  static/index.html      the pool app    (served at /play)
```

### Key API routes

| Route | Purpose |
|-------|---------|
| `GET /api/matches` | Upcoming fixtures with AI odds, bookmaker line, and tips |
| `POST /api/pick` | Record a user's pick (with confidence) |
| `GET /api/leaderboard` | Humans-vs-AI standings (settles real results first) |
| `GET /api/live` | The real match currently in play, with live odds |
| `POST /api/sim/start` · `GET /api/sim` | Demo simulator (not scored) |

---

## Deployment

Configured for **Render** (`render.yaml`, free web service). Pushing to `main`
auto-deploys; set `ODDS_API_KEY` and `GROQ_API_KEY` in the Render dashboard to enable public
lines and tips. A `Procfile` is included so Railway/Fly work too. Picks/results persist to
`app/data/pool.json` (ephemeral on Render's free tier — fine for a demo).

---

## Tech

Python · FastAPI · SciPy/NumPy (Poisson math) · Groq (LLM tips) · vanilla HTML/CSS/JS front
end · ESPN, The Odds API & SportsPredict data. No database, no build step.
