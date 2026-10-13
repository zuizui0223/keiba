#!/usr/bin/env python3
"""REAL-HORSE exploratory early-pacing *consistency* audit.

Observation: verified original Racing Queensland HORSES ID linked by
exact race/name to a positive first-sectional time, from the LOCKED 12
2026 Cannon Park meetings. This is NOT ground-response H1, NOT
competition-context H2, and does not measure fitness or heritability.

A horse's first-sectional time is compared with the other observed GPS
horses IN THE SAME RACE: seconds minus mean other timed runners' seconds.
This contrast is an explicitly RELATIVE behavioral metric: contemporaneous
opponents mechanically change it; therefore it CANNOT establish an
absolute-speed social interaction. This definition is a different
scientific question from the H2 absolute-focal-speed endpoint.

Quantifies covariance of same-HORSES-ID relative early pace across
different dates with the SAME official race distance and first-distance
marker (and a class-matched sensitivity). A seeded within-race-label
permutation is an exploratory null reference, not causal randomization,
confirmatory p value, or peer-pressure mechanism.

No raw horse ID, horse name, timing row, or individual prediction is
saved or returned by this module. Aggregate-only data.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import math
import random
from statistics import mean, median


def prepare(rows: list[dict], min_race_telemetry: int = 4) -> tuple[list[dict], dict]:
    if min_race_telemetry < 3:
        raise ValueError("HOLD_FIELD_COVERAGE_THRESHOLD_TOO_LOW")
    by_race: dict[tuple[str,int], list[dict]] = defaultdict(list)
    horse_day = set()
    for row in rows:
        for key in (
            "day", "race_number", "horse_id", "horse_name",
            "distance", "first_marker_m", "first_section_sec", "class",
        ):
            if key not in row:
                raise ValueError("HOLD_SOURCE_ROW_FIELD_MISSING")
        key = (row["horse_id"], row["day"])
        if key in horse_day:
            raise ValueError("HOLD_SAME_HORSES_ID_REPEATED_WITHIN_DATE")
        horse_day.add(key)
        secs = float(row["first_section_sec"])
        mark = float(row["first_marker_m"])
        if not (math.isfinite(secs) and secs > 0 and
                math.isfinite(mark) and mark > 0):
            raise ValueError("HOLD_FIRST_SECTION_UNAVAILABLE")
        by_race[(row["day"], row["race_number"])].append(row)
    if not by_race:
        raise ValueError("HOLD_NO_POSITIVE_FIRST_SECTION_RECORDS")

    result: list[dict] = []
    distribution = Counter()
    for (day, race), group in sorted(by_race.items()):
        n = len(group)
        distribution[n] += 1
        if n < min_race_telemetry:
            continue
        if len({r["distance"] for r in group}) > 1:
            raise ValueError("HOLD_INCONSISTENT_OFFICIAL_DISTANCE_WITHIN_RACE")
        if len({r["first_marker_m"] for r in group}) > 1:
            raise ValueError("HOLD_INCONSISTENT_FIRST_SECTION_MARKER_WITHIN_RACE")
        if len({r["class"] for r in group}) > 1:
            raise ValueError("HOLD_INCONSISTENT_CLASS_WITHIN_RACE")
        total = sum(r["first_section_sec"] for r in group)
        for row in group:
            # Leave the focal horse OUT of the peer reference average.
            outcome = float(row["first_section_sec"])-(total-row["first_section_sec"])/(n-1)
            result.append({
                "horse_id": row["horse_id"],
                "horse_name": row["horse_name"],
                "day": day,
                "race_number": race,
                "official_distance": row["distance"],
                "first_section_marker": float(row["first_marker_m"]),
                "race_class": row["class"],
                "relative_early_section_sec": outcome,
                "peer_count_with_positive_GPS": n-1,
            })
    return result, {
        "all_races_with_eligible_positive_GPS": len(by_race),
        "races_with_at_least_4_positive_first_intervals":
            sum(k>=min_race_telemetry for k,v in distribution.items() for _ in range(v)),
        "positive_first_section_rows_retained": len(result),
        "races_by_positive_GPS_row_count": dict(sorted(distribution.items())),
        "individual_absent_GPS_or_zero_time_NOT_assumed_DNF": True,
        "complete_verified_official_starter_rosters": False,
    }


def _stratum_key(row: dict, strict_class: bool) -> tuple:
    return (row["horse_id"], row["official_distance"],
            round(row["first_section_marker"], 4),
            row["race_class"] if strict_class else None)


def pairs(rows: list[dict], *, strict_class: bool) -> dict:
    groups = defaultdict(list)
    for row in rows:
        groups[_stratum_key(row, strict_class)].append(row)
    per_horse_stratum = []
    horses = set()
    obs_pairs = 0
    for (hid, *_), items in groups.items():
        days = {v["day"] for v in items}
        if len(days) < 2 or len(days) != len(items):
            continue
        values = [x["relative_early_section_sec"] for x in items]
        products = [
            values[i] * values[j]
            for i in range(len(values))
            for j in range(i+1, len(values))
        ]
        if products:
            horses.add(hid)
            obs_pairs += len(products)
            per_horse_stratum.append(mean(products))
    return {
        "horse_IDs_with_at_least_2_different_date_measurements_same_distance_marker_and_optional_class":
            len(horses),
        "repeated_horse_by_course_strata":len(per_horse_stratum),
        "different_date_observation_pairs":obs_pairs,
        # Means of within-horse pairwise signed products in seconds^2.
        # NOT ICC or model-estimated between-animal variance.
        "equal_stratum_weighted_pair_product_seconds_squared":
            mean(per_horse_stratum) if per_horse_stratum else None,
    }


def randomization_reference(
    rows: list[dict], *, strict_class: bool,
    permutations: int = 299, seed: int = 20261013,
) -> dict:
    if permutations < 50:
        raise ValueError("HOLD_TOO_FEW_SOFTWARE_PERMUTATIONS")
    observed = pairs(rows, strict_class=strict_class)
    if observed["repeated_horse_by_course_strata"] < 5:
        return {
            "status":"HOLD_TOO_FEW_REPEATED_HORSE_CONTEXTS",
            "observed":observed, "permutation_count":0,
            "permutation_reference_is_causal_or_preregistered":False,
        }
    by_race = defaultdict(list)
    for index, row in enumerate(rows):
        by_race[(row["day"],row["race_number"])].append(index)
    reference = []
    rng = random.Random(seed)
    for _ in range(permutations):
        assigned = [r["relative_early_section_sec"] for r in rows]
        for positions in by_race.values():
            perm = [assigned[i] for i in positions]
            rng.shuffle(perm)
            for i, val in zip(positions, perm):
                assigned[i] = val
        mutated = [
            {**row, "relative_early_section_sec":assigned[index]}
            for index,row in enumerate(rows)
        ]
        val = pairs(mutated, strict_class=strict_class)
        if val["equal_stratum_weighted_pair_product_seconds_squared"] is not None:
            reference.append(val["equal_stratum_weighted_pair_product_seconds_squared"])
    if len(reference) != permutations:
        raise ValueError("HOLD_NULL_PERMUTATION_SAMPLES_INCOMPLETE")
    ref_sorted = sorted(reference)
    observed_cov = observed["equal_stratum_weighted_pair_product_seconds_squared"]
    return {
        "status":"EXPLORATORY_IDENTITY_PERMUTATION_REFERENCE_ONLY",
        "observed":observed,
        "permutation_count":permutations,
        "permutation_seed":seed,
        "permutation_null_mean_seconds_squared":mean(reference),
        "permutation_reference_quantiles_05_50_95_seconds_squared":[
            ref_sorted[int((len(ref_sorted)-1)*p)] for p in (.05,.50,.95)
        ],
        "fraction_null_at_least_observed":
            (1+sum(x>=observed_cov for x in reference))/(permutations+1),
        "permutation_reference_is_causal_or_preregistered":False,
        "interpretation": (
            "Identity-label shuffle WITHIN the same timed-GPS race "
            "tests whether stable name/ID labels covary with early relative "
            "position more than a simple label-exchangeable reference. "
            "Nonrandom entry, trainer allocation, source selection and "
            "measurement error invalidate causal or confirmatory conclusions."
        ),
    }


def heldout_early_pace(
    rows: list[dict], *, strict_class: bool, min_prior: int = 1,
) -> dict:
    dates=sorted({r["day"] for r in rows})
    if len(dates)<6:
        return {"status":"HOLD_TOO_FEW_DATES_FOR_DESCRIPTIVE_HOLDOUT"}
    cutoff=dates[int(.8*len(dates))]
    history=defaultdict(list)
    for r in rows:
        if r["day"]<cutoff:
            history[_stratum_key(r, strict_class)].append(
                r["relative_early_section_sec"]
            )
    scores=[]
    repeated_horses=set()
    for r in rows:
        if r["day"]<cutoff:
            continue
        prev=history.get(_stratum_key(r, strict_class),[])
        if len(prev)<min_prior:
            continue
        # Fixed a priori shrinkage prevents overreacting to 1 past
        # noisy estimate; no hyperparameter is fitted on test dates.
        predicted=(len(prev)/(len(prev)+2))*mean(prev)
        obs=r["relative_early_section_sec"]
        scores.append((obs,predicted))
        repeated_horses.add(r["horse_id"])
    if len(scores)<5:
        return {
            "status":"HOLD_TOO_FEW_HELDOUT_REPEATED_HORSE_OBSERVATIONS",
            "train_date_end":max(d for d in dates if d<cutoff),
            "heldout_date_start":cutoff,
            "heldout_rows_with_prior_same_source_conditions":len(scores),
            "heldout_unique_horse_IDs":len(repeated_horses),
        }
    zero_rmse=math.sqrt(mean(y*y for y,p in scores))
    known_rmse=math.sqrt(mean((y-p)**2 for y,p in scores))
    return {
        "status":"EXPLORATORY_PAST_ID_PROFILE_RELATIVE_EARLY_PACE_HELDOUT",
        "train_date_end":max(d for d in dates if d<cutoff),
        "heldout_date_start":cutoff,
        "heldout_rows_with_prior_same_source_conditions":len(scores),
        "heldout_unique_horse_IDs":len(repeated_horses),
        "a_priori_prediction_shrinkage_n_over_n_plus_2":True,
        "null_zero_relative_split_RMSE_sec":zero_rmse,
        "past_ID_profile_RMSE_sec":known_rmse,
        "RMSE_gain_sec_positive_means_persistent_identity_predicts_better":
            zero_rmse-known_rmse,
        "target_uses_contemporaneous_other_timed_runners_after_race":True,
        "not_a_real_time_prediction_or_causal_inference":True,
    }


def analyze(rows: list[dict], permutations: int = 299) -> dict:
    eligible, q=prepare(rows)
    clean_ids = defaultdict(set)
    for row in eligible:
        clean_ids[row["horse_id"]].add(row["horse_name"])
    inconsistencies={hid for hid,names in clean_ids.items() if len(names)!=1}
    if inconsistencies:
        # Missing stable biological provenance: do not choose one spelling
        # or infer which date's source is authoritative.
        raise ValueError("HOLD_HORSES_ID_NAME_CHANGED_ACROSS_OBSERVATIONS")
    return {
        "status":"REAL_EQUINE_EARLY_PACE_REPRODUCIBILITY_EXPLORATORY_NOT_H1_H2",
        "measured_target":"seconds to first official GPS marker MINUS mean seconds of other timed GPS horses in race",
        "quantity":"race-relative FIRST SECTION timing persistence, not absolute focal speed",
        "data_readiness":q,
        "distance_first_marker_consistent": {
            "pair_product":pairs(eligible,strict_class=False),
            "permutation":randomization_reference(
                eligible,strict_class=False,permutations=permutations,
            ),
            "time_ordered_retrospective_check":heldout_early_pace(
                eligible,strict_class=False,
            ),
        },
        "distance_first_marker_AND_original_class_consistent": {
            "pair_product":pairs(eligible,strict_class=True),
            "permutation":randomization_reference(
                eligible,strict_class=True,permutations=permutations,
            ),
            "time_ordered_retrospective_check":heldout_early_pace(
                eligible,strict_class=True,
            ),
        },
        "independent_real_horse_effect_supported_H1":False,
        "independent_real_horse_effect_supported_H2":False,
        "not_yet_standard_ICC_or_random_slope_variance":True,
        "notes":[
            "Horse IDs linked by exact same-race names against official original SOAP only; confirmed starter/finish statuses remain unknown.",
            "GPS rows can be omitted due to missing/sensor-zero data; peer group does not certify all real starters.",
            "Within-race relative measurement depends mechanically on companions' first-section timing. It cannot estimate absolute focal behavioral reaction to opponents.",
            "Class-matched sensitivity is narrower but still not controlled for age, weight, jockey, injury/fitness or nonrandom race entry.",
            "Permuting identity labels within observed races preserves race timing distributions but is not experimental exchangeability.",
            "Source cohort dates were chosen after earlier exploratory analyses; any apparent permutation evidence is not prospectively preregistered.",
            "Observed ID covariance can indicate consistency of conditional race-relative early pace, not stable genetically encoded personality or adaptation.",
        ],
    }
