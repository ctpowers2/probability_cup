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
from datetime import datetime, timezone

from .api_client import SportsPredictClient, EVENT_ID
from .team_data import name_to_code, get_stats
from .models import MatchModel
from .market_solver import solve

API_KEY = "sp_live_d8b6fec43ffe8ae49b0c3af62076eb3a04365ff78736ee3463aa4ee6bf027321"


def parse_match_name(name: str) -> tuple[str, str]:
    """
    Convert 'IRQ vs NOR' → ('IRQ', 'NOR').
    Handles both 3-letter codes and full names.
    """
    parts = [p.strip() for p in name.split(" vs ")]
    if len(parts) != 2:
        raise ValueError(f"Unexpected match name format: {name!r}")

    def resolve(part: str) -> str:
        # Try direct code lookup first
        from .team_data import TEAM_STATS
        if part in TEAM_STATS:
            return part
        code = name_to_code(part)
        if code:
            return code
        # Return as-is (unknown team — will use DEFAULT_STATS)
        return part

    return resolve(parts[0]), resolve(parts[1])


def process_match(client: SportsPredictClient, match: dict, dry_run: bool) -> int:
    """Predict and optionally submit all open markets for a match. Returns # submitted."""
    match_id   = match["id"]
    match_name = match["name"]

    try:
        team_a, team_b = parse_match_name(match_name)
    except ValueError as e:
        print(f"  [SKIP] {e}")
        return 0

    stats_a = get_stats(team_a)
    stats_b = get_stats(team_b)
    model   = MatchModel(stats_a, stats_b, team_a, team_b)

    markets = client.list_markets(match_id)
    if not markets:
        print(f"  No open markets for {match_name}")
        return 0

    predictions: list[dict] = []
    for mkt in markets:
        mkt_id   = mkt["id"]
        question = mkt["question"]
        prob     = solve(question, team_a, team_b, model)
        predictions.append({"market_id": mkt_id, "probability": prob})
        print(f"    {prob:3d}%  {question}")

    if dry_run:
        print(f"  [DRY RUN] Would submit {len(predictions)} predictions for {match_name}")
        return 0

    try:
        result = client.submit_predictions_batch(predictions)
        if isinstance(result, list):
            fail_msgs = [r.get("message") or r.get("error") for r in result
                         if isinstance(r, dict) and
                         not (r.get("success") or r.get("type") == "prediction")]
            if fail_msgs:
                print(f"  [WARN] {len(fail_msgs)} failures: {set(fail_msgs)}")
        print(f"  [OK] Submitted {len(predictions)} predictions for {match_name}")
        return len(predictions)
    except Exception as e:
        print(f"  [ERROR] Batch submit failed: {e}")
        # Fallback: submit one by one
        submitted = 0
        for p in predictions:
            try:
                client.submit_prediction(p["market_id"], p["probability"])
                submitted += 1
            except Exception as e2:
                print(f"    [SKIP] {p['market_id']}: {e2}")
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

    print(f"[{now.strftime('%Y-%m-%d %H:%M UTC')}] Fetching matches for event {EVENT_ID}…")
    matches = client.list_matches(EVENT_ID)
    print(f"Found {len(matches)} total matches with open markets")

    if args.match_id:
        matches = [m for m in matches if m["id"] == args.match_id]
        if not matches:
            print(f"Match ID {args.match_id!r} not found or has no open markets.")
            sys.exit(1)

    total_submitted = 0
    for match in matches:
        opening = datetime.fromisoformat(match["opening_time"].replace("Z", "+00:00"))
        print(f"\n{'='*60}")
        print(f"  {match['name']}  (opens {opening.strftime('%b %d %H:%M UTC')}, "
              f"{match['open_market_count']} markets)")

        submitted = process_match(client, match, args.dry_run)
        total_submitted += submitted

    print(f"\n{'='*60}")
    if args.dry_run:
        print("DRY RUN complete — no predictions submitted.")
    else:
        print(f"Done. Submitted {total_submitted} predictions across {len(matches)} matches.")


if __name__ == "__main__":
    main()
