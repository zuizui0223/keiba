#!/usr/bin/env python3
"""Reconcile source-count drift across ORIGINAL Racing Queensland audit runs.

Old run 38347984553 (2026-10-13): pre-rider Cannon Park calendar
  aggregate-only JSON (548 original HORSES-ID × positive-GPS rows).
New run 38501390778 (2026-10-14): 12-date rider-switch/source-fingerprint
  aggregate-only JSON (543 such rows).

This tool reads ONLY anonymized original-source workflow artifacts,
compares exact per-date original GPS, Meeting and Races SHA-256, and
localizes count changes. It deliberately refuses to infer that an
unchanged GPS means the original HORSES roster also stayed unchanged.

Because old GetHorsesForRace XML response hashes were NEVER saved in
the first run, the causes of a changed HORSES-ID name/telemetry join
remain underidentified between (1) source roster version drift and
(2) code or identity-matching rule changes across the two commits.

No raw horse names, numeric original IDs, licence IDs, GPS rows or
individual predictions are ingested or exported.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


EARLIER_RUN=38347984553
LATER_RUN=38501390778
EARLIER_COMMIT="edabd5f4af01b0508df45ee8eadbaff859243da3"
LATER_COMMIT="8e790d20dded66dee52859e12260b4790f3e6e7a"
# Preexisting source calendar locked in a dedicated file in the PR.
DAYS=(
    "2026-02-16","2026-03-12","2026-03-26","2026-04-04",
    "2026-04-09","2026-05-15","2026-05-29","2026-07-23",
    "2026-08-22","2026-08-28","2026-08-29","2026-10-11",
)
KEYS=("meeting_xml_sha256","race_xml_sha256","gps_csv_sha256")
SHA=re.compile(r"^[0-9a-f]{64}$")


def _validate_sha(value):
    if not isinstance(value,str) or not SHA.fullmatch(value):
        raise ValueError("HOLD_INVALID_SOURCE_SHA256_IN_ARCHIVED_AUDIT")
    return value


def _only_date_info(record:dict,fmt:str)->dict:
    if not isinstance(record,dict):
        raise ValueError("HOLD_ARCHIVE_DATE_VALUE_NOT_OBJECT")
    if fmt=="early":
        if record.get("status") not in {
            "SOURCE_DATE_READ_AND_ID_GPS_MATCHED",
            "SOURCE_DATE_READ_RACE_LEVEL_GROUND_DIFFERS_FROM_PAGE",
        }:
            raise ValueError("HOLD_OLDER_SOURCE_DATE_NOT_AUDITED")
        count=record.get("candidate_ID_linked_positive_first_GPS_rows")
        hashes=record.get("source_hashes")
        roster_sha=None
        n_roster_races=None
    else:
        if record.get("status")!="SOURCE_ORIGINAL_ID_GPS_AND_DECLARED_RIDER_AUDITED":
            raise ValueError("HOLD_NEWER_SOURCE_DATE_NOT_AUDITED")
        count=record.get("first_GPS_matched_original_source_rows")
        hashes=record.get("original_source_SHA256")
        roster_sha=_validate_sha(record.get(
            "original_HORSES_roster_XML_sha256_aggregate"
        ))
        n_roster_races=record.get("official_original_HORSES_roster_races_hashed")
        if (not isinstance(n_roster_races,int) or
                n_roster_races<1 or n_roster_races>8):
            raise ValueError("HOLD_INVALID_NEWER_ROSTER_RESPONSE_COUNT")
    if not isinstance(count,int) or not 0<=count<=150:
        raise ValueError("HOLD_SOURCE_COUNT_OUTSIDE_BOUNDED_RACE_AUDIT")
    if not isinstance(hashes,dict):
        raise ValueError("HOLD_SOURCE_HASH_MAP_MISSING")
    hashes={key:_validate_sha(hashes.get(key)) for key in KEYS}
    return {
        "source_positive_GPS_HORSES_ID_join_count":count,
        "three_source_hashes":hashes,
        "GetHorsesForRace_response_combined_SHA256":roster_sha,
        "number_of_horse_roster_XML_responses_hashed":n_roster_races,
    }


def audit(early:dict,later:dict)->dict:
    """Compare only allowlisted aggregate fields; never pass through payloads.

    Accept only the established two source formats for two known audited
    workflow runs. Do not mistake arbitrary JSON/horse data for a source
    audit or infer that any animal-specific response is zero.
    """
    old=early.get("date_scoped_source_manifest")
    new=later.get("source_manifest_original_SHA256_no_individuals")
    if (not isinstance(old,dict) or not isinstance(new,dict) or
            tuple(sorted(old))!=tuple(sorted(DAYS)) or
            tuple(sorted(new))!=tuple(sorted(DAYS))):
        raise ValueError("HOLD_SOURCE_CALENDARS_NOT_THE_SAME_TWELVE_DAYS")
    status_counts=Counter()
    rows={}
    older_count,newer_count=0,0
    changed=[]
    for date in DAYS:
        before=_only_date_info(old[date],"early")
        after=_only_date_info(new[date],"later")
        old_n=before["source_positive_GPS_HORSES_ID_join_count"]
        new_n=after["source_positive_GPS_HORSES_ID_join_count"]
        delta=new_n-old_n
        identical={
            key:(before["three_source_hashes"][key]
                 ==after["three_source_hashes"][key])
            for key in KEYS
        }
        status_counts["source_meetings_checked"]+=1
        status_counts["meeting_XML_unchanged"]+=int(identical[KEYS[0]])
        status_counts["races_XML_unchanged"]+=int(identical[KEYS[1]])
        status_counts["GPS_CSV_unchanged"]+=int(identical[KEYS[2]])
        status_counts["dates_with_join_count_change"]+=int(delta!=0)
        status_counts["dates_with_original_source_byte_change"]+=int(not all(identical.values()))
        status_counts["newer_roster_has_sha256"]+=1
        if delta:
            changed.append(date)
        rows[date]={
            "before_candidate_count":old_n,
            "after_candidate_count":new_n,
            "candidate_delta_later_minus_earlier":delta,
            "same_exact_original_bytes_per_source":identical,
            # Full source digests are publicly verifiable anonymized
            # provenance. Retain once per run/date for future comparisons.
            "original_source_SHA256_in_earlier_run":
                before["three_source_hashes"],
            "original_source_SHA256_in_later_run":
                after["three_source_hashes"],
            "earlier_horse_roster_SHA256":
                None,
            "later_horse_roster_combined_SHA256":
                after["GetHorsesForRace_response_combined_SHA256"],
            "later_horse_roster_race_responses_hashed":
                after["number_of_horse_roster_XML_responses_hashed"],
            "is_horse_roster_byte_change_identifiable_from_both_snapshots":
                False,
        }
        older_count+=old_n
        newer_count+=new_n
    if status_counts["dates_with_original_source_byte_change"]>0:
        state="HOLD_ORIGINAL_MEETING_RACE_OR_GPS_SOURCE_BYTES_CHANGED"
    elif changed:
        state="HOLD_SAME_ORIGINAL_3_SOURCES_DIFFERENT_JOIN_COUNTS_ROSTER_OR_CODE_UNRESOLVED"
    else:
        state="SOURCE_THREE_COMPONENTS_AND_JOIN_COUNTS_STABLE_ROSTER_PREVIOUSLY_UNHASHED"
    # A minimal count consistency check prevents a malformed artifact
    # from supporting the claim that old/new scientific populations match.
    old_total=early.get("support",{}).get(
        "positive_first_section_id_linked_candidate_rows"
    )
    recent=later.get("source_snapshot_candidate_count_audit",{})
    if (old_total!=older_count or
            recent.get("now_original_Cannon_candidate_rows")!=newer_count):
        raise ValueError("HOLD_ARCHIVED_TOTAL_COUNTS_DO_NOT_MATCH_PER_DATE")
    return {
        "status":state,
        "source_publisher":"Racing Queensland first-party SOAP and GPS",
        "earlier_workflow_run":EARLIER_RUN,
        "earlier_original_commit":EARLIER_COMMIT,
        "later_workflow_run":LATER_RUN,
        "later_original_commit":LATER_COMMIT,
        "source_date_count":len(DAYS),
        "source_original_id_GPS_linked_candidates_earlier":older_count,
        "source_original_id_GPS_linked_candidates_later":newer_count,
        "source_join_candidate_change_later_minus_earlier":newer_count-older_count,
        "source_dates_with_changed_candidate_count":changed,
        "source_component_equality_counts":dict(status_counts),
        "per_original_meeting_day":rows,
        "GetHorsesForRace_comparable_earlier_response_hashes_available":False,
        "different_source_parser_code_versions_cannot_be_ruled_out":True,
        "original_horse_nomination_roster_changes_cannot_be_ruled_out":True,
        "missing_count_means_zero_biological_response":False,
        "source_join_count_stability_proves_same_horse_identity_membership":False,
        "any_ecological_H1_or_H2_claim_permitted_from_drift":False,
        "no_horse_rider_trainer_names_licence_IDs_or_records_exported":True,
        "limits":[
            "Early workflow did not retain per-race original GetHorsesForRace XML hashes; roster bytes across these two historical runs cannot be compared.",
            "Source GPS, meeting and race response SHA-256 equality rules out changes to those exact three downloaded responses, not to GetHorsesForRace or code/join logic.",
            "The two runs used different code commits and may have different matching/selection algorithms, so the source of lost matches is not identifiable.",
            "Per-date count equality alone cannot verify unchanged source horse membership, true starter status, or changes to jockey/trainer assignment.",
            "Never silently use earlier ICCs as numerically reproduced by later official source snapshots without the same code revision and fully pinned original roster inputs.",
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--earlier",type=Path,required=True,
                   help="Original aggregate JSON from workflow run 38347984553")
    p.add_argument("--later",type=Path,required=True,
                   help="Original rider-source aggregate JSON from workflow run 38501390778")
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    original=json.loads(args.earlier.read_text(encoding="utf-8"))
    recent=json.loads(args.later.read_text(encoding="utf-8"))
    outcome=audit(original,recent)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":outcome["status"],
        "old":outcome["source_original_id_GPS_linked_candidates_earlier"],
        "new":outcome["source_original_id_GPS_linked_candidates_later"],
        "per_date_changes":{
            day:outcome["per_original_meeting_day"][day][
                "candidate_delta_later_minus_earlier"
            ] for day in outcome["source_dates_with_changed_candidate_count"]
        },
        "source_equality":outcome["source_component_equality_counts"],
        "older_roster_hash_available":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
