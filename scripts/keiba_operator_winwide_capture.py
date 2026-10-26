#!/usr/bin/env python3
"""Private, append-only-by-convention capture from RIGHTS-AUTHORIZED exports.

Manual operator input -> locally stamped source snapshots -> chained SHA256
files -> full-field WIN/WIDE PR22 feature freeze -> later WIN market scoring.

No JRA/third-party website scraping, download, polling, platform scheduling,
true stake observation, official entrant discovery or automatic betting.
This does NOT acquire data by itself. The operator must lawfully obtain each
snapshot and preserve its publisher update clock and source URI. Local
machine reception clock and chain hashes are NOT external timestamps; past
files can still be edited/deleted. Only PR23's independently fetched GitHub
comment can establish the limited remote existence of a frozen SHA.

All raw data and frozen predictions MUST remain under gitignored private/.
Do not use historical Kyoto R8 or synthetic fixtures as forward evidence.
No outcome labels or payouts ever enter the feature or scoring pipeline.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timedelta
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path
from urllib.parse import urlparse

from odds_shadow_freeze_score import _normalized_odds,_wide_prices
from keiba_fixed_denominator_market_campaign import (
    ROOT,_locked_universe,_aware,JST,
    LOCKED_MARKET_HORIZON_MINUTES,LOCKED_MARKET_TARGET_WINDOW_MINUTES,
    EXPECTED_LEGACY_KIKKA,
)
from keiba_secondary_64_market_slots import defined_slots
from keiba_private_multirace_winwide_shadow import (
    FEATURE_SCHEMA,TARGET_SCHEMA,
    freeze_source_bytes, score_target, verify_freeze,
)

CAPTURE_SCHEMA="KEIBA_OPERATOR_AUTHORIZED_SNAPSHOT_V1"
CARD_SCHEMA="KEIBA_OPERATOR_OFFICIAL_FINAL_CARD_RECEIPT_V1"
LEDGER_SCHEMA="KEIBA_LOCAL_SOURCE_EVENT_HASH_CHAIN_V1"
STATUS="PRIVATE_MANUAL_WIN_WIDE_SOURCE_CAPTURE_LOCAL_CLOCK_NOT_AUTHENTICATED"
PROVENANCES=("authorized_private_local_export","synthetic_test")
MODEL_CODE_LOCK_AT="2026-10-25T23:18:00+09:00"
SNAPSHOT_FIELDS={
    "schema","race_id","provider","market","source_updated_at_jst",
    "source_url","source_clock_declared_verified",
    "rights_reviewed_by_operator","provenance",
}
CARD_FIELDS={
    "schema","slot_id","race_id","provider","race_number",
    "scheduled_post_jst","race_distance_m","horse_numbers",
    "source_card_url","source_card_published_at_jst",
    "source_card_received_at_jst","declared_final_entrant_list",
    "rights_reviewed_by_operator","provenance",
}
LOCAL_CHAIN_HEAD="0"*64


def _dump(o):
    return json.dumps(o,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False)


def _sha(data):
    return sha256(_dump(data).encode("utf-8")).hexdigest()


def _url(value):
    if not isinstance(value,str):
        raise ValueError("HOLD_CAPTURE_SOURCE_URL_REQUIRED")
    u=urlparse(value)
    if (u.scheme!="https" or not u.netloc or u.username or u.password):
        raise ValueError("HOLD_CAPTURE_SOURCE_MUST_HAVE_HTTPS_PROVENANCE")
    return value


def _check_license(flag,provenance):
    if provenance not in PROVENANCES or type(flag) is not bool:
        raise ValueError("HOLD_CAPTURE_SOURCE_RIGHTS_OR_PROVENANCE")
    if (provenance=="authorized_private_local_export" and not flag
        or provenance=="synthetic_test" and flag):
        raise ValueError("HOLD_CAPTURE_RIGHTS_FALSELY_PROMOTED")


def _verify_capture_payload(source):
    if not isinstance(source,dict) or not SNAPSHOT_FIELDS.issubset(source):
        raise ValueError("HOLD_CAPTURE_MARKET_SOURCE_SCHEMA")
    if source["schema"]!=CAPTURE_SCHEMA:
        raise ValueError("HOLD_CAPTURE_MARKET_SOURCE_SCHEMA")
    market=source["market"]
    fields=(SNAPSHOT_FIELDS|{"odds_by_horse_number"} if market=="win"
            else SNAPSHOT_FIELDS|{"pairs"} if market=="wide"
            else None)
    if fields is None or set(source)!=fields:
        raise ValueError("HOLD_UNSUPPORTED_MARKET_OR_EXTRA_FUTURE_FIELDS")
    if (not isinstance(source["race_id"],str) or
        not 1<=len(source["race_id"])<=95 or
        not isinstance(source["provider"],str) or
        not source["provider"].strip() or
        source["source_clock_declared_verified"] is not True):
        raise ValueError("HOLD_UNVERIFIED_CAPTURE_ID_OR_CLOCK")
    _check_license(source["rights_reviewed_by_operator"],
                   source["provenance"])
    _url(source["source_url"])
    _aware(source["source_updated_at_jst"])
    if market=="win":
        _normalized_odds(source["odds_by_horse_number"])
    else:
        rows=source["pairs"]
        if not isinstance(rows,list) or len(rows)<10 or len(rows)>435:
            raise ValueError("HOLD_WIDE_SOURCE_TOO_FEW_OR_MANY_PAIRS")
        # Complete set can only be confirmed against an OFFICIAL card
        # later; basic shape/deduplication still checked immediately.
        seen=set()
        for p in rows:
            if not isinstance(p,dict) or set(p)!={
                "selection","odds_low","odds_high"}:
                raise ValueError("HOLD_WIDE_SOURCE_INVALID_FIELDS")
            sel=p["selection"]
            if (not isinstance(sel,list) or len(sel)!=2 or
                any(type(x) is not int or x<=0 for x in sel) or
                sel[0]==sel[1]):
                raise ValueError("HOLD_WIDE_SOURCE_INVALID_SELECTION")
            pair=tuple(sorted(sel))
            if pair in seen:
                raise ValueError("HOLD_WIDE_SOURCE_DUPLICATE_PAIR")
            seen.add(pair)
            a,b=p["odds_low"],p["odds_high"]
            if (type(a) not in (int,float) or
                type(b) not in (int,float) or
                not math.isfinite(a) or not math.isfinite(b) or
                not 1<a<=b):
                raise ValueError("HOLD_WIDE_SOURCE_INVALID_PRICE")
    return source


def _read_ledger(directory):
    """Verify LOCAL hash chain; no claim deleted/rewritten files detectable."""
    path=Path(directory)
    if not path.exists():
        return []
    files=sorted(path.glob("*.json"))
    records=[]
    prev=LOCAL_CHAIN_HEAD
    last_received=None
    unique=set()
    for ix,fn in enumerate(files,1):
        if not fn.name.startswith(f"{ix:06d}-"):
            raise ValueError("HOLD_CAPTURE_LEDGER_GAP_OR_REORDERED_FILES")
        event=json.loads(fn.read_text(encoding="utf-8"))
        if not isinstance(event,dict) or set(event)!={
            "schema","index","previous_event_sha256","captured_at_jst",
            "captured_source","event_sha256",
        } or event["schema"]!=LEDGER_SCHEMA or event["index"]!=ix or (
                event["previous_event_sha256"]!=prev):
            raise ValueError("HOLD_CAPTURE_LEDGER_SCHEMA_OR_CHAIN_BROKEN")
        digest=event["event_sha256"]
        check={k:v for k,v in event.items() if k!="event_sha256"}
        if digest!=_sha(check) or fn.name!=f"{ix:06d}-{digest[:12]}.json":
            raise ValueError("HOLD_CAPTURE_LEDGER_HASH_OR_FILENAME_CHANGED")
        source=_verify_capture_payload(event["captured_source"])
        clock=_aware(event["captured_at_jst"])
        if _aware(source["source_updated_at_jst"])>clock:
            raise ValueError("HOLD_SOURCE_PUBLISHED_AFTER_LOCAL_CAPTURE")
        if last_received is not None and clock<last_received:
            raise ValueError("HOLD_LOCAL_CAPTURE_WENT_BACKWARDS_IN_TIME")
        last_received=clock
        identity=(source["race_id"],source["provider"],
                  source["market"],source["source_updated_at_jst"])
        if identity in unique:
            raise ValueError("HOLD_DUPLICATE_CAPTURED_PROVIDER_MARKET_UPDATE")
        unique.add(identity)
        records.append(event)
        prev=digest
    return records


def append_capture(directory,source,*,captured_at_jst=None):
    """CREATE a new immutable-by-convention local file, never overwrite.

    CLI always derives reception from machine wall clock. Injected
    captured_at_jst is for clearly labeled synthetic unit tests only and
    is NOT an external timestamp or valid prospective receipt.
    """
    source=_verify_capture_payload(source)
    current=_aware(captured_at_jst or datetime.now(JST).isoformat())
    if _aware(source["source_updated_at_jst"])>current:
        raise ValueError("HOLD_SOURCE_UPDATED_AFTER_CAPTURE_CLOCK")
    past=_read_ledger(directory)
    if past:
        first=past[0]["captured_source"]
        if (first["race_id"]!=source["race_id"] or
                first["provider"]!=source["provider"] or
                first["provenance"]!=source["provenance"]):
            raise ValueError("HOLD_CAPTURE_RACE_PROVIDER_OR_RIGHTS_COHORT_CHANGED")
        if _aware(past[-1]["captured_at_jst"])>current:
            raise ValueError("HOLD_MACHINE_CLOCK_MOVED_BACKWARD")
    key=(source["market"],source["source_updated_at_jst"])
    if any((r["captured_source"]["market"],
            r["captured_source"]["source_updated_at_jst"])==key for r in past):
        raise ValueError("HOLD_DUPLICATE_SOURCE_UPDATE_CAN_NOT_OVERWRITE")
    ix=len(past)+1
    item={
        "schema":LEDGER_SCHEMA,"index":ix,
        "previous_event_sha256":(
            past[-1]["event_sha256"] if past else LOCAL_CHAIN_HEAD),
        "captured_at_jst":current.isoformat(),
        "captured_source":source,
    }
    item["event_sha256"]=_sha(item)
    path=Path(directory)
    path.mkdir(parents=True,exist_ok=True)
    dest=path/f"{ix:06d}-{item['event_sha256'][:12]}.json"
    with dest.open("x",encoding="utf-8") as handle:
        handle.write(json.dumps(item,ensure_ascii=False,indent=2,
                                allow_nan=False)+"\n")
    # Check immediately in case a buggy conversion silently changed source.
    _read_ledger(directory)
    return {
        "status":STATUS,
        "local_event_no":ix,
        "event_sha256_local_only":item["event_sha256"],
        "captured_at_jst_local_clock_only":item["captured_at_jst"],
        "private_file_path":str(dest),
        "GitHub_external_timestamp_proof":False,
        "actual_new_JRA_stake_volume_verified":False,
    }


def _check_card(card):
    if not isinstance(card,dict) or set(card)!=CARD_FIELDS or (
            card["schema"]!=CARD_SCHEMA):
        raise ValueError("HOLD_CONFIRMED_CARD_SCHEMA")
    _check_license(card["rights_reviewed_by_operator"],card["provenance"])
    _url(card["source_card_url"])
    if card["declared_final_entrant_list"] is not True:
        raise ValueError("HOLD_CARD_NOT_DECLARED_FINAL_ENTRY_FIELD")
    if (type(card["race_number"]) is not int or
        not 1<=card["race_number"]<=12 or
        type(card["race_distance_m"]) is not int or
        not 800<=card["race_distance_m"]<=5000):
        raise ValueError("HOLD_CARD_RACE_NUMBER_OR_DISTANCE")
    ids=card["horse_numbers"]
    if (not isinstance(ids,list) or
        not 5<=len(ids)<=30 or
        any(type(x) is not int or x<1 for x in ids) or
        ids!=sorted(set(ids))):
        raise ValueError("HOLD_CARD_NO_CONFIRMED_UNIQUE_HORSE_ROSTER")
    pub=_aware(card["source_card_published_at_jst"])
    got=_aware(card["source_card_received_at_jst"])
    post=_aware(card["scheduled_post_jst"])
    if not (pub<=got<post):
        raise ValueError("HOLD_CARD_SOURCE_PUBLISHED_OR_RECEIVED_AFTER_POST")
    registered,_=_locked_universe()
    grade_slots={x["slot_id"] for x in registered}
    aux_slots={x["slot_id"] for x in defined_slots()}
    slot=card["slot_id"]
    if slot== "2026-10-25|京都|菊花賞":
        raise ValueError("HOLD_ORIGINAL_KIKKA_IS_NOT_A_NEW_NEXT_MARKET_TRIAL")
    if slot not in grade_slots and slot not in aux_slots:
        raise ValueError("HOLD_CARD_UNREGISTERED_RACE_SELECTION")
    if slot in aux_slots:
        tail=slot.split("|")[-1]
        if tail!=f"R{card['race_number']:02d}":
            raise ValueError("HOLD_CARD_DIFFERENT_FROM_FIXED_AUXILIARY_RACE_NO")
    if slot.split("|")[0]!=post.date().isoformat():
        raise ValueError("HOLD_CARD_DATE_VS_REGISTERED_SLOT")
    if not card["race_id"] or not card["provider"]:
        raise ValueError("HOLD_CARD_RACE_ID_OR_PROVIDER")
    return card


def prepare_feature_from_ledger(directory,card,*,freeze_at_jst=None):
    """Deterministic first possible complete triple, not a chosen winner.

    Need early full WIN then FIRST later source-minute matching full
    WIN/WIDE (both captured by freeze clock), same provider+card roster.
    Race target is exactly +15..20 min from chosen middle update.
    """
    card=_check_card(card)
    events=_read_ledger(directory)
    if not events:
        raise ValueError("HOLD_NO_AUTHORIZED_MARKET_EVENTS_CAPTURED")
    clock=_aware(freeze_at_jst or datetime.now(JST).isoformat())
    card_rx=_aware(card["source_card_received_at_jst"])
    market=[]
    for e in events:
        src=e["captured_source"]
        captured=_aware(e["captured_at_jst"])
        if (src["race_id"]!=card["race_id"] or
            src["provider"]!=card["provider"] or
            src["provenance"]!=card["provenance"] or
            src["rights_reviewed_by_operator"]!=
                card["rights_reviewed_by_operator"]):
            raise ValueError("HOLD_CAPTURE_CARD_RACE_PROVIDER_OR_RIGHTS_MISMATCH")
        if captured<=clock:
            if captured<card_rx:
                # The card needs to be available before the first model
                # eligible quote; earlier source capture is not used.
                continue
            market.append(e)
    ids=card["horse_numbers"]
    wins=[]
    wides=[]
    for e in market:
        src=e["captured_source"]
        if src["market"]=="win":
            if set(_normalized_odds(src["odds_by_horse_number"]))!=set(ids):
                # Do not silently edit scratched/late horse numbers.
                raise ValueError("HOLD_CAPTURED_WIN_DIFFERENT_FROM_CONFIRMED_CARD")
            wins.append(e)
        else:
            _wide_prices(src["pairs"],set(ids))
            wides.append(e)
    if len(wins)<2:
        raise ValueError("HOLD_INSUFFICIENT_TWO_FULL_WIN_SOURCE_TIMES")
    first=min(wins,key=lambda x:(
        _aware(x["captured_source"]["source_updated_at_jst"]),
        _aware(x["captured_at_jst"])))
    firstpub=_aware(first["captured_source"]["source_updated_at_jst"])
    matched=[]
    for win in wins:
        pub=_aware(win["captured_source"]["source_updated_at_jst"])
        if pub<=firstpub:
            continue
        for wide in wides:
            if (_aware(wide["captured_source"]["source_updated_at_jst"])
                    .replace(second=0,microsecond=0)
                    ==pub.replace(second=0,microsecond=0)):
                matched.append((pub,win,wide))
    if not matched:
        raise ValueError("HOLD_NO_SAME_SOURCE_MINUTE_FULL_WIN_AND_WIDE_PAIR_GRID")
    midpub,middle,wide=min(
        matched,key=lambda a:(a[0],_aware(a[1]["captured_at_jst"]),
                              _aware(a[2]["captured_at_jst"])))
    post=_aware(card["scheduled_post_jst"])
    first_rx=_aware(first["captured_at_jst"])
    mid_rx=_aware(middle["captured_at_jst"])
    wide_rx=_aware(wide["captured_at_jst"])
    tmin=midpub+timedelta(minutes=LOCKED_MARKET_HORIZON_MINUTES)
    tmax=tmin+timedelta(minutes=LOCKED_MARKET_TARGET_WINDOW_MINUTES)
    if not (card_rx<=firstpub<=first_rx<midpub<=mid_rx<=clock
            and midpub<=wide_rx<=clock<tmin<tmax<
            post-timedelta(minutes=10)):
        raise ValueError("HOLD_TOO_LATE_OR_INCOHERENT_LOCAL_CAPTURE_FOR_FREEZE")
    def panel(e):
        z=e["captured_source"]
        attrs={
            "market":z["market"],"provider":z["provider"],
            "source_clock_verified":True,
            "source_updated_at_jst":_aware(
                z["source_updated_at_jst"]).isoformat(),
            "received_at_jst":_aware(e["captured_at_jst"]).isoformat(),
        }
        if z["market"]=="win":
            attrs["odds_by_horse_number"]=z["odds_by_horse_number"]
        else:
            attrs["pairs"]=z["pairs"]
        return attrs
    return {
        "schema":FEATURE_SCHEMA,
        "provenance":(
            "authorized_private_local_export" if
            card["provenance"]=="authorized_private_local_export"
            else "synthetic_test"),
        "operator_confirmed_research_rights":card[
            "rights_reviewed_by_operator"],
        "race_id":card["race_id"],
        "scheduled_post_jst":post.isoformat(),
        "race_distance_m":card["race_distance_m"],
        "provider":card["provider"],
        "model_coefficient_lock_at_jst":MODEL_CODE_LOCK_AT,
        "local_forecast_created_at_jst":clock.isoformat(),
        "horizon_minutes":LOCKED_MARKET_HORIZON_MINUTES,
        "target_window_minutes":LOCKED_MARKET_TARGET_WINDOW_MINUTES,
        "first_win":panel(first),
        "middle_win":panel(middle),
        "middle_wide":panel(wide),
    }


def freeze_private_from_ledger(directory,card,*,freeze_at_jst=None,
                               horse_draws=120,horse_seed=20261026):
    features=prepare_feature_from_ledger(
        directory,card,freeze_at_jst=freeze_at_jst)
    raw=_dump(features).encode("utf-8")
    frozen=freeze_source_bytes(raw,horse_draws=horse_draws,
                               horse_seed=horse_seed)
    return {
        "feature":features,"freeze":frozen,
        "status":"LOCAL_CAPTURE_TO_PR22_SHA_FREEZE_NOT_GITHUB_PRETARGET_PROOF",
        "source_input_counts":{
            "total_events_in_local_ledger":len(_read_ledger(directory)),
            "used_full_win_snapshots":2,
            "used_full_wide_complete_grids":1,
        },
        "remote_sha_comment_submitted":False,
    }


def score_private_from_ledger(directory,freeze,*,operator_declares_complete,
                              scoring_at_jst=None):
    if operator_declares_complete is not True:
        raise ValueError("HOLD_OPERATOR_DID_NOT_DECLARED_CAPTURE_STREAM_COMPLETE")
    payload=verify_freeze(freeze)
    time=_aware(scoring_at_jst or datetime.now(JST).isoformat())
    snapshots=[]
    for item in _read_ledger(directory):
        src=item["captured_source"]
        received=_aware(item["captured_at_jst"])
        published=_aware(src["source_updated_at_jst"])
        if received>time:
            continue
        if (src["race_id"]!=payload["race_id"] or
                src["provider"]!=payload["provider"]):
            raise ValueError("HOLD_TARGET_PRICE_WRONG_RACE_OR_PROVIDER")
        if (src["market"]=="win" and
                published>_aware(payload["middle_WIN_quote_published_at"])):
            snapshots.append({
                "market":"win","provider":src["provider"],
                "source_clock_verified":True,
                "source_updated_at_jst":published.isoformat(),
                "received_at_jst":received.isoformat(),
                "odds_by_horse_number":src["odds_by_horse_number"],
            })
    if not snapshots:
        raise ValueError("HOLD_NO_POST_FREEZE_WIN_SNAPSHOTS_YET")
    target={
        "schema":TARGET_SCHEMA,"race_id":payload["race_id"],
        "provider":payload["provider"],
        "operator_declares_complete_capture_stream":True,
        "snapshots":snapshots,
    }
    result=score_target(freeze,target)
    return {
        "local_operator_capture_score":result,
        "source_capture_stream_attested_independently":False,
        "local_event_chain_sha256_only":_read_ledger(directory)[-1][
            "event_sha256"],
        "not_an_authentic_forecast_success_or_betting_return":True,
    }


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_new_private(path,obj):
    path=Path(path)
    if "private" not in path.resolve().parts:
        raise ValueError("HOLD_RAW_CAPTURE_OUTPUT_NOT_IN_GITIGNORED_PRIVATE")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        f.write(json.dumps(obj,ensure_ascii=False,indent=2,
                           allow_nan=False)+"\n")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="action",required=True)
    app=sub.add_parser("append")
    app.add_argument("--raw-source",required=True,type=Path)
    app.add_argument("--private-ledger",required=True,type=Path)
    fr=sub.add_parser("freeze")
    fr.add_argument("--private-ledger",required=True,type=Path)
    fr.add_argument("--confirmed-card",required=True,type=Path)
    fr.add_argument("--private-output",required=True,type=Path)
    fr.add_argument("--horse-draws",type=int,default=120)
    fr.add_argument("--seed",type=int,default=20261026)
    sc=sub.add_parser("score")
    sc.add_argument("--private-ledger",required=True,type=Path)
    sc.add_argument("--private-freeze",required=True,type=Path)
    sc.add_argument("--private-output",required=True,type=Path)
    sc.add_argument("--operator-confirms-complete-capture",
                    action="store_true")
    args=p.parse_args()
    if args.action=="append":
        if "private" not in args.private_ledger.resolve().parts:
            raise ValueError("HOLD_CAPTURE_LEDGER_MUST_STAY_IN_PRIVATE_DIRECTORY")
        out=append_capture(args.private_ledger,_read(args.raw_source))
    elif args.action=="freeze":
        out=freeze_private_from_ledger(
            args.private_ledger,_read(args.confirmed_card),
            horse_draws=args.horse_draws,horse_seed=args.seed)
        _write_new_private(args.private_output,out)
    else:
        blob=_read(args.private_freeze)
        out=score_private_from_ledger(
            args.private_ledger,
            blob.get("freeze") if "freeze" in blob else blob,
            operator_declares_complete=args.operator_confirms_complete_capture)
        _write_new_private(args.private_output,out)
    # Never print private quotes or predictions.
    print(json.dumps({
        "status":out["status"] if "status" in out else
                    "LOCAL_QUOTE_ONLY_NOT_CERTIFIED",
        "remote_SHA_confirmed":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
