#!/usr/bin/env python3
"""Calculate manually selected 7R+ plans with the saved supplementary odds."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from analyze import build_report, portfolio, timestamp, validate


PLANS = {
    "one_ticket": {(11, (9, 14))},
    "three_tickets": {(10, (2, 4)), (11, (9, 14)), (12, (1, 14))},
    "four_tickets": {(10, (2, 4)), (11, (9, 14)), (12, (1, 14)), (12, (6, 14))},
}


def calculate(as_of):
    base = build_report(Path("data/2026-10-12"), as_of, 100, 15)
    checkpoint_path = Path("reports/2026-10-12/odds-checkpoint.json")
    raw = checkpoint_path.read_bytes()
    checkpoint = json.loads(raw)
    checked_at = timestamp(checkpoint["checked_at_jst"])
    if checked_at > as_of:
        raise ValueError("future_checkpoint")
    if timestamp(checkpoint["updated_at_jst"]) > checked_at:
        raise ValueError("checkpoint_updated_after_observation")
    races = deepcopy(base["races"])
    for update in checkpoint["tickets"]:
        race = next(r for r in races if r["race"] == update["race"])
        ticket = next(t for t in race["tickets"]
                      if sorted(t["horses"]) == sorted(update["horses"]))
        if timestamp(checkpoint["updated_at_jst"]) < timestamp(ticket["updated_at_jst"]):
            raise ValueError("checkpoint_quote_regression")
        ticket.update({key: update[key] for key in ("odds_low", "odds_high")})
        ticket.update(updated_at_jst=checkpoint["updated_at_jst"],
                      source_url=checkpoint["source_url"])
        race["odds_observed_at_jst"] = max(
            timestamp(race["odds_observed_at_jst"]), checked_at).isoformat()
        validate(race, as_of)
    plans = {}
    for name, pairs in PLANS.items():
        selected = deepcopy(races)
        for race in selected:
            race["tickets"] = [t for t in race["tickets"]
                if (race["race"], tuple(sorted(t["horses"]))) in pairs]
        plans[name] = portfolio(selected, as_of, 100)
    return {"analysis_at_jst": as_of.isoformat(),
            "selection_method": "manual_qualitative_selection_not_model_probability",
            "source_manifest": base["source_manifest"] + [
                {"file": str(checkpoint_path), "sha256": hashlib.sha256(raw).hexdigest()}],
            "plans": plans,
            "limits": ["中間オッズ下限を固定した条件付き収支。最終払戻を保証しない。",
                       "実績率や1/オッズを今日の的中確率と解釈しない。",
                       "発走2分前以降は新規候補から除外。実購入なし。"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output", type=Path,
                        default=Path("reports/2026-10-12/plan-calculations.json"))
    args = parser.parse_args()
    try:
        result = calculate(timestamp(args.as_of))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({name: {"stake_yen": p["stake_yen"],
              "one_hit_nets_yen": [t["only_this_hit_net_yen"] for t in p["tickets"]]}
              for name, p in result["plans"].items()}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, StopIteration) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
