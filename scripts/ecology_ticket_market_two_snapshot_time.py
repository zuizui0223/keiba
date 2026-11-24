#!/usr/bin/env python3
"""Two archived pre-race JRA Kyoto R8 price states: horse-node stability.

The race is identical on 2026-10-12 (11 horses, 55 wide pairs). Saved snapshots:
  early checked 13:35:59 JST; upstream WIN updated 13:22, WIDE 13:33;
  late  checked 13:44:55 JST; upstream WIN and WIDE updated 13:44;
  post 14:00 JST.
Early data are NOT synchronized (11-minute source-update mismatch). This is
not a clean time-series or proof of voter learning, thresholding, biological
individuality, genetic causality, horse-ID transfer, profitable selections,
or independently pre-registered prospective skill.

Despite that caveat we can quantify: aligned horse-node *PRICE* coefficient
correlation, dyadic remainder correlation, fraction of crossmarket price-shift
variance explained by changes in nodes, and early-to-late market-state
prediction using no later prices in estimating early node/global coefficients.

No race outcomes, voting volume, payouts or horse names are processed.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random

try:
    from scripts.ecology_ticket_information_graph import (
        ROOT, decompose_edges, graph_inputs
    )
    from scripts.ecology_ticket_market_smooth_null import (
        feature_map
    )
    from scripts.ecology_ticket_market_edge_block_holdout import (
        fit_weighted, predict
    )
    from scripts.ticket_type_historical_audit import read_json
    from scripts.ticket_type_models import _time
except (ImportError, ModuleNotFoundError):
    from ecology_ticket_information_graph import ROOT, decompose_edges, graph_inputs
    from ecology_ticket_market_smooth_null import feature_map
    from ecology_ticket_market_edge_block_holdout import fit_weighted, predict
    from ticket_type_historical_audit import read_json
    from ticket_type_models import _time

RACE_ID = "2608040508"
SOURCE_DATE = "2026-10-12"
EARLY = ROOT / "data" / SOURCE_DATE / "r8_markets.json"
LATE = ROOT / "data" / SOURCE_DATE / "r8_markets_latest.json"
EXPECTED_N = 11
N_PERMUTATIONS = 499
STATUS = "ONE_RACE_TWO_ARCHIVED_PRICE_STATES_EARLY_MARKETS_ASYNCHRONOUS"


def read_market_snapshot(data: dict) -> dict:
    if (data.get("race_id") != RACE_ID or data.get("race") != 8
            or data.get("horse_count") != EXPECTED_N):
        raise ValueError("snapshot_wrong_race")
    actual_start = _time(data["start_jst"])
    checked = _time(data["checked_at_utc"])
    if not checked < actual_start:
        raise ValueError("snapshot_not_before_race_start")
    frames = {int(i):int(v) for i,v in data["horse_frames"].items()}
    markets=data["markets"]
    if set(frames)!=set(range(1,EXPECTED_N+1)) or not set(("win","wide"))<=set(markets):
        raise ValueError("snapshot_missing_runner_or_market")
    timestamp={}
    for kind in ("win","wide"):
        source_time=_time(markets[kind]["updated_at_jst"])
        if source_time>checked or source_time>=actual_start:
            raise ValueError("post_receipt_or_post_start_quote")
        timestamp[kind]=source_time
    win = {}
    for q in markets["win"]["quotes"]:
        n=q["selection"]
        if (not isinstance(n,list) or len(n)!=1 or type(n[0]) is not int or
                n[0] in win or q["odds_low"]!=q["odds_high"] or q["odds_low"]<1):
            raise ValueError("win_price_field_invalid")
        win[n[0]]=float(q["odds_low"])
    if set(win)!=set(frames):
        raise ValueError("win_coverage_not_complete")
    strength={n:1./price for n,price in win.items()}
    wide=markets["wide"]["quotes"]
    discrepancies, weights, baseline=graph_inputs(strength,frames,wide)
    if len(discrepancies)!=55:
        raise ValueError("wide_55_pairs_incomplete")
    return {
        "race_id":RACE_ID,
        "start_jst":actual_start.isoformat(),
        "receipt_jst":checked.isoformat(),
        "source_updated_jst":{k:v.isoformat() for k,v in timestamp.items()},
        "source_win_wide_update_gap_seconds":abs((timestamp["win"]-timestamp["wide"]).total_seconds()),
        "frames":frames,"win_odds":win,"strength":strength,
        "wide_quotes":wide,"edge_y":discrepancies,"edge_w":weights,
        "baseline":baseline,"node":decompose_edges(discrepancies,weights),
    }


def corr(first:list[float],second:list[float]) -> float | None:
    if len(first)!=len(second) or not first:
        raise ValueError("comparison_vectors_mismatched")
    n=len(first)
    xbar=math.fsum(first)/n
    ybar=math.fsum(second)/n
    x=[v-xbar for v in first]
    y=[v-ybar for v in second]
    varx=math.fsum(v*v for v in x)
    vary=math.fsum(v*v for v in y)
    if varx<=1e-20 or vary<=1e-20:
        return None
    return math.fsum(a*b for a,b in zip(x,y))/math.sqrt(varx*vary)


def report_two_snapshots(early:dict,late:dict,*,n_permutations:int=N_PERMUTATIONS)->dict:
    if type(n_permutations) is not int or not 19<=n_permutations<=999:
        raise ValueError("invalid_descriptive_permutation_count")
    a,b=read_market_snapshot(early),read_market_snapshot(late)
    if (a["frames"]!=b["frames"] or
            a["start_jst"]!=b["start_jst"] or
            not _time(a["receipt_jst"])<_time(b["receipt_jst"]) or
            set(a["edge_y"])!=set(b["edge_y"])):
        raise ValueError("not_same_roster_in_two_prior_price_states")
    nodes=sorted(a["strength"])
    edge_order=sorted(a["edge_y"])
    node0=[a["node"]["node_effect"][n] for n in nodes]
    node1=[b["node"]["node_effect"][n] for n in nodes]
    edge0=[a["edge_y"][e] for e in edge_order]
    edge1=[b["edge_y"][e] for e in edge_order]
    residual0=[a["node"]["dyadic_residual"][e] for e in edge_order]
    residual1=[b["node"]["dyadic_residual"][e] for e in edge_order]
    node_corr=corr(node0,node1)
    if node_corr is None:
        raise ValueError("no_node_variance")
    rng=random.Random(20261123)
    shuffled=[]
    for _ in range(n_permutations):
        v=list(node0)
        rng.shuffle(v)
        shuffled.append(corr(v,node1))
    shuffled.sort()
    weighted_late=b["edge_w"]
    diff={edge:b["edge_y"][edge]-a["edge_y"][edge] for edge in edge_order}
    change=decompose_edges(diff,weighted_late)
    # All early model coefficients use early data ONLY; late deviations act
    # as future-target historical observations, not as covariates.
    sse_baseline=0.
    sse_node=0.
    sse_global=0.
    early_mean=math.fsum(a["edge_y"][e]*a["edge_w"][e] for e in edge_order)
    smooth_x=feature_map(a["strength"],4)
    smooth_coeff,smooth_off=fit_weighted(
        smooth_x,a["edge_y"],a["edge_w"],edge_order
    )
    for edge in edge_order:
        w=weighted_late[edge]
        y=b["edge_y"][edge]
        source=a["node"]["node_pred"][edge]
        global4=predict(smooth_coeff,smooth_off,smooth_x[edge])
        sse_baseline+=w*(y-early_mean)**2
        sse_node+=w*(y-source)**2
        sse_global+=w*(y-global4)**2
    if sse_baseline<=1e-20:
        raise ValueError("no_late_change_for_transfer_test")
    early_wide={tuple(sorted(q["selection"])):math.sqrt(q["odds_low"]*q["odds_high"])
                for q in a["wide_quotes"]}
    late_wide={tuple(sorted(q["selection"])):math.sqrt(q["odds_low"]*q["odds_high"])
               for q in b["wide_quotes"]}
    if set(early_wide)!=set(late_wide):
        raise ValueError("missing_time_pair")
    return {
        "schema_version":1,
        "status":(STATUS if a["source_win_wide_update_gap_seconds"]>0
                  else "ONE_RACE_TWO_ARCHIVED_SYNCHRONIZED_SOURCE_UPDATED_PRICE_STATES"),
        "race_id":RACE_ID,
        "horse_count":len(nodes),"full_wide_pairs":len(edge_order),
        "early_checked_jst":a["receipt_jst"],
        "late_checked_jst":b["receipt_jst"],
        "actual_start_jst":a["start_jst"],
        "early_market_updated_jst":a["source_updated_jst"],
        "late_market_updated_jst":b["source_updated_jst"],
        "early_win_wide_source_update_gap_seconds":
            a["source_win_wide_update_gap_seconds"],
        "late_win_wide_source_update_gap_seconds":
            b["source_win_wide_update_gap_seconds"],
        "early_source_market_mismatched_11_min":
            a["source_win_wide_update_gap_seconds"]==660,
        "early_quote_channels_source_updated_at_identical":
            a["source_win_wide_update_gap_seconds"]==0,
        "win_prices_changed_horses":sum(
            a["win_odds"][n]!=b["win_odds"][n] for n in nodes),
        "wide_pair_geometric_midpoint_changed":sum(
            early_wide[e]!=late_wide[e] for e in edge_order),
        "racing_outcomes_used":False,
        "same_race_11_horse_numbered_node_correlation":node_corr,
        "same_race_all_55_crossmarket_edge_correlation":corr(edge0,edge1),
        "same_race_55_dyadic_residual_correlation":corr(residual0,residual1),
        "source_update_change_node_R2_weighted_late":
            change["R2_node_vs_constant"],
        "early_to_late_market_residual_transfer_R2_vs_early_mean":{
            "early_fitted_node":1-sse_node/sse_baseline,
            "early_global_fourth_degree":1-sse_global/sse_baseline,
            "baseline_early_mean":0.0,
        },
        "horse_node_label_shuffle_reference":{
            "shuffles":n_permutations,
            "observed_corr":node_corr,
            "median_shuffled_corr":shuffled[n_permutations//2],
            "q05_q95":[shuffled[int(.05*(n_permutations-1))],
                       shuffled[int(.95*(n_permutations-1))]],
            "shuffled_at_least_observed_fraction_DESCRIPTIVE":
                sum(x>=node_corr for x in shuffled)/n_permutations,
            "inferential_p_value":None,
        },
        "independent_horse_ID_across_multiple_races":False,
        "multiple_independent_races_repeated_at_multiple_quote_times":False,
        "synchronized_early_win_wide_market_state":
            a["source_win_wide_update_gap_seconds"]==0,
        "actual_voter_or_horse_learning_identified":False,
        "true_replicated_population_market_time_series_available":False,
        "model_frozen_before_2026_10_12":False,
        "interpretation":("Exactly one historical race with two pre-race archived price states. "
                          "Time-aligned quote update stamps still do not identify voters, "
                          "causal social learning, nonlinear thresholds, or heritable horse traits."),
    }


def run_analysis(n_permutations:int=N_PERMUTATIONS)->dict:
    hashes={}
    a=read_json(EARLY,hashes)
    b=read_json(LATE,hashes)
    report=report_two_snapshots(a,b,n_permutations=n_permutations)
    report["source_file_sha256"]=dict(sorted(hashes.items()))
    return report


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path)
    p.add_argument("--permutations",type=int,default=N_PERMUTATIONS)
    a=p.parse_args()
    try:
        data=run_analysis(n_permutations=a.permutations)
    except (ValueError,TypeError,KeyError,OSError,OverflowError) as exc:
        p.error(str(exc))
    out=json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n"
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(out,encoding="utf-8")
    else:
        print(out,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
