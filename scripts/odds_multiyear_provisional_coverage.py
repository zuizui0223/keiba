#!/usr/bin/env python3
"""Join 2026 PRECOMMITTED schedule with distinct 2027 PROVISIONAL JRA annex.

No 2026 historical calendar/protocol rewrite is allowed: verify original
Git blob hashes that were submitted before Kikka in GitHub PR #10
comment 6382991405. The 2027 Jan–Mar candidate annex is based on
JRA's 2026-09-28 PRELIMINARY 2027 program PDF (subject to
government approval and grade review in Jan 2027). Several secondary
transcriptions disagree on four exact race dates; keep BOTH dates
explicitly without claiming either is finalized.

The 26+36=62 candidate events NEVER establish a prospective winner
sample: there are zero validated results and the 2027 36 candidates
remain unapproved. Real prestart independent GH SHA receipt and JRA
postrace verification will be required later, with every missing race
kept in the coverage denominator.

 python scripts/odds_multiyear_provisional_coverage.py \
   --calendar-2026 data/research/jra-graded-flat-2026oct25-dec27-calendar.json \
   --registry-2026 data/research/odds-prequential-2026oct24-coverage-registry.json \
   --protocol docs/odds-prequential-graded-cohort-v1-20261024.json \
   --calendar-2027 data/research/jra-graded-2027jan-mar-provisional-calendar.json \
   --registry-2027 data/research/odds-prequential-2027jan-mar-provisional-registry.json \
   --output tmp/odds-multiyear-provisional-cohort.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime
from hashlib import sha1
import json
from pathlib import Path

from odds_graded_calendar_coverage import audit as audit_2026
from odds_graded_calendar_coverage import CALENDAR_SCHEMA, REGISTRY_SCHEMA

STATUS="PARTIAL_2026_PRECOMMITTED_PLUS_2027_PROVISIONAL_ANNEX_NOT_FINAL_DENOMINATOR"
SOURCE_SCHEMA="KEIBA_JRA_2027_Q1_PROVISIONAL_FLAT_GRADED_CANDIDATES_V1"
REG_SCHEMA="KEIBA_2027_Q1_PROVISIONAL_COVERAGE_STAGING_V1"
PROTOCOL_SCHEMA="KEIBA_WIN_ODDS_PREQUENTIAL_COHORT_V1"
MIN_RACES_FOR_FEASIBILITY=60
EXPECTED_2026_GIT_BLOB={
    "2026_calendar":"f458794971e184fb4cda5fdab84d1c56f277cc2f",
    "2026_registry":"9052dbb3590fd6a93bd6c6732d4e992929f77f0e",
    "protocol_v1":"a0c3b180417ce061b72831fc649c5e5743a20935",
}
VALID_STAGING_STATUS="provisional_upcoming_requires_official_confirmation"
JAN_2027_PENDING_UPGRADES={"根岸ステークス","オーシャンステークス"}
SOURCE_PDF="https://www.jra.go.jp/keiba/program/2027/pdf/nittei.pdf"
SOURCE_NEWS="https://www.jra.go.jp/news/202609/092805.html"
SOURCE_CROSS1="https://joumeshi.jp/articles/jra-program-2027"
SOURCE_CROSS2="https://oyaji-sports.com/2026/09/29/jra-graded-race-calendar-2027/"
DISPUTED_DATE_NAMES={
    "フェアリーステークス","フィリーズレビュー","中山牝馬ステークス",
    "フラワーカップ",
}


def blob_sha(raw):
    if type(raw) is not bytes:
        raise ValueError("HOLD_ORIGINAL_FILE_BYTES_NOT_SUPPLIED")
    return sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()


def parse_json(raw,kind):
    try:
        data=json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError,json.JSONDecodeError) as exc:
        raise ValueError("HOLD_CORRUPT_"+kind+"_JSON") from exc
    if not isinstance(data,dict):
        raise ValueError("HOLD_INVALID_"+kind+"_OBJECT")
    return data


def audit_2027(annex, staged):
    if (annex.get("schema")!=SOURCE_SCHEMA
            or staged.get("schema")!=REG_SCHEMA
            or staged.get("calendar_schema")!=SOURCE_SCHEMA):
        raise ValueError("HOLD_2027_PROVISIONAL_SCHEMA_MISMATCH")
    if (annex.get("source_official_news")!=SOURCE_NEWS
            or annex.get("source_official_provisional_pdf")!=SOURCE_PDF
            or annex.get("source_date_crosscheck_1")!=SOURCE_CROSS1
            or annex.get("source_date_crosscheck_2")!=SOURCE_CROSS2
            or staged.get("source_official_news")!=SOURCE_NEWS):
        raise ValueError("HOLD_UNVERIFIED_JRA_2027_PROVISIONAL_SOURCE")
    if (annex.get("official_announcement_date")!="2026-09-28"
            or annex.get("publication_status")!=
            "OFFICIALLY_ANNOUNCED_PROPOSAL_SUBJECT_TO_MINISTRY_APPROVAL"
            or annex.get("final_2027_JRA_event_grades_approved") is not False
            or staged.get("regulatory_status")!=
            "AWAITING_FINAL_2027_JRA_PROGRAM_AND_GRADE_REVIEW"):
        raise ValueError("HOLD_2027_GRADE_OR_SCHEDULE_NOT_YET_FINAL")
    if (annex.get("segment_start_jst")!="2027-01-01"
            or annex.get("segment_end_jst")!="2027-03-31"
            or annex.get("generated_on_jst")!="2026-10-24"
            or staged.get("asof_jst")!="2026-10-24T22:37:00+09:00"
            or annex.get("separate_from_unmodified_2026_Oct_Dec_precommit") is not True
            or staged.get("can_merge_into_2026_committed_denominator_now") is not False):
        raise ValueError("HOLD_2027_SEGMENT_CHANGED_OR_BACKDATED")
    ev=annex.get("events")
    rows=staged.get("entries")
    if (not isinstance(ev,list) or len(ev)!=36
            or annex.get("candidate_count")!=36
            or not isinstance(rows,list) or len(rows)!=36):
        raise ValueError("HOLD_2027_PROVISIONAL_CANDIDATE_DENOMINATOR_MISSING")
    all_ids=[]
    conflicted=[]
    count_grade=Counter()
    count_month=Counter()
    dates=set()
    pending=set()
    for e in ev:
        if not isinstance(e,dict):
            raise ValueError("HOLD_PROVISIONAL_EVENT_NOT_AN_OBJECT")
        date_text=e.get("candidate_date_jst")
        try:
            d=date.fromisoformat(date_text)
        except (ValueError,TypeError):
            raise ValueError("HOLD_PROVISIONAL_DATE_BAD") from None
        if d.isoformat()!=date_text or d.year!=2027 or d.month not in (1,2,3):
            raise ValueError("HOLD_PROVISIONAL_DATE_NOT_2027_Q1")
        name=e.get("race_name_jp")
        venue=e.get("venue")
        if (not isinstance(name,str) or not name
                or not isinstance(venue,str) or not venue
                or e.get("slot_id")!=f"2027|{venue}|{name}"):
            raise ValueError("HOLD_2027_RACE_IDENTITY_CHANGED")
        all_ids.append(e["slot_id"])
        grade=e.get("provisional_grade")
        if grade not in ("G1","G2","G3"):
            raise ValueError("HOLD_2027_NOT_A_FLAT_GRADE")
        if (e.get("official_race_id") is not None
                or e.get("source_reported_post_jst") is not None
                or e.get("final_grade_approval_verified") is not False
                or e.get("scheduled_date_fully_verified_from_official_chart") is not False
                or e.get("status")!="JRA_2027_PRELIMINARY_CALENDAR_NOT_FINAL"):
            raise ValueError("HOLD_FABRICATED_OFFICIAL_RACE_CLOCK_OR_APPROVAL")
        secondary=e.get("alternate_reported_dates_jst")
        if not isinstance(secondary,list) or len(secondary)>1:
            raise ValueError("HOLD_UNDOCUMENTED_SECONDARY_DATE_CONFLICT")
        if secondary:
            if name not in DISPUTED_DATE_NAMES:
                raise ValueError("HOLD_NEW_UNDOCUMENTED_AMBIGUOUS_DATE")
            alt=secondary[0]
            try:
                da=date.fromisoformat(alt)
            except (ValueError,TypeError):
                raise ValueError("HOLD_BAD_SECONDARY_DATE") from None
            if da.year!=2027 or da.month!=d.month or da==d:
                raise ValueError("HOLD_DISPUTED_DATE_NOT_AN_ALTERNATIVE")
            conflicted.append(name)
        elif name in DISPUTED_DATE_NAMES:
            raise ValueError("HOLD_DISPUTED_2027_RACE_SILENTLY_DECLARED_CONFIRMED")
        claimed=e.get("grade_upgrade_application_pending")
        if name in JAN_2027_PENDING_UPGRADES:
            if grade!="G3" or claimed!="G2":
                raise ValueError("HOLD_PENDING_G2_APPLICATION_IMPROPERLY_FINALIZED")
            pending.add(name)
        elif claimed is not None:
            raise ValueError("HOLD_UNANNOUNCED_GRADE_PROMOTION")
        count_grade[grade]+=1
        count_month[d.month]+=1
        dates.add(d.isoformat())
    if len(all_ids)!=len(set(all_ids)):
        raise ValueError("HOLD_DUPLICATED_PROVISIONAL_RACE_ID")
    if (set(conflicted)!=DISPUTED_DATE_NAMES
            or annex.get("discrepant_date_count")!=len(conflicted)
            or sorted(annex.get("rank_upgrades_pending_in_Jan_2027",[]))!=sorted(pending)
            or len(pending)!=2):
        raise ValueError("HOLD_GRADE_REVIEW_OR_DATE_CONFLICT_CONCEALED")
    if annex.get("intentionally_excluded_jumping_grades") != ["J-G1","J-G2","J-G3"]:
        raise ValueError("HOLD_GRADED_UNIVERSE_CHANGED")
    if (staged.get("full_future_results_scored_count")!=0
            or not isinstance(rows,list)):
        raise ValueError("HOLD_UNATTESTED_2027_RESULTS_MARKED_SCORED")
    staged_ids=[]
    for r in rows:
        if (not isinstance(r,dict) or r.get("status")!=VALID_STAGING_STATUS
                or r.get("source_quote_two_times_full_field_present") is not False
                or r.get("externally_precommitted_win_probability_sha") is not None
                or r.get("official_final_schedule_confirmation") is not None):
            raise ValueError("HOLD_2027_PROVISIONAL_RACE_FALSE_COMPLETION")
        staged_ids.append(r.get("slot_id"))
    if (len(staged_ids)!=len(set(staged_ids))
            or set(staged_ids)!=set(all_ids)):
        raise ValueError("HOLD_2027_COVERAGE_SLOT_OMITTED_OR_EXTRA")
    return {
        "status":"PRELIMINARY_JRA_2027_CALENDAR_PENDING_FINAL_CONFIRMATION",
        "provisional_candidates":len(all_ids),
        "provisional_approximate_race_dates":len(dates),
        "date_uncertainty_cases":sorted(conflicted),
        "n_disputed_exact_dates":len(conflicted),
        "grade_upgrade_applications_pending":sorted(pending),
        "grades_provisionally_labeled":dict(count_grade),
        "month_candidate_counts":{str(k):v for k,v in sorted(count_month.items())},
        "race_ids":set(all_ids),
        "full_calendar_certified":False,
        "all_registered_without_postrace_omission":True,
        "official_race_results_scored":0,
    }


def audit_raw(older_cal,older_reg,protocol_raw,annex_raw,staged_raw):
    sources={
        "2026_calendar":older_cal,
        "2026_registry":older_reg,
        "protocol_v1":protocol_raw,
    }
    if {k:blob_sha(v) for k,v in sources.items()}!=EXPECTED_2026_GIT_BLOB:
        raise ValueError("HOLD_ORIGINAL_PRECOMMITTED_2026_OR_PROTOCOL_BLOB_MUTATED")
    c2026=parse_json(older_cal,"2026_CALENDAR")
    r2026=parse_json(older_reg,"2026_REGISTRY")
    preprotocol=parse_json(protocol_raw,"FROZEN_PROTOCOL")
    if (preprotocol.get("schema")!=PROTOCOL_SCHEMA
            or preprotocol.get("prospective_window_start")!="2026-10-25"
            or preprotocol.get("prospective_window_end")!="2027-03-31"
            or preprotocol.get("fixed_model_M1")!=
            "M0 plus beta=+0.25 times centered log-relative early-to-late price change"):
        raise ValueError("HOLD_PRECOMMITTED_PROSPECTIVE_RULES_REWRITTEN")
    older=audit_2026(c2026,r2026)
    if (older["calendar_segment_event_count"]!=26
            or older["coverage_rows_present"]!=26):
        raise ValueError("HOLD_UNEXPECTED_2026_SEGMENT_SIZE")
    annex=parse_json(annex_raw,"2027_PROVISIONAL")
    staging=parse_json(staged_raw,"2027_STAGE")
    future=audit_2027(annex,staging)
    if any(i.startswith("2026|") for i in future["race_ids"]):
        raise ValueError("HOLD_2027_SLOT_OVERLAPS_FROZEN_2026_RACES")
    return {
        "status":STATUS,
        "original_2026_and_protocol_Git_blobs_unmodified":True,
        "externally_precommitted_2026_26_race_list_comment_id":6382991405,
        "2026_immutable_flat_graded_slots":older["calendar_segment_event_count"],
        "2027_Q1_provisional_candidate_slots":future["provisional_candidates"],
        "preliminary_total_planned_cohort_slots":26+future["provisional_candidates"],
        "2027_disputed_exact_date_count":future["n_disputed_exact_dates"],
        "2027_disputed_names":future["date_uncertainty_cases"],
        "2027_pending_graded_promotion_count":len(
            future["grade_upgrade_applications_pending"]),
        "2027_pending_graded_promotions":future["grade_upgrade_applications_pending"],
        "2027_month_counts_provisional":future["month_candidate_counts"],
        "2027_candidate_race_dates_provisional":future[
            "provisional_approximate_race_dates"],
        "JRA_ministry_approval_and_grade_review_still_required":True,
        "2027_calendar_not_certified_final":True,
        "full_study_period_official_grades_and_exact_dates_verified":False,
        "JRA_provisional_pdf_source":SOURCE_PDF,
        "JRA_2027_provisional_announcement":SOURCE_NEWS,
        "single_SHA_outcome_predictions_proven_for_only_existing_2026_Kikka":
            False,
        "forecast_results_officially_scored_in_this_prestart_cohort":0,
        "software_support_gate_of_60_can_never_be_met_by_calendar_slots_alone":
            True,
        "no_real_forward_winning_probability_advantage_established":True,
        "v31_frozen_holdout_untouched":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("calendar_2026","registry_2026","protocol","calendar_2027","registry_2027"):
        p.add_argument("--"+arg.replace("_","-"),type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    x=p.parse_args()
    report=audit_raw(
        x.calendar_2026.read_bytes(),x.registry_2026.read_bytes(),
        x.protocol.read_bytes(),x.calendar_2027.read_bytes(),
        x.registry_2027.read_bytes())
    x.output.parent.mkdir(parents=True,exist_ok=True)
    x.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "immutable_2026_calendar_entries":26,
        "2027_Q1_provisional_entries":36,
        "ambiguous_2027_dates":report["2027_disputed_exact_date_count"],
        "actually_scored_prospective_real_races":0,
        "official_2027_approvals_pending":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
