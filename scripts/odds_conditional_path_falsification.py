#!/usr/bin/env python3
"""Does the intermediate odds path matter CONDITIONAL on identical endpoints?

A fully SYNTHETIC matched-endpoint falsification for odds-path information.
Pairs of fictional races have exactly the same *early* and *latest* win odds,
but deliberately opposite *middle* deviations. A PL market-only null and
two separately planted path-information mechanisms generate finishing orders.

This is not an actual JRA result, bettor-behavior model, calibrated forecast,
identified market threshold, or an extension of the v3.1 formal holdout.

Run:
  python scripts/odds_conditional_path_falsification.py \
      --output tmp/odds-conditional-path-falsification.json
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import random
from statistics import mean

from odds_threshold_forward_eval import order_probabilities

STATUS = "SYNTHETIC_SAME_ENDPOINT_DIFFERENT_MIDDLE_PATH_FALSIFICATION_ONLY"
MECHANISMS = ("null_latest_sufficient", "smooth_path_signal", "threshold_10x_signal")
BETAS = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.0)
THRESHOLDS = (5.0, 10.0, 20.0, 50.0)


def _normalize(weights):
    if not weights or any(not math.isfinite(w) or w <= 0 for w in weights):
        raise ValueError("HOLD_INVALID_WEIGHTS")
    s = sum(weights)
    return [w / s for w in weights]


def _softmax(log_weights):
    top = max(log_weights)
    return _normalize([math.exp(v - top) for v in log_weights])


def _aware(value):
    ts = datetime.fromisoformat(value)
    if ts.utcoffset() is None:
        raise ValueError("HOLD_NAIVE_SOURCE_CLOCK")
    return ts


def path_feature(early, middle, latest, t0, t1, t2):
    """Centered, elapsed-time-adjusted deviation from endpoint interpolation."""
    if not len(early) == len(middle) == len(latest) or len(early) < 5:
        raise ValueError("HOLD_NONMATCHED_FIELD")
    times = [_aware(x) for x in (t0, t1, t2)]
    if not (times[0] < times[1] < times[2]):
        raise ValueError("HOLD_UNORDERED_PRE_RACE_TIMES")
    u = (times[1] - times[0]) / (times[2] - times[0])
    q0, qm, q2 = [_normalize(x) for x in (early, middle, latest)]
    raw = [
        math.log(qm[i]) - (1 - u) * math.log(q0[i]) - u * math.log(q2[i])
        for i in range(len(q0))
    ]
    middle_level = mean(raw)
    return [v - middle_level for v in raw]


def prepare_before_results(rows):
    """Returns strictly prerace features; never sees winner, place or payout."""
    out = []
    for row in rows:
        snaps = row["snapshots"]
        if len(snaps) != 3 or any(s["market"] != "win" or
                                  s["source_time_verified"] is not True for s in snaps):
            raise ValueError("HOLD_NEED_THREE_VERIFIED_WIN_SNAPSHOTS")
        ids = [int(k) for k in snaps[0]["odds"]]
        if len(set(ids)) != len(ids) or len(ids) < 5:
            raise ValueError("HOLD_BAD_HORSE_IDS")
        ids.sort()
        if any(set(s["odds"]) != set(str(k) for k in ids) for s in snaps):
            raise ValueError("HOLD_CHANGED_SNAPSHOT_FIELD")
        times = [s["published_at_jst"] for s in snaps]
        post = _aware(row["post_jst"])
        if _aware(times[-1]) >= post - timedelta(minutes=10):
            raise ValueError("HOLD_PRICE_AFTER_ALLOWED_CUTOFF")
        series = []
        for s in snaps:
            row_prices = [s["odds"][str(k)] for k in ids]
            if any(type(v) not in (int, float) or
                   not math.isfinite(v) or v <= 1.0 for v in row_prices):
                raise ValueError("HOLD_INVALID_ARCHIVED_PRICE")
            series.append(_normalize([1 / v for v in row_prices]))
        middle_residual = path_feature(*series, *times)
        out.append({
            "id": row["race_id"],
            "date": post.date().isoformat(),
            "twin_id": row["twin_id"],
            "arm": row["arm"],
            "horse_numbers": ids,
            "early_q": series[0],
            "latest_q": series[-1],
            "initial_win_odds": [snaps[0]["odds"][str(k)] for k in ids],
            "curvature": middle_residual,
            "middle_race_centered_deviation_sd": math.sqrt(
                sum(x*x for x in middle_residual) / len(middle_residual)),
        })
    return out


def generate(*, mechanism="null_latest_sufficient", seed=20261023,
             dates=36, twin_pairs_per_date=20, horses=12,
             signal_beta=2.0, shock_sd=0.55):
    """Artificial paired races: same endpoints, opposite middle trajectories."""
    if mechanism not in MECHANISMS or dates < 12 or twin_pairs_per_date < 2 or horses < 8:
        raise ValueError("HOLD_SYNTHETIC_GENERATOR_INVALID_CONFIG")
    rng = random.Random(seed)
    first_date = datetime.fromisoformat("2026-01-01T15:00:00+09:00")
    rows = []
    for day in range(dates):
        for pair_idx in range(twin_pairs_per_date):
            post = first_date + timedelta(days=day, seconds=pair_idx * 120)
            # Midpoint fraction in REAL seconds: t=-180,-90,-30min -> 0.60
            t0, t1, t2 = [post - timedelta(minutes=m) for m in (180, 90, 30)]
            final = _softmax([rng.gauss(0, 1.05) for _ in range(horses)])
            early = _softmax([math.log(q) + rng.gauss(0, .25) for q in final])
            frac = (t1 - t0) / (t2 - t0)
            log_baseline = [
                (1-frac) * math.log(early[i]) + frac * math.log(final[i])
                for i in range(horses)
            ]
            intermediate_shock = [rng.gauss(0, shock_sd) for _ in range(horses)]
            for arm in ("up", "down"):
                sign = 1 if arm == "up" else -1
                middle = _softmax([
                    log_baseline[i] + sign * intermediate_shock[i]
                    for i in range(horses)
                ])
                snaps = []
                for ts, q in zip((t0, t1, t2), (early, middle, final)):
                    snaps.append({
                        "market": "win", "source_time_verified": True,
                        "published_at_jst": ts.isoformat(),
                        "odds": {str(i+1): 1 / q[i] for i in range(horses)},
                    })
                row = {
                    "race_id": f"FICTITIOUS-{mechanism}-{day:03d}-{pair_idx:02d}-{arm}",
                    "twin_id": f"FICTITIOUS-TWIN-{day:03d}-{pair_idx:02d}",
                    "arm": arm, "post_jst": post.isoformat(),
                    "snapshots": snaps,
                    "official_result_recorded_at_jst": (post+timedelta(hours=2)).isoformat(),
                }
                rows.append(row)
    return {
        "status": "FABRICATED_MATCHED_ENDPOINT_RACES_NO_JRA_DATA",
        "mechanism": mechanism,
        "generated_for_purpose": "Falsify same-final-quote path effect with no-path negative control",
        "signal_beta_planted": signal_beta if mechanism != MECHANISMS[0] else 0.0,
        "planted_win_odds_threshold": 10 if mechanism == MECHANISMS[2] else None,
        "dates": dates, "twin_pairs_per_date": twin_pairs_per_date,
        "rows": rows,
        "sampling_seed": seed,
    }


def attach_fictional_results(dataset, *, seed=201313,
                             signal_beta=None):
    """Complete synthetic finish order generated AFTER pre-race paths are fixed."""
    dataset = {**dataset, "rows": [dict(row) for row in dataset["rows"]]}
    rng = random.Random(seed)
    prepared = prepare_before_results(dataset["rows"])
    beta = dataset["signal_beta_planted"] if signal_beta is None else signal_beta
    mechanism = dataset["mechanism"]
    for row, features in zip(dataset["rows"], prepared):
        q = features["latest_q"]
        move = features["curvature"]
        if mechanism == "null_latest_sufficient":
            logtruth = [math.log(x) for x in q]
        elif mechanism == "smooth_path_signal":
            logtruth = [math.log(q[i]) + beta * move[i] for i in range(len(q))]
        elif mechanism == "threshold_10x_signal":
            logtruth = [
                math.log(q[i]) + beta * move[i] *
                (features["initial_win_odds"][i] >= 10.0)
                for i in range(len(q))
            ]
        else:
            raise ValueError("HOLD_UNKNOWN_GENERATOR")
        true_win_weights = _softmax(logtruth)
        available = list(range(len(q)))
        podium = []
        for _ in range(3):
            pick = rng.choices(available, weights=[true_win_weights[i]
                                                   for i in available], k=1)[0]
            podium.append(pick+1)
            available.remove(pick)
        row["synthetic_top3"] = podium
    return dataset


def _prob_win(q, x, beta, threshold, odds):
    logits = [
        math.log(q[i]) + beta * x[i] *
        (1 if threshold is None or odds[i] >= threshold else 0)
        for i in range(len(q))
    ]
    return _softmax(logits)


def _winner_loss(prediction, winner):
    return -math.log(max(1e-12, prediction[winner-1]))


def _select_model(train, labels):
    # Threshold candidates, including beta=0, are selected only with old labels.
    models = {
        "train_selected_smooth": [(b, None) for b in BETAS],
        "train_selected_odds_threshold": [
            (b, t) for t in THRESHOLDS for b in BETAS
        ],
    }
    selected = {}
    for model, candidates in models.items():
        best = None
        for beta, threshold in candidates:
            cost = mean(_winner_loss(
                _prob_win(r["latest_q"], r["curvature"], beta,
                          threshold, r["initial_win_odds"]),
                labels[r["id"]][0]
            ) for r in train)
            if best is None or cost < best[0] - 1e-14:
                best = (cost, beta, threshold)
        selected[model] = {"beta": best[1], "threshold": best[2],
                           "training_winner_log_loss": best[0]}
    return selected


def _score_future(future, labels, selected, *, placebo_seed=112):
    rng = random.Random(placebo_seed)
    records=[]
    for r in future:
        probabilities = {"market_latest_only": r["latest_q"]}
        for name, params in selected.items():
            probabilities[name] = _prob_win(
                r["latest_q"], r["curvature"], params["beta"],
                params["threshold"], r["initial_win_odds"])
        shuffled = list(r["curvature"])
        rng.shuffle(shuffled)
        p = selected["train_selected_smooth"]
        probabilities["placebo_shuffled_middle_path"] = _prob_win(
            r["latest_q"], shuffled, p["beta"], p["threshold"],
            r["initial_win_odds"])
        truth = labels[r["id"]]
        scores={}
        for name, q in probabilities.items():
            win, top3 = order_probabilities(q)
            y=set(truth)
            scores[name]={
                "win_log_loss": _winner_loss(win, truth[0]),
                "top3_brier_per_horse":mean(
                    (top3[i]-(1 if (i+1) in y else 0))**2
                    for i in range(len(q))),
            }
        records.append({"date":r["date"],"id":r["id"],
                        "twin_id":r["twin_id"], "arm":r["arm"],
                        "model_scores":scores})
    return records


def _uncertainty(records, *, base="market_latest_only", iterations=1000, seed=1002):
    """Paired meeting-day block bootstrap; simulation precision ONLY."""
    if iterations < 100 or not records:
        raise ValueError("HOLD_TOO_FEW_BOOTSTRAP_RESAMPLES")
    by_day=defaultdict(list)
    for row in records:
        by_day[row["date"]].append(row)
    days=sorted(by_day)
    rng=random.Random(seed)
    model_names=[k for k in records[0]["model_scores"] if k != base]
    metrics=("win_log_loss", "top3_brier_per_horse")
    out={}
    for model in model_names:
        out[model]={}
        for metric in metrics:
            by_day_means={
                day:mean(r["model_scores"][model][metric]
                         -r["model_scores"][base][metric]
                         for r in by_day[day]) for day in days
            }
            observed=mean(by_day_means.values())
            distribution=sorted(
                mean(by_day_means[d] for d in rng.choices(days,k=len(days)))
                for _ in range(iterations)
            )
            out[model][metric]={
                "paired_mean_delta_model_minus_market_lower_better": observed,
                "synthetic_date_block_bootstrap_95pct":
                    [distribution[int(.025*iterations)],
                     distribution[min(iterations-1,int(.975*iterations))]],
                "independent_resample_unit": "fictional_meeting_day",
                "not_a_real_market_ci_or_identified_threshold":True,
            }
    return out


def evaluate(dataset, *, repetitions=1000, seed=20261023):
    if dataset.get("status") != "FABRICATED_MATCHED_ENDPOINT_RACES_NO_JRA_DATA":
        raise ValueError("HOLD_NO_REAL_DATA_ALLOWED_IN_TOY_MECHANISM_TEST")
    rows=dataset["rows"]
    predictions=prepare_before_results(rows)
    if len(rows)!=len({row["race_id"] for row in rows}):
        raise ValueError("HOLD_DUPLICATE_SYNTHETIC_RACE")
    by_twin=defaultdict(list)
    for p in predictions:
        by_twin[p["twin_id"]].append(p)
    for twin in by_twin.values():
        if (len(twin)!=2 or set(r["arm"] for r in twin)!={"up","down"}
                or twin[0]["early_q"]!=twin[1]["early_q"]
                or twin[0]["latest_q"]!=twin[1]["latest_q"]):
            raise ValueError("HOLD_NOT_EXACT_IDENTICAL_ENDPOINT_TWINS")
        if any(abs(x+y)>1e-9 for x,y in
               zip(twin[0]["curvature"],twin[1]["curvature"])):
            raise ValueError("HOLD_INTERMEDIATE_COUNTERFACTUAL_NOT_OPPOSITE")
    labels={}
    for row in rows:
        podium=row.get("synthetic_top3")
        if (_aware(row["official_result_recorded_at_jst"])
                <=_aware(row["post_jst"])
                or not isinstance(podium,list) or len(podium)!=3
                or len(set(podium))!=3
                or not set(podium).issubset(
                    set(int(k) for k in row["snapshots"][0]["odds"]))):
            raise ValueError("HOLD_SYNTHETIC_OUTCOME_NOT_POSTRACE_OR_INVALID")
        labels[row["race_id"]]=podium
    days=sorted({p["date"] for p in predictions})
    if len(days)<12:
        raise ValueError("HOLD_TOO_FEW_SYNTHETIC_DATES")
    cutoff=max(8, int(len(days)*2/3))
    cutoff=min(cutoff, len(days)-4)
    train_days=set(days[:cutoff])
    train=[p for p in predictions if p["date"] in train_days]
    future=[p for p in predictions if p["date"] not in train_days]
    if len(train)<50 or len(future)<20:
        raise ValueError("HOLD_TOO_FEW_DISTINCT_TRAIN_TEST_TWINS")
    selected=_select_model(train, labels)
    records=_score_future(future, labels, selected, placebo_seed=seed+29)
    means={}
    for model in records[0]["model_scores"]:
        means[model]={
            metric: mean(r["model_scores"][model][metric] for r in records)
            for metric in ("win_log_loss","top3_brier_per_horse")
        }
    boot=_uncertainty(records, iterations=repetitions, seed=seed+97)
    day_avg={day:{
        "sampled_races":sum(v["date"]==day for v in records),
        "smooth_winner_ll_delta":mean(
            r["model_scores"]["train_selected_smooth"]["win_log_loss"]
            -r["model_scores"]["market_latest_only"]["win_log_loss"]
            for r in records if r["date"]==day),
    } for day in sorted(set(r["date"] for r in records))}
    return {
        "status": STATUS, "mechanism":dataset["mechanism"],
        "real_race_data_used":False,
        "generated_twin_cases_identical_initial_and_latest":True,
        "twin_counterfactuals_have_different_middle_quotes":True,
        "planted_synthetic_path_coefficient":dataset["signal_beta_planted"],
        "training_race_count":len(train),"future_race_count":len(future),
        "training_date_count":len(train_days),"future_date_count":len(days)-len(train_days),
        "training_max_date":max(train_days),
        "future_min_date":min(p["date"] for p in future),
        "selected_only_with_past_results":selected,
        "future_mean_scores":means,
        "paired_day_bootstrap_synthetic_only":boot,
        "daily_future_aggregates":day_avg,
        "scientific_limitations":[
            "Same-final-quote matched twins are fabricated counterfactual universes, not matched real JRA starts.",
            "Synthetic result generation deliberately uses PL ranking, no market market prices are recovered from real wagers.",
            "The null and positive path effects are explicitly planted, so learning them is a software-method check.",
            "This test cannot show that real middle-odds paths contain independently predictive information.",
            "No holder of a betting license, no future race prediction, no real betting ROI or bettor herding is identified.",
            "No change to main's frozen v3.1 holdout or tickets.",
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed",type=int,default=20261023)
    p.add_argument("--dates",type=int,default=36)
    p.add_argument("--pairs-per-date",type=int,default=20)
    p.add_argument("--bootstrap",type=int,default=1000)
    p.add_argument("--output",type=Path,default=Path("tmp/odds-conditional-path-falsification.json"))
    args=p.parse_args()
    reports=[]
    for mechanism in MECHANISMS:
        d=generate(mechanism=mechanism,seed=args.seed,
                   dates=args.dates,twin_pairs_per_date=args.pairs_per_date)
        d=attach_fictional_results(d,seed=args.seed+132)
        reports.append(evaluate(d,repetitions=args.bootstrap,seed=args.seed))
    output={"status":STATUS,"synthetic_mechanisms":reports,
            "frozen_grids":{"beta":list(BETAS),"initial_odds_threshold":list(THRESHOLDS)},
            "true_real_market_additional_forecasting_value":"HOLD_NOT_TESTED",
            "shuka2026_current_two_day_six_race_data_cannot_test":"Identical endpoint with different middle path across independent prospective dates"}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":STATUS,
        "scenarios":[{
            "mechanism":v["mechanism"],
            "old_days":v["training_date_count"],"future_days":v["future_date_count"],
            "train_races":v["training_race_count"],"future_races":v["future_race_count"],
            "selected":v["selected_only_with_past_results"],
            "future_market_win_ll":v["future_mean_scores"]["market_latest_only"]["win_log_loss"],
            "future_smooth_win_ll":v["future_mean_scores"]["train_selected_smooth"]["win_log_loss"],
            "future_threshold_win_ll":v["future_mean_scores"]["train_selected_odds_threshold"]["win_log_loss"],
            "future_path_shuffled_win_ll":v["future_mean_scores"]["placebo_shuffled_middle_path"]["win_log_loss"],
            "mean_pair_delta":v["paired_day_bootstrap_synthetic_only"]["train_selected_smooth"]["win_log_loss"],
        } for v in reports],
        "real_market_path_effect": "HOLD_NO_SOURCE_PANEL_WITH_IDENTIFIABLE_MIDDLE_ODDS_PATH"
    },ensure_ascii=False))


if __name__=="__main__":
    main()
