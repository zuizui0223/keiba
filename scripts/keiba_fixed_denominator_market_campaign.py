#!/usr/bin/env python3
"""Source-locked 26-slot denominator for prospective integrated KEIBA research.

Fixed prior JRA graded-flat roster: 26 races/20 dates 2026-10-25..12-27.
This does NOT invent upcoming official race IDs, post times, a license to
download tote prices, complete WIN/WIDE quotes, nor SHA attestations.

The old Kyoto R8 next-price shadow is an engineering replay, *never* a
new genuine forward race. The Kikuka M0/M1/M2 preseal belongs to another
historical outcome protocol; it cannot silently become a new next-price
target. All the other 25 predeclared slots remain in the denominator
even if horse cards, complete WIN/WIDE snapshots, target prices, remote
SHA proof, or source permissions are missing.

Optional PRIVATE local *metadata* receipts or PR22 score files can be
audited; they are not public GitHub-server proofs or source authorization.
Every PR22 model score remains a PRICE-INDEX TV/KL, not a real horse win
probability, actually observed ballot flow, or wagering return.

Do not write original licensed horse records, per-runner quote snapshots
or private predictions to the GitHub repo. Source files are SHA-pinned.
The race/date unit, not a horse/WIDE pair/Monte Carlo path, is the unit
of repeated evidence. A 60-race/8-date development guard cannot be met
from these predeclared 26 races alone.
"""
from __future__ import annotations

import argparse
from datetime import datetime, date, timezone, timedelta
from hashlib import sha1
import json
import math
from pathlib import Path
from statistics import mean
from urllib.parse import urlparse

from keiba_private_multirace_winwide_shadow import (
    SCORE_SCHEMA, SCORE_STATUS,
)

ROOT=Path(__file__).resolve().parents[1]
CALENDAR_PATH="data/research/jra-graded-flat-2026oct25-dec27-calendar.json"
CALENDAR_GIT_BLOB_SHA="f458794971e184fb4cda5fdab84d1c56f277cc2f"
REGISTRY_PATH="data/research/odds-prequential-2026oct24-coverage-registry.json"
REGISTRY_GIT_BLOB_SHA="9052dbb3590fd6a93bd6c6732d4e992929f77f0e"
RECEIPT_SCHEMA="KEIBA_PRIVATE_FIXED_SLOTS_CAPTURE_METADATA_V1"
STATUS="FIXED_26_REGISTERED_MARKET_SLOTS_LOCAL_NOT_EXTERNALLY_VERIFIED"
CAPTURE_STAGES=(
    "metadata_only",
    "missing_full_WIN",
    "missing_full_WIDE",
    "WIN_WIDE_source_clock_mismatch",
    "local_SHA_frozen",
    "next_quote_window_missing",
    "next_quote_local_scored",
)
MODEL_NAMES=(
    "mid_WIN_persistence",
    "mid_WIN_momentum",
    "mid_WIN_momentum_plus_WIDE_node_beta025",
    "coupled_market_qmid_horse_signal_round1",
    "coupled_market_qmid_horse_signal_plus_WIDE_round1",
    "coupled_market_qmid_horse_signal_plus_rotated_WIDE_placebo_round1",
)
LOCAL_SHA_LEN=64
JST=timezone(timedelta(hours=9))
EXPECTED_SLOTS=26
EXPECTED_DATES=20
EXPECTED_LEGACY_KIKKA="2026-10-25|京都|菊花賞"
REQUIRED_ENTRY_FIELDS={
    "slot_id","official_race_id","scheduled_post_jst",
    "racecard_source_url","racecard_received_at_jst",
    "quote_provider_name","source_rights_checked_locally",
    "capture_stage","local_frozen_model_sha256",
}


def _locked_json(root, relpath, expected_blob):
    raw=(Path(root)/relpath).read_bytes()
    blob_sha=sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()
    if blob_sha!=expected_blob:
        raise ValueError("HOLD_FIXED_2026_RACE_UNIVERSE_OR_REGISTRY_BLOB_DRIFT")
    data=json.loads(raw.decode("utf-8"))
    if not isinstance(data,dict):
        raise ValueError("HOLD_INVALID_REGISTRY_SOURCE")
    return data


