#!/usr/bin/env python3
"""Chronologically hold-out a hypothesis: does a preselected odds threshold help?

Future-data method, NOT trained on the one Shuka Sho archive. One specific
market must be captured repeatedly before each start with independently
verifiable quote-publication times. The outcome is only used for training
on earlier *other* races and scoring later races.

Input contract: docs/odds-information-hierarchy-20261023.md
Run toy-only smoke:
 python scripts/odds_threshold_forward_eval.py --demo-synthetic --output tmp/odds-threshold-demo.json

No investment recommendations, payout EV, or v3.1 holdout writes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import random
from statistics import mean

STATUS_HOLD = "HOLD_INSUFFICIENT_DISTINCT_PAST_FUTURE_RACES_FOR_THRESHOLD"
STATUS_SYN = "SYNTHETIC_FORWARD_THRESHOLD_METHOD_ONLY_NOT_MARKET_DISCOVERY"
STATUS_OBS = "EXPLORATORY_FUTURE_PERIOD_TEST_NOT_CAUSAL_OR_CALIBRATED"
SCHEMA = "WIN_ODDS_PATH_PANEL_WITH_VERIFIED_PUBLICATION_TIMES_V1"
BETA_GRID = (-1.0, -0.5, 0.0, 0.5, 1.0)
THRESHOLD_GRID = (5.0, 10.0, 20.0, 50.0)
MIN_RACES = 60
MIN_DATES = 8


def _date(x):
    if not isinstance(x, str):
        raise ValueError("HOLD_TIMESTAMP_TYPE")
    d = datetime.fromisoformat(x)
    if d.utcoffset() is None:
        raise ValueError("HOLD_TIMEZONE_REQUIRED")
    return d


def normalize(values):
    if not values or any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("HOLD_INVALID_WEIGHTS")
    s = sum(values)
    return [v/s for v in values]


def order_probabilities(win_weights):
    """PL winning and top-three inclusion; no Monte Carlo needed."""
    q = normalize(win_weights)
    n = len(q)
    if n < 5:
        raise ValueError("HOLD_TOO_FEW_RUNNERS")
    top = [0.0]*n
    for i in range(n):
        top[i] += q[i]
        for j in range(n):
            if j == i:
                continue
            top[i] += q[j]*q[i]/(1-q[j])
            for k in range(n):
                if k in (i,j):
                    continue
                top[i] += q[j]*q[k]/(1-q[j])*q[i]/(1-q[j]-q[k])
    if not math.isclose(sum(top), 3.0, abs_tol=1e-10):
        raise ValueError("HOLD_TOP3_MASS")
    return q, top


def load_panel(data):
    if data.get("schema") != SCHEMA:
        raise ValueError("HOLD_SCHEMA_MISMATCH")
    synthetic = data.get("provenance") == "synthetic"
    if not synthetic and data.get("provenance") != "rights_audited_source":
        raise ValueError("HOLD_UNVERIFIED_RESEARCH_SOURCE_RIGHTS")
    races = data.get("races")
    if not isinstance(races, list) or not races:
        raise ValueError("HOLD_NO_RACES")
    processed = []
    seen_ids = set()
    for r in races:
        rid = r["race_id"]
        if not isinstance(rid, str) or not rid or rid in seen_ids:
            raise ValueError("HOLD_DUPLICATE_RACE_ID")
        seen_ids.add(rid)
        start = _date(r["post_jst"])
        early, late = r["early_win"], r["latest_win"]
        earlier = _date(early["provider_published_at_jst"])
        later = _date(late["provider_published_at_jst"])
        result_time = _date(r["official_top3_verified_at_jst"])
        if not (earlier < later < start - timedelta(minutes=10)
                and result_time > start):
            raise ValueError("HOLD_TIME_TRAVEL_OR_WRONG_PRE_START_WINDOW")
        for s in (early, late):
            if s.get("provider_timestamp_verified") is not True:
                raise ValueError("HOLD_UNKNOWN_SOURCE_UPDATE_TIME")
            if s.get("market") != "JRA_win":
                raise ValueError("HOLD_NONCOMPARABLE_BET_TYPE")
        first, last = early["odds"], late["odds"]
        if (not isinstance(first, dict) or set(first) != set(last)
                or len(first) < 5):
            raise ValueError("HOLD_FIELD_MISMATCH_OR_TOO_FEW")
        nums = sorted(first)
        if any((not isinstance(first[k], (int,float))
                or not isinstance(last[k], (int,float))
                or not math.isfinite(first[k]) or not math.isfinite(last[k])
                or min(first[k],last[k]) <= 1)
               for k in nums):
            raise ValueError("HOLD_INVALID_ODDS_VECTOR")
        actual = r["official_top3"]
        if len(actual) != 3 or len(set(actual)) != 3 or not set(actual).issubset(nums):
            raise ValueError("HOLD_BAD_VERIFIED_TOP3")
        date = start.date().isoformat()
        q0 = normalize([1/first[k] for k in nums])
        q1 = normalize([1/last[k] for k in nums])
        delta = [math.log(b/a) for a,b in zip(q0,q1)]
        avg = mean(delta)
        processed.append({
            "race_id": rid, "date": date, "start": start.isoformat(),
            "numbers": nums, "early_odds": [first[k] for k in nums],
            "latest_q": q1, "centered_log_quote_movement": [x-avg for x in delta],
            "official_top3": actual,
        })
    processed.sort(key=lambda x: (x["date"], x["start"], x["race_id"]))
    return processed, synthetic


def forecast(r, *, beta=0.0, threshold=None):
    delta = r["centered_log_quote_movement"]
    q = r["latest_q"]
    early_odds = r["early_odds"]
    if threshold is None:
        factor = delta
    else:
        factor = [v if early_odds[i] >= threshold else 0.0
                  for i,v in enumerate(delta)]
    log_scores = [math.log(q[i]) + beta*factor[i] for i in range(len(q))]
    mx = max(log_scores)
    return order_probabilities([math.exp(z-mx) for z in log_scores])


def score(r, win, top):
    top_set = set(r["official_top3"])
    win_id = r["official_top3"][0]
    win_i = r["numbers"].index(win_id)
    return {
        "winner_log_loss": -math.log(max(win[win_i], 1e-12)),
        "top3_brier_per_horse": mean(
            (top[i] - (1.0 if h in top_set else 0.0))**2
            for i,h in enumerate(r["numbers"])),
    }


def mean_scores(rows, beta=0.0, threshold=None):
    vals = [score(r,*forecast(r,beta=beta,threshold=threshold)) for r in rows]
    return {name: mean(v[name] for v in vals) for name in vals[0]}


def evaluate(data):
    rows, synthetic = load_panel(data)
    dates = sorted(set(r["date"] for r in rows))
    if len(rows) < MIN_RACES or len(dates) < MIN_DATES:
        return {
            "status": STATUS_HOLD, "race_count": len(rows),
            "independent_start_dates": len(dates),
            "engineered_min_races": MIN_RACES,
            "engineered_min_dates": MIN_DATES,
            "disclaimer": "These are practical support gates, not a statistical power justification.",
        }
    cutoff = min(len(dates)-2, max(5, int(len(dates)*.7)))
    train_days = set(dates[:cutoff])
    train = [r for r in rows if r["date"] in train_days]
    test = [r for r in rows if r["date"] not in train_days]
    if len(train) < 35 or len(test) < 12:
        return {
            "status": STATUS_HOLD, "race_count": len(rows),
            "independent_start_dates": len(dates),
            "training_races": len(train), "future_races": len(test),
            "disclaimer": "Unbalanced race-date cohort; no numeric performance claim.",
        }
    # Optimize **only** on earlier training dates. The beta=0 baseline is
    # not a choice we can discard after inspecting held-out outcomes.
    grid = [(beta, None) for beta in BETA_GRID if beta != 0]
    grid += [(beta,t) for t in THRESHOLD_GRID for beta in BETA_GRID if beta != 0]
    grid = [g for g in grid if g[1] is None or
            sum(sum(o >= g[1] for o in r["early_odds"]) for r in train) >= 10]
    selected_smooth = min((g for g in grid if g[1] is None),
                          key=lambda g: mean_scores(train,*g)["winner_log_loss"])
    selected_threshold = min((g for g in grid if g[1] is not None),
                             key=lambda g: mean_scores(train,*g)["winner_log_loss"])
    policies = {
        "market_latest_only": (0.0, None),
        "train_selected_smooth_path": selected_smooth,
        "train_selected_threshold_path": selected_threshold,
    }
    model_scores = {name: mean_scores(test,beta,th)
                    for name,(beta,th) in policies.items()}
    base = model_scores["market_latest_only"]
    for name in model_scores:
        model_scores[name]["difference_vs_market_lower_is_better"] = {
            k: model_scores[name][k]-base[k] for k in
            ("winner_log_loss", "top3_brier_per_horse")
        }
    return {
        "status": STATUS_SYN if synthetic else STATUS_OBS,
        "data_provenance_synthetic": synthetic,
        "predeclared_beta_grid": list(BETA_GRID),
        "predeclared_early_odds_threshold_grid": list(THRESHOLD_GRID),
        "training_race_count": len(train), "future_race_count": len(test),
        "training_date_count": len(train_days),
        "future_date_count": len(dates)-len(train_days),
        "train_max_date": max(train_days),
        "future_min_date": min(r["date"] for r in test),
        "training_only_selected_parameters": {
            k: {"beta":v[0],"early_odds_at_least":v[1]}
            for k,v in policies.items()
        },
        "future_race_avg_scores": model_scores,
        "interpretation_limitations": [
            "Synthetic fixture results cannot establish empirical odds thresholds.",
            "Selected coefficients/threshold are based on earlier race outcomes only.",
            "A single chronological split is exploratory, not a formal high-power test.",
            "Do not infer endogenous popularity effects or profit from forecast score.",
            "Market prices/actual outcomes need independent timestamps and source rights.",
            "Train-selected winners or thresholds must not be promoted into v3.1 retrospective holdout.",
        ],
    }


def demo_panel(seed=20261023, dates=15, races_per_day=6,
               n=12, planted_threshold=10.0, planted_beta=.7):
    """An overtly artificial panel to exercise chronology and learnability.

    The winner-generation mechanism is deliberately known, so this is
    an algorithm unit demonstration, NOT evidence of a real threshold.
    """
    rng = random.Random(seed)
    race_rows = []
    start_base = datetime.fromisoformat("2026-01-01T13:00:00+09:00")
    for day in range(dates):
        for r in range(races_per_day):
            start = start_base + timedelta(days=day, minutes=15*r)
            logits = [rng.gauss(0,1) for _ in range(n)]
            baseline = normalize([math.exp(x) for x in logits])
            shock = [rng.gauss(0,.35) for _ in range(n)]
            next_q = normalize([baseline[i]*math.exp(shock[i]) for i in range(n)])
            earlier_odds = [1/b for b in baseline]
            latest_odds = [1/b for b in next_q]
            delta = [math.log(next_q[i]/baseline[i]) for i in range(n)]
            dc = [v-mean(delta) for v in delta]
            true = normalize([
                next_q[i]*math.exp(planted_beta*dc[i]) if earlier_odds[i]>=planted_threshold
                else next_q[i] for i in range(n)])
            # draw first three ordered without replacement by the known
            # synthetic latent distribution.
            available = list(range(n))
            order = []
            for _ in range(3):
                idx = rng.choices(available, weights=[true[i] for i in available], k=1)[0]
                order.append(str(idx+1))
                available.remove(idx)
            race_rows.append({
                "race_id": f"FICTITIOUS-{day:03d}-{r:02d}",
                "post_jst": start.isoformat(),
                "early_win": {
                    "market":"JRA_win", "provider_timestamp_verified":True,
                    "provider_published_at_jst": (start-timedelta(hours=4)).isoformat(),
                    "odds":{str(i+1):earlier_odds[i] for i in range(n)}
                },
                "latest_win": {
                    "market":"JRA_win", "provider_timestamp_verified":True,
                    "provider_published_at_jst": (start-timedelta(minutes=30)).isoformat(),
                    "odds":{str(i+1):latest_odds[i] for i in range(n)}
                },
                "official_top3_verified_at_jst": (start+timedelta(hours=2)).isoformat(),
                "official_top3":order
            })
    return {"schema":SCHEMA, "provenance":"synthetic", "races":race_rows,
            "generator_note":"Fictitious logistic trend threshold: not real official JRA observations"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path)
    p.add_argument("--demo-synthetic", action="store_true")
    p.add_argument("--output", type=Path, default=Path("tmp/odds-threshold-forward.json"))
    args = p.parse_args()
    if args.demo_synthetic == bool(args.input):
        raise ValueError("Provide exactly one of --demo-synthetic or --input")
    data = demo_panel() if args.demo_synthetic else json.loads(args.input.read_text(encoding="utf-8"))
    result = evaluate(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))


if __name__ == "__main__":
    main()
