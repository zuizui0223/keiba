#!/usr/bin/env python3
"""Date-blocked retrospective gamma learning and PRE-START candidate preparation.

Training-source history: Kyoto 2026-10-12 R8..12 (5 races, one date).
Next-date diagnostic: 2026-10-18 9 races, a single date spanning 3 courses.
Train-on-both gamma is ONLY an experimental candidate for 2026-10-25; it is
not a calibrated win probability, a preregistered genuine holdout, or a
demonstrated betting edge. The outcome labels enter only HISTORICAL scoring.

The original 2026-10-24 17:07 JST M0/M1/M2 forecasts are NOT changed.
This script does not load or score any 2026-10-25 outcomes.

Run:
 python scripts/betting_gamma_date_blocked.py \
   --oct18-official /path/from/pr9/betting-20261018-official-top3-postrace.json \
   --output tmp/betting_gamma_date_blocked.json
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
DAY12 = "2026-10-12"
DAY18 = "2026-10-18"
N_RACES = 14
GRID = tuple(round(0.5 + k * 0.05, 2) for k in range(37))
SOURCE_BLOBS = {
    "data/2026-10-12/remaining-snapshots/r8_tfw.json": "65fa640d6a07b7d94eb6e2904f6cc73f07a96448",
    "data/2026-10-12/remaining-snapshots/r9_tfw.json": "be94d8b01a2b67287958598842cc724029f45e89",
    "data/2026-10-12/remaining-snapshots/r10_tfw.json": "cdf8f36a073f68d351417d0046f5ab5c1ccc2be3",
    "data/2026-10-12/remaining-snapshots/r11_tfw.json": "751734355c67149b39cd1ebaf9682aac24f352e5",
    "data/2026-10-12/remaining-snapshots/r12_tfw.json": "6da13808c7b2a9c716a74b1c41d2c08296318c09",
    "data/2026-10-12/official-results-final.json": "fdcc70b78c64a50b8a0f566868b38b69ce2c6ff8",
    "data/2026-10-18/ticket-odds-snapshot.json": "8a7d37f02a40e7c6f93d6ee428089cd5c84e59df",
}
OFFICIAL_OCT18_BLOB = "ca5c9ac0d38e66d927c68786f7793b59c67035ce"
STATUS = "TWO_DATES_RETROSPECTIVE_CHRONOLOGICAL_DIAGNOSTIC_NOT_FORECAST_CALIBRATION"


def verified_time(s):
    d = datetime.fromisoformat(s)
    if d.utcoffset() is None:
        raise ValueError("HOLD_NAIVE_TIMESTAMP")
    return d


def source_json(path, sha):
    content = Path(path).read_bytes()
    computed = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
    if computed != sha:
        raise ValueError("HOLD_GITHUB_SOURCE_BLOB_DRIFT:" + str(path))
    return json.loads(content.decode("utf-8"))


def make_record(day, race_id, prices, top3, quote_time):
    if day not in {DAY12, DAY18}:
        raise ValueError("HOLD_DATE")
    if not isinstance(top3, list) or len(top3) != 3 or len(set(top3)) != 3:
        raise ValueError("HOLD_INVALID_OFFICIAL_TOP3")
    if len(prices) < 5 or len(prices) > 30:
        raise ValueError("HOLD_INVALID_FIELD_SIZE")
    if len({i for i, _ in prices}) != len(prices):
        raise ValueError("HOLD_DUPLICATE_HORSE")
    if (any(type(i) is not int or type(o) not in (int, float)
            or not math.isfinite(o) or o <= 1 for i, o in prices)
            or not set(top3).issubset({i for i, _ in prices})):
        raise ValueError("HOLD_INVALID_PRIOR_ODDS_OR_PODIUM")
    verified_time(quote_time)
    return {"date": day, "race_id": race_id,
            "numbers": [i for i, _ in prices],
            "prices": [float(o) for _, o in prices],
            "top3": top3, "quote_time": quote_time}


def load_14_original_races(root, oct18_official):
    root = Path(root)
    official12 = source_json(root / "data/2026-10-12/official-results-final.json",
                             SOURCE_BLOBS["data/2026-10-12/official-results-final.json"])
    if (official12.get("date") != DAY12
            or official12.get("status") != "official_top3_complete_7_to_12"):
        raise ValueError("HOLD_OFFICIAL_OCT12_SOURCE")
    results12_time = verified_time(official12["verified_at_jst"])
    races = []
    for n in range(8, 13):
        rel = f"data/2026-10-12/remaining-snapshots/r{n}_tfw.json"
        row = source_json(root / rel, SOURCE_BLOBS[rel])
        quote_time = row["updated_at_jst"]
        if verified_time(quote_time) >= results12_time:
            raise ValueError("HOLD_PRICE_AFTER_RESULT")
        prices = [(r["selection"][0], r["odds_low"]) for r in row["quotes"]["win"]]
        actual = official12["races"][str(n)]
        if not actual["complete_top3"] or actual["source_type"] != "JRA_official":
            raise ValueError("HOLD_BAD_OFFICIAL_OCT12_RACE")
        races.append(make_record(DAY12, f"KYOTO-{DAY12}-R{n}",
                                 prices, actual["positions"], quote_time))
    archive = source_json(root / "data/2026-10-18/ticket-odds-snapshot.json",
                          SOURCE_BLOBS["data/2026-10-18/ticket-odds-snapshot.json"])
    actual18 = source_json(oct18_official, OFFICIAL_OCT18_BLOB)
    if (archive.get("status") != "exploratory_market_snapshot_not_v31_holdout"
            or actual18.get("race_date") != DAY18
            or actual18.get("status") !=
            "RETROSPECTIVE_OFFICIAL_JRA_RESULTS_NOT_A_PROSPECTIVE_HOLDOUT"
            or not actual18.get("observed_outcomes_not_allowed_as_model_features")):
        raise ValueError("HOLD_HISTORICAL_SOURCE_PROVENANCE")
    actual_by_id = {a["race_id"]: a for a in actual18["races"]}
    if len(actual_by_id) != len(actual18["races"]):
        raise ValueError("HOLD_DUPLICATE_OFFICIAL_RACE")
    qtime = archive["observed_window_end_jst"]
    for race in archive["races"]:
        if verified_time(qtime) >= verified_time(race["scheduled_post_jst"]):
            raise ValueError("HOLD_QUOTE_AFTER_START")
        evidence = actual_by_id.get(race["race_id"])
        if evidence is None or len(race["horses"]) != race["runner_count"]:
            raise ValueError("HOLD_UNMATCHED_SOURCE_RACE")
        rows = [(h["number"], h["win_odds"]) for h in race["horses"]]
        races.append(make_record(DAY18, race["race_id"],
                                 rows, evidence["finish_order_top3"], qtime))
    if (len(races) != N_RACES
            or {r["race_id"] for r in races}.__len__() != N_RACES
            or sum(r["date"] == DAY12 for r in races) != 5
            or sum(r["date"] == DAY18 for r in races) != 9):
        raise ValueError("HOLD_UNEXPECTED_ARCHIVE_COHORT")
    return races


def score_record(r, gamma):
    if not isinstance(gamma, (int,float)) or gamma <= 0 or not math.isfinite(gamma):
        raise ValueError("HOLD_INVALID_GAMMA")
    w = [o ** -gamma for o in r["prices"]]
    total = sum(w)
    q = [x / total for x in w]
    n = len(q)
    top3 = [0.0] * n
    for a in range(n):
        for b in range(n):
            if a == b:
                continue
            ab = q[a] * q[b] / (1 - q[a])
            for c in range(n):
                if c in (a, b):
                    continue
                p = ab * q[c] / (1 - q[a] - q[b])
                top3[a] += p
                top3[b] += p
                top3[c] += p
    if (not math.isclose(sum(q), 1, abs_tol=1e-10)
            or not math.isclose(sum(top3), 3, abs_tol=1e-10)):
        raise ValueError("HOLD_PROBABILITY_MASS")
    winner = r["numbers"].index(r["top3"][0])
    actual = set(r["top3"])
    brier = mean((p - (1.0 if horse in actual else 0.0))**2
                 for p, horse in zip(top3, r["numbers"]))
    return {"win_log_loss": -math.log(max(q[winner],1e-14)),
            "top3_brier_mean_horse": brier,
            "winner_predicted_probability": q[winner]}


def summarize(races, gamma):
    s = [score_record(r, gamma) for r in races]
    return {"race_count":len(s),
            "mean_winner_log_loss":mean(x["win_log_loss"] for x in s),
            "mean_top3_brier":mean(x["top3_brier_mean_horse"] for x in s)}


def select_gamma(races, objective):
    if objective not in ("win_log_loss","top3_brier_mean_horse"):
        raise ValueError("HOLD_UNKNOWN_OBJECTIVE")
    candidates = [(mean(score_record(r, g)[objective] for r in races),g) for g in GRID]
    loss, gamma = min(candidates)
    return {"gamma":gamma,"training_score":loss}


def audit(races):
    train = [r for r in races if r["date"] == DAY12]
    future = [r for r in races if r["date"] == DAY18]
    if len(train) != 5 or len(future) != 9 or len(races) != N_RACES:
        raise ValueError("HOLD_TWO_DATE_SAMPLE_NOT_MATCHED")
    # Historical outcomes on Oct-18 never enter the choice made by Oct-12.
    fit_win12 = select_gamma(train,"win_log_loss")
    fit_top12 = select_gamma(train,"top3_brier_mean_horse")
    refit_win_all = select_gamma(races,"win_log_loss")
    refit_top_all = select_gamma(races,"top3_brier_mean_horse")
    per_race = []
    for row in future:
        base = score_record(row, 1)
        sharpened = score_record(row, fit_win12["gamma"])
        top_model = score_record(row,fit_top12["gamma"])
        per_race.append({
            "race_id": row["race_id"],
            "winner_logloss_delta_trained_oct12_minus_market":
                sharpened["win_log_loss"] - base["win_log_loss"],
            "top3_brier_delta_trained_oct12_minus_market":
                top_model["top3_brier_mean_horse"] - base["top3_brier_mean_horse"],
        })
    return {
        "status":STATUS,
        "experimental_use_before_20261025_outcome_only":True,
        "source_date_clusters":[DAY12,DAY18],
        "n_races_total":N_RACES,
        "n_independent_meeting_dates":2,
        "source_pins":SOURCE_BLOBS,
        "official_oct18_blob_sha":OFFICIAL_OCT18_BLOB,
        "gamma_grid":[min(GRID),max(GRID),len(GRID),0.05],
        "training_date_only":DAY12,
        "historical_validation_date":DAY18,
        "training_winner_model":fit_win12,
        "training_top3_model":fit_top12,
        "validation_market_gamma1":summarize(future,1),
        "validation_win_selected_gamma":summarize(future,fit_win12["gamma"]),
        "validation_top3_selected_gamma":summarize(future,fit_top12["gamma"]),
        "historical_validation_race_deltas":per_race,
        "refit_on_all_14_past_races_for_new_20261025_shadow":{
            "winner_model":refit_win_all,
            "top3_model":refit_top_all,
            "not_a_calibrated_probability_model":True,
        },
        "limitations":[
            "Two independent dates only. Do not present 14 races as 14 independent date clusters.",
            "Retrospective training/validation was defined after both outcome dates were historically known.",
            "Oct18 intermediate quote upstream time unverified; venue and price-window differ.",
            "Only old results may enter gamma selection; today race outcome is never loaded.",
            "The learned concentration gamma can over-sharpen a heavily-favored G1 field.",
            "No real money or positive-EV forecast has been validated.",
            "Original 2026-10-24 SHA-sealed M0/M1/M2 and formal v3.1 holdout untouched."
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--oct18-official",type=Path,required=True,
                   help="The exact pinned Oct18 result file from separate Draft PR #9")
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=audit(load_14_original_races(a.root,a.oct18_official))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "oct12_winner_gamma":result["training_winner_model"]["gamma"],
        "oct18_gamma1_win_loss":result["validation_market_gamma1"]["mean_winner_log_loss"],
        "oct18_trained_win_loss":result["validation_win_selected_gamma"]["mean_winner_log_loss"],
        "all14_candidate_gamma":result["refit_on_all_14_past_races_for_new_20261025_shadow"]["winner_model"]["gamma"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
