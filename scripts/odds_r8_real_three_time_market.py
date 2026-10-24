#!/usr/bin/env python3
"""One *real* 3-time Kyoto 8R win-odds path and two matched-minute wide grids.

Archival input 2026-10-12 Kyoto 8R (11 horses):
- win at 12:21 and 13:26 from the source-locked Oct12 coverage audit,
- win plus 55 wide pair quotes at 13:44 from another prestart quote archive,
- 55 wide pairs at 13:26 from a separate source-locked page,
- JRA official *after-race* outcome 9-1-7 to score the precomputed prices.

Both win/wide market pages displayed *the same minute* at 13:26 and
13:44. Fetches are distinct HTTP pages, not atomically synchronized
underlying tote transactions. No actual betting flows or social behaviors
are identified. One real race is insufficient to test forecasting value
of the intermediate price path over the latest price.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha1
import json
import math
from pathlib import Path

from odds_real_multirace_archive_audit import SOURCE_SHA, read_file, _one_race
from odds_local_timeseries_preflight import intermediate_path_readiness
from odds_cross_pool_global_async import relative_pair_indices, compare
from odds_six_race_predictive_increment import (
    _odds_probabilities, score_forecast, verify_official_oct12,
)

ROOT = Path(__file__).resolve().parents[1]
OTHER_SOURCE = {
    "mid_wide": ("data/2026-10-12/remaining-snapshots/r8_wide.json",
                 "10bb0d0bcab6035eceaa4edda8c31999d83dae05"),
    "late_all": ("data/2026-10-12/r8_markets_latest.json",
                 "5e84f3c445249564b2cd7ed358591ed02a8b2d88"),
}
STATUS = "ONE_REAL_PRESTART_THREE_POINT_QUOTE_PATH_AND_MATCHED_MINUTE_WIDE_DESC_ONLY"


def _locked(path, sha, root=ROOT):
    raw=(Path(root)/path).read_bytes()
    if sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()!=sha:
        raise ValueError("HOLD_R8_ARCHIVED_SOURCE_CHANGED")
    return json.loads(raw.decode("utf-8"))


def _aware(t):
    stamp=datetime.fromisoformat(t)
    if stamp.utcoffset() is None:
        raise ValueError("HOLD_MISSING_TIMEZONE")
    return stamp


def _win_vector(rows):
    out={}
    for v in rows:
        selection=v["selection"]
        if len(selection)!=1 or not isinstance(selection[0],int):
            raise ValueError("HOLD_NOT_SINGLE_HORSE_QUOTE")
        num=selection[0]
        price=v["odds_low"]
        if (num in out or not isinstance(price,(int,float))
            or price<=1 or not math.isfinite(price) or
            v.get("odds_high")!=price):
            raise ValueError("HOLD_DUPLICATE_OR_INVALID_SINGLE_WIN_QUOTE")
        out[num]=price
    return out


def _wide_vector(rows):
    out={}
    for v in rows:
        selection=v["selection"]
        if (len(selection)!=2 or selection[0]==selection[1]
            or any(not isinstance(x,int) for x in selection)):
            raise ValueError("HOLD_NOT_VALID_TWO_HORSE_WIDE")
        key=tuple(sorted(selection))
        if key in out or v["odds_low"]<=1:
            raise ValueError("HOLD_DUPLICATE_OR_INVALID_WIDE_QUOTE")
        out[key]=v["odds_low"]
    return out


def collect_pre_race_price_panels(root=ROOT):
    a=read_file(root,SOURCE_SHA[8][0])
    b=read_file(root,SOURCE_SHA[8][1])
    _one_race(a,b,8)  # Already enforces full roster and prestart source clocks.
    midwide=_locked(*OTHER_SOURCE["mid_wide"],root=root)
    late=_locked(*OTHER_SOURCE["late_all"],root=root)
    if (midwide.get("race")!=8 or midwide.get("page_code")!="wide"
        or late.get("race_id")!="2608040508" or late.get("horse_count")!=11
        or late["start_jst"]!=a["start_jst"]):
        raise ValueError("HOLD_THIRD_TIME_OR_WIDE_WRONG_RACE")
    a_win={r["number"]:r["win_odds"] for r in a["horses"]}
    b_win=_win_vector(b["quotes"]["win"])
    c_win=_win_vector(late["markets"]["win"]["quotes"])
    early_wide=_wide_vector(midwide["quotes"]["wide"])
    final_wide=_wide_vector(late["markets"]["wide"]["quotes"])
    if (set(a_win)!=set(b_win) or set(a_win)!=set(c_win)
        or len(a_win)!=11 or len(early_wide)!=55
        or set(early_wide)!=set(final_wide)):
        raise ValueError("HOLD_R8_THREE_TIMES_NOT_FULL_MARKET_ROSTER")
    posted=_aware(a["start_jst"])
    points=[
        ("12:21",a["odds_updated_at_jst"],a["odds_observed_at_jst"],a_win),
        ("13:26",b["updated_at_jst"],b["observed_at_jst"],b_win),
        ("13:44",late["markets"]["win"]["updated_at_jst"],
         late["markets"]["win"]["observed_at_utc"],c_win),
    ]
    for i,(_,pub,received,_) in enumerate(points):
        p,obs=_aware(pub),_aware(received)
        if p>obs or obs>=posted or p>=posted or (i and p<=_aware(points[i-1][1])):
            raise ValueError("HOLD_R8_THIRD_MARKET_CLOCK_OR_PRESTART")
    # At both evaluation windows, source page UPDATE clocks exactly match.
    if (midwide["updated_at_jst"]!=b["updated_at_jst"]
        or late["markets"]["wide"]["updated_at_jst"]!=late["markets"]["win"]["updated_at_jst"]):
        raise ValueError("HOLD_R8_WIN_WIDE_PUBLISH_MINUTES_UNALIGNED")
    if not (_aware(midwide["observed_at_jst"])<posted and
            _aware(late["markets"]["wide"]["observed_at_utc"])<posted):
        raise ValueError("HOLD_R8_WIDE_FETCH_AFTER_POST")
    for val in (midwide["url"],b["url"],
                late["markets"]["win"]["source_url"],
                late["markets"]["wide"]["source_url"]):
        if not val.startswith("https://sports.yahoo.co.jp/keiba/"):
            raise ValueError("HOLD_MIXED_SOURCE_PROVIDER")
    def normalized(o):
        weights={i:1/v for i,v in o.items()}
        total=sum(weights.values())
        return {i:v/total for i,v in weights.items()}
    win_q=[normalized(d) for _,_,_,d in points]
    sums=[(_aware(p),q) for (_,p,_,_),q in zip(points,win_q)]
    path=intermediate_path_readiness(sums)
    if not path["status"].startswith("SOURCE_TIME_WEIGHTS"):
        raise ValueError("HOLD_R8_CANNOT_MEASURE_INTERMEDIATE_CURVATURE")
    jwin=[]
    for label,ts,receipt,prices in points:
        q=normalized(prices)
        jwin.append({
            "label":label,"provider_published_quote_minute":ts,
            "observed_at":receipt,"n_horses":len(prices),
            "provisional_model_probabilities":_odds_probabilities(prices),
            "win_prices":prices,
            "relative_weights":q,
        })
    pair_before=relative_pair_indices({"label":"r8_1326","win":b_win,
                                        "wide":early_wide})
    pair_after=relative_pair_indices({"label":"r8_1344","win":c_win,
                                       "wide":final_wide})
    pair_compare=compare(pair_before,pair_after)
    return jwin, path, pair_compare, a["start_jst"], (
        b_win, c_win, early_wide, final_wide
    )


def audit(root=ROOT):
    # Forecast and cross-pool indices computed before loading postrace outcome.
    panels, path, pairs, post_jst, raw=collect_pre_race_price_panels(root)
    t=panels
    def tv(a,b):
        return 50*sum(abs(a["relative_weights"][k]-b["relative_weights"][k])
                      for k in a["relative_weights"])
    official,at=verify_official_oct12(root)
    if not _aware(post_jst)<at:
        raise ValueError("HOLD_OFFICIAL_OUTCOME_AVAILABLE_BEFORE_RACE")
    labels=official["races"]["8"]["positions"]
    if labels!=[9,1,7]:
        raise ValueError("HOLD_R8_JRA_OFFICIAL_OUTCOME_CHANGING")
    obs=[]
    for p in panels:
        score=score_forecast(p["provisional_model_probabilities"],labels)
        obs.append({
            "label":p["label"],
            "published":p["provider_published_quote_minute"],
            "receipt":p["observed_at"],
            "winning_horse_9_displayed_win_odds":p["win_prices"][9],
            "winning_horse_9_PL_win_reference":p["relative_weights"][9],
            "proper_outcome_metrics": {
                "winner_log_loss":score["win_categorical_log_loss"],
                "top3_binary_brier":score["top3_binary_brier_mean_per_horse"],
            },
        })
    b_win,c_win,b_wide,c_wide=raw
    return {
        "status":STATUS,
        "race":"2026-10-12 Kyoto 8R, source_id=2608040508",
        "actual_official_top3":labels,
        "jra_official_result_source":official["races"]["8"]["source_url"],
        "n_horses":11,
        "price_path_three_real_complete_source_timepoints":True,
        "earliest_snapshot_is_not_opening_sale":True,
        "source_update_timestamp_is_only_reported_to_minute":True,
        "source_pages_not_an_atomic_combined_tote_snapshot":True,
        "before_race_quote_snapshots":obs,
        "time_weighted_middle_curvature":path,
        "price_redistribution_pp":{
            "1221_to_1326":tv(t[0],t[1]),
            "1326_to_1344":tv(t[1],t[2]),
            "1221_to_1344":tv(t[0],t[2]),
        },
        "win_wide_source_update_minutes_match_at_both_checkpoints":True,
        "wide_two_time_full_pair_count":pairs["pair_count"],
        "win_wide_relative_pair_index_change":pairs,
        "selected_pair_3_11":{
            "before_wide_lower":b_wide[(3,11)],
            "after_wide_lower":c_wide[(3,11)],
            "horse3_win_odds_before_after":[b_win[3],c_win[3]],
            "horse11_win_odds_before_after":[b_win[11],c_win[11]],
            "different_direction_win_and_pair_price":(
                c_wide[(3,11)]>b_wide[(3,11)]
                and c_win[3]<b_win[3]
                and c_win[11]<b_win[11]),
        },
        "scientific_limitations":[
            "One race only. Three price observations make curvature mathematically observable but not predictive information identifiable.",
            "Cross-pool pages carry matching displayed source minutes, not proof of atomic pool updates or all-bettor transaction times.",
            "55 winning wide bets overlap; their pair residuals are not 55 independent races or 55 risk-adjusted probabilities.",
            "PL win/top3 is an exact ranking assumption from normalized inverse displayed odds, not calibrated empirical horse probability.",
            "No threshold, positive payout EV, price-following causality or incremental win/place skill has been validated.",
            "No retroactive v3.1 holdout evaluation or betting selection is created.",
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=Path("tmp/odds-r8-real-three-point-path.json"))
    args=p.parse_args()
    r=audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":r["status"],
        "n_win_horses":r["n_horses"],
        "full_wide_pairs":r["wide_two_time_full_pair_count"],
        "market_TV":r["price_redistribution_pp"],
        "middle_path_curvature_sd":r["time_weighted_middle_curvature"][
            "crosshorse_sd_of_centered_intermediate_log_relative_price_curvature"],
        "middle_path_direction_reversals":r["time_weighted_middle_curvature"][
            "horses_with_direction_reversal_from_first_to_mid_to_last"],
        "outcome_scores":[{"time":v["label"],"win_ll":v["proper_outcome_metrics"]["winner_log_loss"],
                           "top3_brier":v["proper_outcome_metrics"]["top3_binary_brier"]}
                          for v in r["before_race_quote_snapshots"]],
        "pairs_25pct_threshold":r["win_wide_relative_pair_index_change"][
            "pairs_with_cross_pool_residual_ratio_change_at_least_25pct"],
        "crosspool_residual_rank_spearman":r["win_wide_relative_pair_index_change"][
            "residual_rank_spearman"],
        "pair3_11_nonconcordant":r["selected_pair_3_11"]["different_direction_win_and_pair_price"],
        "causal_inference_or_forecast_threshold":"HOLD_ONE_RACE"
    },ensure_ascii=False))


if __name__=="__main__":
    main()
