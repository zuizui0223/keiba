#!/usr/bin/env python3
"""A second source-locked race: real 3-time full-field WIN price curvature.

The original 2026-10-12 Kyoto R8 archived 11-horse WIN quotes at
12:21, 13:26, 13:44 (and all 55 WIDE pairs at two moments) have locked
Git-blob SHA and publication/reception clocks in existing research.
This module takes those three WIN vectors ONLY, and uses PR39's exact
interval-valued monotonicity test to check ALL 55 distinct horse pairs.

Comparison: PR39's 2026-10-31 Tenno Sho edited article partial 5-horse
path. These are TWO races, not 55+10 independent observations; they have
different provenance/clock quality and are not pooled for a p value.

Three illustrative display quantization assumptions:
  nearest tenth [d-.05,d+.05]; truncation [d,d+.10];
  union (conservative) [d-.05,d+.10].
None proves the actual JRA display convention. A monotonicity rejection
means only that every permitted latent price-ratio sequence must turn
direction in the source timestamps, NOT a discontinuity/criticality.

New exact deterministic frontier: for samples at times t_i, their
interval-valued z_i=log(o_a/o_b) admit a continuous piecewise-linear
interpolation with max absolute slope <=L iff
  L >= max_{i<j} max(0, low_i-high_j, low_j-high_i)/(t_j-t_i).
Return this minimum L and a constructive Lipschitz interpolation through
feasible latent values. This rate is conditional on SOURCE-REPORTED quote
clocks, not true bettor transaction times or calibrated market velocity.

In addition, an 11-horse JOINT C2 smoothstep interpolation passes through
all actual displayed quote centers exactly, with each normalized M0
market index positive and adding to 1. It is a mathematical existence
witness: even the whole observed field does NOT REQUIRE discrete market
jumps, exogenous shocks or self-excited feedback. Neither null is fitted
to independent future target quotes nor can establish race win probabilities.

NEVER read official finishing order, payouts, external events, stakes,
actual horse GPS, or newly collected market q2. Frozen PR37 prospective
11 candidate models, Kikka M0-M2, v3.1 and main are untouched.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from itertools import combinations
from pathlib import Path

from odds_r8_real_three_time_market import collect_pre_race_price_panels
from keiba_tenno_quantized_nonmonotone_identification import (
    QUANTIZATION_SCHEMES, _pair_samples, monotonicity_certificate,
    _blog_reported_quotes, _quintic, _time, EPS,
)

ROOT=Path(__file__).resolve().parents[1]
STATUS="R8_SOURCE_LOCKED_FULL_WIN_THREE_POINTS_TWO_RACE_NONMONOTONE_DESCRIPTIVE"
R8_RACE_ID="2608040508"
R8_EXPECTED_CLOCKS=("2026-10-12T12:21:00+09:00",
                    "2026-10-12T13:26:00+09:00",
                    "2026-10-12T13:44:00+09:00")
R8_EXPECTED_FIELD=list(range(1,12))
ILLUSTRATIVE_MAX_RATE_LIMITS_PER_H=(0.,0.10,0.50,1.,2.,3.)


def source_locked_r8_records(root=ROOT):
    """Source-locked archive, no official JRA results or payoff labels read."""
    panels,_,_,post,_=collect_pre_race_price_panels(root)
    if (len(panels)!=3 or
            tuple(p["provider_published_quote_minute"]
                  for p in panels)!=R8_EXPECTED_CLOCKS):
        raise ValueError("HOLD_R8_SOURCE_TIMEPOINTS_CHANGED")
    post_at=_time(post)
    records=[]
    for p in panels:
        if (p["n_horses"]!=11 or
                sorted(p["win_prices"])!=R8_EXPECTED_FIELD or
                not _time(p["provider_published_quote_minute"])<
                     _time(p["observed_at"])<post_at):
            raise ValueError("HOLD_R8_ORIGINAL_FULL_ROSTER_OR_RECEIPT_CLOCK")
        prices=p["win_prices"]
        if (any(type(v) not in (float,int) or
                    not math.isfinite(v) or v<=1 for v in prices.values())):
            raise ValueError("HOLD_R8_SOURCE_INVALID_ODDS")
        records.append({
            "source_reported_jst":p["provider_published_quote_minute"],
            "original_local_receipt_at":p["observed_at"],
            "prices":prices,
            "original_11_horses_full_field":True,
            "archived_provider_family":"Yahoo/SportsNavi",
            "source_bytes_Git_blob_SHA_verified_by_original_module":True,
        })
    return records


def minimum_continuous_logratio_rate(samples):
    """Sharp minimum L for interval-valued pointwise L-Lipschitz feasibility.

    A witness is constructed by max_j (lower_j-L|t-t_j|). If all pair
    interval distances <=L time gap, that L-Lipschitz function lies inside
    each sample's allowed interval. Small 1e-10 buffer is ONLY numerical.
    """
    if not isinstance(samples,list) or len(samples)<3:
        raise ValueError("HOLD_LIPSCHITZ_REQUIRES_THREE_REAL_SAMPLE_TIMES")
    base=_time(samples[0]["source_reported_at_NOT_verified_provider_clock"])
    hours=[(_time(s["source_reported_at_NOT_verified_provider_clock"])-
            base).total_seconds()/3600 for s in samples]
    if any(hours[i]>=hours[i+1] for i in range(len(hours)-1)):
        raise ValueError("HOLD_LIPSCHITZ_REPORT_CLOCK_NOT_STRICTLY_ORDERED")
    low=[s["lower"] for s in samples]
    high=[s["upper"] for s in samples]
    if (any(type(x) not in (int,float) or not math.isfinite(x)
            for x in low+high) or any(a>b for a,b in zip(low,high))):
        raise ValueError("HOLD_LIPSCHITZ_INVALID_QUOTE_INTERVAL")
    constraints=[]
    bound=0.
    for i,j in combinations(range(len(samples)),2):
        d=hours[j]-hours[i]
        separation=max(0.,low[i]-high[j],low[j]-high[i])
        value=separation/d
        constraints.append({"earlier":i,"later":j,
                            "min_log_ratio_change":separation,
                            "minimum_conditional_rate_per_reported_hour":value})
        bound=max(bound,value)
    witness_L=bound+1e-10
    values=[max(low[j]-witness_L*abs(t-s) for j,s in enumerate(hours))
            for t in hours]
    if (any(not a-1e-8<=v<=b+1e-8
            for a,b,v in zip(low,high,values)) or
            any(abs(values[i]-values[j]) >
                    witness_L*abs(hours[i]-hours[j])+1e-8
                for i,j in combinations(range(len(samples)),2))):
        raise ValueError("HOLD_LIPSCHITZ_CERTIFICATE_NOT_FEASIBLE")
    strongest=max(constraints,
                  key=lambda x:x["minimum_conditional_rate_per_reported_hour"])
    return {
        "minimal_conditional_max_abs_logratio_speed_per_reported_hour":bound,
        "tightest_two_timepoint_constraint":strongest,
        "piecewise_linear_continuous_interpolant_feasible":True,
        "latent_values_constructively_feasible":values,
        "reported_hour_coordinates":hours,
        "witness_numeric_slack_rate_added":1e-10,
        "rate_is_not_true_tote_transaction_speed":True,
        "smooth_movement_suffices_without_discontinuous_jump":True,
    }


def full_field_C2_smooth_construct(records):
    """One coherent full-horse smooth price path, NOT pairwise inconsistent.

    At the exact three actual SOURCE-REPORTED quote knots, price arrays
    are the displayed values. For intermediate t, log odds of EACH
    original horse is smoothly interpolated using C2 quintic smoothstep.
    Every implied M0 q(t) is positive and sums to 1. A C2 path can pass
    through any positive discrete price quotes: this is NOT a fit test.
    """
    if len(records)!=3:
        raise ValueError("HOLD_JOINT_SMOOTH_REQUIRES_R8_THREE_POINTS")
    ids=sorted(records[0]["prices"])
    if ids!=R8_EXPECTED_FIELD or any(sorted(r["prices"])!=ids
                                     for r in records):
        raise ValueError("HOLD_JOINT_SMOOTH_INCOMPLETE_ROSTER")
    base=_time(records[0]["source_reported_jst"])
    t=[(_time(z["source_reported_jst"])-base).total_seconds()/3600
       for z in records]
    def at(h):
        if h<=t[0]:
            lg=[math.log(records[0]["prices"][i]) for i in ids]
        elif h>=t[-1]:
            lg=[math.log(records[-1]["prices"][i]) for i in ids]
        else:
            k=0 if h<=t[1] else 1
            u=(h-t[k])/(t[k+1]-t[k])
            weight=_quintic(u)
            lg=[(1-weight)*math.log(records[k]["prices"][i])+
                 weight*math.log(records[k+1]["prices"][i])
                for i in ids]
        odds=[math.exp(z) for z in lg]
        inverses=[1/o for o in odds]
        mass=sum(inverses)
        return odds,[a/mass for a in inverses]
    knots=[at(h) for h in t]
    intermediate=[at((t[i]+t[i+1])/2) for i in range(2)]
    err=max(abs(knots[k][0][j]-records[k]["prices"][horse])
            for k in range(3) for j,horse in enumerate(ids))
    if err>1e-10 or any(not math.isclose(sum(q),1,abs_tol=1e-12)
                        or any(v<=0 for v in q)
                        for _,q in knots+intermediate):
        raise ValueError("HOLD_C2_FULL_FIELD_INTERPOLANT_NOT_COHERENT")
    return {
        "original_distinct_horses":len(ids),
        "original_reported_knot_count":3,
        "full_source_displayed_WIN_prices_exactly_interpolated_max_error":err,
        "same_joint_all_horses_C2_price_and_M0_simplex_path_exists":True,
        "at_knots_price_indices_mass":[sum(z[1]) for z in knots],
        "at_segment_midpoints_price_indices_mass":[sum(z[1]) for z in intermediate],
        "not_an_empirically_validated_smooth_stochastic_market_model":True,
        "no_discrete_jump_or_herding_necessarily_implied":True,
    }


def _audit_cohort(records,ids,*,kind):
    by_scheme={}
    for scheme in QUANTIZATION_SCHEMES:
        rows=[]
        for i,j in combinations(ids,2):
            samples=_pair_samples(records,i,j,scheme)
            cert=monotonicity_certificate(samples)
            frontier=minimum_continuous_logratio_rate(samples)
            rows.append({
                "horse_numbers":[i,j],
                "n_original_price_sample_points":len(samples),
                "nonmonotone_strict_under_assumed_display_error":
                    cert["strict_global_nonmonotonicity_mathematically_required"],
                "monotonicity_witness":cert,
                "minimum_continuous_rate_witness":frontier,
            })
        ranked=sorted(rows,
                      key=lambda x:-x["minimum_continuous_rate_witness"][
                        "minimal_conditional_max_abs_logratio_speed_per_reported_hour"])
        nonmono=[x["horse_numbers"] for x in rows if x[
            "nonmonotone_strict_under_assumed_display_error"]]
        speeds=[x["minimum_continuous_rate_witness"][
            "minimal_conditional_max_abs_logratio_speed_per_reported_hour"]
                for x in rows]
        n_blocked={str(rate):sum(v>rate+EPS for v in speeds)
                   for rate in ILLUSTRATIVE_MAX_RATE_LIMITS_PER_H}
        if any(not x["minimum_continuous_rate_witness"][
                 "piecewise_linear_continuous_interpolant_feasible"]
                for x in rows):
            raise ValueError("HOLD_NO_CONTINUOUS_PRICE_PATH_CERTIFICATE")
        by_scheme[scheme]={
            "reported_pair_count_dependent_within_one_race":len(rows),
            "strict_nonmonotone_pair_count":len(nonmono),
            "nonmonotone_horse_pairs":nonmono,
            "largest_minimum_continuous_logratio_speed_per_reported_hour":
                ranked[0]["minimum_continuous_rate_witness"][
                    "minimal_conditional_max_abs_logratio_speed_per_reported_hour"],
            "pair_with_largest_required_continuous_rate":
                ranked[0]["horse_numbers"],
            "pairwise_continuous_speed_caps_hypothetical_not_calibrated":
                n_blocked,
            "all_pairwise_interval_rate_and_monotonicity_results":rows,
            "all_admit_continuous_movement_with_sufficient_speed":True,
        }
    return {
        "source_kind":kind,
        "actual_race_count":1,
        "horse_numbers_in_source":ids,
        "sample_count":[len([x for x in records if i in x["prices"]])
                        for i in ids],
        "by_quantization_assumption":by_scheme,
    }


def audit(root=ROOT):
    kyoto=source_locked_r8_records(root)
    partial,original_sha=_blog_reported_quotes()
    kyoto_ids=sorted(kyoto[0]["prices"])
    partial_ids=sorted(set().union(*(set(x["prices"]) for x in partial)))
    r8=_audit_cohort(kyoto,kyoto_ids,
                     kind="SOURCE_LOCKED_REAL_THREE_TIME_FULL_11_HORSE_QUOTE")
    tenno=_audit_cohort(partial,partial_ids,
                        kind="EDITORIALLY_REPORTED_FIVE_PARTIAL_TIMEPOINTS")
    c2=full_field_C2_smooth_construct(kyoto)
    actual_r8_sources=(
        "data/2026-10-12/kyoto_08.json",
        "data/2026-10-12/remaining-snapshots/r8_tfw.json",
        "data/2026-10-12/r8_markets_latest.json",
    )
    return {
        "status":STATUS,
        "source_locked_r8_source_files":list(actual_r8_sources),
        "source_race_id":R8_RACE_ID,
        "r8_original_price_publication_timestamps":list(R8_EXPECTED_CLOCKS),
        "R8_original_source_full_field_horse_count":len(kyoto_ids),
        "R8_original_source_full_field_price_points":len(kyoto),
        "R8_source_sha_verified_by_existing_collect_pre_race_price_panels":True,
        "R8_one_original_race_not_55_independent_replicates":True,
        "tenno_PR38_same_reported_partial_values_not_new_scraped_snapshots":True,
        "tenno_original_blog_declared_sha_not_authenticated_source_receipt":
            original_sha,
        "two_distinct_source_races_not_pooled_for_p_value":2,
        "R8_and_tenno_have_different_original_source_clock_provenance":True,
        "archived_kyoto_R8":r8,
        "editorial_tenno_top_five_only":tenno,
        "R8_joint_full_horse_continuous_C2_counterexample":c2,
        "original_JRA_race_outcome_or_betting_payout_read":False,
        "real_bettor_stakes_or_an_independent_GPS_horse_skill_used":False,
        "no_real_exogenous_news_or_herding_inferred_from_curvature":True,
        "independently_new_prospective_market_q2_trials":0,
        "PR37_original_eleven_models_and_sealed_v31_unchanged":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=Path(
        "tmp/kyotoR8-vs-tenno-quantized-nonmonotone-rate-null.json"))
    a=p.parse_args()
    out=audit()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2,
                                   allow_nan=False)+"\n",encoding="utf-8")
    for field in ("archived_kyoto_R8","editorial_tenno_top_five_only"):
        cohort=out[field]
        for scheme,sub in cohort["by_quantization_assumption"].items():
            print("CROSSRACE_QUANTIZED_MONOTONICITY",
                  field,scheme,sub["strict_nonmonotone_pair_count"],
                  "/",sub["reported_pair_count_dependent_within_one_race"],
                  "max_min_continuous_rate",
                  sub["largest_minimum_continuous_logratio_speed_per_reported_hour"])
    print("ALL_R8_11_HORSES_ADMIT_A_SINGLE_C2_SMOOTH_FULL_MARKET_PATH",
          out["R8_joint_full_horse_continuous_C2_counterexample"][
              "same_joint_all_horses_C2_price_and_M0_simplex_path_exists"])
    print("ZERO_REAL_HERDING_EVENT_CAUSAL_OR_PROSPECTIVE_VALIDATION",True)


if __name__=="__main__":
    main()
