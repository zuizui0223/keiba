#!/usr/bin/env python3
"""Source-update-aligned two-time horse-node and dyad market-price study.

Actual saved Kyoto R8, 2026-10-12, 14:00 post. We discovered an
independent EARLIER *paired* Yahoo-source capture:
 - data/2026-10-12/remaining-snapshots/r8_tfw.json
 - data/2026-10-12/remaining-snapshots/r8_wide.json
Both say source-updated_at_jst=13:26 and were read at 13:27:02.145
and 13:27:01.902 (within 0.243 seconds), 11 win, 55 wide.

Previously analyzed late saved r8_markets_latest.json has both win and wide
source-updated_at_jst=13:44, read before 13:44:56.

The earlier r8_markets.json (win13:22 wide13:33) is an
ASYNCHRONOUS sensitivity case, not the synchronized primary comparison.

Analyze *quote source timestamp aligned* (13:26 -> 13:44), but 2 samples
from ONE race cannot identify information cascades, learning mechanisms,
significant changes in time scale, or stable animal individuality.
Quote update labels are from saved market metadata, original HTML is not
published here, and price normalizations are NOT actual voting distributions.

Combined analysis:
  - existing node/dyad 2-snapshot comparison with source status corrected
  - exact arithmetic win-only vs wide-only cross-channel source factorization
  - async-early sensitivity for whether timing mismatch changes interpretation
No outcomes, payouts, betting stakes, names, IDs, kinship or genomes used.
"""
from __future__ import annotations

import argparse
from datetime import timezone
import json
import math
from pathlib import Path
import re

try:
    from scripts.ecology_ticket_market_two_snapshot_time import (
        ROOT, read_json, read_market_snapshot, report_two_snapshots,
        EARLY as ASYNC_OLD, LATE, RACE_ID, _time,
    )
    from scripts.ecology_ticket_market_source_channel_decomposition import (
        effect_splits,
    )
except (ImportError, ModuleNotFoundError):
    from ecology_ticket_market_two_snapshot_time import (
        ROOT, read_json, read_market_snapshot, report_two_snapshots,
        EARLY as ASYNC_OLD, LATE, RACE_ID, _time,
    )
    from ecology_ticket_market_source_channel_decomposition import effect_splits


TFW = ROOT / "data" / "2026-10-12" / "remaining-snapshots" / "r8_tfw.json"
WIDE = ROOT / "data" / "2026-10-12" / "remaining-snapshots" / "r8_wide.json"
SHA = re.compile(r"^[0-9a-f]{64}$")
STATUS = "ONE_KYOTO_R8_TWO_SOURCE_TIMESTAMP_ALIGNED_MARKET_STATES_OBSERVED_NOT_CAUSAL"


def reconstruct_early_pair(tfw:dict, wide:dict, late:dict)->tuple[dict,dict]:
    """Create a faithful normalized representation of two saved source files."""
    if (tfw.get("race")!=8 or tfw.get("page_code")!="tfw" or
            wide.get("race")!=8 or wide.get("page_code")!="wide" or
            tfw.get("missing")!=[] or wide.get("missing")!=[]):
        raise ValueError("incomplete_or_wrong_early_race_source")
    from urllib.parse import urlsplit
    for row,required in (
        (tfw,"/keiba/race/odds/tfw/2608040508"),
        (wide,"/keiba/race/odds/wide/2608040508"),
    ):
        url=urlsplit(row["url"])
        if url.scheme!="https" or url.hostname!="sports.yahoo.co.jp" or url.path!=required:
            raise ValueError("untrusted_early_source_url")
        if not SHA.fullmatch(row["html_sha256"]):
            raise ValueError("source_html_hash_not_recorded")
    earlier_updates={kind:_time(row["updated_at_jst"]) for kind,row in (
        ("win",tfw),("wide",wide)
    )}
    if earlier_updates["win"] != earlier_updates["wide"]:
        raise ValueError("early_source_market_not_update_time_aligned")
    first_observed=_time(tfw["observed_at_jst"])
    second_observed=_time(wide["observed_at_jst"])
    receipt=max(first_observed,second_observed)
    gap=abs((first_observed-second_observed).total_seconds())
    if (gap>90 or any(t>receipt for t in earlier_updates.values()) or
            earlier_updates["win"] >= _time(late["start_jst"]) or
            receipt >= _time(late["start_jst"])):
        raise ValueError("early_market_receipts_or_updates_invalid")
    horses=tfw.get("horses")
    if not isinstance(horses,list) or len(horses)!=11:
        raise ValueError("missing_runner_number_frames")
    frames={str(h["number"]):int(h["frame"]) for h in horses}
    if (len(frames)!=11 or set(frames)!={str(i) for i in range(1,12)}
            or any(not 1<=frame<=8 for frame in frames.values())):
        raise ValueError("early_horse_frames_inconsistent")
    if (len(tfw.get("quotes",{}).get("win",[]))!=11 or
            len(wide.get("quotes",{}).get("wide",[]))!=55):
        raise ValueError("early_win_or_wide_board_incomplete")
    for kind,row in (("win",tfw),("wide",wide)):
        if row["updated_at_jst"]!="2026-10-12T13:26:00+09:00":
            raise ValueError("early_source_updated_time_not_original")
    normalized={
        "race_id":RACE_ID,"race":8,
        "start_jst":late["start_jst"],
        "checked_at_utc":receipt.astimezone(timezone.utc).isoformat(),
        "horse_count":11,"horse_frames":frames,
        "markets":{
            "win":{"updated_at_jst":tfw["updated_at_jst"],
                   "quotes":tfw["quotes"]["win"]},
            "wide":{"updated_at_jst":wide["updated_at_jst"],
                    "quotes":wide["quotes"]["wide"]},
        },
    }
    summary={
        "earlier_market_source_updated_at":tfw["updated_at_jst"],
        "win_received_at_jst":first_observed.isoformat(),
        "wide_received_at_jst":second_observed.isoformat(),
        "win_wide_receipt_gap_seconds":gap,
        "win_wide_source_update_gap_seconds":0,
        "quotes_win":11,"quotes_wide":55,
        "original_html_sha256":{
            "win":tfw["html_sha256"],"wide":wide["html_sha256"]
        },
        "raw_html_archived_in_this_analysis":False,
        "original_urls_verified_as_allowed_market_sources":True,
    }
    return normalized,summary