def _aware(s):
    if not isinstance(s,str):
        raise ValueError("HOLD_EXPLICIT_OFFSET_TIME_REQUIRED")
    try:
        d=datetime.fromisoformat(s.replace("Z","+00:00"))
    except ValueError as e:
        raise ValueError("HOLD_INVALID_OFFSET_DATETIME") from e
    if d.tzinfo is None or d.utcoffset() is None:
        raise ValueError("HOLD_NAIVE_HISTORICAL_OR_FUTURE_TIMESTAMP")
    return d.astimezone(JST)


def _https_url(uri):
    if not isinstance(uri,str):
        raise ValueError("HOLD_PUBLIC_RACE_CARD_HTTPS_PROVENANCE")
    r=urlparse(uri)
    if r.scheme!="https" or not r.hostname or r.username or r.password:
        raise ValueError("HOLD_PUBLIC_RACE_CARD_HTTPS_PROVENANCE")
    return uri


def _sha(s):
    if (not isinstance(s,str) or len(s)!=LOCAL_SHA_LEN or
            any(x not in "0123456789abcdef" for x in s)):
        raise ValueError("HOLD_INVALID_PRIVATE_MODEL_SHA_256")
    return s


def _locked_universe(root=ROOT):
    calendar=_locked_json(root,CALENDAR_PATH,CALENDAR_GIT_BLOB_SHA)
    registry=_locked_json(root,REGISTRY_PATH,REGISTRY_GIT_BLOB_SHA)
    events=calendar.get("events")
    coverage=registry.get("entries")
    if (calendar.get("schema")!="KEIBA_OFFICIAL_GRADED_FLAT_CALENDAR_SEGMENT_V1"
            or calendar.get("expected_event_count")!=EXPECTED_SLOTS
            or calendar.get("all_official_event_post_times_known") is not False
            or calendar.get("not_an_externally_signed_official_calendar_snapshot") is not True
            or registry.get("schema")!="KEIBA_GRADED_PRESTART_COVERAGE_REGISTRY_V1"
            or not isinstance(events,list) or len(events)!=EXPECTED_SLOTS
            or not isinstance(coverage,list) or len(coverage)!=EXPECTED_SLOTS):
        raise ValueError("HOLD_PRECOMMITTED_JRA_COHORT_CHANGED")
    ids=[row.get("slot_id") for row in events]
    recorded=[row.get("slot_id") for row in coverage]
    if (len(set(ids))!=EXPECTED_SLOTS or len(set(recorded))!=EXPECTED_SLOTS
            or set(ids)!=set(recorded)
            or len({row["scheduled_date_jst"] for row in events})!=EXPECTED_DATES
            or ids[0]!=EXPECTED_LEGACY_KIKKA):
        raise ValueError("HOLD_MISSING_OR_DUPLICATED_PREDECLARED_RACE_SLOT")
    for row in events:
        race_date=date.fromisoformat(row["scheduled_date_jst"])
        if not ("2026-10-25"<=str(race_date)<="2026-12-27"):
            raise ValueError("HOLD_RACE_OUTSIDE_PRIOR_REGISTERED_WINDOW")
        if row["slot_id"].split("|")[0]!=row["scheduled_date_jst"]:
            raise ValueError("HOLD_INCONSISTENT_CALENDAR_SLOT_DATE")
    registered={row["slot_id"]:row for row in coverage}
    if (registered[EXPECTED_LEGACY_KIKKA]["status"]!="preseal_sha_submitted_unverified"
            or sum(x["status"]=="upcoming_not_due" for x in coverage)!=25):
        raise ValueError("HOLD_FORMAL_KIKKA_PRESERVED_STATUS_CHANGED")
    return events,registered


