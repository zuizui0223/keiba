#!/usr/bin/env python3
"""Post-race, *development-only* market-by-ticket audit, Kyoto 2026-10-12 R8–R12.

Historical source: pre-race saved intermediary Yahoo market quotes and
independently archived JRA official top-three results. The odds-only PL
predictions are not out-of-sample validated: this is retrospective diagnostics.
Never uses finish positions for features, model fitting, or quote selection.
Do not append scores to the frozen v3.1 forward ledger.
"""
from __future__ import annotations

import argparse
from datetime import timezone
import hashlib
import json
import math
from pathlib import Path

try:
    from scripts.ticket_type_models import (
        KINDS, _normalized_key, _time, event_selection, predict_tickets
    )
except ModuleNotFoundError:
    from ticket_type_models import (
        KINDS, _normalized_key, _time, event_selection, predict_tickets
    )

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DATE = "2026-10-12"
TARGET_RACES = (8, 9, 10, 11, 12)
MARKET_FILES = ("tfw", "wide", "ur", "ut", "sf", "st")
EXPECTED_KIND_COUNT = {"win": 1, "place": 3, "frame": 1,
                       "quinella": 1, "wide": 3, "exacta": 1,
                       "trio": 1, "trifecta": 1}


def read_json(path: Path, hashes: dict) -> dict:
    payload = path.read_bytes()
    hashes[str(path.relative_to(ROOT))] = hashlib.sha256(payload).hexdigest()
    return json.loads(payload)


def market_race(race_number: int, hashes: dict) -> dict:
    """Read pre-result market data only; enforce within-race timestamps."""
    if race_number not in TARGET_RACES:
        raise ValueError("unapproved_development_race")
    base = ROOT / "data" / SOURCE_DATE
    racecard = read_json(base / f"kyoto_{race_number:02d}.json", hashes)
    if int(racecard["race"]) != race_number or racecard["date"] != SOURCE_DATE:
        raise ValueError("racecard_identity_mismatch")
    start = _time(racecard["start_jst"])
    markets = {}
    market_observation_times = {}
    if race_number == 8:
        snapshot = read_json(base / "r8_markets_latest.json", hashes)
        frames = {int(n): f for n, f in snapshot["horse_frames"].items()}
        receipt = _time(snapshot["checked_at_utc"])
        for kind, raw in snapshot["markets"].items():
            if kind not in KINDS:
                continue
            observed = _time(raw["observed_at_utc"])
            updated = _time(raw["updated_at_jst"])
            if updated > observed or observed > receipt or receipt >= start:
                raise ValueError("post_start_market_r8")
            markets[kind] = raw["quotes"]
            market_observation_times[kind] = observed.isoformat()
    else:
        prefix = base / "remaining-snapshots"
        receipt = None
        frames = None
        for page in MARKET_FILES:
            row = read_json(prefix / f"r{race_number}_{page}.json", hashes)
            if row["race"] != race_number or row["page_code"] != page:
                raise ValueError("source_page_race_mismatch")
            observed = _time(row["observed_at_jst"])
            updated = _time(row["updated_at_jst"])
            if updated > observed or observed >= start or updated >= start:
                raise ValueError("post_start_market_quote")
            receipt = max(receipt, observed) if receipt is not None else observed
            if page == "tfw":
                if not row["horses"]:
                    raise ValueError("missing_horse_frames")
                frames = {int(h["number"]): int(h["frame"]) for h in row["horses"]}
                if len(frames) != len(row["horses"]):
                    raise ValueError("duplicate_horse_frame")
            for kind, quotes in row["quotes"].items():
                if kind not in KINDS or kind in markets:
                    raise ValueError("duplicate_or_unknown_market_kind")
                markets[kind] = quotes
                market_observation_times[kind] = observed.isoformat()
    if receipt is None or frames is None or receipt >= start:
        raise ValueError("invalid_snapshot_receipt")
    if set(markets) != set(KINDS):
        raise ValueError("not_all_ticket_types_in_snapshot")
    win_odds = {}
    for q in markets["win"]:
        num = q["selection"]
        odds = q["odds_low"]
        if len(num) != 1 or type(num[0]) is not int or num[0] in win_odds:
            raise ValueError("duplicated_win_selection")
        if isinstance(odds, bool) or not isinstance(odds, (float, int)) or not math.isfinite(odds) or odds < 1:
            raise ValueError("invalid_win_odds")
        if q["odds_low"] != q["odds_high"]:
            raise ValueError("win_odds_unexpected_range")
        win_odds[num[0]] = float(odds)
    if set(win_odds) != set(frames) or len(win_odds) != len(racecard["horses"]):
        raise ValueError("racecard_market_number_mismatch")
    return {
        "race_number": race_number,
        "race_id": racecard["race_id"],
        "start_jst": racecard["start_jst"],
        "receipt_as_of": receipt.isoformat(),
        "win_odds": win_odds,
        "frames": frames,
        "markets": markets,
        "market_observation_times": market_observation_times,
    }


