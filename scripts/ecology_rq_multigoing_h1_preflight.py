#!/usr/bin/env python3
"""Bounded REAL Thoroughbred within-ID Good/Soft/Heavy availability audit.

Source: Racing Queensland original SOAP HORSES IDs + original GPS sectionals.
EXACTLY FIVE preselected Cannon Park dates, at most four races/date.
Records no animal names, numeric IDs, official XML, or GPS runner rows.

This is a *design feasibility* screen, NOT a biological effect test.
Internal HORSES IDs may appear on NOMINATIONS rather than verified starts.
All-zero telemetry is not DNF; a positive sectional is not a certified
individual full-race finish. No behavior, plasticity or adaptation claims.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path

from ecology_rq_single_race_id_probe import (
    attr, horse_candidates, identified_meeting, request_xml, value, xml_nodes,
)
from ecology_rq_thoroughbred_sectional_audit import (
    duration_s, fetch_official, finite_number, parse as parse_sections,
)
from ecology_rq_official_id_crosswalk import canon_name, sections_in_memory


SELECTED = {
    "2026-05-15": {
        "source": "20260515-cairns", "ground_expected": "Heavy", "races": (1, 2, 3, 8)
    },
    "2026-05-29": {
        "source": "20260529-cairns", "ground_expected": "Soft", "races": (1, 2, 3, 8)
    },
    "2026-08-22": {
        "source": "20260822-cairns", "ground_expected": "Soft", "races": (1, 2, 3, 8)
    },
    "2026-08-29": {
        "source": "20260829-cairns", "ground_expected": "Good", "races": (1, 2, 3, 8)
    },
    "2026-10-11": {
        "source": "20261011-cairns", "ground_expected": "Good", "races": (1, 2, 3, 8)
    },
}
VENUE = "Ladbrokes Cannon Park"
MAX_RACES_PER_DAY = 8
MAX_DAYS = 5
ALL_EIGHT_RACES = tuple(range(1, 9))


def ground_class(label: str | None) -> str:
    """Only categorical recognition; no equal-distance ordinal scale."""
    label = (label or "").strip().lower()
    for name in ("good", "soft", "heavy"):
        if label.startswith(name):
            return name.title()
    return "UNKNOWN"


def selected_official_races(root, selected: tuple[int, ...]) -> tuple[dict, int]:
    nodes = xml_nodes(root, "Race")
    chosen = {}
    for node in nodes:
        number = value(node, "RaceNumber")
        if not number or not number.isdecimal():
            continue
        number = int(number)
        if number not in selected:
            continue
        rid = attr(node, "Id")
        if not rid or not rid.isdecimal() or number in chosen:
            raise ValueError("HOLD_DUPLICATE_OR_UNVERIFIED_RACE_ID")
        chosen[number] = {
            "id": rid,
            "ground": ground_class(value(node, "TrackRating")),
            "distance": (value(node, "Distance") or "UNKNOWN").strip(),
            "class": (value(node, "Class") or "UNKNOWN").strip(),
        }
    if not chosen:
        raise ValueError("HOLD_NO_OFFICIAL_SELECTED_RACES")
    return chosen, len(nodes)


def first_section_table(raw: bytes, date_iso: str) -> dict[tuple[int, str], dict]:
    """Timing and distance-marker values, never a whole-race or DNF label."""
    table = {}
    for full in raw.decode("utf-8-sig").splitlines():
        line = full.strip()
        if not line:
            continue
        parts = line.split(",", 2)
        if len(parts) != 3:
            raise ValueError("HOLD_BAD_VENDOR_SECTION_CSV")
        a, b, packed = (p.strip() for p in parts)
        if a == "Date" and b == "RaceNumber":
            continue
        day = datetime.strptime(a, "%d/%m/%Y").date().isoformat()
        if day != date_iso:
            raise ValueError("HOLD_GPS_SOURCE_DATE_DISAGREEMENT")
        number = int(b)
        columns = [x.strip() for x in packed.split(";")]
        if len(columns) < 5:
            raise ValueError("HOLD_INCOMPLETE_GPS_SECTIONS")
        name = canon_name(columns[0])
        key = number, name
        if key in table:
            raise ValueError("HOLD_DUPLICATE_GPS_NAME_IN_ONE_RACE")
        marker = finite_number(columns[2])
        signal = finite_number(columns[3])
        duration = duration_s(columns[4])
        # Strict: telemetry is considered observed only with both
        # positive source signal and positive first-section duration.
        observed = (marker is not None and marker > 0
                    and signal is not None and signal > 0
                    and duration is not None and duration > 0)
        table[key] = {
            "first_marker_m": marker if observed else None,
            "first_section_seconds": duration if observed else None,
            "early_section_observed": bool(observed),
        }
    if not table:
        raise ValueError("HOLD_EMPTY_SOURCE_SECTIONAL_FILE")
    return table


def audit_one_day(day: str, *, soap=request_xml, gps=fetch_official,
                  race_selection: tuple[int,...] | None = None,
                  locked_config: dict | None = None):
    if locked_config is None:
        if day not in SELECTED:
            raise ValueError("HOLD_DAY_NOT_IN_LOCKED_EXPOSURE_SAMPLE")
        config = SELECTED[day]
    else:
        # A separately versioned calendar cohort, not an arbitrary URL:
        # original files remain restricted to the explicit allowlist.
        from ecology_rq_thoroughbred_sectional_audit import APPROVED
        if (day[:5] != "2026-" or
                set(locked_config) != {"source", "ground_expected", "races"} or
                locked_config["source"] != day.replace("-", "") + "-cairns" or
                locked_config["source"] not in APPROVED or
                locked_config["ground_expected"] not in {"Good", "Soft", "Heavy"} or
                tuple(locked_config["races"]) != ALL_EIGHT_RACES):
            raise ValueError("HOLD_UNAPPROVED_EXTERNAL_COHORT_CONFIGURATION")
        config = locked_config
    selected = tuple(race_selection) if race_selection is not None else config["races"]
    if selected not in (config["races"], ALL_EIGHT_RACES):
        raise ValueError("HOLD_UNAPPROVED_RACE_SELECTION")
    if len(selected) > MAX_RACES_PER_DAY:
        raise ValueError("HOLD_TOO_MANY_RACES_PER_DATE")
    meeting_xml, _, meeting_sha = soap("GetMeetingsForDate", {"meetingDate": day})
    meeting_id, _ = identified_meeting(meeting_xml, day, VENUE)
    race_xml, _, race_sha = soap(
        "GetRacesForMeeting", {"meetingId": meeting_id}
    )
    races, available_count = selected_official_races(race_xml, selected)
    raw, _ = gps(config["source"])
    parsed = parse_sections(raw, "original Racing Queensland; aggregate only")
    if parsed["race_counts"]["source_dates"] != [day]:
        raise ValueError("HOLD_ORIGINAL_GPS_DATE_MISMATCH")
    first = first_section_table(raw, day)
    all_gps = sections_in_memory(raw)
    race_gps = defaultdict(list)
    name_race_ids = defaultdict(set)
    for row in all_gps:
        name = row["name_normalized"]
        race_gps[row["race_number"]].append(row)
        name_race_ids[name].add(row["race_number"])
    # A duplicate name in multiple race headings (usually one all-zero)
    # should never become a factual repeat starter.
    duplicate_day_names = {
        name for name, rr in name_race_ids.items() if len(rr) > 1
    }
    all_candidates = []
    for number, race in races.items():
        horses_xml, _, _ = soap(
            "GetHorsesForRace", {"raceId": race["id"]}
        )
        horses, shape = horse_candidates(horses_xml)
        ids = [h["horse_id"] for h in horses]
        names = [canon_name(h["horse_name"]) for h in horses]
        if not horses or len(set(ids)) != len(ids) or len(set(names)) != len(names):
            raise ValueError("HOLD_INVALID_OFFICIAL_RACE_HORSE_IDENTITIES")
        gps_names = [r["name_normalized"] for r in race_gps[number]]
        if len(set(gps_names)) != len(gps_names):
            raise ValueError("HOLD_DUPLICATE_GPS_RACE_HORSE_NAME")
        for horse, norm_name in zip(horses, names):
            measurement = first.get((number, norm_name))
            all_candidates.append({
                "horse_id": horse["horse_id"],
                "horse_name": norm_name,
                "day": day, "race_number": number,
                "ground": race["ground"],
                "expected_ground": config["ground_expected"],
                "distance": race["distance"], "class": race["class"],
                "first_marker_m": (measurement or {}).get("first_marker_m"),
                "first_section_sec": (measurement or {}).get("first_section_seconds"),
                "gps_named_row": bool(measurement),
                "gps_first_positive": bool(
                    measurement and measurement["early_section_observed"]
                ),
                "duplicate_gps_same_day_name": norm_name in duplicate_day_names,
            })
    counts = Counter(r["horse_id"] for r in all_candidates)
    for row in all_candidates:
        row["official_id_in_multiple_races_same_day"] = counts[row["horse_id"]] > 1
        row["eligible"] = bool(
            row["gps_first_positive"]
            and not row["duplicate_gps_same_day_name"]
            and not row["official_id_in_multiple_races_same_day"]
            and row["ground"] != "UNKNOWN"
            and row["distance"] != "UNKNOWN"
            and row["class"] != "UNKNOWN"
        )
    good = [row for row in all_candidates if row["eligible"]]
    inconsistent = sum(
        race["ground"] != config["ground_expected"]
        for race in races.values()
    )
    info = {
        "day": day, "venue": VENUE,
        "requested_race_numbers": list(selected),
        "official_race_numbers_available": sorted(races),
        "missing_official_race_numbers": sorted(set(selected) - set(races)),
        "source_api_race_total": available_count,
        "ground_expected_from_official_meeting_page": config["ground_expected"],
        "ground_disagreeing_with_page": inconsistent,
        "actual_official_ground_labels": dict(
            Counter(race["ground"] for race in races.values())
        ),
        "official_race_class_labels": dict(
            Counter(race["class"] for race in races.values())
        ),
        "official_race_distances": dict(
            Counter(race["distance"] for race in races.values())
        ),
        "api_horse_row_count": len(all_candidates),
        "distinct_official_ids_selected": len(counts),
        "official_ids_listed_more_than_once_on_date": sum(
            count > 1 for count in counts.values()
        ),
        "gps_first_positive_candidate_rows": sum(
            r["gps_first_positive"] for r in all_candidates
        ),
        "candidate_rows_with_same_day_duplicate_gps_name": sum(
            r["duplicate_gps_same_day_name"] for r in all_candidates
        ),
        "candidate_rows_with_no_exact_positive_first_section": sum(
            not r["gps_first_positive"] for r in all_candidates
        ),
        "eligible_official_ID_matched_first_section_rows": len(good),
        "source_hashes": {
            "meeting_xml_sha256": meeting_sha,
            "race_xml_sha256": race_sha,
            "gps_csv_sha256": hashlib.sha256(raw).hexdigest(),
        },
        "source_rights_attributed_to": "Racing Queensland",
        "raw_individual_horse_rows_exported": False,
    }
    return info, good


def comparison(*, soap=request_xml, gps=fetch_official,
               scope: str = "focused_four"):
    if scope not in ("focused_four", "extended_eight"):
        raise ValueError("HOLD_UNAPPROVED_EXPOSURE_SCOPE")
    if len(SELECTED) != MAX_DAYS:
        raise ValueError("HOLD_UNFROZEN_COHORT_SIZE")
    days = {}
    rows = []
    selection = {
        day: (cfg["races"] if scope == "focused_four" else ALL_EIGHT_RACES)
        for day, cfg in SELECTED.items()
    }
    for day in SELECTED:
        info, selected = audit_one_day(
            day, soap=soap, gps=gps, race_selection=selection[day])
        days[day] = info
        rows += selected
    per_id = defaultdict(list)
    for row in rows:
        per_id[row["horse_id"]].append(row)
    changed_name = sum(
        len({r["horse_name"] for r in series}) != 1
        for series in per_id.values()
        if len({r["day"] for r in series}) > 1
    )
    # Exclude any internally reused horse ID with *changed* canonical
    # horse name across days: true biological identity not established.
    consistent = [
        series for series in per_id.values()
        if len({r["horse_name"] for r in series}) == 1
    ]
    repeat = [
        series for series in consistent
        if len({r["day"] for r in series}) >= 2
    ]
    def wet_good(c):
        good = [r for r in c if r["ground"] == "Good"]
        wet = [r for r in c if r["ground"] in ("Soft", "Heavy")]
        return good, wet

    cross = [series for series in repeat if all(wet_good(series))]
    def same_stratum_pairs(include_class: bool):
        out = []
        qualifying = set()
        for series in consistent:
            strata = defaultdict(list)
            for row in series:
                key = (
                    row["distance"],
                    round(row["first_marker_m"], 3),
                    row["class"] if include_class else None,
                )
                strata[key].append(row)
            for key, data in strata.items():
                good, wet = wet_good(data)
                if not good or not wet:
                    continue
                qualifying.add(series[0]["horse_id"])
                diff = (sum(r["first_section_sec"] for r in wet)/len(wet) -
                        sum(r["first_section_sec"] for r in good)/len(good))
                out.append({
                    "horse_id": series[0]["horse_id"],
                    "mean_wet_minus_good_seconds": diff,
                    "n_good": len(good), "n_non_good": len(wet),
                    "marker_m": key[1],
                })
        return out, qualifying
    matched, ids = same_stratum_pairs(False)
    strict, strict_ids = same_stratum_pairs(True)
    replicated = [
        item for item in strict if item["n_good"] >= 2
        and item["n_non_good"] >= 2
    ]
    # These are DESCRIPTIVE directions only. Source cohorts have
    # opportunistic API coverage, nonrandom entry, true starter status
    # unverified and no horse-specific *official finishing* time.
    def summarize_pairs(data):
        return {
            "comparable_horse_ID_by_distance_first_marker_class": len(
                {r["horse_id"] for r in data}
            ),
            "same_horse_strata": len(data),
            "simple_unweighted_stratum_mean_wet_minus_good_first_section_seconds": (
                sum(v["mean_wet_minus_good_seconds"] for v in data)/len(data)
                if data else None
            ),
            "count_wet_first_section_slower": sum(
                v["mean_wet_minus_good_seconds"] > 0 for v in data
            ),
            "count_wet_first_section_faster": sum(
                v["mean_wet_minus_good_seconds"] < 0 for v in data
            ),
            "not_causal_or_individual_slope_variance": True,
        }
    wet_1_counts = Counter()
    for series in cross:
        labels = set(r["ground"] for r in series)
        wet_1_counts["good_vs_soft"] += int("Soft" in labels)
        wet_1_counts["good_vs_heavy"] += int("Heavy" in labels)
    supports = {
        "gps_positive_source_rows": len(rows),
        "distinct_official_HORSES_ID_after_same_day_ambiguity_exclusion": len(per_id),
        "HORSES_ids_recurring_across_at_least_two_actual_dates": len(repeat),
        "recurring_ids_with_inconsistent_names_blocked": changed_name,
        "recurrent_ids_with_both_Good_and_non_Good": len(cross),
        "contrast_types_with_at_least_one_repeat": dict(wet_1_counts),
        "horse_ID_with_Good_nonGood_at_same_race_distance_and_first_section_marker": len(ids),
        "strict_horse_ID_matching_official_distance_first_section_marker_and_race_class": len(strict_ids),
        "strict_strata_with_at_least_two_good_AND_two_wet_starts": len(replicated),
        "non_strict_distance_marker_first_section_contrast": summarize_pairs(matched),
        "same_distance_marker_and_class_first_section_contrast": summarize_pairs(strict),
        "strict_twice_each_support_count_is_a_power_analysis": False,
    }
    all_ground = Counter(
        row["ground"] for day in SELECTED for row in rows
        if row["day"] == day
    )
    unknown_counts = [
        day for day, v in days.items()
        if v["ground_disagreeing_with_page"] > 0
    ]
    return {
        "status": "REAL_EQUINE_MULTIGOING_FEASIBILITY_NOT_H1_H2_EVIDENCE",
        "source_publisher": "Racing Queensland original HORSES IDs and GPS",
        "design_frozen_before_statistical_effect_testing": scope == "focused_four",
        "race_selection_scope": scope,
        "exploratory_full_race_expansion_following_initial_design_audit": scope == "extended_eight",
        "selected_dates": list(SELECTED),
        "race_number_selection_per_date": {
            day: list(selection[day]) for day in SELECTED
        },
        "going_categories_from_official_API_not_numeric_assumed": True,
        "source_ground_metadata_conflicts": unknown_counts,
        "per_date": days,
        "overall_ground_labels_of_eligible_rows": dict(all_ground),
        "within_horse_support": supports,
        "data_row_horse_ID_or_name_output": False,
        "true_starter_and_finisher_status_verified": False,
        "first_section_timing_is_certified_full_race_performance": False,
        "fit_random_slope_H1": False,
        "fit_social_competition_H2": False,
        "limits": [
            "Official HORSES lists can include nominations, scratchings and multiple-race entries; positive GPS confirms telemetry, not final verified starter status.",
            "Same-day repeated IDs and duplicate GPS names are excluded, not selected by outcome.",
            "True horse finish times and official early-running order are not available from this source pairing.",
            "Non-good includes Soft and Heavy only for simple overlap screens; their effects need separate biologically meaningful estimates.",
            "Exact distance, first-section measurement marker and race class are required for strict within-horse support.",
            "Five dates and four preselected race numbers each in the original focused pilot; exploratory follow-on includes numbers 1-8 after inspecting design overlap.",
            "Neither the focused pilot nor subsequent eight-race expansion is a random ecological population sample or preregistered effect test.",
            "Even repeated ground contrasts can reflect selective nomination, course/weather/class/jockey and developmental changes.",
            "No published individual horse identities, names, sectional source rows, or derived performance predictions.",
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--scope", choices=("focused_four", "extended_eight"), default="focused_four")
    args = p.parse_args()
    out = comparison(scope=args.scope)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": out["status"],
        "scope":out["race_selection_scope"],
        "going": out["overall_ground_labels_of_eligible_rows"],
        "source_ground_metadata_conflicts": out["source_ground_metadata_conflicts"],
        "support": out["within_horse_support"],
        "per_date": {
            day: {
                "official_races_available": v["official_race_numbers_available"],
                "official_races_missing": v["missing_official_race_numbers"],
                "eligible_ID_first_GPS_rows": v["eligible_official_ID_matched_first_section_rows"],
                "API_ground_labels": v["actual_official_ground_labels"],
            } for day, v in out["per_date"].items()
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
