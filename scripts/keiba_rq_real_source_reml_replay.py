#!/usr/bin/env python3
"""REAL Racing Queensland original-source replay, aggregate-only.

Read the EXISTING 12-date locked Cannon Park cohort via pinned
main scripts. DO NOT reselect dates/markets/horses after seeing results.
Original horse IDs, race IDs, GPS time rows, jockey/trainer names and
SOAP response content remain in memory only; the JSON returns ONLY
counts, official-source SHA256s, model variance summaries and HOLDs.

These source records were published after their races. Therefore
this is RETROSPECTIVE within-source horse-identity/repeatability
validation ONLY, NEVER a true pre-market objective forecast, same
JRA animal, observed live ballot, price threshold or wagering ROI.

Requires pinned main first-party RQ source collectors via PYTHONPATH.
Do not treat the native label/status as proof of true stable biological
personality. The source roster may be revised.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from keiba_source_race_fixed_reml import _helmert, _golden_min
from keiba_rq_within_race_identity_shuffle import identity_history_shuffle
from keiba_rq_absolute_first_section_forward import absolute_first_section_forward_audit
from keiba_rq_frozen_target_date_sensitivity import audit as frozen_future_date_sensitivity
from ecology_rq_2026_calendar_overlap import COHORT, LOCKED_RACE_NUMBERS, validate_cohort
from ecology_rq_cross_venue_identity_support import collect_cannon
from ecology_rq_eagle_farm_external_icc import identity_overlap
from ecology_rq_early_pace_repeatability import prepare
from ecology_rq_rider_switch_consistency import source_timed_panel
from ecology_rq_forward_alternative_history import audit_other_horse_baselines
from ecology_rq_race_fixed_icc import race_fixed_reml
from ecology_rq_single_race_id_probe import request_xml
from ecology_rq_thoroughbred_sectional_audit import fetch_official

SCHEMA="RQ_ORIGINAL_CANNON_12DATE_REAL_SOURCE_REML_REPLAY_V1"
SOURCE_STATUS="SOURCE_CANNON_PARK_IDS_AND_GPS_AUDITED"
DATE_COUNT=12
MIN_ROWS=80
MIN_RACES=12
MIN_DATES=6
MIN_REPEATED=20
MIN_CONTRASTS=50
ARCHIVE_SCHEMA="racing-queensland-original-horse-source-fingerprint-v1"
SOURCE_HASH_MAP={
  "meeting_xml_sha256":"meeting_XML_SHA256",
  "race_xml_sha256":"race_XML_SHA256",
  "gps_csv_sha256":"gps_CSV_SHA256",
}

def _hold(error, **extra):
    if not isinstance(error,str) or not error.startswith("HOLD_"):
        error="HOLD_REVIEW_REQUIRED"
    return {"schema":SCHEMA,"status":error,
            "target":"RETROSPECTIVE_RQ_FIRST_GPS_ONLY",
            "is_a_new_JRA_early_odds_forecast":False,
            "is_observed_market_ABM_causal_effect":False,
            "no_individual_GPS_horse_names_or_IDs_exported":True,
            **extra}


def _original_read():
    """Only the existing bounded RQ source APIs; trace original roster digests."""
    roster_shas=defaultdict(dict)
    current=[None]
    def traced(op,params):
        out=request_xml(op,params)
        if op=="GetMeetingsForDate":
            day=str(params["meetingDate"])
            if day not in COHORT:
                raise ValueError("HOLD_UNPRESELECTED_SOURCE_DAY")
            current[0]=day
        if op=="GetHorsesForRace":
            day=current[0]
            if not day or day not in COHORT:
                raise ValueError("HOLD_ROSTER_BEFORE_SOURCE_DATE")
            race=str(params["raceId"])
            if race in roster_shas[day]:
                raise ValueError("HOLD_DUPLICATE_SOURCE_ROSTER_ID_REQUEST")
            roster_shas[day][race]=out[2]
        return out
    rows,manifest=collect_cannon(
        soap=traced,gps=fetch_official,on_source_error="record_HOLD")
    for day,digests in roster_shas.items():
        if day not in manifest or manifest[day]["status"]!=SOURCE_STATUS:
            continue
        serial="".join(f"{rid}:{dig}\n" for rid,dig in sorted(digests.items()))
        manifest[day]["original_horse_roster_sha256_combined"]=hashlib.sha256(
            serial.encode("ascii")).hexdigest()
        manifest[day]["original_horse_roster_response_count"]=len(digests)
    return rows,manifest


def _frozen_fingerprints(manifest, baseline):
    if (baseline.get("schema")!=ARCHIVE_SCHEMA
            or set(baseline.get("per_date",{}))!=set(COHORT)
            or len(COHORT)!=DATE_COUNT):
        raise ValueError("HOLD_WRONG_OR_MISSING_ORIGINAL_SOURCE_FINGERPRINTS")
    results={}
    for day in COHORT:
        meta=manifest[day]
        original=baseline["per_date"][day]
        if meta["status"]!=SOURCE_STATUS:
            results[day]={"status":"HOLD_DATE_CURRENT_SOURCE_INCOMPLETE",
                          "all_components_match":False}
            continue
        observed=meta.get("original_source_SHA256_only",{})
        detail={k:observed.get(k)==original[ref]
                for k,ref in SOURCE_HASH_MAP.items()}
        detail["positive_row_count"]=(
            meta.get("positive_first_GPS_candidates")==
            original["verified_positive_first_GPS_HORSES_ID_matches"])
        detail["original_horse_roster"]=(
            meta.get("original_horse_roster_sha256_combined")==
            original["combined_original_GetHorsesForRace_roster_SHA256"])
        detail["roster_response_count"]=(
            meta.get("original_horse_roster_response_count")==
            original["number_of_original_HORSES_roster_responses_hashed"])
        results[day]={"status":(
            "MATCHES_ORIGINAL_20261014_SOURCE_BYTES_AND_ID_COUNTS"
            if all(detail.values()) else "HOLD_ORIGINAL_SOURCE_EDITION_CHANGED"),
                      "all_components_match":all(detail.values()),
                      "comparison_to_frozen_source":detail}
    return results


def _source_rows_contrasts(rows):
    """Same measurement eligibility as main's ecology race_fixed_reml."""
    rel,quality=prepare(rows,min_race_telemetry=4)
    # Build the numerator WITHOUT ever exporting the horse IDs or first GPS
    # seconds. Main's absolute first-section model uses the same keys.
    original={(r["day"],r["horse_id"]):float(r["first_section_sec"])
              for r in rows}
    by_race=defaultdict(list)
    for r in rel:
        key=(r["day"],r["race_number"])
        sec=original.get((r["day"],r["horse_id"]))
        if sec is None:
            raise ValueError("HOLD_ORIGINAL_GPS_ABSOLUTE_SECTION_MISSING")
        by_race[key].append((r["horse_id"],sec))
    counts=Counter(r["horse_id"] for r in rel)
    dates={day for day,n in by_race}
    repeated=sum(v>=2 for v in counts.values())
    if (len(rel)<MIN_ROWS or len(by_race)<MIN_RACES
            or len(dates)<MIN_DATES or repeated<MIN_REPEATED):
        raise ValueError("HOLD_SOURCE_REAL_REML_ELIGIBILITY")
    ids=sorted(counts)
    ix={h:i for i,h in enumerate(ids)}
    Z=[]
    response=[]
    for race,group in sorted(by_race.items()):
        n=len(group)
        Q=_helmert(n)
        y=np.asarray([v for _,v in group])
        M=np.zeros((n,len(ids)))
        for i,(ident,_) in enumerate(group):
            M[i,ix[ident]]=1.
        response.append(Q@y)
        Z.append(Q@M)
    z=np.concatenate(response)
    B=np.vstack(Z)
    if len(z)<MIN_CONTRASTS:
        raise ValueError("HOLD_FEW_INDEPENDENT_REAL_RACE_CONTRASTS")
    evidence={
        "original_source_rows_with_positive_GPS_and_min_four_peers":len(rel),
        "original_races_measured":len(by_race),
        "original_meeting_dates":len(dates),
        "anonymous_horse_ID_count":len(counts),
        "anonymous_horse_IDs_with_two_plus_dates":repeated,
        "independent_race_contrast_dimensions":len(z),
        "gps_missingness_or_official_final_starter_roster_adjusted":False,
        "same_first_GPS_marker_across_all_original_rows":(
            len({r["first_section_marker"] for r in rel})==1),
    }
    return z,B,evidence


