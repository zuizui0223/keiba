#!/usr/bin/env python3
"""Count actual race-level full-field odds timelines already archived in keiba.

Five same-day Kyoto races from 2026-10-12 and one multi-snapshot 2026-10-18
Shuka Sho race. No post-race outcome, wager, live scrape, or cross-race
probability modeling. 84 horse ENTRIES are NOT 84 independent races.

This does not infer significant thresholds: only 6 races over 2 dates, and
the Shuka overnight transition also changes provider and observation clock.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
from statistics import mean

from shuka2026_odds_information_hierarchy import (
    adjacent_summary, git_blob_sha, load_snapshots, read_locked, share,
)

ROOT = Path(__file__).resolve().parents[1]
STATUS = "SIX_REAL_RACES_TWO_DATES_DESCRIPTIVE_ONLY_NO_VALID_THRESHOLD"
SOURCE_SHA = {
    8: (
        ("data/2026-10-12/kyoto_08.json",
         "40b8626ece484ef6631d4bd97aaf89f26eedec09"),
        ("data/2026-10-12/remaining-snapshots/r8_tfw.json",
         "65fa640d6a07b7d94eb6e2904f6cc73f07a96448"),
    ),
    9: (
        ("data/2026-10-12/kyoto_09.json",
         "71f6fd82a3c8f44d99ce66354ae077e998b6a238"),
        ("data/2026-10-12/remaining-snapshots/r9_tfw.json",
         "be94d8b01a2b67287958598842cc724029f45e89"),
    ),
    10: (
        ("data/2026-10-12/kyoto_10.json",
         "4b8c098eedb478ebd6a9e3e874aa6b692adcfe9a"),
        ("data/2026-10-12/remaining-snapshots/r10_tfw.json",
         "cdf8f36a073f68d351417d0046f5ab5c1ccc2be3"),
    ),
    11: (
        ("data/2026-10-12/kyoto_11.json",
         "72180071976ffb9efe81cf6b4a6dfdb2aa458bd0"),
        ("data/2026-10-12/remaining-snapshots/r11_tfw.json",
         "751734355c67149b39cd1ebaf9682aac24f352e5"),
    ),
    12: (
        ("data/2026-10-12/kyoto_12.json",
         "3b9194da50df0ead111d179dac609e3c61d3a1c2"),
        ("data/2026-10-12/remaining-snapshots/r12_tfw.json",
         "6da13808c7b2a9c716a74b1c41d2c08296318c09"),
    ),
}
BANDS = ((0, 5, "<5"), (5, 15, "5-15"),
         (15, 50, "15-50"), (50, math.inf, "50+"))


def independent_uniform_newvote_fit(q0, q1):
    """Best one-parameter fit of uniform, independent new votes.

    The INPUT is a price-derived relative index, NOT the actual vote
    distribution. q1_pred=(1-lambda)*q0+lambda*uniform.
    lambda is a least-squares *hypothetical* mixing parameter, not
    measured incremental stakes or a causal share of real bettors.
    A poor fit falsifies only uniform-new-vote dilution, NOT every
    possible model without herding (informed non-herders can be skewed).
    """
    if set(q0)!=set(q1) or len(q0)<3:
        raise ValueError("HOLD_MISMATCHED_FULL_RACE_SHARE_VECTOR")
    if not math.isclose(sum(q0.values()),1.0,abs_tol=1e-9) or not math.isclose(
            sum(q1.values()),1.0,abs_tol=1e-9):
        raise ValueError("HOLD_UNNORMALIZED_PROXIES")
    n=len(q0)
    direction={i:1/n-q0[i] for i in q0}
    observed={i:q1[i]-q0[i] for i in q0}
    norm=sum(v*v for v in direction.values())
    lstar=(sum(observed[i]*direction[i] for i in q0)/norm) if norm>1e-15 else 0.0
    lstar=max(0.0,min(1.0,lstar))
    pred={i:(1-lstar)*q0[i]+lstar/n for i in q0}
    observed_TV=50*sum(abs(observed[i]) for i in q0)
    residual_TV=50*sum(abs(q1[i]-pred[i]) for i in q0)
    before=sum(observed[i]**2 for i in q0)
    after=sum((q1[i]-pred[i])**2 for i in q0)
    return {
        "status":"CONSTRAINED_LEAST_SQUARES_UNIFORM_NEWVOTE_NULL_ONLY",
        "fitted_hypothetical_uniform_newvote_fraction":lstar,
        "observed_normalized_inverse_odds_TV_pp":observed_TV,
        "unexplained_TV_after_uniform_dilution_fit_pp":residual_TV,
        "fraction_squared_share_change_explained_by_uniform_null":
            1-after/before if before>1e-20 else None,
        "not_an_estimate_of_true_incremental_bets":True,
        "rejecting_uniform_bets_would_not_identify_herding":True,
    }


def read_file(root, item):
    path, locked_sha = item
    raw = (Path(root)/path).read_bytes()
    if git_blob_sha(raw) != locked_sha:
        raise ValueError("HOLD_UPSTREAM_SOURCE_DRIFT:" + path)
    return json.loads(raw.decode("utf-8"))


def _time(x):
    t = datetime.fromisoformat(x)
    if t.utcoffset() is None:
        raise ValueError("HOLD_UNVERIFIED_OR_NAIVE_TIMESTAMP")
    return t


def _one_race(early, late, race_no):
    rid = "26080405" + str(race_no).zfill(2)
    if (early.get("race_id") != rid or late.get("race") != race_no
            or late.get("page_code") != "tfw"
            or early.get("date") != "2026-10-12"
            or early.get("venue") != "京都"):
        raise ValueError("HOLD_CROSS_RACE_JOIN_MISMATCH")
    first, second, start = (_time(early["odds_updated_at_jst"]),
                            _time(late["updated_at_jst"]),
                            _time(early["start_jst"]))
    fetched_first, fetched_second = (_time(early["odds_observed_at_jst"]),
                                      _time(late["observed_at_jst"]))
    if not (first <= fetched_first and second <= fetched_second
            and first < second and fetched_first < fetched_second
            and fetched_second < start):
        raise ValueError("HOLD_SOURCE_TIME_TRAVEL_OR_POSTRACE_QUOTES")
    if late.get("missing") != []:
        raise ValueError("HOLD_INCOMPLETE_LATE_SOURCE")
    a={}
    for h in early["horses"]:
        number=h["number"];price=h["win_odds"]
        if number in a:
            raise ValueError("HOLD_DUPLICATE_EARLY_HORSE")
        a[number]=price
    b={}
    for h in late["quotes"]["win"]:
        if len(h["selection"]) != 1 or h["odds_low"] != h["odds_high"]:
            raise ValueError("HOLD_INCONSISTENT_WIN_QUOTE")
        n=h["selection"][0]
        if n in b:
            raise ValueError("HOLD_DUPLICATE_LATE_HORSE")
        b[n]=h["odds_low"]
    if set(a)!=set(b) or len(a)!=len(late["horses"]) or len(a)<5:
        raise ValueError("HOLD_INCOMPLETE_FULL_FIELD_PAIRING")
    if any(type(v) not in (float,int) or v<=1 or not math.isfinite(v)
           for v in list(a.values())+list(b.values())):
        raise ValueError("HOLD_BAD_WIN_ODDS")
    q0, q1 = share(a), share(b)
    tv = 50 * sum(abs(q0[i]-q1[i]) for i in a)
    rank0 = sorted(a, key=lambda h:(a[h],h))
    rank1 = sorted(b, key=lambda h:(b[h],h))
    changed = [
        {"horse_number":i,"first_odds":a[i],"later_odds":b[i],
         "delta_quote_pct":100*(b[i]/a[i]-1),
         "abs_delta_quote_pct":abs(100*(b[i]/a[i]-1))}
        for i in sorted(a)
    ]
    return {
        "race_id":rid,"date":"2026-10-12","venue":"京都",
        "race":race_no,"n_horses":len(a),
        "source_publisher":"Yahoo/SportsNavi",
        "source_quote_timestamp_provenance":"displayed updated_at, not verified origin transaction time",
        "earlier_source_quote_update_at":first.isoformat(),
        "later_source_quote_update_at":second.isoformat(),
        "earlier_source_received_at":fetched_first.isoformat(),
        "later_source_received_at":fetched_second.isoformat(),
        "minutes_between_displayed_update_times":
            (second-first).total_seconds()/60,
        "normalized_inverse_quote_total_variation_pp":tv,
        "uniform_independent_new_votes_reference":
            independent_uniform_newvote_fit(q0,q1),
        "horses_absolute_quote_move_ge20pct":
            sum(x["abs_delta_quote_pct"]>=20 for x in changed),
        "full_field_top_five_membership_unchanged":
            set(rank0[:5])==set(rank1[:5]),
        "count_of_horses_with_changed_ordinal_ranks":
            sum(rank0.index(h)!=rank1.index(h) for h in a),
        "per_horse_descriptive_quote_change":changed,
        "twenty_percent_is_a_preexisting_monitoring_threshold_not_predictive":True,
    }


def _bands(races):
    all_changes = [
        row for race in races for row in race["per_horse_descriptive_quote_change"]]
    out=[]
    for low, high, label in BANDS:
        x=[v for v in all_changes if low<=v["first_odds"]<high]
        out.append({
            "earlier_win_odds_band":label,
            "horse_entries":len(x),
            "horses_over20pct":sum(v["abs_delta_quote_pct"]>=20 for v in x),
            "mean_absolute_quote_change_pct":
                mean(v["abs_delta_quote_pct"] for v in x) if x else None,
            "independent_sample_unit_is_race_not_horse":True,
        })
    return out


def audit(root=ROOT):
    races=[]
    for race_no, (path_a,path_b) in SOURCE_SHA.items():
        a, b = read_file(root,path_a),read_file(root,path_b)
        races.append(_one_race(a,b,race_no))
    snaps=load_snapshots(read_locked(root))
    summaries=[adjacent_summary(snaps[i],snaps[i+1])
               for i in range(len(snaps)-1)]
    if len(snaps)!=4 or set(s["label"] for s in snaps)!={
            "sat_1437","sat_1537","sun_1142","sun_1218"}:
        raise ValueError("HOLD_SHUKA_SOURCE_COUNT")
    dates={"2026-10-12","2026-10-18"}
    n_real_races=len(races)+1
    return {
        "status":STATUS,
        "distinct_real_races":n_real_races,
        "distinct_meeting_dates":len(dates),
        "win_horse_entries_with_2_or_more_prestart_captures":
            sum(r["n_horses"] for r in races)+len(snaps[0]["win"]),
        "independent_comparison_races_same_day_with_two_full_quote_sets":len(races),
        "additional_distinct_Shuka_20261018_races_with_four_full_quotes":1,
        "kyoto_20261012_races":[
            {k:v for k,v in race.items() if k!="per_horse_descriptive_quote_change"}
            for race in races
        ],
        "kyoto_20261012_initial_odds_band_descriptive":_bands(races),
        "kyoto_20261012_race_equal_mean_quote_TV_pp":
            mean(r["normalized_inverse_quote_total_variation_pp"] for r in races),
        "kyoto_20261012_total_runner_entries":sum(r["n_horses"] for r in races),
        "kyoto_20261012_horses_absolute_quote_move_ge20pct":
            sum(r["horses_absolute_quote_move_ge20pct"] for r in races),
        "kyoto_20261012_top_five_membership_unchanged_races":
            sum(r["full_field_top_five_membership_unchanged"] for r in races),
        "kyoto_20261012_uniform_newvote_best_fit_at_zero_races":
            sum(r["uniform_independent_new_votes_reference"]
                ["fitted_hypothetical_uniform_newvote_fraction"]<1e-12
                for r in races),
        "kyoto_20261012_uniform_newvote_null_is_not_every_independent_information_model":
            True,
        "shuka_snapshot_adjacent_transitions":[
            {"from":s["from"],"to":s["to"],
             "normalized_inverse_quote_TV_pp":s["relative_share_total_variation_pp"],
             "provider_changed_or_quote_timestamp_unaligned":
                 s["mixed_provider_or_timestamp_semantics"]}
            for s in summaries
        ],
        "limitation":"Only six independent races on two dates. A horse-by-race row is NOT an independent forecast test unit; monitoring threshold >20% not a validated odds or outcome threshold.",
        "prediction_skill": "HOLD_NO_RACE_BLOCKED_FUTURE_HOLDOUT",
        "winning_probability_calibrated":False,
        "source_winning_odds_data_rights_to_redistribute_bulk":False,
        "official_time_critical_update_clock_verified_for_all_sources":False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,
                        default=Path("tmp/odds-real-multirace-coverage.json"))
    args=parser.parse_args()
    r=audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":r["status"],
        "race_count":r["distinct_real_races"],
        "meeting_dates":r["distinct_meeting_dates"],
        "horse_entries":r["win_horse_entries_with_2_or_more_prestart_captures"],
        "kyoto_20261012_TV_by_race":[
            {"race":x["race"],"TV_pp":round(x["normalized_inverse_quote_total_variation_pp"],3)}
            for x in r["kyoto_20261012_races"]],
        "official_forecasting_claim":r["prediction_skill"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
