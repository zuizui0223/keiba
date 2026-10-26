#!/usr/bin/env python3
"""Real RQ original-source chronological ABSOLUTE first GPS time benchmark.

The dependent variable is focal horse's OWN positive first-section
seconds, NOT its difference from the present race's observed peers.
This resolves a key ambiguity in the prior source-only comparison:
a same-race peer-relative test uses outcomes of future peers to define
the response, whereas a focal absolute time does not.

To keep target eligibility precommitted, use the EXACT frozen existing
matched future population (horse ID, source declared NEW jockey, official
distance + first GPS marker, optional original race Class).
For each candidate's future original date, predictions use ONLY GPS
from strictly EARLIER locked source dates:

  other = mean(first_section_sec for past other horse/context)
  own   = n/(n+2)*mean(past focal/context) + 2/(n+2)*other

The n/(n+2) shrinkage is from the main ecology research lock, not
tuned to this new outcome. This score is for a historical retrospective
analysis: source rows may have been republished after their race and
were NOT proven to be available at the old first market quote.

The historical-label negative control shuffles original absolute
first-section seconds WITHIN each earlier real GPS race but leaves
the strictly-older OTHER-horse context baseline (and all future focal
outcomes) unchanged. Thus the only changed feature is attribution of
past sectional outcomes to horse identities, not target cohort or
source date. This is a descriptive, nonexchangeability-validated null,
not a confirmatory causal test or population p-value.

Only anonymous aggregates are returned; never serialize source horse
IDs, jockey/trainer licences, original sectional rows or predictions.
"""
from __future__ import annotations

from collections import defaultdict
from math import sqrt, isfinite
from statistics import mean
import random

from ecology_rq_forward_alternative_history import (
    _context, _paired_score, matched_source_rows_private
)

STATUS="RETROSPECTIVE_ORIGINAL_SOURCE_ABSOLUTE_FIRST_GPS_FORWARD_IDENTITY_CHECK"


def _paired_equal_horse_rmse(chosen,predictions):
    if len(chosen)!=len(predictions):
        raise ValueError("HOLD_ABSOLUTE_GPS_SCORE_DENOMINATOR_CHANGED")
    grouped=defaultdict(list)
    for row,pred in zip(chosen,predictions):
        if not isfinite(pred):
            raise ValueError("HOLD_ABSOLUTE_NONFINITE_PREDICTION")
        grouped[row["horse_id"]].append((row["absolute_seconds"]-pred)**2)
    if not grouped:
        raise ValueError("HOLD_NO_ABSOLUTE_SCORABLE_HORSES")
    return sqrt(mean(mean(x) for x in grouped.values()))


def _setup(timed,original,strict_class):
    # The original target selection is already frozen by main ecology
    # and cannot be chosen after observing the new absolute outcome.
    candidates,_=matched_source_rows_private(
        timed,strict_class=strict_class)
    check=_paired_score(candidates,"context_prediction")
    eligibility={
        "original_status":check["status"],
        "matched_future_rows":check["matched_chronological_future_source_rows"],
        "matched_distinct_horse_IDs":check["distinct_original_HORSES_IDs"],
        "distinct_scored_source_days":
            check["distinct_future_original_source_dates"],
        "source_class_matched":strict_class,
        "same_original_frozen_matched_future_population":True
    }
    if check["status"].startswith("HOLD_"):
        return None,None,None,eligibility
    select=[dict(r) for r in candidates if
            r["context_prediction"] is not None]
    # The official horse ID links the same animal to its source time
    # INSIDE this function; the IDs never leave the runner.
    all_abs={}
    for row in original:
        key=(str(row["day"]),row["race_number"],row["horse_id"])
        if key in all_abs:
            raise ValueError("HOLD_DUPLICATE_ABSOLUTE_GPS_SOURCE_HORSE")
        seconds=float(row["first_section_sec"])
        if not isfinite(seconds) or seconds<=0:
            raise ValueError("HOLD_INVALID_ABSOLUTE_FIRST_GPS_SECTION")
        all_abs[key]=seconds
    by_row={}
    by_race=defaultdict(list)
    for row in timed:
        key=(str(row["day"]),row["race_number"],row["horse_id"])
        if key not in all_abs:
            raise ValueError("HOLD_RELATIVE_SOURCE_ROW_WITHOUT_ABSOLUTE_GPS")
        by_row[key]=all_abs[key]
        by_race[(str(row["day"]),row["race_number"])].append(key)
    if len(by_row)!=len(timed):
        raise ValueError("HOLD_DUPLICATE_TIMED_SOURCE_HORSE")
    lookup={(str(r["day"]),r["horse_id"]):r
            for r in timed}
    if len(lookup)!=len(timed):
        raise ValueError("HOLD_HORSE_MULTIPLE_RACES_SAME_ORIGINAL_DATE")
    for r in select:
        original_row=lookup.get((str(r["day"]),r["horse_id"]))
        if original_row is None:
            raise ValueError("HOLD_ABSOLUTE_SCORING_TARGET_MISSING")
        key=(str(r["day"]),original_row["race_number"],
             original_row["horse_id"])
        r["absolute_seconds"]=by_row[key]
    return select,by_row,by_race,eligibility


