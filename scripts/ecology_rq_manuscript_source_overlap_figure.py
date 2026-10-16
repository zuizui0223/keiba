#!/usr/bin/env python3
"""Figure 2: anonymized source-eligibility overlap, NOT behavioral effect.

Render only the permanently pinned anonymous original Doomben 2025/26
HORSES-ID/first GPS source-incidence summary. No source data, horse IDs,
names, rider/trainer licences or individual timings are accessed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"docs"/"evidence"/"rq-doomben-identical-horse-timescale-overlap-20261015.json"


def validate_evidence(path:Path=EVIDENCE)->dict:
    a=json.loads(path.read_text(encoding="utf-8"))
    if a["type"]!="ANONYMOUS_ORIGINAL_SOURCE_IDENTIFIABILITY_AUDIT":
        raise ValueError("HOLD_SOURCE_OVERLAP_FIGURE_NOT_FROM_FROZEN_AGGREGATE")
    source=a["source_identity_and_GPS_support"]
    if not (source["distinct_original_HORSES_IDs_any_marker"]==977
            and source["IDs_recorded_on_two_or_more_distinct_original_source_dates_any_context"]==228
            and source["original_IDs_blocked_for_inconsistent_names"]==0):
        raise ValueError("HOLD_ORIGINAL_ANIMAL_SOURCE_INCIDENCE_CHANGED")
    lock=a["locked_cohort"]
    if not (lock["original_2025_dates"]==23
            and lock["original_2026_dates"]==19
            and lock["fetched_source_dates_successfully"]==38
            and len(lock["source_HOLD_dates"])==4
            and lock["first_marker_m"]==150):
        raise ValueError("HOLD_SOURCE_CALENDAR_AND_MARKER_NOT_LOCKED")
    groups=a["two_original_horizon_population_comparisons"]
    primary=groups["same_150m_first_marker_and_official_race_distance"]
    strict=groups["add_exact_original_race_Class"]
    if not (primary["individuals_with_2plus_distinct_source_dates_in_2025"]==23
            and primary["individuals_with_1plus_date_in_both_2025_and_2026"]==26
            and strict["individuals_with_2plus_distinct_source_dates_in_2025"]==17
            and strict["individuals_with_1plus_date_in_both_2025_and_2026"]==6):
        raise ValueError("HOLD_SOURCE_YEAR_EVALUATION_POPULATIONS_INCONSISTENT")
    for group in (primary,strict):
        if not (
            group["individuals_with_2plus_dates_2025_and_1plus_date_2026"]==0
            and group["individuals_with_2plus_dates_each_year"]==0
            and group["cross_horizon_original_horse_ID_overlap_between_two_scored_groups_even_ignoring_context"]==0
            and group["scientific_status"]==
            "HOLD_INSUFFICIENT_SAME_HORSE_TWO_TIMESCALE_CONTEXT_SUPPORT"
        ):
            raise ValueError("HOLD_SAME_HORSE_2025_2026_INCIDENT_SUPPORT_NOT_ZERO")
    replicas=a["independent_original_source_replays"]
    if not (len(replicas)==2
            and replicas[0]["anonymous_aggregate_json_sha256"]==
                replicas[1]["anonymous_aggregate_json_sha256"]
            and replicas[0]["source_dates_fetched"]==
                replicas[1]["source_dates_fetched"]==38
            and a["comparison"]["CANNOT_identify_within_horse_temporal_decay_or_age_effect"]
            and a["comparison"]["no_original_horse_names_IDs_rider_trainer_licences_or_times_exposed"]):
        raise ValueError("HOLD_REPLAY_PROVENANCE_OR_CAUSAL_SCOPE_INCONSISTENT")
    return a


def overlap_figure(a:dict)->str:
    source=a["source_identity_and_GPS_support"]
    cohorts=a["two_original_horizon_population_comparisons"]
    primary=cohorts["same_150m_first_marker_and_official_race_distance"]
    strict=cohorts["add_exact_original_race_Class"]
    early=primary["individuals_with_2plus_distinct_source_dates_in_2025"]
    spanning=primary["individuals_with_1plus_date_in_both_2025_and_2026"]
    center=primary["individuals_with_2plus_dates_2025_and_1plus_date_2026"]
    rendered=[
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="750" viewBox="0 0 1200 750" role="img" aria-labelledby="figtitle figdesc">',
        '<title id="figtitle">No same horse has both earlier-year repeated and later-year marker-matched observations</title>',
        '<desc id="figdesc">At the same first 150 metre GPS marker and race distance, 23 individuals were recorded at least twice in 2025 and 26 were recorded in both 2025 and 2026. The source-ID intersection is zero. It is not evidence of loss of individual behavior.</desc>',
        '<rect width="1200" height="750" fill="#FFFFFF"/>',
        '<text x="48" y="45" font-size="27" font-weight="bold" fill="#263846" font-family="Arial,sans-serif">A common-horse test across time horizons is not estimable</text>',
        '<text x="48" y="75" font-size="15" fill="#506271" font-family="Arial,sans-serif">Doomben, original 2025 / 2026 source • first GPS 150 m • identical official race distance</text>',
        '<line x1="48" y1="97" x2="1150" y2="97" stroke="#CCD5DB"/>',
        '<circle cx="330" cy="288" r="158" fill="#E8EDF0" stroke="#7792A2" stroke-width="2"/>',
        '<circle cx="870" cy="288" r="158" fill="#F3EFE8" stroke="#A79A87" stroke-width="2"/>',
        f'<text x="330" y="262" font-size="78" fill="#304D61" font-weight="bold" text-anchor="middle" font-family="Arial,sans-serif">{early}</text>',
        '<text x="330" y="294" font-size="17" fill="#304D61" font-weight="bold" text-anchor="middle" font-family="Arial,sans-serif">horses</text>',
        '<text x="330" y="330" font-size="16" fill="#304D61" text-anchor="middle" font-family="Arial,sans-serif">≥2 separate dates in 2025</text>',
        f'<text x="870" y="262" font-size="78" fill="#645543" font-weight="bold" text-anchor="middle" font-family="Arial,sans-serif">{spanning}</text>',
        '<text x="870" y="294" font-size="17" fill="#645543" font-weight="bold" text-anchor="middle" font-family="Arial,sans-serif">horses</text>',
        '<text x="870" y="330" font-size="16" fill="#645543" text-anchor="middle" font-family="Arial,sans-serif">≥1 date in EACH year</text>',
        '<path d="M495,288 L525,288 M675,288 L705,288" stroke="#A9B4BE" stroke-width="2" stroke-dasharray="5,5"/>',
        f'<text x="600" y="268" font-size="78" font-weight="bold" text-anchor="middle" fill="#9B4B43" font-family="Arial,sans-serif">{center}</text>',
        '<text x="600" y="303" font-size="16" font-weight="bold" text-anchor="middle" fill="#9B4B43" font-family="Arial,sans-serif">shared horses</text>',
        '<text x="600" y="325" font-size="13" text-anchor="middle" fill="#596774" font-family="Arial,sans-serif">under BOTH rules</text>',
        '<text x="56" y="480" font-size="20" font-weight="bold" fill="#2C3945" font-family="Arial,sans-serif">Stricter control: also require identical official race Class</text>',
        '<rect x="54" y="499" width="1092" height="92" rx="9" fill="#F8F9FA" stroke="#E4E7EA"/>',
        f'<text x="220" y="555" font-size="47" text-anchor="middle" fill="#304D61" font-family="Arial,sans-serif">{strict["individuals_with_2plus_distinct_source_dates_in_2025"]}</text>',
        '<text x="322" y="552" font-size="16" fill="#52616B" font-family="Arial,sans-serif">2+ dates in 2025</text>',
        f'<text x="635" y="555" font-size="47" text-anchor="middle" fill="#645543" font-family="Arial,sans-serif">{strict["individuals_with_1plus_date_in_both_2025_and_2026"]}</text>',
        '<text x="733" y="552" font-size="16" fill="#52616B" font-family="Arial,sans-serif">observed in both years</text>',
        f'<text x="1030" y="555" font-size="47" text-anchor="middle" fill="#9B4B43" font-weight="bold" font-family="Arial,sans-serif">{strict["individuals_with_2plus_dates_2025_and_1plus_date_2026"]}</text>',
        '<text x="56" y="631" font-size="16" font-weight="bold" fill="#304254" font-family="Arial,sans-serif">Scientific decision: HOLD — no common individual with sufficient observations in both horizons</text>',
        f'<text x="56" y="657" font-size="14" fill="#5A6875" font-family="Arial,sans-serif">All first-GPS source markers: {source["distinct_original_HORSES_IDs_any_marker"]} unique horse IDs, {source["IDs_recorded_on_two_or_more_distinct_original_source_dates_any_context"]} repeated across dates; 38 / 42 original source meetings available.</text>',
        '<text x="56" y="681" font-size="14" fill="#5A6875" font-family="Arial,sans-serif">Two original source runs produced identical anonymous SHA256 aggregates. This is a sampling/identifiability result, NOT aging or loss of personality.</text>',
        '<text x="56" y="724" font-size="11" fill="#63717E" font-family="Arial,sans-serif">Source: Racing Queensland original Sectionals &amp; Open Data Web Services. Source-locked analyses; animal-level identifiers not published.</text>',
        '</svg>',
    ]
    return "\n".join(rendered)+"\n"


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence",type=Path,default=EVIDENCE)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    data=validate_evidence(args.evidence)
    graphic=overlap_figure(data)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(graphic,encoding="utf-8")
    print(json.dumps({
        "status":"AGGREGATE_ONLY_FIGURE_TWO_SOURCE_TIMESCALE_HOLD",
        "same_horses_meeting_both_original_date_exposure_rules":
            data["two_original_horizon_population_comparisons"][
                "same_150m_first_marker_and_official_race_distance"
            ]["individuals_with_2plus_dates_2025_and_1plus_date_2026"],
        "no_original_horse_IDs_or_GPS_outcomes_published":True,
        "not_a_causal_temporal_decay_effect":True,
    }))


if __name__=="__main__":
    main()
