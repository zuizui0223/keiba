#!/usr/bin/env python3
"""Recheck frozen official Racing Queensland HORSES roster/GPS fingerprints.

Unlike the first 548-row Canon/Cannon source audit, the Oct 14 543-row
archive stores per-date combined original GetHorsesForRace XML hashes,
alongside raw meeting, race and GPS SHA-256. The fixed allowlisted
12-date manifest is permanently retained as anonymous repository data.

Re-fetch only 5 originally changed days (+ one stable-control day)
by default; optionally all 12 dates. Use the SAME original
HORSES-ID/first-positive-GPS join logic as previous source audits.
Report source bytes and anonymous candidate counts; no original
HORSES, rider or trainer identifiers, names, GPS runner rows, predictions
or betting information are ever exported.

Crucial:
- A match with the Oct 14 snapshot does NOT identify why the
  Oct 13 548-row archive disagreed: Oct 13 horse-roster hashes were
  unavailable and the original analysis code also evolved.
- A mismatch is a source/code PROVENANCE hold, NEVER evidence for
  an environmental, behavioral or fitness change in any horse.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from ecology_rq_2026_calendar_overlap import COHORT, LOCKED_RACE_NUMBERS
from ecology_rq_multigoing_h1_preflight import (
    VENUE, audit_one_day
)
from ecology_rq_single_race_id_probe import request_xml
from ecology_rq_thoroughbred_sectional_audit import fetch_official


SCHEMA="racing-queensland-original-horse-source-fingerprint-v1"
DAYS=tuple(COHORT)
AFFECTED_DATES=(
    "2026-02-16","2026-03-26","2026-04-09",
    "2026-08-28","2026-10-11",
)
STABLE_CONTROL_DATE="2026-05-29"
SOURCE_KEYS=(
    "meeting_XML_SHA256",
    "race_XML_SHA256",
    "gps_CSV_SHA256",
    "combined_original_GetHorsesForRace_roster_SHA256",
)
SHA256=re.compile(r"^[0-9a-f]{64}$")
MAX_SOURCE_RACES_PER_DATE=8


def validate_baseline(o:dict)->dict:
    if (not isinstance(o,dict) or o.get("schema")!=SCHEMA
            or o.get("source_snapshot_run_id")!=38501390778
            or o.get("date_count")!=12 or
            tuple(sorted(o.get("per_date",{})))!=tuple(sorted(DAYS))):
        raise ValueError("HOLD_INVALID_OR_UNPINNED_12DATE_ORIGINAL_SOURCE_MANIFEST")
    total=0
    for date in DAYS:
        datum=o["per_date"][date]
        if not isinstance(datum,dict):
            raise ValueError("HOLD_SOURCE_MANIFEST_DATE_IS_NOT_OBJECT")
        for key in SOURCE_KEYS:
            if not isinstance(datum.get(key),str) or not SHA256.fullmatch(datum[key]):
                raise ValueError("HOLD_MALFORMED_ANONYMOUS_SOURCE_DIGEST")
        n=datum.get("verified_positive_first_GPS_HORSES_ID_matches")
        nr=datum.get("number_of_original_HORSES_roster_responses_hashed")
        if not isinstance(n,int) or not 0<=n<=150:
            raise ValueError("HOLD_MANIFEST_SOURCE_MATCH_COUNT_OUT_OF_BOUNDS")
        if not isinstance(nr,int) or not 1<=nr<=MAX_SOURCE_RACES_PER_DATE:
            raise ValueError("HOLD_MANIFEST_ROSTER_COUNT_OUT_OF_BOUNDS")
        total+=n
    if total!=o.get("source_positive_ID_GPS_total") or total!=543:
        raise ValueError("HOLD_TOTAL_ANONYMOUS_SOURCE_MATCHES_NOT_VERIFIED")
    return o["per_date"]


def check_original_archive(o:dict,archived:dict)->dict:
    """Verify the permanent digest fixture against the actual Oct-14 artifact."""
    baseline=validate_baseline(o)
    original=archived.get("source_manifest_original_SHA256_no_individuals")
    if not isinstance(original,dict) or set(original)!=set(DAYS):
        raise ValueError("HOLD_ARCHIVED_ORIGINAL_HORSES_MANIFEST_UNAVAILABLE")
    mismatches=[]
    for day in DAYS:
        old=original[day]
        hashes=old.get("original_source_SHA256") or {}
        expected=baseline[day]
        eq=(
            old.get("status")=="SOURCE_ORIGINAL_ID_GPS_AND_DECLARED_RIDER_AUDITED"
            and old.get("first_GPS_matched_original_source_rows")
                ==expected["verified_positive_first_GPS_HORSES_ID_matches"]
            and old.get("official_original_HORSES_roster_races_hashed")
                ==expected["number_of_original_HORSES_roster_responses_hashed"]
            and old.get("original_HORSES_roster_XML_sha256_aggregate")
                ==expected["combined_original_GetHorsesForRace_roster_SHA256"]
            and hashes.get("meeting_xml_sha256")
                ==expected["meeting_XML_SHA256"]
            and hashes.get("race_xml_sha256")
                ==expected["race_XML_SHA256"]
            and hashes.get("gps_csv_sha256")
                ==expected["gps_CSV_SHA256"]
        )
        if not eq:
            mismatches.append(day)
    if mismatches:
        raise ValueError("HOLD_PERMANENT_HASH_FIXTURE_DIFFERS_FROM_ORIGINAL_ARCHIVE")
    return {
        "status":"VERIFIED_PERMANENT_FINGERPRINT_FIXTURE_AGAINST_ORIGINAL_ARCHIVED_JSON",
        "original_source_workflow_run":38501390778,
        "verified_original_days":len(DAYS),
        "source_components_checked_per_day":4,
        "source_count_components_checked_per_day":2,
        "no_source_IDs_names_raw_horse_rows_exported":True,
    }


def compare_live_to_baseline(
    o:dict, live:dict, scope:str="affected_five_plus_control",
)->dict:
    baseline=validate_baseline(o)
    choices={
        "affected_five_plus_control":(*AFFECTED_DATES,STABLE_CONTROL_DATE),
        "all_twelve":DAYS,
    }
    if scope not in choices:
        raise ValueError("HOLD_REPLAY_SCOPE_NOT_LOCKED_OR_UNSUPPORTED")
    expected=set(choices[scope])
    if set(live)!=expected:
        raise ValueError("HOLD_UNEXPECTED_LIVE_SOURCE_DATE_SET")
    result={}
    counts=Counter()
    for day in sorted(expected):
        obs=live[day]
        if not isinstance(obs,dict):
            raise ValueError("HOLD_LIVE_SOURCE_RECORD_NOT_OBJECT")
        if obs.get("status")!="SOURCE_DATE_READ_AND_JOIN_AUDITED":
            result[day]={
                "status":"HOLD_LIVE_SOURCE_NOT_RETRIEVED_OR_AUDITED",
                "error_category":obs.get("error_category","HOLD_UNKNOWN_SOURCE"),
                "unretrieved_is_not_zero_horses":True,
            }
            counts["source_days_HOLD"]+=1
            continue
        old=baseline[day]
        eq={}
        for key in SOURCE_KEYS:
            value=obs.get(key)
            if not isinstance(value,str) or not SHA256.fullmatch(value):
                raise ValueError("HOLD_LIVE_SOURCE_HASH_INVALID")
            eq[key]=(value==old[key])
        curr=obs.get("verified_positive_first_GPS_HORSES_ID_matches")
        n=obs.get("number_of_original_HORSES_roster_responses_hashed")
        if (not isinstance(curr,int) or curr<0 or
                not isinstance(n,int) or not 1<=n<=MAX_SOURCE_RACES_PER_DATE):
            raise ValueError("HOLD_LIVE_SOURCE_COUNTS_INVALID")
        count_same=curr==old["verified_positive_first_GPS_HORSES_ID_matches"]
        roster_count_same=n==old["number_of_original_HORSES_roster_responses_hashed"]
        if not all(eq.values()):
            status="HOLD_ONE_OR_MORE_OFFICIAL_ORIGINAL_RESPONSE_BYTES_DIFFER_FROM_FROZEN_ROSTER_GPS_SOURCE"
            counts["dates_with_one_or_more_original_source_bytes_changed"]+=1
        elif not count_same or not roster_count_same:
            status="HOLD_EXACT_SAME_ORIGINAL_BYTES_BUT_MATCHING_COUNT_DIFFERS_CODE_OR_ENVIRONMENT"
            counts["dates_with_same_bytes_but_join_count_changed"]+=1
        else:
            status="SOURCE_BYTES_AND_JOIN_COUNTS_MATCH_PINNED_20261014_SNAPSHOT"
            counts["dates_fully_matching_frozen_source_and_count"]+=1
        counts["source_days_audited"]+=1
        for key,match in eq.items():
            counts[key+"_matching"]+=int(match)
        result[day]={
            "status":status,
            "source_bytes_match_exact_20261014_by_component":eq,
            "original_horse_roster_XML_response_count_matches":roster_count_same,
            "source_join_count_matches_frozen_roster_snapshot":count_same,
            "frozen_matched_source_rows":old[
                "verified_positive_first_GPS_HORSES_ID_matches"
            ],
            "live_matched_source_rows":curr,
            "matched_source_row_difference_later_minus_frozen":curr-old[
                "verified_positive_first_GPS_HORSES_ID_matches"
            ],
            "no_individual_original_ID_or_name_exported":True,
        }
    if counts["source_days_HOLD"]>0:
        overall="HOLD_SOME_ORIGINAL_SOURCE_DATES_NOT_RETRIEVED"
    elif counts["dates_with_one_or_more_original_source_bytes_changed"]>0:
        overall="HOLD_RQ_SOURCE_ROSTER_OR_OTHER_ORIGINAL_RESPONSE_DRIFTED"
    elif counts["dates_with_same_bytes_but_join_count_changed"]>0:
        overall="HOLD_RQ_ORIGINAL_BYTES_STABLE_BUT_MATCHING_RULE_CHANGED"
    else:
        overall="SOURCE_SNAPSHOT_REPLAY_MATCHES_20261014_FOUR_ORIGINAL_COMPONENTS"
    return {
        "status":overall,
        "scope":scope,
        "compared_to_frozen_workflow_run":38501390778,
        "source_id":"Racing Queensland official original HORSES and first GPS",
        "source_dates_queried":sorted(expected),
        "source_component_status_counts":dict(counts),
        "per_date_anonymous_comparison":result,
        "does_not_reconstruct_earlier_original_548_row_roster":True,
        "old_20261013_GetHorsesForRace_XML_was_NOT_fingerprinted":True,
        "same_bytes_do_not_verify_actual_starter_status_or_biological_response":True,
        "not_H1_H2_heritability_personality_competition_evidence":True,
        "no_animal_rider_trainer_identifiers_or_raw_GPS_written":True,
    }


def safe_original_source_error_code(exc:Exception)->str:
    """Allow ONLY finite, non-identifying source-validation error codes."""
    prefix=str(exc).split(":",1)[0]
    if isinstance(exc,ValueError) and re.fullmatch(r"HOLD_[A-Z0-9_]{3,100}",prefix):
        return prefix
    if isinstance(exc,TimeoutError):
        return "HOLD_ORIGINAL_SOURCE_TIMEOUT"
    if isinstance(exc,OSError):
        return "HOLD_ORIGINAL_SOURCE_NETWORK_IO"
    return "HOLD_SOURCE_FAILURE_UNCLASSIFIED"


def fetch_live(
    *, scope:str="affected_five_plus_control",
    soap=request_xml,
    gps=fetch_official,
)->dict:
    choices={
        "affected_five_plus_control":(*AFFECTED_DATES,STABLE_CONTROL_DATE),
        "all_twelve":DAYS,
    }
    if scope not in choices:
        raise ValueError("HOLD_UNAPPROVED_REPLAY_DATE_SCOPE")
    observed={}
    for day in choices[scope]:
        expected_ground,source_key=COHORT[day]
        roster_digests={}
        def traced_request(op,params):
            root,url,sha=soap(op,params)
            if op=="GetHorsesForRace":
                race_id=str(params["raceId"])
                if race_id in roster_digests:
                    raise ValueError("HOLD_DUPLICATE_RACE_ROSTER_SOURCE_RESPONSE")
                if not SHA256.fullmatch(sha):
                    raise ValueError("HOLD_UNVERIFIABLE_ORIGINAL_RACE_ROSTER_SOURCE_SHA")
                roster_digests[race_id]=sha
            return root,url,sha
        try:
            info,entries=audit_one_day(
                day,soap=traced_request,gps=gps,
                venue=VENUE,locked_config={
                    "source":source_key,
                    "ground_expected":expected_ground,
                    "races":LOCKED_RACE_NUMBERS,
                },
                race_selection=LOCKED_RACE_NUMBERS,
            )
            combined=hashlib.sha256("".join(
                f"{rid}:{digest}\n"
                for rid,digest in sorted(roster_digests.items())
            ).encode("ascii")).hexdigest()
            source=info["source_hashes"]
            observed[day]={
                "status":"SOURCE_DATE_READ_AND_JOIN_AUDITED",
                "verified_positive_first_GPS_HORSES_ID_matches":len(entries),
                "number_of_original_HORSES_roster_responses_hashed":len(roster_digests),
                "meeting_XML_SHA256":source["meeting_xml_sha256"],
                "race_XML_SHA256":source["race_xml_sha256"],
                "gps_CSV_SHA256":source["gps_csv_sha256"],
                "combined_original_GetHorsesForRace_roster_SHA256":combined,
            }
        except (ValueError,OSError,TimeoutError) as error:
            # Never output the exception string: a third-party response
            # may contain original names or internal numeric IDs.
            observed[day]={
                "status":"HOLD_UNRECONCILED_OFFICIAL_SOURCE_DATE",
                "error_category":type(error).__name__,
                "anonymous_HOLD_validation_code":safe_original_source_error_code(error),
                "unretrieved_is_not_zero_horses":True,
            }
    return observed


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--archived-aggregate",type=Path,default=None)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--scope",
        choices=("affected_five_plus_control","all_twelve"),
        default="affected_five_plus_control")
    p.add_argument("--no-live",action="store_true",
                   help="Only validate the permanent baseline against archived source JSON")
    args=p.parse_args()
    baseline=json.loads(args.baseline.read_text(encoding="utf-8"))
    permanent_archive=None
    if args.archived_aggregate is not None:
        archive=json.loads(args.archived_aggregate.read_text(encoding="utf-8"))
        permanent_archive=check_original_archive(baseline,archive)
    elif args.no_live:
        raise ValueError("HOLD_OFFLINE_ARCHIVE_VERIFICATION_REQUIRES_ARCHIVED_JSON")
    if args.no_live:
        report={
            "status":"ARCHIVED_ORIGINAL_SOURCE_FINGERPRINT_PIN_VERIFIED",
            "archive_validation":permanent_archive,
            "no_original_horse_IDs_or_raw_runner_rows_exported":True,
        }
    else:
        current=fetch_live(scope=args.scope)
        report=compare_live_to_baseline(baseline,current,scope=args.scope)
        report["archived_fixture_validation"]=permanent_archive
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "scope":args.scope,
        "archived_fixture_verified":bool(permanent_archive),
        "counts":report.get("source_component_status_counts",{}),
    },ensure_ascii=False))


if __name__=="__main__":
    main()