def _forecasts(timed,targets,true_abs,assigned_abs,strict_class):
    """Future results are never read before their own source date."""
    by_day=defaultdict(list)
    for row in timed:
        by_day[str(row["day"])].append(row)
    wanted=defaultdict(list)
    for ix,row in enumerate(targets):
        wanted[str(row["day"])].append((ix,row))
    pred_self=[None]*len(targets)
    pred_other=[None]*len(targets)
    self_history=defaultdict(list)
    unpermuted_context=defaultdict(list)
    for day in sorted(by_day):
        for ix,row in wanted.get(day,[]):
            horse,context=row["context"]
            same=self_history[(horse,context)]
            peers=[v for i,v in unpermuted_context[context]
                   if i!=horse]
            if not same or not peers:
                raise ValueError("HOLD_STRICTLY_EARLIER_ABSOLUTE_PROFILE_NOT_AVAILABLE")
            anchor=mean(peers)
            fraction=len(same)/(len(same)+2)
            pred_self[ix]=fraction*mean(same)+(1-fraction)*anchor
            pred_other[ix]=anchor
        # Append this completed day only after every today's
        # prediction is computed (all historical publication ages
        # remain unverified; no future DATE values are used).
        for row in by_day[day]:
            ctx=_context(row,strict_class=strict_class)
            key=(str(row["day"]),row["race_number"],row["horse_id"])
            self_history[(row["horse_id"],ctx)].append(assigned_abs[key])
            unpermuted_context[ctx].append((row["horse_id"],true_abs[key]))
    if any(x is None for x in pred_self+pred_other):
        raise ValueError("HOLD_ABSOLUTE_FORECAST_MISSING")
    return pred_self,pred_other


def _shuffle_abs_races(true_abs,by_race,rng):
    vals={}
    for key,member_keys in sorted(by_race.items()):
        options=[true_abs[x] for x in member_keys]
        rng.shuffle(options)
        for k,v in zip(member_keys,options):
            vals[k]=v
    if set(vals)!=set(true_abs):
        raise ValueError("HOLD_UNSAFE_ABSOLUTE_SHUFFLE_ROSTER")
    return vals


def absolute_first_section_forward_audit(
        timed,original,*,strict_class=False,permutations=299,
        seed=20261026):
    if (type(strict_class) is not bool or type(seed) is not int
            or type(permutations) is not int or
            not 49<=permutations<=2000):
        raise ValueError("HOLD_UNREGISTERED_ABSOLUTE_SOURCE_NULL_DESIGN")
    targets,true_abs,by_race,eligibility=_setup(
        timed,original,strict_class)
    meta={
        "status":"HOLD_ORIGINAL_HORSE_HISTORY_EVIDENCE_GATE"
                 if targets is None else STATUS,
        "design":"previously_locked_earlier_source_horse_vs_other_population",
        "target_measured":"real_focal_absolute_first_GPS_section_seconds",
        "target_is_not_peer_relative":True,
        "same_race_future_peer_outcomes_not_used_as_prediction_features":True,
        "pre_first_market_source_availability_not_independently_verified":True,
        "original_source_edition_matches_20261014":False,
        "no_real_JRA_wagering_training_or_critical_odds_inferred":True,
        "not_a_new_confirmatory_prospective_test":True,
        "no_animal_rider_trainer_IDs_or_individual_times_exported":True,
        **eligibility,
    }
    if targets is None:
        return meta
    true_preds,other=_forecasts(
        timed,targets,true_abs,true_abs,strict_class)
    real_rmse=_paired_equal_horse_rmse(targets,true_preds)
    other_rmse=_paired_equal_horse_rmse(targets,other)
    rng=random.Random(seed)
    null=[]
    for _ in range(permutations):
        synthetic=_shuffle_abs_races(true_abs,by_race,rng)
        preds,context=_forecasts(
            timed,targets,true_abs,synthetic,strict_class)
        if any(abs(a-b)>1e-12 for a,b in zip(context,other)):
            raise AssertionError("HOLD_PAST_CONTEXT_BASELINE_CHANGED_BY_IDENTITY_NULL")
        null.append(_paired_equal_horse_rmse(targets,preds))
    null.sort()
    empirical_fraction=sum(v<=real_rmse for v in null)/len(null)
    return {
        **meta,
        "observed_original_horse_history_absolute_RMSE_seconds":real_rmse,
        "observed_original_other_horse_history_absolute_RMSE_seconds":other_rmse,
        "other_minus_own_RMSE_seconds":other_rmse-real_rmse,
        "relative_RMSE_improvement_vs_other_history":(
            (other_rmse-real_rmse)/other_rmse if other_rmse>0 else None),
        "same_race_history_identity_permutations":permutations,
        "null_fixed_seed":seed,
        "null_mean_absolute_RMSE_seconds":mean(null),
        "null_rmse_q05_q50_q95_seconds":[
            null[int((len(null)-1)*q)] for q in (.05,.5,.95)],
        "fraction_of_shuffled_past_horse_assignment_RMSE_better_or_equal_real":
            empirical_fraction,
        "descriptive_observed_minus_shuffled_null_mean_seconds":
            real_rmse-mean(null),
        "source_original_absolute_first_section_only":True,
        "context_and_future_target_population_fixed_across_nulls":True,
        "test_date_removed_from_training_before_scoring":True,
        "within_race_shuffling_is_not_a_validated_exchangeability_null":True,
        "no_population_p_value_CI_or_biological_causality_inferred":True
    }