def _fit_new_reml(rows):
    """Algebraically independently assembled likelihood using shared solver."""
    z,B,support=_source_rows_contrasts(rows)
    gram=B.T@B
    eigen,U=np.linalg.eigh((gram+gram.T)/2)
    if min(eigen)<-1e-7:
        raise ValueError("HOLD_GPS_CONTRAST_GRAM_NOT_PSD")
    eigen=np.maximum(eigen,0)
    mask=eigen>max(1.,max(eigen))*1e-8
    if sum(mask)<2 or len(z)<=sum(mask):
        raise ValueError("HOLD_UNIDENTIFIABLE_RQ_VARIANCE_COMPONENT")
    lam=eigen[mask]
    t=U[:,mask].T@(B.T@z)
    alpha=t*t/lam
    rest=max(0.,float(z@z)-float(alpha.sum()))
    m=len(z)
    if rest<=1e-12:
        raise ValueError("HOLD_NO_RESIDUAL_NOISE_IDENTIFIABILITY")
    def profile(r):
        infl=1+r*lam
        v=(rest+float(np.sum(alpha/infl)))/m
        if v<=0:
            return float("inf")
        return float(m*math.log(v)+np.log(infl).sum())
    gg=np.linspace(-18.,18.,121)
    yy=[profile(math.exp(q)) for q in gg]
    optimum=int(np.argmin(yy))
    if optimum in (0,120):
        raise ValueError("HOLD_REML_VARIANCE_RATIO_BOUNDARY")
    logr,loss=_golden_min(
        lambda v:profile(math.exp(v)),
        float(gg[optimum-1]),float(gg[optimum+1]))
    ratio=math.exp(logr)
    if loss>=profile(0)-1e-7:
        raise ValueError("HOLD_ZERO_HORSE_ID_VARIANCE")
    e2=float((rest+np.sum(alpha/(1+ratio*lam)))/m)
    a2=ratio*e2
    return {"status":"REAL_SOURCE_RESTRICTED_GAUSSIAN_REML_POINT_ONLY",
            **support,
            "horse_variance_seconds_squared":a2,
            "independent_noise_variance_seconds_squared":e2,
            "conditional_icc_point":ratio/(1+ratio),
            "source_mixed_measurement_markers_not_a_single_trait":
                not support["same_first_GPS_marker_across_all_original_rows"],
            "this_is_a_real_GPS_association_not_inherited_personality":True,
            "all_numeric_effects_retrospective_source_conditional":True,
            "no_original_IDs_names_or_GPS_values_in_output":True}