def analysis()->dict:
    hashes={}
    tfw=read_json(TFW,hashes)
    wide=read_json(WIDE,hashes)
    late_raw=read_json(LATE,hashes)
    original_async=read_json(ASYNC_OLD,hashes)
    early_normalized,receipt=reconstruct_early_pair(tfw,wide,late_raw)
    e=read_market_snapshot(early_normalized)
    l=read_market_snapshot(late_raw)
    older=read_market_snapshot(original_async)
    if e["source_win_wide_update_gap_seconds"]!=0 or l["source_win_wide_update_gap_seconds"]!=0:
        raise ValueError("not_two_source_timestamp_synchronized_states")
    if e["frames"]!=l["frames"] or set(e["win_odds"])!=set(l["win_odds"]):
        raise ValueError("early_late_roster_not_identical")
    comparison=report_two_snapshots(e,l,n_permutations=499)
    if comparison["status"]!="ONE_RACE_TWO_ARCHIVED_SYNCHRONIZED_SOURCE_UPDATED_PRICE_STATES":
        raise ValueError("incorrect_synchronized_status")
    decomposition=effect_splits(e,l)
    prior_async=report_two_snapshots(older,l,n_permutations=49)
    if prior_async["early_win_wide_source_update_gap_seconds"]!=660:
        raise ValueError("previous_asynchronous_archive_modified")
    align={
        "status":STATUS,"race_id":RACE_ID,
        "date":"2026-10-12",
        "race_and_market_state_count":[1,2],
        "source_matched_earlier_snapshot":receipt,
        "late_market_source_updates":l["source_updated_jst"],
        "first_both_market_source_updated_jst":e["source_updated_jst"],
        "actual_source_updated_elapsed_minutes":
            ( _time(l["source_updated_jst"]["wide"]) -
              _time(e["source_updated_jst"]["wide"]) ).total_seconds()/60,
        "source_timestamp_aligned_quote_update_states":2,
        "earlier_and_later_market_roster_equal":True,
        "observed_primary_snapshot_comparison":comparison,
        "arithmetic_source_channel_splits":decomposition,
        "asynchronous_early_source_sensitivity":{
            "early_win_wide_update_gap_seconds":
                prior_async["early_win_wide_source_update_gap_seconds"],
            "node_correlation_with_later":prior_async["same_race_11_horse_numbered_node_correlation"],
            "dyad_residual_correlation_with_later":prior_async["same_race_55_dyadic_residual_correlation"],
            "node_explained_fraction_of_price_change":
                prior_async["source_update_change_node_R2_weighted_late"],
        },
        "source_file_sha256":dict(sorted(hashes.items())),
        "independent_two_race_or_named_individual_repeatability":False,
        "source_updated_at_not_raw_provider_HTML_verified_against_live_page":True,
        "real_market_vote_volume_or_human_cognition_measured":False,
        "nonlinear_social_feedback_threshold_not_identified":True,
        "biological_behavior_kinship_or_genomic_effect_not_identified":True,
        "posthoc_after_inspecting_old_2026_10_12_race_outcome":True,
        "not_race_outcome_or_betting_inference":True,
    }
    return align


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    try:
        item=analysis()
    except (ValueError,KeyError,TypeError,OSError,OverflowError,ZeroDivisionError) as exc:
        p.error(str(exc))
    raw=json.dumps(item,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(raw,encoding="utf-8")
    else:
        print(raw,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
