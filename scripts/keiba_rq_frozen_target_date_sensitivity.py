#!/usr/bin/env python3
"""Same frozen RQ target records: relative vs ABSOLUTE first GPS predictive gain.

Previously reported 'individual memory' benefits on the contemporaneous
race-relative target must not be interpreted as future absolute-speed
predictability. This audit is deliberately restricted to the SAME 35/44
and 20/22 original future record populations, with the same previous
rider-source eligibility. It NEVER selects different scored horses after
seeing gains, never uses today's peers as a predictive input to the
absolute model, and never serializes horse IDs or individual timings.

Leave-one-FUTURE-meeting-date deletion and date-block-resampling are
retrospective influence diagnostics only. They are NOT preregistered
held-out biological replications, population 95% CIs, horse genetic
effects, actual jockey changes, market price effects, or p-values.
"""
from __future__ import annotations

from collections import defaultdict
from math import sqrt, isfinite
from statistics import mean
import random

from ecology_rq_forward_alternative_history import (
    matched_source_rows_private, _paired_score,
)
from keiba_rq_absolute_first_section_forward import (
    _setup, _forecasts, _paired_equal_horse_rmse
)

STATUS="RETROSPECTIVE_FIXED_TARGET_DATE_CLUSTER_SENSITIVITY_ONLY"
MIN_HORSES=20
MIN_ROWS=20
MIN_FUTURE_DATES=6


def _key(r):
    return str(r["day"]), str(r["horse_id"])


def _horse_weighted_errors(group, endpoint):
    if not group:
        raise ValueError("HOLD_NO_FROZEN_FUTURE_ROWS")
    by_horse=defaultdict(list)
    for r in group:
        y,a,b=r[endpoint]
        if not all(isfinite(x) for x in (y,a,b)):
            raise ValueError("HOLD_NONFINITE_FUTURE_ENDPOINT")
        by_horse[r["horse_id"]].append(((y-a)**2,(y-b)**2))
    a=sqrt(mean(mean(v[0] for v in arr) for arr in by_horse.values()))
    b=sqrt(mean(mean(v[1] for v in arr) for arr in by_horse.values()))
    return {"own_rmse":a, "other_rmse":b,
            "other_minus_own_rmse":b-a,
            "n_horses":len(by_horse),
            "n_future_rows":len(group),
            "n_dates":len({r["day"] for r in group})}


def _date_sensitivity(scored, endpoint, *, draws, seed):
    dates=sorted({r["day"] for r in scored})
    if len(dates)<MIN_FUTURE_DATES:
        raise ValueError("HOLD_TOO_FEW_FUTURE_DATE_CLUSTERS")
    full=_horse_weighted_errors(scored,endpoint)
    deletions=[]
    for day in dates:
        subset=[r for r in scored if r["day"]!=day]
        value=_horse_weighted_errors(subset,endpoint)
        admissible=(value["n_horses"]>=MIN_HORSES and
                    value["n_future_rows"]>=MIN_ROWS and
                    value["n_dates"]>=MIN_FUTURE_DATES)
        deletions.append((value["other_minus_own_rmse"],admissible))
    valid=[v for v,yes in deletions if yes]
    # A failed date-removal eligibility gate is NOT evidence of
    # no individual-history effect. Record every rejected deletion.
    rng=random.Random(seed)
    group_by_date={d:[r for r in scored if r["day"]==d] for d in dates}
    simulated=[]
    for _ in range(draws):
        sampled=[row for d in rng.choices(dates,k=len(dates))
                 for row in group_by_date[d]]
        # Future DATE is sampled as a whole, preserving the within-date
        # horse/observation clusters and the paired outcome comparison.
        simulated.append(_horse_weighted_errors(
            sampled,endpoint)["other_minus_own_rmse"])
    simulated.sort()
    q=lambda p:simulated[int((len(simulated)-1)*p)]
    return {
       "status":(
           "EXPLORATORY_DATE_DELETION_MEETS_OLD_SUPPORT_THRESHOLDS"
           if len(valid)==len(dates) else
           "HOLD_AT_LEAST_ONE_DATE_DELETION_BELOW_OLD_SUPPORT_THRESHOLDS"),
       "full_equal_horse_RMSE":full,
       "attempted_future_date_deletions":len(dates),
       "valid_deletions_original_minimum_evidence_support":len(valid),
       "HOLD_deletions_below_original_threshold":len(dates)-len(valid),
       "valid_deletion_difference_min_seconds":min(valid) if valid else None,
       "valid_deletion_difference_max_seconds":max(valid) if valid else None,
       "valid_deletions_positive_other_minus_own":sum(x>0 for x in valid),
       "valid_deletions_negative_other_minus_own":sum(x<0 for x in valid),
       "historical_date_block_resamplings":draws,
       "simulated_other_minus_own_q05_q50_q95":[q(.05),q(.5),q(.95)],
       "fraction_resampled_date_sets_with_positive_own_history_gain":
           sum(x>0 for x in simulated)/draws,
       "these_are_not_future_meeting_outcomes_or_a_population_CI":True,
       "never_drop_HOLD_days_silently":True,
       "full_denominator_not_changed_between_predictors":True,
    }