def _leave_one_original_source_date_reml(screened, compare):
    """Original source DATE is the deletion unit; never a per-horse CI."""
    results=[]
    for day in COHORT:
        without=[r for r in screened if r["day"]!=day]
        try:
            fit=compare(without)
            icc=fit["conditional_icc_point"]
            if not (math.isfinite(icc) and 0<=icc<=1):
                raise ValueError("HOLD_NONFINITE_DELETED_DATE_ICC")
            results.append({"status":"ORIGINAL_DATE_DELETED_VALID",
                            "icc":float(icc)})
        except ValueError as exc:
            if not str(exc).startswith("HOLD_"):
                raise
            results.append({"status":"HOLD_ONE_SOURCE_DATE_LEFT_OUT",
                            "error_code":str(exc).split(":",1)[0]})
    valid=[v["icc"] for v in results if v["status"]=="ORIGINAL_DATE_DELETED_VALID"]
    return {
        "status":(
            "EXPLORATORY_ORIGINAL_SOURCE_DATE_DELETION_NOT_CONFIDENCE_INTERVAL"
            if len(valid)>=len(COHORT)-2
            else "HOLD_INSUFFICIENT_DATE_DELETE_VARIANCE_FITS"),
        "original_dates_deletion_attempted":len(COHORT),
        "successful_reml_delete_one_original_source_date":len(valid),
        "source_dates_with_variance_hold":len(COHORT)-len(valid),
        "minimum_source_deleted_ICC":min(valid) if valid else None,
        "maximum_source_deleted_ICC":max(valid) if valid else None,
        "original_source_date_not_horse_rows_is_deletion_unit":True,
        "no_individual_original_source_date_ICC_rankings_exported":True,
        "not_a_jackknife_95pct_CI_or_a_preregistered_replication":True,
    }



