#!/usr/bin/env python3
"""Horse-history signal -> future quoted-market innovation (retrospective).

Important: Archived detailed Kyoto form was retrieved/normalized AFTER the
2026-10-12 target races. The JRA race rows have historical event dates but no
authenticated pre-target receipt. This is NOT a prospective observation.

Build a forecast ONLY from earlier saved WIN quotes and source-locked *past*
horse form; the held-out later WIN quote is accessed only for comparison.
NO target podium, payout, or final quote is ever a model feature. The same
form_prior() is supplied as the physical input to the existing horse/bettor
ABM, rather than inventing a disconnected second horse model.

Forecasts compare: unchanged q0, q0^0.8 * h^0.2, and same blend with
h assigned to a different horse via a fixed cyclic shift. q1 is a
normalized inverse displayed-odds PRICE INDEX, NOT individual vote counts
or calibrated winning probability. Scores KL(q1||prediction) and TV are
price-shape discrepancies, NOT proper future race-outcome scores.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from statistics import mean
import numpy as np

from keiba_coupled_history_falsification import history_map, form_prior
from keiba_coupled_horse_market_pde import ROOT, vector
from odds_threshold_regime_bridge import (
    load_source_locked_panels, market_features,
)

STATUS = "REAL_SAVED_TWO_PRICE_PANELS_HISTORY_RETRIEVED_POSTRACE_NOT_FORWARD"
BLEND = 0.20
MODEL_NAMES = ("early_market_only", "market_plus_past_history_020",
               "market_plus_shifted_history_020")


def geometric_bridge(q0, h, *, fraction=BLEND):
    """Fixed geometric pool-to-form bridge without future odds or outcomes."""
    q0, h = vector(q0), vector(h)
    if (len(q0) != len(h) or
        not math.isfinite(fraction) or not 0 <= fraction <= 1):
        raise ValueError("HOLD_MARKET_HISTORY_BRIDGE_BAD_INPUT")
    logs=(1-fraction)*np.log(q0)+fraction*np.log(h)
    return vector(np.exp(logs-np.max(logs)))


def prepare_market_prediction(row, archive):
    """Does NOT read row['last_odds'], target outcomes, or race payouts."""
    h = form_prior(row, archive)
    ids = h["horse_numbers"]
    early = row["first_odds"]
    if set(ids) != set(early):
        raise ValueError("HOLD_DIFFERENT_EARLY_HORSE_ROSTER")
    q0 = vector([1/early[i] for i in ids])
    prior = vector(h["prior"])
    wrong_identity = np.roll(prior, 1)
    predictions = {
        "early_market_only": q0,
        "market_plus_past_history_020": geometric_bridge(q0,prior),
        "market_plus_shifted_history_020": geometric_bridge(q0,wrong_identity),
    }
    return {
        "race_id":row["race_id"],
        "meeting_date":row["meeting_day"],
        "horse_numbers":ids,
        "q0_for_market":q0,
        "history_prior_for_horse_ABM":prior,
        "candidate_next_market_predictions":predictions,
        "history_record_count":h["past_race_records_examined"],
        "history_horse_missing_count":h["entrants_without_any_past_run"],
        "independent_history_capture_was_not_asof_authenticated":True,
        "model_did_not_consume_later_win_quote_or_official_result":True,
    }


def _kl(target, forecast):
    if len(target)!=len(forecast):
        raise ValueError("HOLD_KL_UNMATCHED_RUNNERS")
    return float(np.sum(target*np.log(target/forecast)))


def _tv(target, forecast):
    if len(target)!=len(forecast):
        raise ValueError("HOLD_TV_UNMATCHED_RUNNERS")
    return float(50*np.sum(np.abs(target-forecast)))


def score_later_market(prepared, row):
    """Read quoted q1 only after all forecast candidate vectors were built."""
    f = market_features(row)
    if f["horse_numbers"] != prepared["horse_numbers"]:
        raise ValueError("HOLD_LATER_WIN_HORSE_FIELD_CHANGE")
    q0 = prepared["q0_for_market"]
    q1 = vector(f["latest"])
    hist = prepared["history_prior_for_horse_ABM"]
    scores={}
    for key,p in prepared["candidate_next_market_predictions"].items():
        scores[key]={"price_index_TV_pp":_tv(q1,p),
                     "price_index_KL_nats":_kl(q1,p)}
    # This is an algebraic *alignment*, not estimated transmission.
    z=np.log(hist/q0)
    v=np.log(q1/q0)
    z-=float(np.sum(q0*z))
    v-=float(np.sum(q0*v))
    directional_cov=float(np.sum(q0*z*v))
    return {
        "race_id":prepared["race_id"],
        "day":prepared["meeting_date"],
        "entries":len(q0),
        "hours_between_quotes":f["hours"],
        "mean_abs_observed_market_log_rate_per_hour":
            float(np.mean(f["absolute_log_relative_support_change_per_hour"])),
        "per_policy":scores,
        "observed_history_market_log_residual_alignment_weighted":directional_cov,
        "history_blend_minus_market_TV_pp":
            (scores["market_plus_past_history_020"]["price_index_TV_pp"]-
             scores["early_market_only"]["price_index_TV_pp"]),
        "history_blend_minus_shifted_TV_pp":
            (scores["market_plus_past_history_020"]["price_index_TV_pp"]-
             scores["market_plus_shifted_history_020"]["price_index_TV_pp"]),
        "not_actual_transaction_vote_flows":True,
        "not_a_formal_prestart_or_prospective_score":True,
    }


def audit(root=ROOT):
    rows=load_source_locked_panels(root)
    hist=history_map(root)
    if len(rows)!=6 or set(hist)!={r["race_id"] for r in rows}:
        raise ValueError("HOLD_ARCHIVED_HISTORY_RACE_COVERAGE")
    prepared = [prepare_market_prediction(r,hist[r["race_id"]])
                for r in rows]
    # Forecasts all exist at the software level before later quotes are read.
    scored=[score_later_market(p,r) for p,r in zip(prepared,rows)]
    dates=sorted({r["meeting_day"] for r in rows})
    if len(dates)!=2:
        raise ValueError("HOLD_NOT_TWO_HISTORICAL_MEETING_DATES")
    by_date = {
        day:{
            "n_races":sum(r["day"]==day for r in scored),
            "mean_history_minus_early_market_TV_pp":
                mean(r["history_blend_minus_market_TV_pp"]
                    for r in scored if r["day"]==day),
            "mean_history_minus_shifted_TV_pp":
                mean(r["history_blend_minus_shifted_TV_pp"]
                    for r in scored if r["day"]==day),
        } for day in dates}
    aggregate={
        name:{
            metric:mean(r["per_policy"][name][metric] for r in scored)
            for metric in ("price_index_TV_pp", "price_index_KL_nats")
        } for name in MODEL_NAMES}
    return {
        "status":STATUS,
        "independent_race_outcomes":6,"independent_dates":len(dates),
        "horse_race_rows":sum(s["entries"] for s in scored),
        "fixed_history_information_weight":BLEND,
        "source_last_quote_used_only_as_score_target":True,
        "past_record_history_retrieved_after_target":True,
        "no_independent_past_horse_source_receipt":True,
        "no_actual_bettor_ballots_or_stakes_observed":True,
        "market_q0_and_history_horse_prior_stay_separate":True,
        "original_M0_M1_M2_sha_and_v31_ledger_unchanged":True,
        "per_race":scored,
        "mean_race_equal_market_price_index_scores":aggregate,
        "n_races_history_blend_lower_TV_than_q0":
            sum(r["history_blend_minus_market_TV_pp"]<0 for r in scored),
        "n_races_correct_history_lower_TV_than_shifted":
            sum(r["history_blend_minus_shifted_TV_pp"]<0 for r in scored),
        "by_meeting_date":by_date,
        "mean_meeting_date_equal_history_minus_early_market_TV_pp":
            mean(r["mean_history_minus_early_market_TV_pp"]
                 for r in by_date.values()),
        "not_forecast_calibration_or_critical_threshold_discovery":True,
        "research_decision":"HOLD_NO_EXTERNAL_ASOF_PAST_HISTORY_RECEIPTS_AND_ONLY_TWO_DATES",
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,
                        default=Path("tmp/coupled-past-form-next-market.json"))
    a=parser.parse_args()
    result=audit()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({
        "status":result["status"],"races":result["independent_race_outcomes"],
        "mean_price_index_TV":result["mean_race_equal_market_price_index_scores"],
        "decision":result["research_decision"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
