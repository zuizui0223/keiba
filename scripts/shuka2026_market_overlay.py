#!/usr/bin/env python3
"""Carry locked v3.1 Shuka Sho C1/U/Q1/K1 into an ACTUAL odds M overlay.

With no actual date-stamped JRA win-odds snapshot, output ONLY exact
mathematical candidate-coverage bounds, not fake M members, odds, or
win probability. Once JRA betting actually opens, a user may supply
a real independently captured official-source odds snapshot. The
frozen market_channel(...) function is imported unchanged.

This is a separate, not-tuned SHADOW analysis in Draft PR #5,
NOT a formal 20-race v3.1 holdout freeze. No automatic wagering.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

from shuka2026_official_rule_audit import (
    SOURCE_FILE, MANIFEST, CLASSIFIER, HERE,
    audit as history_audit, blob_sha,
)
from shuka2026_bind_draw_numbers import DRAW_FILE, join_draw
from v31_candidate_channels import market_channel

JST=timezone(timedelta(hours=9))
START=datetime(2026,10,18,15,40,tzinfo=JST)
PRESALE_OPEN=datetime(2026,10,16,18,30,tzinfo=JST)
PRESALE_CLOSE=datetime(2026,10,17,17,30,tzinfo=JST)
RACE_SALE_OPEN=datetime(2026,10,17,19,30,tzinfo=JST)
REGULAR_ODDS_LAST=datetime(2026,10,18,15,39,tzinfo=JST)
FIXED_NOMINAL_M=5
SOURCE_IDS=set(range(1,18))
HISTORICAL_CANDIDATES={1,3,6,8,9,12}
MAX_CANDIDATE_FRAC=0.65


def source_base()->dict:
    history=json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    draw=json.loads(DRAW_FILE.read_text(encoding="utf-8"))
    base=history_audit(
        history,manifest=manifest,
        actual_classifier_blob_sha=blob_sha(CLASSIFIER),
    )
    source=join_draw(base,draw)
    got=set(source["official_nonmarket_v31_candidate_numbers_NOT_RANKING"])
    if (got!=HISTORICAL_CANDIDATES or source["horse_count"]!=17
        or sorted(r["official_horse_number"] for r in source["horse_records"])
           !=sorted(SOURCE_IDS)):
        raise ValueError("HOLD_PREVIOUS_17_HORSE_JRA_OFFICIAL_SOURCE_HAS_CHANGED")
    return source


def scenario_bounds()->dict:
    """Exact combinatorial bounds. NO assumptions about market probabilities."""
    nominal=FIXED_NOMINAL_M
    fixed=len(HISTORICAL_CANDIDATES)
    possible=[]
    for market_size in range(nominal,18):
        min_intersection=max(0,market_size+fixed-17)
        max_intersection=min(fixed,market_size)
        min_union=fixed+market_size-max_intersection
        max_union=fixed+market_size-min_intersection
        min_intersection_to_maintain_65pct=max(
            0,fixed+market_size-math.floor(MAX_CANDIDATE_FRAC*17)
        )
        possible.append({
            "market_M_size_including_cutoff_ties":market_size,
            "required_MIN_overlap_with_six_existing_candidates_to_keep_union_le_65pct":
                min_intersection_to_maintain_65pct,
            "feasible_overlap_range":[min_intersection,max_intersection],
            "possible_union_size_min":min_union,
            "possible_union_size_max":max_union,
            "possible_union_size_range_fraction":[min_union/17,max_union/17],
            "market_size_not_an_odds_prediction":True,
        })
    return {
        "source_field_size":17,
        "original_locked_nonmarket_candidates":sorted(HISTORICAL_CANDIDATES),
        "frozen_M_nominal_top_quarter_count_without_ties":nominal,
        "fixed_candidate_rate_ceiling_from_formal_holdout":MAX_CANDIDATE_FRAC,
        "maximum_candidate_count_below_or_equal_65pct":math.floor(MAX_CANDIDATE_FRAC*17),
        "nominal_M_no_ties_final_union_min":fixed,
        "nominal_M_no_ties_final_union_max":fixed+nominal,
        "cutoff_ties_can_expand_M_above_five":True,
        "all_possible_M_size_support_not_market_prediction":possible,
        "these_are_set_theory_bounds_not_probabilistic_expected_value":True,
    }


def _parse_source_time(v:str)->datetime:
    try:
        dt=datetime.fromisoformat(v)
    except (TypeError,ValueError) as exc:
        raise ValueError("HOLD_UNVERIFIABLE_MARKET_OBSERVATION_TIMESTAMP") from exc
    if dt.tzinfo is None or dt.utcoffset()!=timedelta(hours=9):
        raise ValueError("HOLD_MARKET_TIMESTAMP_NOT_JST_OFFSET_AWARE")
    return dt


def validate_actual_JRA_win_odds_snapshot(snapshot:dict)->tuple[datetime,list[dict]]:
    """Gates a documented input. Independent capture must still be verified."""
    if snapshot.get("schema")!="JRA_OFFICIAL_SHUKA2026_ACTUAL_WIN_ODDS_V1":
        raise ValueError("HOLD_NOT_ACTUAL_OFFICIAL_WIN_ODDS_SCHEMA")
    if (snapshot.get("race_id")!="2026-10-18-KYOTO-11"
        or snapshot.get("quote_type")!="actual_displayed_win_odds"
        or snapshot.get("is_pre_race") is not True):
        raise ValueError("HOLD_NOT_CORRECT_RACE_OR_PRE_RESULT_OFFICIAL_WIN_MARKET")
    url=str(snapshot.get("source_url") or "")
    parsed=urlsplit(url)
    if (parsed.scheme!="https"
        or parsed.hostname not in {"www.jra.go.jp","jra.go.jp"}
        or not (parsed.path.startswith("/JRADB/")
                or parsed.path.startswith("/keiba/odds"))):
        raise ValueError("HOLD_ORIGINAL_WIN_ODDS_URL_NOT_OFFICIAL_JRA")
    d=_parse_source_time(snapshot.get("observed_at_jst"))
    valid_time=(PRESALE_OPEN<=d<=PRESALE_CLOSE or
                RACE_SALE_OPEN<=d<REGULAR_ODDS_LAST)
    if not valid_time:
        raise ValueError("HOLD_JRA_NOT_IN_REAL_ADVANCE_OR_RACE_SALE_WINDOW")
    values=snapshot.get("horses")
    if not isinstance(values,list) or len(values)!=17:
        raise ValueError("HOLD_INCOMPLETE_17_RUNNER_ACTUAL_WIN_ODDS")
    rows=[]
    for row in values:
        if type(row.get("number")) is not int or row["number"] not in SOURCE_IDS:
            raise ValueError("HOLD_NOT_JRA_1_TO_17_TRUE_HORSE_NUMBERS")
        try:
            odd=float(row.get("win_odds"))
        except (TypeError,ValueError) as exc:
            raise ValueError("HOLD_UNOBSERVED_WIN_ODDS_VALUE") from exc
        if not math.isfinite(odd) or odd<1.0:
            raise ValueError("HOLD_UNOBSERVED_WIN_ODDS_VALUE")
        rows.append({"number":row["number"],"win_odds":odd})
    if {r["number"] for r in rows}!=SOURCE_IDS:
        raise ValueError("HOLD_DUPLICATE_OR_MISSING_JRA_RUNNER_IN_ACTUAL_ODDS")
    # A JRA URL and a timestamp alone do not cryptographically verify the
    # original tote page's contents; state that limitation explicitly.
    return d,rows


def run_market_overlay(base:dict,snapshot:dict|None=None)->dict:
    fixed=set(base["official_nonmarket_v31_candidate_numbers_NOT_RANKING"])
    if fixed!=HISTORICAL_CANDIDATES:
        raise ValueError("HOLD_HISTORICAL_V31_CLASSIFICATION_NOT_MATCHED")
    baseline={
        "status":"HOLD_UNTIL_ACTUAL_JRA_WIN_ODDS_ARE_AVAILABLE",
        "race":"2026-10-18 Kyoto 11R, Shuka Sho GI, 17 horses, 15:40 JST",
        "original_v31_classifier_blob_sha":base["original_v31_classifier_git_blob_SHA"],
        "JRA_card_source":base["JRA_official_card_source"],
        "official_JRA_horse_numbers_verified":True,
        "historical_C1_U_Q1_AND_K1_candidates":sorted(fixed),
        "candidate_names":{
            str(r["official_horse_number"]):r["horse_name"]
            for r in base["horse_records"] if r["official_horse_number"] in fixed
        },
        "JRA_2026_GI_first_advance_sale_opens_at_JST":
            PRESALE_OPEN.isoformat(),
        "JRA_GI_friday_sale_to_saturday_close":PRESALE_CLOSE.isoformat(),
        "JRA_saturday_evening_full_sunday_sale_opens_at":RACE_SALE_OPEN.isoformat(),
        "source_market_M_timestamps_and_price_not_seen_without_snapshot":snapshot is None,
        "market_M_numbers":None,
        "full_union_candidate_numbers":None,
        "locked_market_coverage_scenario":scenario_bounds(),
        "not_an_estimated_win_probability_or_positive_EV":True,
        "formal_20_race_v31_holdout_score_NOT_modified":True,
    }
    if snapshot is None:
        return baseline
    source_at,actual=validate_actual_JRA_win_odds_snapshot(snapshot)
    m=market_channel(actual)
    all_candidates=sorted(fixed|m)
    by_num={x["number"]:x["win_odds"] for x in actual}
    new_market_only=sorted(m-fixed)
    frac=len(all_candidates)/17
    return {
        **baseline,
        "status":"SHADOW_ONLY_ACTUAL_SOURCE_LABELED_WIN_ODDS_V31_FULL_UNION",
        "snapshot_captured_at_jst":source_at.isoformat(),
        "snapshot_source_url":snapshot["source_url"],
        "snapshot_independent_source_text_byte_VERIFICATION_NOT_DONE":True,
        "observed_ODDS_not_postrace_result":True,
        "market_M_numbers":sorted(m),
        "market_M_size_including_ties":len(m),
        "original_M_nominal_count":FIXED_NOMINAL_M,
        "market_cutoff_win_odds":max(by_num[n] for n in m),
        "market_M_only_not_historical_candidates":new_market_only,
        "overlap_M_with_history_count":len(fixed&m),
        "full_union_candidate_numbers":all_candidates,
        "candidate_fraction":frac,
        "candidate_rate_above_65pct":frac>MAX_CANDIDATE_FRAC,
        "full_union_size":len(all_candidates),
        "win_odds_for_market_M_only":{
            str(n):by_num[n] for n in sorted(m)
        },
        "reciprocal_ODDS_as_mathematical_breakeven_not_win_probability":{
            str(n):1/by_num[n] for n in sorted(m)
        },
        "shadow_only_not_a_formal_holdout_freeze_even_if_15_25min_before_start":True,
        "no_claim_betting_expectation_or_calibrated_horse_probabilities":True,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot",type=Path,
                   help="ONLY an independently captured genuine official JRA win odds input.")
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    base=source_base()
    odds=json.loads(args.snapshot.read_text(encoding="utf-8")) if args.snapshot else None
    output=run_market_overlay(base,odds)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":output["status"],
        "JRA_market_sale_begins":output["JRA_2026_GI_first_advance_sale_opens_at_JST"],
        "historic_six":output["historical_C1_U_Q1_AND_K1_candidates"],
        "M":output["market_M_numbers"],
        "union":output["full_union_candidate_numbers"],
        "candidate_fraction":output.get("candidate_fraction"),
        "not_a_calibrated_probability_or_bet":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