def _previously_locked_out_of_date_horse_vs_other_horse(screened):
    """Reapply a PREVIOUSLY FROZEN source-conditional experiment.

    All focal records are scored against only earlier original dates;
    exact GPS first marker and official distance must match, and a
    newly documented source jockey ID is required by the *OLD*
    comparator eligibility. It is a POSTRACE peer-relative GPS
    measurement, never an odds-market or absolute focal speed forecast.
    Return only already-safe aggregates of the original method.
    """
    timed,coverage=source_timed_panel(screened,min_gps=4)
    if not timed:
        return {"status":"HOLD_NO_ORIGINAL_TIMED_PEER_RELATIVE_GPS",
                "no_animal_IDs_or_records_exported":True}
    report=audit_other_horse_baselines(timed)
    if not report["strictly_earlier_date_train_then_update"]:
        raise ValueError("HOLD_EARLIER_DATE_PREDICTION_RULE_NOT_ENFORCED")
    contexts={}
    for context,details in report["contexts"].items():
        forecasts={}
        for name,e in details["identical_scored_future_records"].items():
            keep=[
              "status","distinct_original_HORSES_IDs",
              "matched_chronological_future_source_rows",
              "distinct_future_original_source_dates",
              "distinct_original_horse_by_matching_contexts",
              "same_future_rows_for_each_compared_predictor",
              "equal_HORSES_weighted_past_horse_RMSE_sec",
              "equal_HORSES_weighted_past_other_horse_baseline_RMSE_sec",
              "past_other_horse_minus_focal_horse_RMSE_sec",
            ]
            forecasts[name]={k:e[k] for k in keep if k in e}
        contexts[context]=forecasts
    return {
        "status":"RETROSPECTIVE_ORIGINAL_METHOD_PAST_HORSE_VS_OTHER_HORSE_SOURCE_EDITION",
        "source_timed_rows":len(timed),
        "source_meeting_dates_with_timed_rows":
            coverage["original_source_dates_after_race_minimum"],
        "same_locked_old_shrinkage_n_over_n_plus_2":True,
        "same_old_new_documented_rider_comparator_population":True,
        "not_a_new_preregistered_validation":True,
        "not_absolute_horse_speed_or_prestart_market_prediction":True,
        "original_source_rider_ids_not_verified_actual_riders":True,
        "no_animal_IDs_or_records_exported":True,
        "contexts":contexts,
    }