def direct_own_market(quotes: list, kind: str,
                      probability_keys: set[tuple[int, ...]],
                      *, odds_position: str = "geometric") -> tuple[dict, dict]:
    """Proxy p proportional to inverse low/mid/high quote, no trained model."""
    if kind not in KINDS:
        raise ValueError("invalid_kind")
    if odds_position not in {"low", "geometric", "high"}:
        raise ValueError("invalid_odds_position")
    mapped = {}
    for q in quotes:
        key = _normalized_key(kind, q["selection"])
        low, high = q["odds_low"], q["odds_high"]
        if key in mapped:
            raise ValueError("duplicate_market_quote")
        if any(isinstance(o, bool) or not isinstance(o, (int, float)) or not math.isfinite(o) or o < 1
               for o in (low, high)) or high < low:
            raise ValueError("invalid_market_odds_range")
        odds = {"low": low, "geometric": math.sqrt(low * high), "high": high}[odds_position]
        mapped[key] = 1 / odds
    if not set(mapped) <= probability_keys:
        raise ValueError("quote_not_in_probability_support")
    coverage = {
        "quoted": len(mapped), "possible": len(probability_keys),
        "complete": set(mapped) == probability_keys,
    }
    if not coverage["complete"]:
        return {}, {**coverage, "status": "HOLD_INCOMPLETE_QUOTE_SET"}
    # There are 3 winning wide/place tickets per 8+ runner race.
    rawsum = math.fsum(mapped.values())
    out = {key: EXPECTED_KIND_COUNT[kind] * v / rawsum for key, v in mapped.items()}
    if max(out.values()) > 1 + 1e-12:
        return {}, {**coverage, "status": "HOLD_IMPLIED_PROBABILITY_OVER_ONE"}
    return out, {**coverage, "status": "AVAILABLE_UNCALIBRATED_PROXY"}


def score_binary_events(probs: dict, winning: set) -> dict:
    if not probs or not winning or not winning <= set(probs):
        raise ValueError("invalid_evaluation_support")
    n = len(probs)
    brier = math.fsum((p - (1 if key in winning else 0)) ** 2
                      for key, p in probs.items()) / n
    losses = [
        -math.log(max(p, 1e-15)) if key in winning else -math.log(max(1 - p, 1e-15))
        for key, p in probs.items()
    ]
    return {
        "brier_mean_per_ticket": brier,
        "binary_log_loss_mean_per_ticket": math.fsum(losses) / n,
        "realized_winning_probability_sum": math.fsum(probs[key] for key in winning),
    }


def audit_race(race_number: int, official: dict, hashes: dict) -> dict:
    snapshot = market_race(race_number, hashes)
    actual = official["races"][str(race_number)]
    if not actual["complete_top3"] or actual["source_type"] != "JRA_official":
        raise ValueError("official_result_not_verified")
    top3 = actual["positions"]
    if len(top3) != 3 or len(set(top3)) != 3 or not set(top3) <= set(snapshot["win_odds"]):
        raise ValueError("invalid_official_top3")
    strength = {n: 1 / odds for n, odds in snapshot["win_odds"].items()}
    full = predict_tickets(strength, snapshot["frames"])
    market_summaries = {}
    for kind, dist in full.items():
        winning = set(event_selection(kind, tuple(top3), snapshot["frames"]))
        own, coverage = direct_own_market(snapshot["markets"][kind], kind, set(dist))
        # All possible combinatorial tickets have a valid market-odds-only PL p.
        pl_score = score_binary_events(dist, winning)
        own_score = score_binary_events(own, winning) if own else None
        bound_sensitivity = {}
        if kind in ("place", "wide"):
            for bound in ("low", "high"):
                direct, info = direct_own_market(
                    snapshot["markets"][kind], kind, set(dist), odds_position=bound
                )
                bscore = score_binary_events(direct, winning) if direct else None
                bound_sensitivity[bound] = {
                    "status": info["status"],
                    "brier_direct_minus_PL":
                        bscore["brier_mean_per_ticket"] - pl_score["brier_mean_per_ticket"]
                        if bscore else None,
                }
        ranked = sorted(dist, key=lambda key: (-dist[key], key))
        market_summaries[kind] = {
            "possible": len(dist),
            "quoted": coverage["quoted"],
            "direct_quote_status": coverage["status"],
            "actual_winning_selections": [list(x) for x in sorted(winning)],
            "all_actual_winners_quoted": all(x in {
                _normalized_key(kind, q["selection"]) for q in snapshot["markets"][kind]
            } for x in winning),
            "PL_win_odds_only": pl_score,
            "direct_same_ticket_market": own_score,
            "direct_price_bound_sensitivity": bound_sensitivity,
            "delta_brier_direct_minus_PL":
                own_score["brier_mean_per_ticket"] - pl_score["brier_mean_per_ticket"]
                if own_score else None,
            "top_PL_selection": list(ranked[0]),
            "top_PL_probability": dist[ranked[0]],
            "best_winning_PL_rank": min(i + 1 for i, k in enumerate(ranked) if k in winning),
        }
    return {
        "race_number": race_number,
        "race_id": snapshot["race_id"],
        "runner_count": len(snapshot["win_odds"]),
        "snapshot_receipt_as_of": snapshot["receipt_as_of"],
        "scheduled_start_jst": snapshot["start_jst"],
        "actual_top3": top3,
        "ticket_types": market_summaries,
    }