def _metadata(receipts,events):
    if receipts is None:
        return {}
    if (not isinstance(receipts,dict) or set(receipts)!={"schema","entries"}
            or receipts["schema"]!=RECEIPT_SCHEMA
            or not isinstance(receipts["entries"],list)):
        raise ValueError("HOLD_PRIVATE_CAMPAIGN_METADATA_SCHEMA")
    universe={row["slot_id"]:row for row in events}
    out={}
    used_race_ids=set()
    for entry in receipts["entries"]:
        if not isinstance(entry,dict) or set(entry)!=REQUIRED_ENTRY_FIELDS:
            raise ValueError("HOLD_CAPTURE_RECEIPT_FIELDS_NOT_CLOSED")
        slot=entry["slot_id"]
        if slot not in universe or slot in out or slot==EXPECTED_LEGACY_KIKKA:
            raise ValueError("HOLD_UNREGISTERED_DUPLICATE_OR_PAST_CAPTURE_SLOT")
        if entry["capture_stage"] not in CAPTURE_STAGES:
            raise ValueError("HOLD_UNKNOWN_LOCAL_CAPTURE_STAGE")
        eid=entry["official_race_id"]
        post=entry["scheduled_post_jst"]
        card=entry["racecard_source_url"]
        card_received=entry["racecard_received_at_jst"]
        provider=entry["quote_provider_name"]
        rights=entry["source_rights_checked_locally"]
        digest=entry["local_frozen_model_sha256"]
        supplied=[v is not None for v in (eid,post,card,card_received,provider)]
        if any(supplied) and not all(supplied):
            raise ValueError("HOLD_PARTIAL_RACE_CARD_SOURCE_AND_RECEIPT")
        if type(rights) is not bool:
            raise ValueError("HOLD_UNVERIFIED_RESEARCH_SOURCE_PERMISSION_FLAG")
        if all(supplied):
            if (not isinstance(eid,str) or not eid.strip()
                    or eid in used_race_ids
                    or not isinstance(provider,str) or not provider.strip()):
                raise ValueError("HOLD_DUPLICATED_OR_INVALID_OFFICIAL_RACE_ID")
            used_race_ids.add(eid)
            _https_url(card)
            when=_aware(post)
            receipt=_aware(card_received)
            if (when.date().isoformat()!=universe[slot]["scheduled_date_jst"]
                    or receipt>=when):
                raise ValueError("HOLD_LOCAL_RACE_CARD_TIME_OR_EVENT_DATE_MISMATCH")
        frozen_stages={
            "local_SHA_frozen","next_quote_window_missing",
            "next_quote_local_scored",
        }
        if entry["capture_stage"] in frozen_stages:
            if not all(supplied) or not rights:
                raise ValueError("HOLD_SOURCE_RIGHTS_OR_CARD_BEFORE_LOCAL_FREEZE")
            _sha(digest)
        elif digest is not None:
            raise ValueError("HOLD_SHA_EXISTS_WITHOUT_ELIGIBLE_FREEZE_STAGE")
        if entry["capture_stage"]=="next_quote_local_scored" and not rights:
            raise ValueError("HOLD_SCORE_FROM_UNREVIEWED_PRIVATE_SOURCE")
        out[slot]=entry
    return out


def _scores(score_files,metadata):
    """Private PR22 scores are useful but cannot attest themselves remotely."""
    if not isinstance(score_files,list):
        raise ValueError("HOLD_LOCAL_SCORE_INPUT_NOT_A_LIST")
    by_official={}
    for slot,r in metadata.items():
        if r["official_race_id"] is not None:
            by_official[r["official_race_id"]]=slot
    out={}
    for score in score_files:
        if (not isinstance(score,dict) or score.get("schema")!=SCORE_SCHEMA
                or score.get("race_id") not in by_official):
            raise ValueError("HOLD_SCORED_RACE_NOT_PREDECLARED_WITH_CARD")
        slot=by_official[score["race_id"]]
        if slot in out:
            raise ValueError("HOLD_MULTIPLE_NEXT_MARKET_SCORES_FOR_SAME_RACE")
        receipt=metadata[slot]
        if score.get("status") not in (
                SCORE_STATUS,"HOLD_TARGET_NOT_OBSERVED_IN_LOCKED_TIME_WINDOW"):
            raise ValueError("HOLD_UNRECOGNIZED_NEXT_QUOTE_OUTCOME")
        expected=("next_quote_local_scored" if score["status"]==SCORE_STATUS
                  else "next_quote_window_missing")
        if receipt["capture_stage"]!=expected:
            raise ValueError("HOLD_CAPTURE_STAGE_AND_TARGET_AVAILABILITY_CONFLICT")
        if score.get("external_preseal_authenticated") is not False:
            raise ValueError("HOLD_LOCAL_SCORE_MUST_NOT_SELF_CERTIFY_GITHUB_PROOF")
        if score["status"]==SCORE_STATUS:
            if (score.get("capture_stream_independently_complete") is not False
                    or score.get("scheduled_post_jst") is None
                    or _aware(score["scheduled_post_jst"])!=
                       _aware(receipt["scheduled_post_jst"])
                    or score.get("sealed_prediction_sha256")!=
                       receipt["local_frozen_model_sha256"]):
                raise ValueError("HOLD_LOCAL_SHA_RACE_OR_TARGET_CAPTURE_MISMATCH")
            models=score.get("all_model_scores")
            if not isinstance(models,dict) or not set(MODEL_NAMES).issubset(models):
                raise ValueError("HOLD_INCOMPLETE_PREDECLARED_MODEL_CANDIDATES")
            if len(models) not in (12,21):
                raise ValueError("HOLD_CHANGED_WIN_WIDE_PHYSICAL_MODEL_UNIVERSE")
            for val in models.values():
                if not isinstance(val,dict) or set(val)!={
                        "next_price_index_TV_pp","next_price_index_KL_nats"}:
                    raise ValueError("HOLD_MISSING_PRICE_INDEX_SCORING_COMPONENT")
                if any(type(x) not in (int,float) or not math.isfinite(x)
                       or x<0 for x in val.values()):
                    raise ValueError("HOLD_NONFINITE_NEXT_PRICE_TV_OR_KL")
        out[slot]=score
    return out


