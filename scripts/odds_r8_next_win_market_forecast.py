#!/usr/bin/env python3
"""Kyoto 8R: does pre-13:44 WIDE contain incremental next-WIN quote information?

Descriptive, retrospective ONE-RACE next-market forecast experiment.
Predictions depend ONLY on 12:21 win, 13:26 win and all 55 wide-pair quotes.
The 13:44 full-win target is a separate, source-hash-locked file loaded
AFTER forecasts are constructed. No JRA actual result, winning probability
or payout is modeled. This is NOT a prospective performance claim.

The scoring TARGET is the next vector of NORMALIZED inverse win display
odds. These are not verified true pool shares or race-outcome probabilities.

A +18min comparison horizon and arbitrary coefficient 0.25 are fixed
for this single retrospective illustration, NOT selected by training
on different races. Looking at several coefficients afterwards does not
provide external validation or a discovered odds threshold.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import random
from statistics import mean

from odds_real_multirace_archive_audit import SOURCE_SHA, read_file, _one_race
from odds_r8_real_three_time_market import OTHER_SOURCE, _locked
from odds_cross_pool_global_async import relative_pair_indices
from odds_pair_hierarchy_decomposition import complete_graph_decompose
from odds_pair_hierarchy_robustness import _to_full_pair_prices

ROOT = Path(__file__).resolve().parents[1]
STATUS = "ONE_RACE_RETROSPECTIVE_NEXT_WIN_QUOTE_NOT_RACE_WINNER_VALIDATION"
SOURCE_RACE = "2608040508"
SOURCE_CUTOFF = "2026-10-12T13:26:00+09:00"
NEXT_HORIZON_MINUTES = 18
NODE_BETA_ILLUSTRATIVE = 0.25


def aware(value):
    dt = datetime.fromisoformat(value)
    if dt.utcoffset() is None:
        raise ValueError("HOLD_UNVERIFIED_CLOCK_OFFSET")
    return dt


def win_proxy(odds):
    if not isinstance(odds, dict) or len(odds)<5:
        raise ValueError("HOLD_INCOMPLETE_WIN_PRICE_VECTOR")
    if any(type(i) is not int or type(o) not in (int,float)
           or not math.isfinite(o) or o <= 1.0 for i,o in odds.items()):
        raise ValueError("HOLD_INVALID_WIN_QUOTES")
    w={i:1/o for i,o in odds.items()}
    total=sum(w.values())
    return {i:v/total for i,v in w.items()}


def _mid_win_vector(mid):
    out={}
    for x in mid["quotes"]["win"]:
        ids=x["selection"]
        if len(ids)!=1 or type(ids[0]) is not int or (
                x["odds_low"] != x["odds_high"]) or ids[0] in out:
            raise ValueError("HOLD_AMBIGUOUS_MID_WIN_QUOTES")
        out[ids[0]]=x["odds_low"]
    return out


def source_only_features(root=ROOT, *, pl_gamma=1.0, wide_mode="lower"):
    """Does not open, import or consult any file containing the later win quotes."""
    if pl_gamma not in (0.75,1.0,1.25) or wide_mode not in (
            "lower", "geometric", "upper"):
        raise ValueError("HOLD_NON_PREDEFINED_MARKET_MODEL_SENSITIVITY")
    early=read_file(root,SOURCE_SHA[8][0])
    mid=read_file(root,SOURCE_SHA[8][1])
    _one_race(early,mid,8)
    wide=_locked(*OTHER_SOURCE["mid_wide"],root=root)
    if (early["race_id"]!=SOURCE_RACE or wide.get("race")!=8
            or wide.get("page_code")!="wide"
            or mid.get("updated_at_jst")!=SOURCE_CUTOFF
            or wide.get("updated_at_jst")!=SOURCE_CUTOFF):
        raise ValueError("HOLD_WRONG_RACE_OR_UNMATCHED_MARKET_UPDATE")
    if (not mid["url"].startswith("https://sports.yahoo.co.jp/keiba/")
            or not wide["url"].startswith("https://sports.yahoo.co.jp/keiba/")):
        raise ValueError("HOLD_DIFFERENT_PRICE_PROVIDER")
    t0=aware(early["odds_updated_at_jst"])
    t1=aware(mid["updated_at_jst"])
    rx_mid=max(aware(mid["observed_at_jst"]),aware(wide["observed_at_jst"]))
    post=aware(early["start_jst"])
    if not (t0<t1<=rx_mid<post and
            aware(early["odds_observed_at_jst"])<=rx_mid
            and t1+timedelta(minutes=NEXT_HORIZON_MINUTES)<post):
        raise ValueError("HOLD_MISORDERED_PRESTART_SOURCE_TIMES")
    q0_raw={h["number"]:h["win_odds"] for h in early["horses"]}
    q1_raw=_mid_win_vector(mid)
    if set(q0_raw)!=set(q1_raw) or len(q1_raw)!=11:
        raise ValueError("HOLD_CHANGED_COMPLETE_RUNNER_ROSTER")
    q0=win_proxy(q0_raw)
    q1=win_proxy(q1_raw)
    pairs=_to_full_pair_prices(wide["quotes"]["wide"],len(q1),wide_mode)
    # Transform only the PL market benchmark for the cross-pool index,
    # not the baseline latest public win-price weights.
    transformed={i:q1_raw[i]**pl_gamma for i in q1_raw}
    residuals=relative_pair_indices({
        "label":"before_next_win_update_1326",
        "win":transformed, "wide":pairs})["pair_residual"]
    nodes=complete_graph_decompose(residuals)
    if nodes["n"]!=11 or nodes["m"]!=55 or (
            nodes["status"]!="COMPLETE_GRAPH_HORSE_ADDITIVE_DESCRIPTIVE_DECOMPOSITION"):
        raise ValueError("HOLD_INCOMPLETE_WIDE_PRICE_HIERARCHY")
    return {
        "status":"SOURCE_ONLY_1221_AND_1326_FULL_WIN_PLUS_1326_WIDE",
        "race_id":SOURCE_RACE, "n_horses":11,
        "source_captured_without_future_file":True,
        "feature_first_published":t0.isoformat(),
        "feature_latest_published":t1.isoformat(),
        "feature_later_market_received":rx_mid.isoformat(),
        "race_scheduled_post":post.isoformat(),
        "prior_earlier_minutes":(t1-t0).total_seconds()/60,
        "comparison_horizon_minutes_in_advance":NEXT_HORIZON_MINUTES,
        "hypothetical_PL_gamma":pl_gamma,
        "hypothetical_WIDE_mapping":wide_mode,
        "last_market_q":q1,
        "earlier_market_q":q0,
        "wide_extra_horse_node":nodes["node_effects"],
        "horse_node_from_single_snapshot_is_not_information_shock":True,
    }


def construct_advance_forecast(feature, *, beta_momentum=1.0, beta_node=0.0,
                               node_reassignment=None):
    """qhat ∝ q_latest exp(b_m*h/dt*Delta log q + b_n*WIDE node)."""
    if any(not math.isfinite(v) or abs(v)>2.0 for v in
           (beta_momentum,beta_node)):
        raise ValueError("HOLD_UNBOUNDED_HYPOTHETICAL_COEFFICIENT")
    q0=feature["earlier_market_q"]
    q1=feature["last_market_q"]
    node=feature["wide_extra_horse_node"] if node_reassignment is None else node_reassignment
    if set(q0)!=set(q1) or set(q1)!=set(node):
        raise ValueError("HOLD_CHANGED_MARKET_RUNNER_UNIVERSE")
    h=feature["comparison_horizon_minutes_in_advance"]
    previous=feature["prior_earlier_minutes"]
    if not (0<h<=30 and previous>0):
        raise ValueError("HOLD_INVALID_PREDECLARED_HORIZON")
    exponent={
        i:beta_momentum*(h/previous)*math.log(q1[i]/q0[i])+
          beta_node*node[i]
        for i in q1
    }
    qhat={i:q1[i]*math.exp(exponent[i]) for i in q1}
    total=sum(qhat.values())
    return {i:v/total for i,v in qhat.items()}


def evaluate_market_prediction(qhat, observed_q):
    """Compare future quote *shapes*. This is not race winner log loss."""
    if set(qhat)!=set(observed_q) or not math.isclose(
            sum(qhat.values()),1.0,abs_tol=1e-9):
        raise ValueError("HOLD_MARKET_DISTRIBUTION_MISMATCH")
    return {
        "normalized_inverse_odds_TV_pp":50*sum(
            abs(qhat[i]-observed_q[i]) for i in qhat),
        "KL_next_displayed_price_proxy_vs_prediction":sum(
            observed_q[i]*math.log(observed_q[i]/qhat[i]) for i in qhat),
        "mean_abs_log_relative_quote_weight_error":mean(
            abs(math.log(qhat[i]/observed_q[i])) for i in qhat),
        "not_empirical_winner_probability_log_loss":True,
    }


def _permutation_reference(feature, target, *, permutations=999, seed=20261023):
    if permutations<99:
        raise ValueError("HOLD_TOO_FEW_MATHEMATICAL_PLACEBO_SHUFFLES")
    q=feature["wide_extra_horse_node"]
    ordered=sorted(q)
    node_values=[q[i] for i in ordered]
    actual=construct_advance_forecast(
        feature,beta_momentum=1,beta_node=NODE_BETA_ILLUSTRATIVE)
    actual_TV=evaluate_market_prediction(actual,target)[
        "normalized_inverse_odds_TV_pp"]
    rng=random.Random(seed)
    shuffled_TVs=[]
    for _ in range(permutations):
        rng.shuffle(node_values)
        random_node=dict(zip(ordered,node_values))
        p=construct_advance_forecast(
            feature,beta_momentum=1,beta_node=NODE_BETA_ILLUSTRATIVE,
            node_reassignment=random_node)
        shuffled_TVs.append(evaluate_market_prediction(
            p,target)["normalized_inverse_odds_TV_pp"])
    return {
        "status":"EXPLORATORY_WITHIN_ONE_RACE_HORSE_LABEL_SHUFFLE_NOT_P_VALUE",
        "permutations":permutations,"seed":seed,
        "observed_association_TV_pp":actual_TV,
        "fraction_label_shuffles_TV_no_worse_than_actual":
            sum(v<=actual_TV for v in shuffled_TVs)/permutations,
        "label_shuffle_median_TV_pp":sorted(shuffled_TVs)[permutations//2],
        "horse_entries_do_not_constitute_independent_race_replicates":True,
        "exchangeability_or_significance_not_established":True,
    }


def audit(*, permutations=999,seed=20261023,root=ROOT):
    # Build *all* candidate next-market forecasts BEFORE reading the target.
    source=source_only_features(root)
    candidate_specs={
        "last_win_only":(0.0,0.0),
        "elapsed_time_scaled_win_momentum":(1.0,0.0),
        "wide_horse_node_only_beta_025":(0.0,NODE_BETA_ILLUSTRATIVE),
        "momentum_plus_wide_node_beta_025":(1.0,NODE_BETA_ILLUSTRATIVE),
        "opposite_wide_node_beta_minus025":(1.0,-NODE_BETA_ILLUSTRATIVE),
        "momentum_plus_wide_node_beta_05":(1.0,0.5),
    }
    forecasts={
        label:construct_advance_forecast(
            source,beta_momentum=bm,beta_node=bn)
        for label,(bm,bn) in candidate_specs.items()
    }
    # The target is a SEPARATE hash-locked file, not a tuning input.
    future=_locked(*OTHER_SOURCE["late_all"],root=root)
    latest=future["markets"]["win"]
    observed_at=aware(latest["observed_at_utc"])
    target_pub=aware(latest["updated_at_jst"])
    if (future["race_id"]!=SOURCE_RACE or future["horse_count"]!=11 or
            target_pub!=aware(source["feature_latest_published"])+
            timedelta(minutes=NEXT_HORIZON_MINUTES) or not
            aware(source["feature_later_market_received"])<target_pub<=
            observed_at<aware(source["race_scheduled_post"])):
        raise ValueError("HOLD_TARGET_IS_NOT_LATER_PRESTART_FULL_MARKET")
    future_prices={}
    for r in latest["quotes"]:
        k=r["selection"]
        if (len(k)!=1 or type(k[0]) is not int or k[0] in future_prices or
                r["odds_low"]!=r["odds_high"]):
            raise ValueError("HOLD_TARGET_DUPLICATED_OR_AMBIGUOUS")
        future_prices[k[0]]=r["odds_low"]
    target=win_proxy(future_prices)
    if set(target)!=set(source["last_market_q"]) or len(target)!=11:
        raise ValueError("HOLD_FUTURE_RUNNER_FIELD_MISMATCH")
    scored={name:evaluate_market_prediction(q,target)
            for name,q in forecasts.items()}
    main=scored["momentum_plus_wide_node_beta_025"]
    previous=scored["elapsed_time_scaled_win_momentum"]
    alternatives=[]
    for gamma in (0.75,1.0,1.25):
        for mapping in ("lower","geometric","upper"):
            f=source_only_features(root,pl_gamma=gamma,wide_mode=mapping)
            p=construct_advance_forecast(
                f,beta_momentum=1,beta_node=NODE_BETA_ILLUSTRATIVE)
            alternatives.append({
                "gamma":gamma,"WIDE_quote_mapping":mapping,
                "future_market_quote_TV_pp":
                    evaluate_market_prediction(p,target)
                    ["normalized_inverse_odds_TV_pp"],
            })
    tv=[x["future_market_quote_TV_pp"] for x in alternatives]
    return {
        "status":STATUS,"real_independent_races":1,
        "venue_race":"2026-10-12 Kyoto 8R, 11 full runner win prices",
        "model_uses_pre_target_win_and_wide_quotes_only":True,
        "source_first_update":source["feature_first_published"],
        "source_last_update":source["feature_latest_published"],
        "source_last_received":source["feature_later_market_received"],
        "target_source_published":target_pub.isoformat(),
        "target_received":observed_at.isoformat(),
        "comparison_horizon_minutes_retrospective_fixed":NEXT_HORIZON_MINUTES,
        "coefficients_are_arbitrary_and_not_trained_or_registered_before_race":True,
        "model_coefficients":{k:{"momentum":p[0],"wide_node":p[1]}
                              for k,p in candidate_specs.items()},
        "next_market_price_proxy_scores":scored,
        "additional_TV_reduction_vs_momentum_pp":
            previous["normalized_inverse_odds_TV_pp"]-
            main["normalized_inverse_odds_TV_pp"],
        "additional_KL_reduction_vs_momentum":
            previous["KL_next_displayed_price_proxy_vs_prediction"]-
            main["KL_next_displayed_price_proxy_vs_prediction"],
        "observed_wide_node_cross_market_association":
            "One archived 11-horse field only; no independently replicable predictive threshold",
        "sensitivity_nine_PL_and_conditional_WIDE_mappings":alternatives,
        "sensitivity_TV_min_max":[min(tv),max(tv)],
        "mathematical_horse_label_negative_control":_permutation_reference(
            source,target,permutations=permutations,seed=seed),
        "limitations":[
            "All numbers are retrospective single-race source-saved historical quotes, not a preregistered market prediction.",
            "The normalized inverse win odds are price-derived relative indices, not actual tote money shares or real winning probabilities.",
            "The 0.25 and 0.5 coefficients were not calibrated on any training race; do not select the best based on this target.",
            "The 18 minute horizon is a retrospective operational target, not evidence of an automatically available future 13:44 quote.",
            "One race, 11 horses, 55 overlapping WIDE pairs: no independent race blocks, no stable test of additional information.",
            "Matching displayed win/WIDE update minute is not confirmation of atomic pari-mutuel pool state or bettor information lag.",
            "Wide lower and upper quoted odds encode conditional payout cases, not measurement uncertainty bounds.",
            "Shuffling horse node labels is only a mechanics reference and is not a scientific p value or causal identification.",
            "Forecasting later market quotes does not imply improved winner, Top3 or positive expected betting returns.",
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--permutations",type=int,default=999)
    p.add_argument("--seed",type=int,default=20261023)
    p.add_argument("--output",type=Path,
                   default=Path("tmp/odds-r8-next-market-crosspool.json"))
    a=p.parse_args()
    out=audit(permutations=a.permutations,seed=a.seed)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({
        "status":out["status"],"real_races":out["real_independent_races"],
        "source_latest":out["source_last_update"],
        "target_published":out["target_source_published"],
        "market_shape_scores":{k:{
            "TV_pp":v["normalized_inverse_odds_TV_pp"],
            "KL":v["KL_next_displayed_price_proxy_vs_prediction"],
        } for k,v in out["next_market_price_proxy_scores"].items()},
        "incremental_TV_pp":out["additional_TV_reduction_vs_momentum_pp"],
        "nine_case_TV_range":out["sensitivity_TV_min_max"],
        "randomized_negative_control":out[
            "mathematical_horse_label_negative_control"],
        "actual_winning_probability_benefit":"HOLD_NOT_TESTED"
    },ensure_ascii=False))


if __name__=="__main__":
    main()
