"""
Main runner for the World Cup probability prediction bot.

Usage:
    python -m src.main [--dry-run] [--match-id MATCH_ID]

Flags:
    --dry-run       Print predictions without submitting to the API.
    --match-id      Only process a single match (useful for debugging).
"""

import argparse
import sys
import time
from datetime import datetime, timezone

from .api_client import SportsPredictClient, EVENT_ID
from .team_data import name_to_code, get_stats
from .models import MatchModel
from .market_solver import solve
from .live_scores import get_live_states
from .bayesian_updater import get_dynamic_stats

API_KEY = "sp_live_d8b6fec43ffe8ae49b0c3af62076eb3a04365ff78736ee3463aa4ee6bf027321"


def parse_match_name(name: str) -> tuple[str, str]:
    """Convert 'IRQ vs NOR' → ('IRQ', 'NOR')."""
    parts = [p.strip() for p in name.split(" vs ")]
    if len(parts) != 2:
        raise ValueError(f"Unexpected match name format: {name!r}")

    def resolve(part: str) -> str:
        from .team_data import TEAM_STATS
        if part in TEAM_STATS:
            return part
        code = name_to_code(part)
        return code if code else part

    return resolve(parts[0]), resolve(parts[1])


def process_match(client: SportsPredictClient, match: dict, dry_run: bool,
                  live_states: dict, dynamic_stats: dict,
                  existing: dict[str, dict]) -> int:
    """
    Predict and submit/update all open markets for a match.

    existing: {market_id: {"id": prediction_id, "probability": int}}
    Returns number of predictions created or updated.
    """
    match_id   = match["id"]
    match_name = match["name"]

    try:
        team_a, team_b = parse_match_name(match_name)
    except ValueError as e:
        print(f"  [SKIP] {e}")
        return 0

    stats_a = dynamic_stats.get(team_a) or get_stats(team_a)
    stats_b = dynamic_stats.get(team_b) or get_stats(team_b)
    model   = MatchModel(stats_a, stats_b, team_a, team_b)

    # Apply live score if match is currently in play
    live_key = frozenset([team_a, team_b])
    state = live_states.get(live_key)
    if state and state["in_play"]:
        score_a = state["scores"].get(team_a, 0)
        score_b = state["scores"].get(team_b, 0)
        minute  = state["minute"]
        model.apply_live(score_a, score_b, minute)
        print(f"  [LIVE] {team_a} {score_a}-{score_b} {team_b}  ({minute}')")

    markets = client.list_markets(match_id)
    if not markets:
        print(f"  No open markets for {match_name}")
        return 0

    to_submit: list[dict] = []
    to_update: list[dict] = []

    for mkt in markets:
        mkt_id   = mkt["id"]
        question = mkt["question"]
        new_prob = solve(question, team_a, team_b, model)
        print(f"    {new_prob:3d}%  {question}")

        if mkt_id in existing:
            to_update.append({"pred_id": existing[mkt_id]["id"], "probability": new_prob})
        else:
            to_submit.append({"market_id": mkt_id, "probability": new_prob})

    if dry_run:
        print(f"  [DRY RUN] {len(to_submit)} new, {len(to_update)} updates for {match_name}")
        return 0

    submitted = 0

    # Batch-submit new predictions
    if to_submit:
        try:
            client.submit_predictions_batch(to_submit)
            submitted += len(to_submit)
        except Exception as e:
            print(f"  [ERROR] Batch submit failed: {e}")
            for p in to_submit:
                try:
                    client.submit_prediction(p["market_id"], p["probability"])
                    submitted += 1
                except Exception as e2:
                    print(f"    [SKIP] {p['market_id']}: {e2}")

    # Update changed predictions individually (small delay to avoid rate limiting)
    for p in to_update:
        try:
            client.update_prediction(p["pred_id"], p["probability"])
            submitted += 1
            time.sleep(0.2)
        except Exception as e:
            print(f"    [SKIP UPDATE] {p['pred_id']}: {e}")

    label = f"{len(to_submit)} new, {len(to_update)} updated"
    print(f"  [OK] {label} for {match_name}")
    return submitted


def main():
    parser = argparse.ArgumentParser(description="World Cup probability prediction bot")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print predictions without submitting")
    parser.add_argument("--match-id", default=None,
                        help="Only process this specific match ID")
    args = parser.parse_args()

    client = SportsPredictClient(API_KEY)
    now    = datetime.now(timezone.utc)

    print(f"[{now.strftime('%Y-%m-%d %H:%M UTC')}] Fetching matches, live scores, and completed results…")
    matches        = client.list_matches(EVENT_ID)
    live_states    = get_live_states()
    dynamic_stats, n_results = get_dynamic_stats()

    # Build market_id → {id, probability} from all existing predictions
    all_preds = client.list_predictions() or []
    existing: dict[str, dict] = {
        p["market_id"]: {"id": p["id"], "probability": p["probability"]}
        for p in all_preds
    }

    if live_states:
        print(f"Live matches detected: {len(live_states)}")
    print(f"Bayesian model updated from {n_results} completed WC matches")
    print(f"Found {len(matches)} matches | {len(existing)} existing open predictions")

    if args.match_id:
        matches = [m for m in matches if m["id"] == args.match_id]
        if not matches:
            print(f"Match ID {args.match_id!r} not found or has no open markets.")
            sys.exit(1)

    total = 0
    for match in matches:
        opening = datetime.fromisoformat(match["opening_time"].replace("Z", "+00:00"))
        print(f"\n{'='*60}")
        print(f"  {match['name']}  (opens {opening.strftime('%b %d %H:%M UTC')}, "
              f"{match['open_market_count']} markets)")

        try:
            total += process_match(client, match, args.dry_run,
                                   live_states, dynamic_stats, existing)
        except Exception as e:
            print(f"  [ERROR] {match['name']}: {e}")

    print(f"\n{'='*60}")
    if args.dry_run:
        print("DRY RUN complete — no predictions submitted.")
    else:
        print(f"Done. {total} predictions created/updated across {len(matches)} matches.")


if __name__ == "__main__":
    main()
