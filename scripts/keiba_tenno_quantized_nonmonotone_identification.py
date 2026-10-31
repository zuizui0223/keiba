#!/usr/bin/env python3
"""Quantization-aware, source-limited non-monotonicity and identification audit.

DATA: The five 2026-10-31 *editorially reported* partial WIN quote points
for the SAME 2026-11-01 Tenno Sho race, already declared and SHA-pinned in
PR38. This never reconstructs unreported runner odds, a complete M0
normalizer, actual JRA vote records, q2, or results.

For each of ten distinct pairs among {1,3,7,11,17}, use only timestamps
at which BOTH horses were reported. Compare three assumptions for a
displayed 0.1-unit price p:
  nearest tenth: [p-0.05,p+0.05]  (hypothetical)
  tenth truncation: [p,p+0.10]   (hypothetical)
  union of both: [p-0.05,p+0.10] (deliberately wider)
None of these proves which processing rule the original source uses.

The latent relative log-price z_ij=log(o_i/o_j) has an exact interval
[log(lo_i/hi_j),log(hi_i/lo_j)] given these assumptions. A SINGLE global
nondecreasing path exists only if no EARLIER lower bound is strictly
above a LATER upper bound. Likewise a nonincreasing path exists only
if no EARLIER upper bound lies strictly below a LATER lower bound.

If neither monotone direction is possible, the source-conditional
relative price history NECESSARILY changed direction, within the chosen
quantization bounds; this does not imply an abrupt jump or any bettor
feedback. It rejects only globally monotone trajectories, not smooth
nonmonotone diffusion/mean-reverting processes.

As a mechanism non-identification control, construct THREE exact fits to
the same displayed-center path: (a) C2 quintic smooth interpolation,
(b) timepoint-step exogenous changes, (c) discrete feedback with
AR-like persistence phi and UNRESTRICTED innovations. All fits are
algebraic, not estimated models or prospective predictive tests.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from itertools import combinations
import json
import math
from pathlib import Path

from keiba_tenno_partial_article_timepath import (
    _blog_reported_quotes, BLOG_URL,
    PINNED_BLOG_DECLARED_PARTIAL_SHA256
)

STATUS="PARTIAL_REPORTED_QUOTES_QUANTIZATION_NONMONOTONICITY_NOT_MECHANISM_ID"
QUANTIZATION_SCHEMES={
    "nearest_tenth_hypothetical":(-0.05,0.05),
    "truncate_tenth_hypothetical":(0.0,0.10),
    "union_of_both_conservative":(-0.05,0.10),
}
EPS=1e-12
EXAMPLE_HORSES=(1,7)
EXAMPLE_TIMES=("08:09","12:07","13:08")
FEEDBACK_PHI_EXAMPLES=(0.0,0.5,0.9)


def _time(stamp):
    if not isinstance(stamp,str):
        raise ValueError("HOLD_INVALID_REPORTED_CLOCK")
    t=datetime.fromisoformat(stamp)
    if t.utcoffset() is None:
        raise ValueError("HOLD_NAIVE_REPORTED_CLOCK")
    return t


def _price_interval(p,scheme):
    if (scheme not in QUANTIZATION_SCHEMES or
            type(p) not in (int,float) or
            not math.isfinite(p) or p<=1):
        raise ValueError("HOLD_UNSUPPORTED_QUANTIZATION_OR_ODDS")
    lo,hi=QUANTIZATION_SCHEMES[scheme]
    if p+lo<=0:
        raise ValueError("HOLD_NONPOSITIVE_ODDS_INTERVAL_BOUND")
    return (p+lo,p+hi)


def _pair_log_bounds(first,second,scheme):
    a,b=_price_interval(first,scheme),_price_interval(second,scheme)
    lo=math.log(a[0]/b[1])
    hi=math.log(a[1]/b[0])
    center=math.log(first/second)
    if not lo-EPS<=center<=hi+EPS:
        raise ValueError("HOLD_ACTUAL_DISPLAYED_CENTER_OUTSIDE_ENVELOPE")
    return {"lower":lo,"upper":hi,"displayed_center":center}


def _pair_samples(records,i,j,scheme):
    if (type(i) is not int or type(j) is not int or i>=j or
            not isinstance(records,list)):
        raise ValueError("HOLD_BAD_PAIR_OR_SOURCE_RECORDED_TIMES")
    out=[]
    previous=None
    for record in records:
        stamp=record["source_reported_jst"]
        when=_time(stamp)
        if previous is not None and not previous<when:
            raise ValueError("HOLD_EDITORIAL_SOURCE_TIME_ORDER_CHANGED")
        previous=when
        field=record["prices"]
        if i in field and j in field:
            bounds=_pair_log_bounds(field[i],field[j],scheme)
            out.append({
                "source_reported_at_NOT_verified_provider_clock":stamp,
                "horse_i":i,"horse_j":j,
                "display_odds_i":field[i],"display_odds_j":field[j],
                **bounds,
            })
    if len(out)<3:
        raise ValueError("HOLD_NOT_ENOUGH_SHARED_REPORTED_PRICE_POINTS")
    return out


def monotonicity_certificate(samples):
    """Exact interval-feasibility result, not a time-series trend p-value.

    Earliest-to-later pair inequalities characterize existence of an
    arbitrary monotone latent sequence through ordered intervals.
    """
    if not isinstance(samples,list) or len(samples)<3:
        raise ValueError("HOLD_MONOTONE_CERTIFICATE_NEEDS_THREE_POINTS")
    down=[]
    up=[]
    for a,b in combinations(samples,2):
        t0=_time(a["source_reported_at_NOT_verified_provider_clock"])
        t1=_time(b["source_reported_at_NOT_verified_provider_clock"])
        if not t0<t1:
            raise ValueError("HOLD_MONOTONE_SOURCE_NOT_CHRONOLOGICAL")
        if a["lower"]>b["upper"]+EPS:
            down.append({
                "earlier":a["source_reported_at_NOT_verified_provider_clock"],
                "later":b["source_reported_at_NOT_verified_provider_clock"],
                "guaranteed_downward_logratio_magnitude":
                    a["lower"]-b["upper"],
            })
        if b["lower"]>a["upper"]+EPS:
            up.append({
                "earlier":a["source_reported_at_NOT_verified_provider_clock"],
                "later":b["source_reported_at_NOT_verified_provider_clock"],
                "guaranteed_upward_logratio_magnitude":
                    b["lower"]-a["upper"],
            })
    valleys=[]
    peaks=[]
    for a,b,c in zip(samples,samples[1:],samples[2:]):
        if a["lower"]>b["upper"]+EPS and c["lower"]>b["upper"]+EPS:
            valleys.append({
                "times":[x["source_reported_at_NOT_verified_provider_clock"]
                         for x in (a,b,c)],
                "minimum_required_drop_in_logratio":
                    a["lower"]-b["upper"],
                "minimum_required_rebound_in_logratio":
                    c["lower"]-b["upper"],
                "minimum_two_step_total_logratio_variation":
                    a["lower"]+c["lower"]-2*b["upper"],
            })
        if b["lower"]>a["upper"]+EPS and b["lower"]>c["upper"]+EPS:
            peaks.append({
                "times":[x["source_reported_at_NOT_verified_provider_clock"]
                         for x in (a,b,c)],
                "minimum_required_rise_in_logratio":
                    b["lower"]-a["upper"],
                "minimum_required_fall_in_logratio":
                    b["lower"]-c["upper"],
                "minimum_two_step_total_logratio_variation":
                    2*b["lower"]-a["upper"]-c["upper"],
            })
    mono_inc=len(down)==0
    mono_dec=len(up)==0
    return {
        "n_times_with_both_horses_originally_reported":len(samples),
        "nondecreasing_latent_path_feasible":mono_inc,
        "nonincreasing_latent_path_feasible":mono_dec,
        "strict_global_nonmonotonicity_mathematically_required":
            not mono_inc and not mono_dec,
        "first_forced_decrease_witness":down[0] if down else None,
        "first_forced_increase_witness":up[0] if up else None,
        "consecutive_strict_valley_witnesses":valleys,
        "consecutive_strict_peak_witnesses":peaks,
        "quantization_is_assumed_not_JRA_mechanism_verified":True,
        "market_nonmonotonicity_does_not_identify_social_feedback":True,
    }


def _quintic(u):
    if not 0<=u<=1:
        raise ValueError("HOLD_QUINTIC_QUERY_OUTSIDE_SEGMENT")
    return u*u*u*(10+u*(-15+6*u))


def _smooth_value(times,centers,t):
    """C2 interpolation with zero velocity and acceleration at knots."""
    if len(times)!=len(centers) or len(times)<3:
        raise ValueError("HOLD_SMOOTH_SOURCE_KNOTS")
    if t<=times[0]:
        return centers[0]
    if t>=times[-1]:
        return centers[-1]
    for j in range(len(times)-1):
        if times[j]<=t<=times[j+1]:
            h=times[j+1]-times[j]
            if h<=0:
                raise ValueError("HOLD_SMOOTH_SOURCE_INTERVAL_NONPOSITIVE")
            u=(t-times[j])/h
            return centers[j]+(centers[j+1]-centers[j])*_quintic(u)
    raise ValueError("HOLD_SMOOTH_INTERVAL_NOT_COVERED")


def mechanism_nonidentification_example(samples):
    """Algebraic exact interpolation only. DO NOT interpret fit as evidence.

    - smooth C2 function through each value, arbitrary signed drift
    - step process with jump at each reported time
    - feedback delta_t=phi*delta_{t-1}+innovation_t, for any fixed phi.
      Innovations are unrestricted, so phi is NOT identified.
    """
    if len(samples)<3:
        raise ValueError("HOLD_NONIDENTIFICATION_NEEDS_MULTIPLE_POINTS")
    first=_time(samples[0]["source_reported_at_NOT_verified_provider_clock"])
    times=[(_time(s["source_reported_at_NOT_verified_provider_clock"])-
           first).total_seconds()/3600 for s in samples]
    centers=[s["displayed_center"] for s in samples]
    if any(times[i]>=times[i+1] for i in range(len(times)-1)):
        raise ValueError("HOLD_NONIDENTIFICATION_TIME_ORDER")
    smooth=[_smooth_value(times,centers,t) for t in times]
    smooth_error=max(abs(x-y) for x,y in zip(smooth,centers))
    # Piecewise constant at reported boundaries; no claim that any jump
    # actually happened at the editorial clock.
    step_error=max(abs(centers[k]-centers[k])
                   for k in range(len(centers)))
    diffs=[centers[k]-centers[k-1] for k in range(1,len(centers))]
    feedback={}
    for phi in FEEDBACK_PHI_EXAMPLES:
        innovations=[d if k==0 else d-phi*diffs[k-1]
                     for k,d in enumerate(diffs)]
        reconstructed=[centers[0]]
        previous_delta=0.
        for epsilon in innovations:
            delta=phi*previous_delta+epsilon
            reconstructed.append(reconstructed[-1]+delta)
            previous_delta=delta
        feedback[str(phi)]={
            "max_error_at_editorial_points":
                max(abs(a-b) for a,b in zip(reconstructed,centers)),
            "artificial_innovation_values_NOT_observed_bets":innovations,
            "feedback_parameter_is_ARBITRARY_not_calibrated":True,
        }
    if (smooth_error>EPS or step_error>EPS or
            any(v["max_error_at_editorial_points"]>EPS
                for v in feedback.values())):
        raise ValueError("HOLD_THREE_CONSTRUCTIONS_DID_NOT_REPRODUCE_QUOTES")
    return {
        "n_actual_displayed_points_not_independent_races":len(samples),
        "smooth_time_varying_drift_C2_interpolant":{
            "max_error_at_editorial_points":smooth_error,
            "zero_first_and_second_derivatives_at_knots":True,
            "monotonic_drift_NOT_required":True,
        },
        "discrete_exogenous_step_construction":{
            "max_error_at_editorial_points":step_error,
            "jumps_at_reported_points_are_illustrative_not_measured":True,
        },
        "feedback_AR1_with_unrestricted_exogenous_innovations":feedback,
        "all_three_structures_fit_at_observation_points_not_model_comparison":
            True,
        "observational_equivalence_without_restrictions_on_innovations":True,
        "no_causal_feedback_or_event_inference_from_exact_fits":True,
    }


def audit():
    records,sha=_blog_reported_quotes()
    if sha!=PINNED_BLOG_DECLARED_PARTIAL_SHA256:
        raise ValueError("HOLD_PR38_ORIGINAL_BLOG_SOURCE_DRIFT")
    allids=sorted(set().union(*(set(r["prices"]) for r in records)))
    if allids!=[1,3,7,11,17] or [len(r["prices"]) for r in records]!=[
            4,5,5,5,5]:
        raise ValueError("HOLD_PARTIAL_ORIGINAL_BLOG_COHORT_CHANGED")
    pairs=list(combinations(allids,2))
    schemes={}
    for scheme in QUANTIZATION_SCHEMES:
        rows=[]
        for i,j in pairs:
            samples=_pair_samples(records,i,j,scheme)
            certificate=monotonicity_certificate(samples)
            rows.append({
                "pair":[i,j],
                "source_horse_observation_count":len(samples),
                **certificate,
            })
        schemes[scheme]={
            "n_tested_pairs_not_independent_races":len(pairs),
            "pairs_necessarily_nonmonotone_under_assumed_quantization":[
                x["pair"] for x in rows if x[
                    "strict_global_nonmonotonicity_mathematically_required"]],
            "count_pairs_necessarily_nonmonotone":sum(
                x["strict_global_nonmonotonicity_mathematically_required"]
                for x in rows),
            "all_pairwise_interval_feasibility_results":rows,
        }
    triple={}
    full=[]
    for scheme in QUANTIZATION_SCHEMES:
        samples=_pair_samples(records,*EXAMPLE_HORSES,scheme)
        interesting=[s for s in samples if
                     s["source_reported_at_NOT_verified_provider_clock"][11:16]
                     in EXAMPLE_TIMES]
        if [s["source_reported_at_NOT_verified_provider_clock"][11:16]
            for s in interesting]!=list(EXAMPLE_TIMES):
            raise ValueError("HOLD_EXAMPLE_V_TRIPLE_SOURCE_CHANGED")
        cert=monotonicity_certificate(interesting)
        valleys=cert["consecutive_strict_valley_witnesses"]
        if len(valleys)!=1:
            raise ValueError("HOLD_EXAMPLE_V_NOT_ROBUST_TO_ASSUMED_ROUNDING")
        bound=valleys[0]
        hours_down=(
            _time(interesting[1]["source_reported_at_NOT_verified_provider_clock"])-
            _time(interesting[0]["source_reported_at_NOT_verified_provider_clock"])
        ).total_seconds()/3600.
        hours_up=(
            _time(interesting[2]["source_reported_at_NOT_verified_provider_clock"])-
            _time(interesting[1]["source_reported_at_NOT_verified_provider_clock"])
        ).total_seconds()/3600.
        triple[scheme]={
            "reported_times":list(EXAMPLE_TIMES),
            "latent_log_ratio_intervals":[
                {"low":v["lower"],"high":v["upper"]}
                for v in interesting],
            "minimum_guaranteed_decline_logratio":
                bound["minimum_required_drop_in_logratio"],
            "minimum_guaranteed_rebound_logratio":
                bound["minimum_required_rebound_in_logratio"],
            "minimum_two_interval_total_logratio_variation":
                bound["minimum_two_step_total_logratio_variation"],
            "min_necessary_decline_logratio_per_reported_hour_conditional":
                bound["minimum_required_drop_in_logratio"]/hours_down,
            "min_necessary_rebound_logratio_per_reported_hour_conditional":
                bound["minimum_required_rebound_in_logratio"]/hours_up,
            "reported_elapsed_hours_not_true_provider_market_clock":[
                hours_down,hours_up],
            "no_intrainterval_behavior_observed":True,
        }
        full.append((scheme,samples))
    example=mechanism_nonidentification_example(full[-1][1])
    return {
        "status":STATUS,
        "source_url":BLOG_URL,
        "original_PR38_blog_declared_SHA_not_receipt":sha,
        "five_reported_partial_timepoints_not_tote_transaction_times":5,
        "distinct_reported_horse_ids":allids,
        "ten_originally_reported_horse_pairs_not_independent_trials":len(pairs),
        "reported_horses_editorially_selected_not_random_field_sample":True,
        "all_17_runner_prevalence_of_nonmonotonicity_not_estimable":True,
        "relative_price_ratios_do_not_require_missing_horse_market_normalizer":True,
        "quantization_sensitivity":schemes,
        "strict_v_shape_witness_horses_1_and_7":triple,
        "three_observationally_equivalent_mechanism_constructions":example,
        "strict_monotone_drift_rejected_but_smooth_nonmonotone_possible":True,
        "external_news_event_and_bettor_feedback_not_separated":True,
        "actual_bettor_volume_or_independently_time_attested_JRA_source":False,
        "original_race_outcome_or_wager_payout_used":False,
        "new_remote_SHA_verified_prospective_trials":0,
        "original_PR37_eleven_models_and_sealed_v31_unchanged":True,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path(
        "tmp/tenno-quantization-nonmonotone-mechanism-nonidentification.json"))
    opts=parser.parse_args()
    result=audit()
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,
                                      allow_nan=False)+"\n",encoding="utf-8")
    for scheme,d in result["quantization_sensitivity"].items():
        print("PARTIAL_QUOTE_NONMONOTONE_HORSE_PAIRS",scheme,
              d["count_pairs_necessarily_nonmonotone"])
    for scheme,v in result["strict_v_shape_witness_horses_1_and_7"].items():
        print("TENNO_ROUNDING_BOUND_V_WITNESS",scheme,
              v["minimum_guaranteed_decline_logratio"],
              v["minimum_guaranteed_rebound_logratio"])
    print("ZERO_CAUSAL_SELF_EXCITATION_IDENTIFICATION_AND_PROSPECTIVE_TRIALS",True)


if __name__=="__main__":
    main()
