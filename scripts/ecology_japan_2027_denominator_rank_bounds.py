#!/usr/bin/env python3
"""2027 pre-race frozen-denominator and not-yet-observed-race rank-loss bounds.

Two distinct problems must not be conflated:
  - A result among fully classified observed races can be selection-biased.
  - The population of races where a prediction was actually committed may
    be a selected subset of all source-eligible races.

This module audits an already frozen PRIVATE 2027 M0/M1/M2 prediction and
manifest, never refits, guesses ranks, scrapes JRA or certifies provider
licensing. Missing results produce an exact permutation envelope CONDITIONAL
on every unresolved race eventually being a fully classified 1..N race.
If a DNF/cancelled/unclassified race appears, its normalized-rank target is
UNDEFINED; no all-race gain can be asserted. An optional independent private
schedule lists expected eligible races as of the original forecast cutoff.
It remains SELF-SUPPLIED, not a certified complete JRA/NAR denominator.

All race and horse identifiers and per-race predictions remain PRIVATE.
Only aggregate counts, hypothetical bounds and provenance flags are exported.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import math

from ecology_japan_2027_official_knownon_preflight import local_jst
from ecology_japan_2027_point_in_time_ledger import (
    score as frozen_score, digest_bytes, canonical_bytes
)

STATUS="HOLD_NOT_INDEPENDENTLY_ATTESTED_PROSPECTIVE_SOURCE_AND_UNIVERSE"
JST=timezone(timedelta(hours=9))
START=datetime(2027,1,1,tzinfo=JST)
END=datetime(2027,7,1,tzinfo=JST)
RACE_UNIVERSE_FIELDS=("race_id","race_start_at_jst","eligibility_known_at_jst")
PAIRINGS=(("M1","M2"),("M0","M2"))


def _gain(p:dict, y:float, *, base:str) -> float:
    return (y-float(p[base]))**2-(y-float(p["M2"]))**2


def _race_permutation_extrema(rows:list[dict], weights:dict[str,float],
                              *, base:str) -> tuple[float,float]:
    """Sharp min/max if any permutation of all 1..N ranks remains possible.

    Weighted squared-loss difference is affine in normalized rank:
    w*((y-p_base)^2-(y-p_M2)^2)
      = 2*w*(p_M2-p_base)*y + w*(p_base^2-p_M2^2).
    Rearrangement inequality minimizes sum by giving the smallest y to the
    largest slope and maximizes by giving smallest y to smallest slope.
    No data-dependent fitting or stochastic imputation.
    """
    n=len(rows)
    if n<2:
        raise ValueError("HOLD_PERMUTATION_NEEDS_COMPLETE_2PLUS_RUNNERS")
    slopes=[]
    offset=0.0
    for p in rows:
        w=weights[p["horse_id"]]
        a=float(p[base]); b=float(p["M2"])
        slopes.append(2*w*(b-a))
        offset+=w*(a*a-b*b)
    ranks=[k/(n-1) for k in range(n)]
    minimum=offset+sum(v*y for v,y in zip(sorted(slopes,reverse=True),ranks))
    maximum=offset+sum(v*y for v,y in zip(sorted(slopes),ranks))
    if minimum>maximum+1e-12:
        raise ValueError("HOLD_INVALID_REARRANGEMENT_BOUNDS")
    return float(minimum),float(maximum)


def _schedule_contract(expected:list[dict]|None, predicted:dict[str,list[dict]],
                       asof:datetime) -> dict:
    """Audit a supplied private eligible-race list; do not certify completeness."""
    out={
        "provided_source_eligible_race_universe":expected is not None,
        "official_jra_nar_schedule_completeness_independently_certified":False,
        "provided_universe_proves_all_actual_JRA_races_in_period":False,
        "forecasted_races":len(predicted),
        "universe_input_must_be_known_by_forecast_cutoff":True,
    }
    if expected is None:
        return {**out,"status":"HOLD_NO_SEPARATE_PRETARGET_RACE_UNIVERSE",
                "eligible_races_declared":None,
                "eligible_races_without_a_frozen_prediction":None}
    if not expected:
        raise ValueError("HOLD_EMPTY_PRIVATE_TARGET_RACE_UNIVERSE")
    indices={}
    for row in expected:
        if not isinstance(row,dict) or not set(RACE_UNIVERSE_FIELDS).issubset(row):
            raise ValueError("HOLD_PRIVATE_TARGET_UNIVERSE_SCHEMA")
        race=str(row["race_id"]).strip()
        if not race.startswith("JRA:") or race=="JRA:":
            raise ValueError("HOLD_PRIVATE_TARGET_RACE_NAMESPACE")
        target=local_jst(row["race_start_at_jst"])
        known=local_jst(row["eligibility_known_at_jst"])
        if (race in indices or not START<=target<END
                or not known<=asof<target):
            raise ValueError("HOLD_TARGET_UNIVERSE_DUPLICATE_LATE_OR_FUTURE")
        indices[race]=target
    unknown=set(predicted)-set(indices)
    if unknown:
        raise ValueError("HOLD_FROZEN_FORECAST_OUTSIDE_DECLARED_RACE_UNIVERSE")
    for race, rows in predicted.items():
        start=local_jst(rows[0]["race_start_at_jst"])
        if indices[race]!=start:
            raise ValueError("HOLD_FROZEN_RACE_START_NOT_IN_PRETARGET_UNIVERSE")
    absent=len(set(indices)-set(predicted))
    return {
        **out,
        "status":("HOLD_PREDECLARED_RACES_WITHOUT_FORECAST"
                  if absent else "SOURCE_UNIVERSE_COVERED_WITHIN_SUPPLIED_LIST_ONLY"),
        "eligible_races_declared":len(indices),
        "eligible_races_without_a_frozen_prediction":absent,
        "forecast_coverage_fraction_in_supplied_universe":
            len(predicted)/len(indices),
        "universe_assessed_pre_outcome_not_from_final_results":True,
    }


def audit_universe(private:dict, manifest:dict, final_rows:list[dict], *,
                   expected_races:list[dict]|None=None) -> dict:
    """Privacy-safe forecast denominator, missing-outcome and bound audit.

    The original score() enforces the immutable private prediction SHA, exact
    source-forecast parity, results publication ordering, duplicate IDs and
    classified-race completeness. Reuse its validation but never promote its
    scored-only RMSE into a whole-universe gain if records are missing.
    """
    prior=frozen_score(private,manifest,final_rows)
    preds=private["predictions"]
    if not preds:
        raise ValueError("HOLD_EMPTY_FROZEN_FORECAST")
    if private.get("target_outcomes_included") is not False:
        raise ValueError("HOLD_PRE_RACE_COMMIT_HAS_TARGET_OUTCOMES")
    by_race=defaultdict(list)
    by_horse=Counter()
    for p in preds:
        race=p["race_id"]
        by_race[race].append(p)
        by_horse[p["horse_id"]]+=1
    for race, rows in by_race.items():
        if len(rows)<2 or len({p["horse_id"] for p in rows})!=len(rows):
            raise ValueError("HOLD_UNVERIFIED_FROZEN_RACE_COHORT")
        if len({p["race_start_at_jst"] for p in rows})!=1:
            raise ValueError("HOLD_FROZEN_RACE_START_CONFLICT")
    asof=local_jst(manifest["asof_at_jst"])
    universe=_schedule_contract(expected_races,by_race,asof)
    n_horses=len(by_horse)
    weights={hid:1/(n_horses*cnt) for hid,cnt in by_horse.items()}
    if abs(sum(weights[p["horse_id"]] for p in preds)-1.0)>1e-10:
        raise ValueError("HOLD_FROZEN_HORSE_EQUAL_WEIGHTS_NOT_ONE")
    result_by_race=defaultdict(dict)
    for r in final_rows:
        result_by_race[r["race_id"]][r["horse_id"]]=r
    starts=Counter()
    race_quality=Counter()
    partial_rank_information_ignored=0
    exact={pair:0.0 for pair in PAIRINGS}
    low={pair:0.0 for pair in PAIRINGS}
    high={pair:0.0 for pair in PAIRINGS}
    bad_unclassified=False
    for race,rows in by_race.items():
        rr=result_by_race.get(race,{})
        n=len(rows)
        no_results=(len(rr)==0)
        if no_results:
            label="no_reported_result"
        elif len(rr)<n:
            label="partially_reported_result"
        else:
            label="all_rows_reported"
        # A nonfinisher or a contradictory source rank makes a 1..N
        # classified outcome undefined, not a missing y to be imputed.
        invalid=False
        seen=[]
        for res in rr.values():
            if res["finish_status"]!="CLASSIFIED":
                invalid=True
                break
            try:
                rank=int(res["finish_rank"])
                total=int(res["classified_field_size"])
            except (ValueError,TypeError,KeyError):
                invalid=True
                break
            if not 1<=rank<=n or total!=n:
                invalid=True
                break
            seen.append(rank)
        if len(seen)!=len(set(seen)):
            invalid=True
        if invalid:
            label="undefined_rank_target_or_source_conflict"
            bad_unclassified=True
        elif len(rr)==n:
            if sorted(seen)!=list(range(1,n+1)):
                label="undefined_rank_target_or_source_conflict"
                bad_unclassified=True
            else:
                label="complete_classified_race"
        elif len(rr)>0:
            partial_rank_information_ignored+=1
        race_quality[label]+=1
        starts[label]+=n
        if label=="undefined_rank_target_or_source_conflict":
            continue
        for pair in PAIRINGS:
            base=pair[0]
            if label=="complete_classified_race":
                observed=sum(
                    weights[p["horse_id"]]*_gain(
                        p,(int(rr[p["horse_id"]]["finish_rank"])-1)/(n-1),base=base
                    ) for p in rows
                )
                exact[pair]+=observed
                low[pair]+=observed
                high[pair]+=observed
            else:
                lo,hi=_race_permutation_extrema(rows,weights,base=base)
                low[pair]+=lo
                high[pair]+=hi

    if sum(starts.values())!=len(preds) or sum(race_quality.values())!=len(by_race):
        raise ValueError("HOLD_FROZEN_FORECAST_DENOMINATOR_NOT_PARTITIONED")
    if race_quality["complete_classified_race"]!=prior.get(
        "races_scored",0) and not (
        prior.get("status")=="HOLD_NO_FULLY_PUBLISHED_COMPLETE_RACES"
        and race_quality["complete_classified_race"]==0
    ):
        raise ValueError("HOLD_EXISTING_SCORE_COMPLETE_RACE_PARITY")
    bounds={}
    has_forecast_gap=bool(universe["eligible_races_without_a_frozen_prediction"])
    feasible=not bad_unclassified and not has_forecast_gap
    for base,other in PAIRINGS:
        key=f"{base}_minus_{other}_full_frozen_population_MSE"
        b={
            "difference_definition":f"(y-{base})^2-(y-{other})^2",
            "positive_would_favor_M2":True,
            "observed_classified_race_contribution_to_frozen_horse_equal_MSE_difference":
                float(exact[(base,other)]),
            "frozen_horse_denominator_stays_all_precommitted_starts":True,
        }
        if feasible:
            lo,hi=low[(base,other)],high[(base,other)]
            b.update({
                "status":("FULLY_CLASSIFIED_FROZEN_BUNDLE_MSE_ALREADY_OBSERVED"
                          if not race_quality["no_reported_result"] and
                             not race_quality["partially_reported_result"]
                          else "HYPOTHETICAL_ALL_MISSING_RACES_FINISH_CLASSIFIED"),
                "min_feasible_MSE_difference":float(lo),
                "max_feasible_MSE_difference":float(hi),
                "all_hypothetically_valid_rank_permutations_favor_M2":bool(lo>0),
                "all_hypothetically_valid_rank_permutations_favor_other":bool(hi<0),
                "some_hypothetical_completions_cross_or_touch_zero":bool(lo<=0<=hi),
                "missing_partial_result_rows_not_used_to_narrow_bounds":True,
            })
        else:
            b.update({
                "status":("HOLD_PREDICTED_RACE_WITH_UNDEFINED_NORMALIZED_RANK_TARGET"
                          if bad_unclassified else
                          "HOLD_MISSING_FORECASTS_IN_SUPPLIED_SOURCE_UNIVERSE"),
                "min_feasible_MSE_difference":None,
                "max_feasible_MSE_difference":None,
                "whole_scope_gain_unidentified":True,
            })
        bounds[key]=b
    if feasible and race_quality["complete_classified_race"]==len(by_race):
        rmse=prior["RMSE_equal_horse_weight"]
        for base,other in PAIRINGS:
            q=f"{base}_minus_{other}_full_frozen_population_MSE"
            by_rmse=rmse[base]**2-rmse[other]**2
            if abs(by_rmse-bounds[q]["min_feasible_MSE_difference"])>1e-10:
                raise ValueError("HOLD_FULLY_OBSERVED_RMSE_SQUARED_PARITY")
    return {
        "status":STATUS,
        "source_scope":"ONE_LOCALLY_FROZEN_PREDICTION_BUNDLE_NOT_CERTIFIED_ALL_JRA",
        "frozen_private_prediction_SHA256":manifest["private_prediction_file_SHA256"],
        "public_commitment_sha256":digest_bytes(canonical_bytes(manifest)),
        "frozen_races":len(by_race),
        "frozen_starts":len(preds),
        "frozen_unique_horses":n_horses,
        "source_eligible_race_universe_coverage":universe,
        "result_availability_counts_races":dict(race_quality),
        "result_availability_counts_frozen_starts":dict(starts),
        "reported_partial_race_rank_values_ignored_for_conservative_bounds":
            partial_rank_information_ignored,
        "original_local_scorer_status":prior["status"],
        "original_scorer_scored_only_conditional_not_a_population_estimate":True,
        "MSE_gain_bounds":bounds,
        "hypothetical_missing_finish_rank_permutation_bounds_not_biological_fitness":True,
        "unknown_DNF_or_cancelled_finish_rank_is_NOT_imputed":True,
        "actual_external_Github_pre_race_attestation_verified_by_this_tool":False,
        "licensed_official_race_universe_and_JRA_IDs_verified_by_this_tool":False,
        "no_real_2027_model_effect_established_by_software_test":True,
        "privacy_no_horse_race_identifiers_or_individual_predictions_exported":True,
    }


def _csv(path:Path) -> list[dict]:
    with path.open("r",encoding="utf-8-sig",newline="") as fd:
        reader=csv.DictReader(fd)
        if not reader.fieldnames:
            raise ValueError("HOLD_MISSING_PRIVATE_CSV_HEADER")
        return [dict(row) for row in reader]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-frozen-forecast",type=Path,required=True)
    p.add_argument("--aggregate-forecast-commitment",type=Path,required=True)
    p.add_argument("--published-results",type=Path,required=True)
    p.add_argument("--private-eligible-universe",type=Path)
    p.add_argument("--aggregate-out",type=Path,required=True)
    a=p.parse_args()
    raw=json.loads(a.private_frozen_forecast.read_text(encoding="utf-8"))
    manifest=json.loads(a.aggregate_forecast_commitment.read_text(encoding="utf-8"))
    result=audit_universe(
        raw,manifest,_csv(a.published_results),
        expected_races=_csv(a.private_eligible_universe) if a.private_eligible_universe else None
    )
    a.aggregate_out.parent.mkdir(parents=True,exist_ok=True)
    a.aggregate_out.write_text(json.dumps(result,ensure_ascii=False,
        sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True,ensure_ascii=False,allow_nan=False))


if __name__=="__main__":
    main()