def _prelocked_marker_specific_rem_l(rows, *, compare=_fit_new_reml,
                                     reference=race_fixed_reml):
    """Original Cannon 150m/250m sensitivity, report explicit support HOLD.

    Marker choices were locked in main BEFORE this retrospective
    current-edition replay. Do not interpret the pair as equivalent
    genetic/behavioral traits or reuse estimates across race distances.
    """
    tested={}
    for marker in (150.0,250.0):
        filtered=[r for r in rows
                  if r["first_marker_m"] is not None
                  and float(r["first_marker_m"])==marker]
        source_days={r["day"] for r in filtered}
        field={
            "first_GPS_marker_m":int(marker),
            "original_positive_GPS_rows_before_4_race_peer_gate":
                len(filtered),
            "source_days_with_marker_rows":len(source_days),
            "same_marker_only_but_official_race_distance_may_differ":True,
            "source_current_roster_edition_not_the_old_frozen_roster":True,
            "no_individual_horse_ID_or_GPS_time_exported":True,
        }
        if not filtered:
            tested[str(int(marker))]={
                **field,"status":"HOLD_NO_SOURCE_GPS_ROWS_AT_LOCKED_MARKER"}
            continue
        try:
            old=reference(filtered,min_race_telemetry=4)
            if old["status"].startswith("HOLD_"):
                tested[str(int(marker))]={
                    **field,"status":"HOLD_OLD_ECOLOGY_MARKER_COHORT_NOT_IDENTIFIABLE",
                    "existing_reference_status":old["status"]}
                continue
            new=compare(filtered)
            err=abs(new["conditional_icc_point"]-
                    old["conditional_observational_ICC_point_estimate"])
            if err>=1e-5:
                tested[str(int(marker))]={
                    **field,"status":"HOLD_MARKER_SPECIFIC_NUMERICAL_MODEL_DISAGREEMENT",
                    "absolute_method_difference":err}
                continue
            tested[str(int(marker))]={
                **field,"status":"EXPLORATORY_FIXED_MARKER_OBSERVED_SOURCE_VERSION",
                "source_rows_in_min_four_eligible_races":
                    new["original_source_rows_with_positive_GPS_and_min_four_peers"],
                "races_with_same_fixed_marker":
                    new["original_races_measured"],
                "source_dates_after_race_gate":
                    new["original_meeting_dates"],
                "distinct_horse_ids_anonymous":
                    new["anonymous_horse_ID_count"],
                "repeated_horse_ids_anonymous":
                    new["anonymous_horse_IDs_with_two_plus_dates"],
                "conditional_icc_current_source_only":
                    new["conditional_icc_point"],
                "reference_main_conditional_icc":
                    old["conditional_observational_ICC_point_estimate"],
                "absolute_method_difference":err}
        except ValueError as exc:
            if not str(exc).startswith("HOLD_"):
                raise
            tested[str(int(marker))]={
                **field,
                "status":"HOLD_MARKER_SPECIFIC_FIT_NOT_IDENTIFIABLE",
                "reason_code":str(exc).split(":",1)[0]}
    return {
        "status":"PRELOCKED_CANNON_FIRST_GPS_MARKER_SENSITIVITY",
        "marker_selection_m":[150,250],
        "study_is_conditioned_on_updated_source_edition":True,
        "not_same_phenotype_across_markers_without_biological_measurement_match":True,
        "no_CI_heritability_or_ground_reaction_slope":True,
        "results":tested,
    }

