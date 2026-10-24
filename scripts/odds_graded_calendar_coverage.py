#!/usr/bin/env python3
"""Audit the outcome-INDEPENDENT denominator of a future G1/G2/G3 cohort.

One slot for EVERY official JRA flat G1/G2/G3 event in the declared 2026
Oct25–Dec27 schedule segment, no hidden selection of winning or losing
races. The 2027 Jan–Mar segment of the protocol is not yet included and
MUST remain HOLD for full-period calendar completeness.

Official source: https://jra.jp/datafile/seiseki/replay/2026/jyusyo.html
Only future scheduling information is included. All J-G steeplechase
grades and non-JRA races are OUT OF SCOPE. Only Kikka's finalized post
and official race ID are known. Future race numbers are NEVER invented.

This does NOT download licensed odds or validate actual results.
Manual source transcription is not an independently signed JRA calendar
feed. Locally claimed SHA/comment status is not independent prestart GH
proof. Outcome-based drops and unlisted races are prohibited.

CLI:
  python scripts/odds_graded_calendar_coverage.py \
    --calendar data/research/jra-graded-flat-2026oct25-dec27-calendar.json \
    --registry data/research/odds-prequential-2026oct24-coverage-registry.json \
    --output tmp/odds-graded-calendar-coverage.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

CALENDAR_SCHEMA="KEIBA_OFFICIAL_GRADED_FLAT_CALENDAR_SEGMENT_V1"
REGISTRY_SCHEMA="KEIBA_GRADED_PRESTART_COVERAGE_REGISTRY_V1"
PROTOCOL_SCHEMA="KEIBA_WIN_ODDS_PREQUENTIAL_COHORT_V1"
STATUS="PARTIAL_2026_JRA_FLAT_CALENDAR_ALL_SLOTS_COVERED_NOT_FULL_STUDY_HORIZON"
JST=ZoneInfo("Asia/Tokyo")
_GRADES={"G1","G2","G3"}
_ALLOWED={
    "upcoming_not_due",
    "preseal_sha_submitted_unverified",
    "preseal_external_proof_verified",
    "no_complete_two_win_snapshots",
    "source_publication_too_late",
    "runner_roster_changed",
    "public_source_unverified",
    "official_race_cancelled",
    "official_race_postponed",
    "result_independently_unavailable",
    "sealed_no_independent_GitHub_proof",
    "postrace_scored_provenance_not_independently_checked",
}
_SHA=re.compile(r"^[a-f0-9]{64}$")


def aware(ts):
    if not isinstance(ts,str):
        raise ValueError("HOLD_MISSING_COVERAGE_ASOF_TIME")
    val=datetime.fromisoformat(ts.replace("Z","+00:00"))
    if val.tzinfo is None or val.utcoffset() is None:
        raise ValueError("HOLD_COVERAGE_CLOCK_NEEDS_OFFSET")
    return val.astimezone(JST)


def _date(iso):
    if not isinstance(iso,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",iso):
        raise ValueError("HOLD_BAD_JRA_SCHEDULE_DATE")
    return datetime.fromisoformat(iso).date()


def _jra_official_url(url):
    try:
        uri=urlparse(url)
        return uri.scheme=="https" and uri.hostname in {
            "jra.jp","www.jra.jp","www.jra.go.jp"}
    except (TypeError,ValueError):
        return False


def validate_calendar(cal):
    if cal.get("schema")!=CALENDAR_SCHEMA:
        raise ValueError("HOLD_OFFICIAL_SEGMENT_SCHEMA_MISMATCH")
    if not _jra_official_url(cal.get("source_jra")):
        raise ValueError("HOLD_NO_OFFICIAL_JRA_SOURCE")
    if (cal.get("scope")!=(
            "JRA flat G1/G2/G3 only; excludes distinct J-G1/J-G2/J-G3 steeplechase grades and non-JRA racing")
            or cal.get("calendar_segment_is_entire_study_horizon") is not False
            or cal.get("all_official_event_post_times_known") is not False):
        raise ValueError("HOLD_UNCERTIFIED_COMPLETE_OR_DIFFERENT_CALENDAR_SCOPE")
    start=_date(cal.get("segment_start_jst"))
    end=_date(cal.get("segment_end_jst"))
    study_end=_date(cal.get("protocol_window_end_jst"))
    if not start<=end<study_end:
        raise ValueError("HOLD_SEGMENT_IS_NOT_PARTIAL_FUTURE_WINDOW")
    rows=cal.get("events")
    if not isinstance(rows,list) or not rows:
        raise ValueError("HOLD_NO_JRA_GRADED_RACE_SCHEDULE")
    if cal.get("expected_event_count")!=len(rows):
        raise ValueError("HOLD_JRA_CALENDAR_EVENT_COUNT_CHANGED")
    ids=set()
    by_date=Counter()
    for item in rows:
        dt=_date(item.get("scheduled_date_jst"))
        if not start<=dt<=end:
            raise ValueError("HOLD_GRADED_RACE_OUTSIDE_SCHEDULE_SEGMENT")
        if item.get("grade") not in _GRADES:
            raise ValueError("HOLD_NON_FLAT_GRADE_OR_UNKNOWN_CLASS")
        venue=item.get("venue")
        name=item.get("race_name_jp")
        if (not isinstance(venue,str) or not venue.strip()
                or not isinstance(name,str) or not name.strip()):
            raise ValueError("HOLD_UNIDENTIFIED_GRADED_RACE_VENUE_NAME")
        sid=f"{dt.isoformat()}|{venue}|{name}"
        if item.get("slot_id")!=sid or sid in ids:
            raise ValueError("HOLD_DUPLICATE_OR_MUTATED_CALENDAR_SLOT")
        ids.add(sid)
        by_date[dt.isoformat()]+=1
        post=item.get("source_reported_post_jst")
        if post is not None and aware(post).date()!=dt:
            raise ValueError("HOLD_OFFICIAL_POST_DATE_INCONSISTENT")
        rid=item.get("official_race_id")
        if rid is not None and (
                not isinstance(rid,str) or not rid.startswith(dt.isoformat()+"-")):
            raise ValueError("HOLD_RACE_ID_ATTACHED_TO_WRONG_DATE")
    return {
        "slot_ids":ids,
        "by_date":dict(by_date),
        "event_count":len(rows),
        "race_dates":len(by_date),
        "period_start":start.isoformat(),
        "period_end":end.isoformat(),
        "study_end":study_end.isoformat(),
    }


def audit(calendar,registry):
    verified_cal=validate_calendar(calendar)
    if registry.get("schema")!=REGISTRY_SCHEMA:
        raise ValueError("HOLD_COVERAGE_REGISTRY_SCHEMA")
    if registry.get("protocol_schema")!=PROTOCOL_SCHEMA:
        raise ValueError("HOLD_NOT_FROZEN_PROSPECTIVE_PROTOCOL")
    if registry.get("source_segment_jra")!=calendar.get("source_jra"):
        raise ValueError("HOLD_COVERAGE_REGISTRY_SOURCE_NOT_SAME_JRA_SCHEDULE")
    asof=aware(registry.get("declared_as_of_jst"))
    entries=registry.get("entries")
    if not isinstance(entries,list):
        raise ValueError("HOLD_MISSING_COVERAGE_REGISTER")
    if any(not isinstance(x,dict) or
           not isinstance(x.get("slot_id"),str) for x in entries):
        raise ValueError("HOLD_MALFORMED_COVERAGE_REGISTER")
    keys=[x["slot_id"] for x in entries]
    if len(set(keys))!=len(keys):
        raise ValueError("HOLD_DUPLICATED_REGISTERED_GRADED_RACE")
    unknown=sorted(set(keys)-verified_cal["slot_ids"])
    missing=sorted(verified_cal["slot_ids"]-set(keys))
    # These are errors in the monitoring denominator, not failures of
    # the horse's statistical forecast; do not silently ignore either.
    if unknown:
        raise ValueError("HOLD_NONCALENDAR_RACE_INSERTED_IN_PROSPECTIVE_COHORT")
    if missing:
        raise ValueError("HOLD_CALENDAR_RACES_OMITTED_FROM_COVERAGE_REGISTER")
    rows_by_slot={x["slot_id"]:x for x in entries}
    statuses=Counter()
    early_claims=0
    overdue_pending=[]
    no_outcome_exclusions=0
    slot_output=[]
    for event in calendar["events"]:
        row=rows_by_slot[event["slot_id"]]
        status=row.get("status")
        if status not in _ALLOWED:
            raise ValueError("HOLD_UNDECLARED_OUTCOME_DRIVEN_SELECTION_STATUS")
        statuses[status]+=1
        date=_date(event["scheduled_date_jst"])
        if status=="upcoming_not_due" and date<asof.date():
            overdue_pending.append(event["slot_id"])
        if status=="preseal_sha_submitted_unverified":
            if (not isinstance(row.get("preseal_comment_id"),int)
                    or row["preseal_comment_id"]<=0
                    or not isinstance(row.get("preseal_digest_sha256"),str)
                    or not _SHA.fullmatch(row["preseal_digest_sha256"])
                    or not isinstance(row.get("claimed_race_id"),str)
                    or row.get("claimed_race_id")!=event.get("official_race_id")):
                raise ValueError("HOLD_SHA_COMMITMENT_CANNOT_BE_MATCHED_TO_RACE")
            early_claims+=1
        elif status=="upcoming_not_due":
            if (row.get("preseal_comment_id") is not None
                    or row.get("preseal_digest_sha256") is not None):
                raise ValueError("HOLD_UNDECLARED_EARLY_PRESEAL_FOR_PENDING_RACE")
        # A private registry alone does NOT authenticate any trusted
        # server receipt or official score, even if status says verified.
        if status in ("preseal_external_proof_verified",
                      "postrace_scored_provenance_not_independently_checked"):
            no_outcome_exclusions+=1
        slot_output.append({
            "slot_id":event["slot_id"],
            "date":event["scheduled_date_jst"],
            "grade":event["grade"],
            "venue":event["venue"],
            "race_name_jp":event["race_name_jp"],
            "registered_status":status,
            "past_asof_by_local_declared_date":date<asof.date(),
            "is_eligible_for_actual_prospective_scoring_now":False,
            "has_only_local_SHA_claim_no_GitHub_proof":
                status=="preseal_sha_submitted_unverified",
        })
    if no_outcome_exclusions:
        raise ValueError("HOLD_SELF_CLAIMED_REMOTE_PROOF_OR_POSTRACE_SCORE")
    return {
        "status":STATUS,
        "segment_start_jst":verified_cal["period_start"],
        "segment_end_jst":verified_cal["period_end"],
        "full_protocol_study_end_jst":verified_cal["study_end"],
        "asof_local_claimed_jst":asof.isoformat(),
        "official_JRA_public_calendar_source":calendar["source_jra"],
        "calendar_segment_event_count":verified_cal["event_count"],
        "calendar_segment_distinct_race_dates":verified_cal["race_dates"],
        "coverage_rows_present":len(entries),
        "covered_jra_flat_graded_events_not_independent_horse_trials":
            verified_cal["event_count"],
        "coverage_all_registered_for_segment":True,
        "future_2027_Jan_Mar_segment_NOT_REGISTERED":True,
        "full_period_calendar_denominator_verified":False,
        "calendar_data_transcribed_from_official_site_not_cryptographically_signed":True,
        "registered_local_SHA_submission_count_not_externally_verified":
            early_claims,
        "externally_proven_prestart_submissions_count":0,
        "official_results_used_to_select_race_slots":False,
        "actual_forward_graded_stakes_scores_count":0,
        "status_counts":dict(statuses),
        "overdue_pending_unresolved_races":overdue_pending,
        "registry_must_keep_unscored_and_missing_source_races":True,
        "no_statistical_winner_information_advantage_established":True,
        "per_slot_coverage":slot_output,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calendar",required=True,type=Path)
    parser.add_argument("--registry",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    c=json.loads(args.calendar.read_text(encoding="utf-8"))
    r=json.loads(args.registry.read_text(encoding="utf-8"))
    report=audit(c,r)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "covered_2026_flat_grade_slots":report["calendar_segment_event_count"],
        "distinct_JRA_race_dates":report["calendar_segment_distinct_race_dates"],
        "locally_claimed_preseal_submissions":
            report["registered_local_SHA_submission_count_not_externally_verified"],
        "actual_future_races_scored":0,
        "full_study_window_calendar_proven_complete":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