def campaign(root=ROOT, *, asof="2026-10-25T22:04:00+09:00",
             local_receipts=None,private_scores=None):
    now=_aware(asof)
    calendar,coverage=_locked_universe(root)
    local=_metadata(local_receipts,calendar)
    scored=_scores(private_scores if private_scores is not None else [],local)
    statuses=[]
    for e in calendar:
        slot=e["slot_id"]
        event_date=date.fromisoformat(e["scheduled_date_jst"])
        r=local.get(slot)
        is_past=(event_date<now.date())
        is_future=(event_date>now.date())
        post=e.get("source_reported_post_jst")
        if event_date==now.date() and post is not None:
            is_past=_aware(post)<=now
            is_future=_aware(post)>now
        elif event_date==now.date() and post is None:
            # On date without an independently verified post time, we
            # must NEVER decide whether a race was before/after capture.
            is_future=False
        if slot==EXPECTED_LEGACY_KIKKA:
            state="PRIOR_KIKKA_OUTCOME_PRESEAL_UNVERIFIED_NOT_NEXT_MARKET"
        elif r is None:
            state=("PAST_OR_DUE_UNCOLLECTED_FIXED_SLOT" if not is_future
                   else "UPCOMING_NO_VERIFIED_RACE_ID_POST_OR_WIN_WIDE_INPUT")
        elif slot in scored:
            state=("LOCAL_PRICE_INDEX_SCORE_UNATTESTED" if
                   scored[slot]["status"]==SCORE_STATUS else
                   "TARGET_WINDOW_UNOBSERVED_NOT_REPLACED")
        else:
            state="PRIVATE_LOCAL_"+r["capture_stage"].upper()
        missing=[]
        if r is None:
            missing=[
                "OFFICIAL_RACE_ID_AND_POST_TIME_NOT_SOURCE_VERIFIED",
                "AUTHORIZED_FULL_WIN_AND_WIDE_SOURCE_NOT_CAPTURED",
                "NO_FROZEN_NEXT_PRICE_SHA_OR_ELIGIBLE_TARGET",
            ]
        else:
            if r["official_race_id"] is None:
                missing.append("OFFICIAL_RACE_ID_AND_POST_TIME_NOT_SOURCE_VERIFIED")
            if not r["source_rights_checked_locally"]:
                missing.append("SOURCE_RESEARCH_RIGHTS_NOT_SELF_REVIEWED")
            if r["local_frozen_model_sha256"] is None:
                missing.append("NO_LOCAL_SHA_FOR_NEXT_PRICE_MARKET")
            if slot not in scored:
                missing.append("NO_ELIGIBLE_NEXT_PRICE_TARGET_SCORE_FILE")
        statuses.append({
            "slot_id":slot,
            "scheduled_date_jst":e["scheduled_date_jst"],
            "venue":e["venue"],"race_name_jp":e["race_name_jp"],
            "grade":e["grade"],
            "calendar_scheduled_post_fully_verified":False,
            "prior_precommitted_coverage_status":coverage[slot]["status"],
            "capture_state":state,
            "required_or_missing_gates":missing,
            "external_SHA_creation_time_verified_by_this_campaign":False,
            "official_result_or_wager_profit_used":False,
        })
    eligible=[x for x in statuses if x["slot_id"]!=EXPECTED_LEGACY_KIKKA]
    grouped={}
    for model in MODEL_NAMES:
        samples=[]
        for slot,score in scored.items():
            if score["status"]==SCORE_STATUS:
                x=score["all_model_scores"]
                samples.append((
                    slot.split("|",1)[0],
                    float(x[model]["next_price_index_TV_pp"]-
                          x["mid_WIN_persistence"]["next_price_index_TV_pp"]),
                ))
        dates=sorted({d for d,_ in samples})
        grouped[model]={
            "locally_scored_distinct_real_market_intervals_not_authenticated":
                len(samples),
            "local_score_dates":len(dates),
            "race_equal_delta_next_price_TV_vs_persistence_pp":(
                mean(v for _,v in samples) if samples else None),
            "meeting_date_equal_delta_next_price_TV_vs_persistence_pp":(
                mean(mean(v for d,v in samples if d==day) for day in dates)
                if dates else None),
            "cannot_claim_future_outcome_calibration":True,
        }
    actual_scored=sum(v["status"]==SCORE_STATUS for v in scored.values())
    future=sum(x["scheduled_date_jst"]>now.date().isoformat() for x in eligible)
    return {
        "status":STATUS,
        "asof_jst":now.isoformat(),
        "fixed_legacy_calendar_git_blob_sha":CALENDAR_GIT_BLOB_SHA,
        "fixed_original_coverage_git_blob_sha":REGISTRY_GIT_BLOB_SHA,
        "source_calendar_not_externally_signed":True,
        "registered_flat_G1_G2_G3_slots_including_Kikka":EXPECTED_SLOTS,
        "registered_meeting_dates":EXPECTED_DATES,
        "registered_next_price_candidate_slots_excluding_old_Kikka":
            EXPECTED_SLOTS-1,
        "future_registered_slots_after_asof_date":future,
        "official_post_and_race_id_unresolved_in_public_registry":sum(
            e["official_race_id"] is None or
            e["source_reported_post_jst"] is None
            for e in calendar if e["slot_id"]!=EXPECTED_LEGACY_KIKKA),
        "locally_received_capture_metadata_records":len(local),
        "locally_scored_next_price_intervals_unattested":actual_scored,
        "missing_locked_next_quote_target_intervals":sum(
            v["status"]=="HOLD_TARGET_NOT_OBSERVED_IN_LOCKED_TIME_WINDOW"
            for v in scored.values()),
        "remotely_SHA_pre_next_price_verified_intervals":0,
        "new_independent_real_prospective_quote_trials_confirmed":0,
        "require_complete_same_provider_WIN_2point_and_WIDE_pair_grid":True,
        "target_selection_first_source_update_in_frozen_window":True,
        "unsubmitted_slots_always_remain_in_denominator":True,
        "one_real_market_interval_not_many_horses_or_WIDE_pairs_is_unit":True,
        "six_prior_historical_real_races_are_not_new_forward_trials":True,
        "minimum_60_races_8_dates_development_guard_met":False,
        "this_26_race_calendar_alone_cannot_meet_60_race_guard":True,
        "predeclared_comparison_metrics":{
            "primary":"next_WIN_price_index_TV_pp",
            "secondary":"next_quote_index_KL_nats",
            "baseline":"mid_WIN_persistence",
            "model_universe":list(MODEL_NAMES),
        },
        "by_model_local_scores_not_prospective_certified":grouped,
        "registered_slot_readiness":statuses,
        "real_market_criticality_horse_GPS_or_bettor_contagion":"HOLD",
        "prior_Kikka_M0_M2_SHA_and_v31_holdout_unchanged":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--as-of",default=None)
    p.add_argument("--receipts",type=Path)
    p.add_argument("--scores",nargs="*",type=Path,default=[])
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    now=a.as_of or datetime.now(JST).isoformat()
    receipts=(json.loads(a.receipts.read_text(encoding="utf-8"))
              if a.receipts is not None else None)
    scores=[json.loads(x.read_text(encoding="utf-8")) for x in a.scores]
    v=campaign(asof=now,local_receipts=receipts,private_scores=scores)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(v,ensure_ascii=False,indent=2,
                                   allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":v["status"],
        "fixed_slots":v["registered_flat_G1_G2_G3_slots_including_Kikka"],
        "new_real_prospective_trials":
            v["new_independent_real_prospective_quote_trials_confirmed"],
        "unverified_official_post_or_id":
            v["official_post_and_race_id_unresolved_in_public_registry"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