def run_backtest() -> dict:
    hashes = {}
    official = read_json(ROOT / "data" / SOURCE_DATE / "official-results-final.json", hashes)
    if official["date"] != SOURCE_DATE or official["status"] != "official_top3_complete_7_to_12":
        raise ValueError("result_source_version_mismatch")
    races = [audit_race(num, official, hashes) for num in TARGET_RACES]
    aggregate = {}
    for kind in KINDS:
        paired = [r["ticket_types"][kind] for r in races
                  if r["ticket_types"][kind]["direct_same_ticket_market"] is not None]
        aggregate[kind] = {
            "races_with_PL": len(races),
            "races_with_complete_direct_market": len(paired),
            "mean_PL_brier_per_ticket_equal_race":
                math.fsum(r["ticket_types"][kind]["PL_win_odds_only"]["brier_mean_per_ticket"]
                          for r in races) / len(races),
            "paired_mean_PL_brier_per_ticket":
                math.fsum(r["PL_win_odds_only"]["brier_mean_per_ticket"] for r in paired) / len(paired)
                if paired else None,
            "paired_mean_direct_brier_per_ticket":
                math.fsum(r["direct_same_ticket_market"]["brier_mean_per_ticket"] for r in paired) / len(paired)
                if paired else None,
            "paired_delta_direct_minus_PL":
                math.fsum(r["delta_brier_direct_minus_PL"] for r in paired) / len(paired)
                if paired else None,
            "paired_races_direct_lower_brier":
                sum(r["delta_brier_direct_minus_PL"] < -1e-12 for r in paired),
            "paired_races_tied_within_numeric_tolerance":
                sum(abs(r["delta_brier_direct_minus_PL"]) <= 1e-12 for r in paired),
        }
        if kind in ("place", "wide"):
            sensitivity = {}
            for bound in ("low", "high"):
                supported = [
                    r["ticket_types"][kind]["direct_price_bound_sensitivity"][bound]["brier_direct_minus_PL"]
                    for r in races
                ]
                valid = [value for value in supported if value is not None]
                sensitivity[bound] = {
                    "supported_race_count": len(valid),
                    "mean_delta_direct_minus_PL": math.fsum(valid) / len(valid) if valid else None,
                    "races_PL_lower_brier": sum(value > 1e-12 for value in valid),
                }
            aggregate[kind]["price_bound_sensitivity"] = sensitivity
    return {
        "schema_version": 1,
        "data_scope": "2026-10-12 Kyoto 8R-12R, retrospective development only",
        "source_role": "Recorded intermediary pre-race odds -> market proxy; JRA official top3 -> later scoring only",
        "model_A": "1/win_odds Plackett-Luce top3 probability",
        "model_B": "per-ticket-market inverse geometric midpoint odds normalized to ticket winning slots",
        "probabilities_calibrated": False,
        "predictive_out_of_sample_validated": False,
        "positive_EV_established": False,
        "market_ratio_causal_effect": False,
        "notes": [
            "All source quote timestamps precede target race; as_of is receipt of latest selected quote.",
            "The saved snapshot is not equivalent to the final odds.",
            "M0 and ticket-type quote proxies are both market-only, not independent horse predictors.",
            "Comparison is on the same observed race and ticket kind; 5 same-day races are not independent validation.",
            "Incomplete trifecta and trio price boards yield HOLD, not missing-price imputation.",
            "Brier/log-loss are averages over the same event set within each race/type; ticket rows are correlated.",
            "All 8 types are scored from one coherent top-three distribution; no purchase was performed.",
        ],
        "file_sha256": dict(sorted(hashes.items())),
        "races": races,
        "by_ticket_type": aggregate,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        out = run_backtest()
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    payload = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