def audit(timed,original,*,strict_class=False,seed=20261027,draws=399):
    if (type(strict_class) is not bool or type(seed) is not int
            or type(draws) is not int or not (99<=draws<=2000)):
        raise ValueError("HOLD_UNREGISTERED_DATE_SENSITIVITY_PLAN")
    # Use EXACT previously fixed prospective-in-date target eligibility,
    # determined by the source's declared new rider ID and source context.
    candidates,_=matched_source_rows_private(
        timed,strict_class=strict_class)
    ref=_paired_score(candidates,"context_prediction")
    base={
        "status":STATUS,
        "endpoint_comparison":"historical_relative_vs_absolute_same_scored_eligible_horses",
        "same_original_future_horses_and_dates_for_both_outcomes":True,
        "relative_outcome_depends_on_current_future_race_peer_values":True,
        "absolute_target_outcome_is_focal_horse_seconds_only":True,
        "no_race_future_peer_outcomes_used_as_absolute_features":True,
        "same_original_main_rider_label_and_shrinkage_design":True,
        "jockey_source_id_is_not_independent_verified_actual_rider":True,
        "not_a_preregistered_prospective_biological_validation":True,
        "original_source_roster_edition_drift_still_HOLD":True,
        "raw_horse_rider_trainer_IDs_and_GPS_and_dates_not_exported":True,
        "no_real_RQ_or_JRA_betting_odds_used":True,
    }
    if ref["status"].startswith("HOLD_"):
        return {**base,"status":"HOLD_ORIGINAL_SOURCE_FROZEN_TARGET_NOT_SCORABLE",
                "reference_eligible_counts":{k:ref.get(k) for k in (
                    "matched_chronological_future_source_rows",
                    "distinct_original_HORSES_IDs",
                    "distinct_future_original_source_dates")}}
    selected=[r for r in candidates if r["context_prediction"] is not None]
    actual,pool,by_race,abs_eligibility=_setup(timed,original,strict_class)
    if actual is None:
        raise ValueError("HOLD_ABSOLUTE_TARGET_ELIGIBILITY_CHANGED")
    qown,qother=_forecasts(timed,actual,pool,pool,strict_class)
    rel_by_key={_key(r):r for r in selected}
    abs_by_key={_key(r):(r,own,other) for r,own,other
                in zip(actual,qown,qother)}
    if (len(rel_by_key)!=len(selected) or
        len(abs_by_key)!=len(actual) or
        set(rel_by_key)!=set(abs_by_key) or
        len(selected)!=ref["matched_chronological_future_source_rows"]):
        raise ValueError("HOLD_DIFFERENT_FUTURE_TARGETS_RELATIVE_VS_ABSOLUTE")
    scored=[]
    for key in sorted(rel_by_key):
        r=rel_by_key[key]
        a,own_abs,other_abs=abs_by_key[key]
        scored.append({
           "horse_id":r["horse_id"],"day":str(r["day"]),
           "relative":(float(r["observed"]),
                       float(r["horse_prediction"]),
                       float(r["context_prediction"])),
           "absolute":(float(a["absolute_seconds"]),
                       float(own_abs),float(other_abs)),
        })
    relative=_date_sensitivity(scored,"relative",draws=draws,seed=seed)
    absolute=_date_sensitivity(scored,"absolute",draws=draws,seed=seed)
    # Fail closed if the entire historical denominator/scoring design
    # no longer matches the earlier fixed main metric.
    if (abs(relative["full_equal_horse_RMSE"]["own_rmse"]-
            ref["equal_HORSES_weighted_past_horse_RMSE_sec"])>1e-11 or
        abs(relative["full_equal_horse_RMSE"]["other_rmse"]-
            ref["equal_HORSES_weighted_past_other_horse_baseline_RMSE_sec"])>1e-11):
        raise AssertionError("HOLD_ORIGINAL_RELATIVE_SCORE_CHANGED")
    check_a=_paired_equal_horse_rmse(actual,qown)
    check_b=_paired_equal_horse_rmse(actual,qother)
    if (abs(absolute["full_equal_horse_RMSE"]["own_rmse"]-check_a)>1e-11
            or abs(absolute["full_equal_horse_RMSE"]["other_rmse"]-check_b)>1e-11):
        raise AssertionError("HOLD_ABSOLUTE_SCORE_CHANGED")
    return {
       **base,
       "frozen_target_n_horses":len({r["horse_id"] for r in scored}),
       "frozen_target_n_future_observations":len(scored),
       "frozen_target_n_future_meeting_dates":
           len({r["day"] for r in scored}),
       "additional_original_class_matching":strict_class,
       "relative":relative,"absolute":absolute,
       "primary_interpretation":"Different targets and source editions; evaluate within each endpoint separately",
       "no_primary_reanalysis_claim_of_market_prediction_or_caused_horse_personality":True,
    }