def replay(*,reader=_original_read,baseline, compare=_fit_new_reml,
           reference=race_fixed_reml):
    validate_cohort()
    rows,manifest=reader()
    if set(manifest)!=set(COHORT):
        raise ValueError("HOLD_SOURCE_DATE_DENOMINATOR_CHANGED")
    status_by_day={k:manifest[k]["status"] for k in COHORT}
    injected_test_collector = reader is not _original_read
    meta={
        "schema":SCHEMA,
        "source_collector_is_injected_test_fixture":injected_test_collector,
        "original_calendar_date_count":len(COHORT),
        "original_requested_races":list(LOCKED_RACE_NUMBERS),
        "official_source_publisher":"Racing Queensland",
        "source_request_utc":datetime.now(timezone.utc).isoformat(),
        "retrieval_time_is_NOT_historical_first_odds_clock":True,
        "no_JRA_or_RQ_first_market_quote_fitted":True,
        "all_rows_retained_in_memory_only":True,
        "no_original_horse_ID_names_jockey_licence_or_GPS_timing_exported":True,
        "is_new_empirical_animal_phenotype_evidence":False,
        "retrospective_source_only":True,
        "original_date_source_status":status_by_day,
    }
    unmatched=[d for d in COHORT if status_by_day[d]!=SOURCE_STATUS]
    fingerprints=_frozen_fingerprints(manifest,baseline)
    meta["original_20261014_source_component_match"]={
       "fully_matched_dates":sum(x["all_components_match"]
                                 for x in fingerprints.values()),
       "source_changed_or_held_dates":[d for d in COHORT
                                       if not fingerprints[d]["all_components_match"]],
       "components_by_original_date":fingerprints,
       "old_548_vs_543_original_horse_join_unresolved":True,
    }
    if unmatched:
        return {**_hold("HOLD_INCOMPLETE_ORIGINAL_12DATE_LIVE_RQ_COHORT"),
                **meta,"current_source_dates_HOLD":unmatched,
                "ICC_or_horse_effect_not_scored_with_incomplete_cohort":True}
    screened,identity=identity_overlap(rows)
    meta["anonymous_original_ID_source_screen"]={
      "positive_GPS_rows_before_ID_name_screen":len(rows),
      "positive_GPS_rows_after_ID_name_screen":len(screened),
      "distinct_original_IDs_after_name_screen":
         identity["distinct_original_IDs_after_name_identity_screen"],
      "HORSES_IDs_with_name_conflicts_blocked":
         identity["HORSES_IDs_with_different_names_across_dates_blocked"],
      "not_verified_actual_starter_roster":True,
    }
    if not screened:
        return {**_hold("HOLD_NO_SOURCE_LINKED_REPEAT_GPS"),**meta}
    existing=reference(screened,min_race_telemetry=4)
    if existing["status"].startswith("HOLD_"):
        return {**_hold("HOLD_EXISTING_ECOLOGY_REML_UNIDENTIFIABLE"),
                **meta,"existing_main_status":existing["status"]}
    try:
        updated=compare(screened)
    except ValueError as exc:
        if not str(exc).startswith("HOLD_"):
            raise
        return {**_hold(str(exc)),**meta,
                "existing_main_status":existing["status"]}
    source_date_deletion=_leave_one_original_source_date_reml(
        screened,compare)
    historical_forward=_previously_locked_out_of_date_horse_vs_other_horse(
        screened)
    timed_null, _null_source_cov = source_timed_panel(
        screened,min_gps=4)
    horse_identity_history_null={
        "same_distance_and_GPS_marker":
            identity_history_shuffle(
                timed_null,strict_class=False,permutations=299,seed=20261026),
        "additionally_same_original_class":
            identity_history_shuffle(
                timed_null,strict_class=True,permutations=299,seed=20261027),
    }
    absolute_first_GPS_horse_history_forward={
        "same_distance_and_GPS_marker":
            absolute_first_section_forward_audit(
                timed_null,screened,strict_class=False,
                permutations=299,seed=20261028),
        "additionally_same_original_class":
            absolute_first_section_forward_audit(
                timed_null,screened,strict_class=True,
                permutations=299,seed=20261029),
    }
    future_date_sensitivity={
        "same_official_distance_and_exact_first_GPS_marker":
            frozen_future_date_sensitivity(
                timed_null,screened,strict_class=False,
                draws=399,seed=20261027),
        "also_same_original_race_Class":
            frozen_future_date_sensitivity(
                timed_null,screened,strict_class=True,
                draws=399,seed=20261028),
    }
    marker_replay=_prelocked_marker_specific_rem_l(
        screened,compare=compare,reference=reference)
    old_a=existing["horse_variance_component_sec_squared"]
    old_e=existing["independent_error_variance_component_sec_squared"]
    old_icc=existing["conditional_observational_ICC_point_estimate"]
    diff={
        "horse_variance_abs_seconds_squared":abs(old_a-updated["horse_variance_seconds_squared"]),
        "absolute_noise_variance_abs_seconds_squared":abs(old_e-updated["independent_noise_variance_seconds_squared"]),
        "conditional_icc_abs_difference":abs(old_icc-updated["conditional_icc_point"]),
    }
    comparable=all(v<1e-5 for v in diff.values())
    frozen=all(v["all_components_match"] for v in fingerprints.values())
    return {
        **meta,
        "status":(
            ("SYNTHETIC_FIXTURE_NUMERIC_METHOD_REPLAY_NOT_REAL_HORSE_DATA"
             if comparable and frozen else
             "SYNTHETIC_FIXTURE_SOURCE_EDITION_CHANGED_HOLD"
             if comparable else
             "HOLD_SYNTHETIC_METHODS_DISAGREE")
            if injected_test_collector else
            "OBSERVED_REAL_RQ_SOURCE_REML_INDEPENDENT_NUMERICAL_REPLAY"
            if comparable and frozen else
            "OBSERVED_REAL_RQ_SOURCE_REML_SOURCE_EDITION_HOLD"
            if comparable else
            "HOLD_NUMERICAL_NEW_VS_ECOLOGY_REML_DIFFERENCE"),
        "source_fingerprints_unchanged_since_20261014":frozen,
        "existing_main_retrospective": {
             "status":existing["status"],
             "conditional_icc":old_icc,
             "horse_variance_seconds2":old_a,
             "noise_variance_seconds2":old_e,
             "not_new_or_independent_biological_cohort":True},
        "new_same_original_horse_race_source":
             updated,
        "independent_algorithm_absolute_numerical_differences":diff,
        "original_source_date_deletion_sensitivity":source_date_deletion,
        "same_original_20261014_design_horse_vs_other_history_on_current_source":
            historical_forward,
        "within_race_history_identity_shuffle_source_conditional_null":
            horse_identity_history_null,
        "original_absolute_first_GPS_timing_frozen_cohort_out_of_date_comparison":
            absolute_first_GPS_horse_history_forward,
        "same_frozen_future_targets_relative_vs_absolute_date_block_sensitivity":
            future_date_sensitivity,
        "prelocked_marker_specific_source_icc_sensitivity":
            marker_replay,
        "both_same_original_source_and_eligibility":True,
        "did_NOT_use_actual_future_target_prices_or_race_finishes":True,
        "no_real_social_causality_critical_odds_or_ROI_inferred":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    baseline=json.loads(args.baseline.read_text(encoding="utf-8"))
    try:
        report=replay(baseline=baseline)
    except (ValueError,OSError,TimeoutError) as exc:
        # Exception strings from 3p metadata can contain identifiers;
        # only return machine-coded HOLD strings.
        code=str(exc).split(":",1)[0]
        report=_hold(code if code.startswith("HOLD_") else "HOLD_SOURCE_REVIEW_REQUIRED")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf8")
    print(json.dumps({
        "scientific_status":report["status"],
        "real_source_replayed":report.get("original_calendar_date_count"),
        "observed_numeric_ICC":report.get("new_same_original_horse_race_source",{}).get(
             "conditional_icc_point"),
        "matched_original_source_date_count":report.get(
           "original_20261014_source_component_match",{}).get("fully_matched_dates"),
        "no_real_bettor_market_join":True
    },ensure_ascii=False))


if __name__=="__main__":
    main()
