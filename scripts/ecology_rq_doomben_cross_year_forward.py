#!/usr/bin/env python3
"""2025→2026 genuinely same-HORSES-ID early sectional history test at Doomben.

LOCKED computational test (read docs/ecology-rq-doomben-cross-year-own-vs-other-history-lock.md):
Use previously fixed 23 + 19 Doomben source dates. Train ONLY on
2025 first GPS race-relative timing, evaluate ONLY 2026 original
HORSES-ID returns at the same exact source first marker + race distance.
Compare own 2025 history to zero and to historical OTHER HORSES
at exactly the same source marker/distance; exact original race Class
is a separate sensitivity. If <20 real repeated identities and <20
scored future rows, report HOLD without showing an RMSE gain.

NOT a pre-registered ecological effect, nor H1 ground plasticity,
H2 rival-causal interactions, heritability, aging effects, betting
or an observation of a certified starter/finisher population.

No original horse names, numeric IDs, individual GPS times,
prediction scores or matched animal rows are returned or published.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
from statistics import mean

from ecology_rq_doomben_2025_marker_extension import (
    DATES_2025, PREVIOUS_2026_DATES, LOCKED_DATES,
    FIRST_MARKERS, collect, verify_lock,
)
from ecology_rq_eagle_farm_external_icc import identity_overlap
from ecology_rq_early_pace_repeatability import prepare
from ecology_rq_single_race_id_probe import request_xml
from ecology_rq_thoroughbred_sectional_audit import fetch_official


MIN_HORSES_WITH_YEAR_BRIDGE = 20
MIN_SCORED_2026_OBSERVATIONS = 20
MIN_SOURCE_DATES_EACH_YEAR = 3
MIN_OTHER_ORIGINAL_HORSES_IDS = 3
MIN_GPS_PEERS_IN_RACE = 4
# Already used in our former rider-change/horse-vs-other checks:
FIXED_HISTORY_PSEUDOCOUNT = 2


def context(row: dict, strict_class: bool) -> tuple:
    return (
        round(float(row["first_section_marker"]), 4),
        str(row["official_distance"]),
        str(row["race_class"]) if strict_class else None,
    )


def _scored_rows_private(
    relative:list[dict], marker:float, strict_class:bool,
)->tuple[list[dict],dict]:
    """PRIVATE matches; never include these rows in the returned artifact."""
    hist=defaultdict(list)
    others=defaultdict(list)
    subsequent=[]
    source={"2025":set(),"2026":set()}
    for row in relative:
        if abs(float(row["first_section_marker"])-marker)>1e-6:
            continue
        year=row["day"][:4]
        if year not in source:
            raise ValueError("HOLD_UNEXPECTED_RACING_YEAR_IN_SOURCE")
        key=context(row,strict_class)
        source[year].add(row["day"])
        if year=="2025":
            hist[(row["horse_id"],key)].append(row["relative_early_section_sec"])
            others[key].append((row["horse_id"],row["relative_early_section_sec"]))
        else:
            subsequent.append(row)

    bridge=[]
    for r in subsequent:
        key=context(r,strict_class)
        own=hist.get((r["horse_id"],key),[])
        if own:
            bridge.append(r)
    bridge_ids={r["horse_id"] for r in bridge}

    scored=[]
    no_alternative=0
    for row in bridge:
        key=context(row,strict_class)
        past=hist[(row["horse_id"],key)]
        # Exclude focal HORSES ID from ALL alternative history,
        # not merely the exact source row of the target event.
        other=[v for hid,v in others[key] if hid!=row["horse_id"]]
        other_ids={hid for hid,_ in others[key] if hid!=row["horse_id"]}
        if len(other_ids)<MIN_OTHER_ORIGINAL_HORSES_IDS:
            no_alternative+=1
            continue
        prediction_own=len(past)/(len(past)+FIXED_HISTORY_PSEUDOCOUNT)*mean(past)
        prediction_other=len(other)/(len(other)+FIXED_HISTORY_PSEUDOCOUNT)*mean(other)
        scored.append({
            # Never serialize this list; only aggregate by HORSES ID.
            "horse_id":row["horse_id"],
            "day":row["day"],
            "observed":float(row["relative_early_section_sec"]),
            "own_prediction":prediction_own,
            "other_prediction":prediction_other,
            "zero_prediction":0.,
        })
    support={
        "original_2025_dates_with_positive_timed_GPS_in_this_marker":len(source["2025"]),
        "original_2026_dates_with_positive_timed_GPS_in_this_marker":len(source["2026"]),
        "cross_year_HORSES_IDs_matching_exact_marker_distance_optional_class_BEFORE_other_history_screen":len(bridge_ids),
        "cross_year_2026_positive_GPS_rows_with_exact_2025_own_history":len(bridge),
        "future_rows_lacking_3_historical_OTHER_HORSES_ids_in_same_context":no_alternative,
        "cross_year_horses_scored_against_identical_other_history":len({r["horse_id"] for r in scored}),
        "original_2026_scored_rows":len(scored),
        "all_training_obs_always_prior_source_year_2025":True,
        "no_2026_values_used_to_fit_a_historical_profile":True,
        "other_history_excludes_all_original_focal_HORSES_ID_rows":True,
        "no_original_horse_ID_or_individual_observations_exported":True,
    }
    return scored,support


def _equal_horse_rmse_gain(private_rows:list[dict])->float:
    by_horse=defaultdict(list)
    for r in private_rows:
        by_horse[r["horse_id"]].append(r)
    if not by_horse:
        raise ValueError("HOLD_EMPTY_HORSE_SCORING_POPULATION")
    own=math.sqrt(mean(
        mean((r["observed"]-r["own_prediction"])**2 for r in rr)
        for rr in by_horse.values()
    ))
    other=math.sqrt(mean(
        mean((r["observed"]-r["other_prediction"])**2 for r in rr)
        for rr in by_horse.values()
    ))
    return other-own


def posthoc_delete_one_source_unit(private_rows:list[dict])->dict:
    """Post-hoc influence, NEVER an independent uncertainty interval.

    Delete one original HORSES ID or all future 2026 observations from
    one original meeting date; keep 2025 predictors UNCHANGED. Do not
    tune the shrinkage or the minimum ID/row support thresholds.
    """
    ids=sorted({r["horse_id"] for r in private_rows})
    dates=sorted({r["day"] for r in private_rows})
    result={
        "status":"EXPLORATORY_POSTHOC_YEAR_FORWARD_INFLUENCE_NOT_CI",
        "original_matched_IDs":len(ids),
        "original_2026_scored_dates":len(dates),
        "source_support_threshold_not_relaxed":MIN_HORSES_WITH_YEAR_BRIDGE,
        "no_original_IDs_or_individual_predictions_exported":True,
        "not_an_independent_validation_or_95pct_confidence_interval":True,
    }
    for dimension,categories,selector in (
        ("one_original_HORSES_ID",ids,lambda r,id:r["horse_id"]!=id),
        ("one_2026_source_date",dates,lambda r,date:r["day"]!=date),
    ):
        gains=[]
        held=0
        for key in categories:
            keep=[r for r in private_rows if selector(r,key)]
            if (len(keep)<MIN_SCORED_2026_OBSERVATIONS or
                    len({r["horse_id"] for r in keep})<
                    MIN_HORSES_WITH_YEAR_BRIDGE):
                held+=1
                continue
            gains.append(_equal_horse_rmse_gain(keep))
        result[dimension]={
            "attempted_deletions":len(categories),
            "numerically_and_source_supported_deletions":len(gains),
            "HOLD_due_to_falling_below_fixed_20_ID_or_20_future_row_gate":held,
            "OTHER_minus_OWN_RMSE_gain_min_sec":min(gains) if gains else None,
            "OTHER_minus_OWN_RMSE_gain_max_sec":max(gains) if gains else None,
            "deletions_where_own_2025_history_better":sum(x>0 for x in gains),
            "deletions_where_other_horses_history_better":sum(x<0 for x in gains),
            "not_an_uncertainty_interval":True,
        }
    return result


def score(
    relative:list[dict], *, marker:float, strict_class:bool
)->dict:
    if marker not in FIRST_MARKERS:
        raise ValueError("HOLD_UNAPPROVED_ORIGINAL_GPS_MARKER")
    matches,cover=_scored_rows_private(relative,marker,strict_class)
    base={
        "original_first_section_marker_metres":int(marker),
        "original_race_distance_must_match_exactly_between_years":True,
        "original_race_class_must_match_exactly":strict_class,
        "train_year":2025,"evaluate_year":2026,
        "minimum_real_HORSES_IDs_required":MIN_HORSES_WITH_YEAR_BRIDGE,
        "minimum_scored_2026_rows_required":MIN_SCORED_2026_OBSERVATIONS,
        "minimum_source_dates_per_year":MIN_SOURCE_DATES_EACH_YEAR,
        "other_source_history_minimum_DISTINCT_HORSES_IDs":MIN_OTHER_ORIGINAL_HORSES_IDS,
        "source_support":cover,
        "not_an_age_growth_social_effect_or_independent_confirmation":True,
        "race_relative_GPS_target_uses_measured_contemporaneous_rivals":True,
        "not_a_betting_prediction":True,
        "no_original_horse_ID_animal_rows_or_predictions_exported":True,
    }
    sufficient=(
        cover["cross_year_horses_scored_against_identical_other_history"]
        >= MIN_HORSES_WITH_YEAR_BRIDGE
        and len(matches)>=MIN_SCORED_2026_OBSERVATIONS
        and cover["original_2025_dates_with_positive_timed_GPS_in_this_marker"]
        >=MIN_SOURCE_DATES_EACH_YEAR
        and cover["original_2026_dates_with_positive_timed_GPS_in_this_marker"]
        >=MIN_SOURCE_DATES_EACH_YEAR
    )
    if not sufficient:
        return {
            **base,
            "status":"HOLD_TOO_FEW_YEAR_BRIDGE_HORSES_OR_FUTURE_OUTCOMES",
            "no_RMSE_or_anecdotal_2026_individual_values_published":True,
        }

    by_horse=defaultdict(list)
    for row in matches:
        by_horse[row["horse_id"]].append(row)
    names=("zero_prediction","own_prediction","other_prediction")
    rmse={}
    mae={}
    for name in names:
        rmse[name]=math.sqrt(mean(
            mean((r["observed"]-r[name])**2 for r in rr)
            for rr in by_horse.values()
        ))
        mae[name]=mean(
            mean(abs(r["observed"]-r[name]) for r in rr)
            for rr in by_horse.values()
        )
    return {
        **base,
        "status":"EXPLORATORY_REAL_HORSES_ID_2025_TO_2026_TIMING_PERSISTENCE_ONLY",
        "equal_original_HORSES_ID_weighted_2026_RMSE_seconds":{
            "no_identity_baseline":rmse["zero_prediction"],
            "historical_focal_HORSES_ID":rmse["own_prediction"],
            "historical_OTHER_HORSES_same_marker_and_distance":rmse["other_prediction"],
            "OTHER_minus_OWN_RMSE_gain_positive_own_better":
                rmse["other_prediction"]-rmse["own_prediction"],
            "ZERO_minus_OWN_RMSE_gain_positive_own_better":
                rmse["zero_prediction"]-rmse["own_prediction"],
        },
        "equal_original_HORSES_ID_weighted_2026_MAE_seconds":{
            "zero":mae["zero_prediction"],
            "own":mae["own_prediction"],
            "other":mae["other_prediction"],
        },
        "posthoc_leave_one_horse_and_one_2026_date_out_influence":
            posthoc_delete_one_source_unit(matches),
        "source_design_this_is_NOT_a_valid_cross_year_effect_size":True,
        "no_confidence_interval_or_causal_p_value":True,
    }


def evaluate(
    *, soap=request_xml,gps=fetch_official,
    source_error_mode:str="record_HOLD",
)->dict:
    verify_lock()
    if source_error_mode not in ("record_HOLD","raise"):
        raise ValueError("HOLD_UNAPPROVED_SOURCE_ERROR_MODE")
    raw,source_status=collect(soap=soap,gps=gps,on_error=source_error_mode)
    clean,identity=identity_overlap(raw)
    if not clean:
        prepared=[]
        peer_info={"status":"HOLD_NO_REAL_HORSES_SOURCE_GPS_RECORDS"}
    else:
        prepared,peer_info=prepare(clean,min_race_telemetry=MIN_GPS_PEERS_IN_RACE)

    comparisons={}
    for marker in FIRST_MARKERS:
        for strict,key in ((False,"same_distance"),(True,"same_distance_and_Class")):
            comparisons[f"{int(marker)}m_{key}"]=score(
                prepared,marker=marker,strict_class=strict
            )

    successes=sorted(day for day,info in source_status.items()
        if info["status"]=="OFFICIAL_2025_OR_2026_DOOMBEN_SOURCE_ID_GPS_AUDITED")
    failed=sorted(set(LOCKED_DATES)-set(successes))
    return {
        "status":"POSTHOC_DOOMBEN_YEAR_FORWARD_DATA_SUPPORT_NOT_CAUSAL_H1_H2",
        "original_source": "Racing Queensland public SOAP HORSES ID and original positive first GPS sections",
        "pre_scoring_computational_protocol":"docs/ecology-rq-doomben-cross-year-own-vs-other-history-lock.md",
        "locked_2025_date_count":len(DATES_2025),
        "locked_2026_date_count":len(PREVIOUS_2026_DATES),
        "original_source_dates_successful":successes,
        "original_source_dates_HOLD":failed,
        "original_source_fingerprints_SHA256_only":{
            date:{
                "status":info["status"],
                "meeting_race_GPS_SHA256":info.get(
                    "original_first_party_meeting_race_GPS_source_SHA256"
                ),
                "original_horse_roster_combined_SHA256":info.get(
                    "original_horse_roster_combined_SHA256"
                ),
            } for date,info in source_status.items()
        },
        "identical_source_identity_validation":identity,
        "race_relative_peer_subset_support":peer_info,
        "cross_year_score_by_first_GPS_marker_and_context":comparisons,
        "2025_training_ONLY_and_2026_heldout_ONLY":True,
        "not_a_preregistered_biological_or_developmental_effect":True,
        "not_an_experiment_or_H1_H2_evolutionary_trait":True,
        "actual_2026_starter_finisher_age_and_track_sensor_equivalence_not_verified":True,
        "no_original_HORSES_ID_name_rider_trainer_licence_individual_GPS_or_prediction_output":True,
        "limits":[
            "This tests historical ID-linked race-relative early GPS performance, not full-race speed or individual ground response.",
            "2025 source chronology only enters historical profiles; 2026 source chronology is never used for training, even for later 2026 races.",
            "The same-source training and heldout horses had self-selected race entry, nonrandom trainers and age differences.",
            "First GPS observed peers do not establish the full starter/finisher roster; target is postrace relative to contemporaneous observed rivals.",
            "Identical marker and official race distance do not imply matching original race Class, horse age, weight or jockey unless Class sensitivity permits.",
            "A changed pooled Gaussian ICC from 2025 alone to 2025+2026 does not prove within-horse decline; population composition changes.",
            "Unreturned official source dates remain HOLD; no missing runner records or GPS times are fabricated.",
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--strict-source-errors",action="store_true")
    opts=p.parse_args()
    result=evaluate(source_error_mode=("raise" if opts.strict_source_errors else "record_HOLD"))
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    brief={k:{
        "status":v["status"],
        "source_support":v["source_support"],
        "RMSE_seconds":v.get("equal_original_HORSES_ID_weighted_2026_RMSE_seconds"),
    } for k,v in result["cross_year_score_by_first_GPS_marker_and_context"].items()}
    print(json.dumps({
        "status":result["status"],
        "source_dates_successful":len(result["original_source_dates_successful"]),
        "source_dates_HOLD":result["original_source_dates_HOLD"],
        "comparisons":brief,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
