#!/usr/bin/env python3
"""One-race market-source-update decomposition, NOT observed voter causality.

Archived 2026-10-12 Kyoto R8: two pre-race sets of win and wide prices.
Observed archives:
  E/E : earlier win 13:22, earlier wide 13:33 (not synchronized).
  L/L : later win 13:44, later wide 13:44.
Counterfactual *arithmetic* recombinations, never actual joint snapshots:
  L/E : later win 13:44 with earlier wide 13:33.
  E/L : earlier win 13:22 with later wide 13:44.

The log price ratio r_ij=log(q_wide_ij/p_winPL_wide_ij) separates:
 Δr_total = Δr_win_only + Δr_wide_only exactly.
Re-fitting weighted horse-node and dyad components on all four combinations,
using one FIXED late-PL weight scheme, similarly partitions node/dyad update.
Numerical variance allocations are descriptive covariance shares and can
be negative or exceed one: NOT causal effects or independent time updates.

Both prices are derived from source-visible displayed odds, not actual
market vote volumes, posterior beliefs or animal behavior. The early win
and wide feeds are 11 minutes apart and this is ONE single race.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

try:
    from scripts.ecology_ticket_market_two_snapshot_time import (
        EARLY, LATE, read_market_snapshot, read_json, corr, RACE_ID,
    )
    from scripts.ecology_ticket_information_graph import (
        graph_inputs, decompose_edges,
    )
except (ImportError, ModuleNotFoundError):
    from ecology_ticket_market_two_snapshot_time import (
        EARLY, LATE, read_market_snapshot, read_json, corr, RACE_ID,
    )
    from ecology_ticket_information_graph import (
        graph_inputs, decompose_edges,
    )

STATUS = "ONE_RACE_TWO_SOURCE_ARITHMETIC_DECOMPOSITION_NOT_CAUSAL_TIME_SERIES"
SOURCES = {
    "early_win_early_wide": ("early", "early"),
    "late_win_early_wide": ("late", "early"),
    "early_win_late_wide": ("early", "late"),
    "late_win_late_wide": ("late", "late"),
}


def _weighted_mean(values:dict,weights:dict)->float:
    return (math.fsum(weights[k]*values[k] for k in values) /
            math.fsum(weights.values()))


def weighted_cov(a:dict,b:dict,weights:dict)->float:
    if not a or set(a)!=set(b) or set(a)!=set(weights):
        raise ValueError("invalid_weighted_pair_support")
    ma,mb=_weighted_mean(a,weights),_weighted_mean(b,weights)
    return math.fsum(weights[k]*(a[k]-ma)*(b[k]-mb) for k in a)/math.fsum(weights.values())


def price_distribution(state:dict,kind:str)->dict:
    if kind=="win":
        inv={i:1/o for i,o in state["win_odds"].items()}
    elif kind=="wide":
        inv={
            tuple(sorted(q["selection"])):1/math.sqrt(q["odds_low"]*q["odds_high"])
            for q in state["wide_quotes"]
        }
        if len(inv)!=len(state["wide_quotes"]):
            raise ValueError("duplicate_wide_market_quote")
    else:
        raise ValueError("invalid_price_channel")
    z=math.fsum(inv.values())
    return {k:v/z for k,v in inv.items()}


def js_divergence(p:dict,q:dict)->float:
    if set(p)!=set(q) or not p or any(x<=0 for x in p.values()) or any(x<=0 for x in q.values()):
        raise ValueError("invalid_js_support")
    if not math.isclose(math.fsum(p.values()),1,abs_tol=1e-10):
        raise ValueError("not_normalized_p")
    if not math.isclose(math.fsum(q.values()),1,abs_tol=1e-10):
        raise ValueError("not_normalized_q")
    return .5*math.fsum(
        p[k]*math.log(2*p[k]/(p[k]+q[k])) +
        q[k]*math.log(2*q[k]/(p[k]+q[k]))
        for k in p
    )


def effect_splits(early_market:dict,late_market:dict)->dict:
    if (early_market["race_id"]!=RACE_ID or late_market["race_id"]!=RACE_ID or
            early_market["frames"]!=late_market["frames"] or
            early_market["start_jst"]!=late_market["start_jst"] or
            set(early_market["edge_y"])!=set(late_market["edge_y"])):
        raise ValueError("invalid_race_matching_two_states")
    states={}
    for name,(which_win,which_wide) in SOURCES.items():
        swin=early_market if which_win=="early" else late_market
        swide=early_market if which_wide=="early" else late_market
        y,w,base=graph_inputs(
            swin["strength"],swin["frames"],swide["wide_quotes"]
        )
        states[name]={"y":y,"weights":w,"pl":base}
    # Use ONE immutable weighting to make WLS projection linear in y.
    w=late_market["edge_w"]
    for item in states.values():
        item["node"]=decompose_edges(item["y"],w)
    early=states["early_win_early_wide"]
    late=states["late_win_late_wide"]
    winnew=states["late_win_early_wide"]
    widenew=states["early_win_late_wide"]
    keys=sorted(w)
    delta_total={e:late["y"][e]-early["y"][e] for e in keys}
    delta_win={e:winnew["y"][e]-early["y"][e] for e in keys}
    delta_wide={e:widenew["y"][e]-early["y"][e] for e in keys}
    maximum=max(
        abs(delta_total[e]-delta_win[e]-delta_wide[e]) for e in keys
    )
    if maximum>1e-10:
        raise ValueError("price_decomposition_not_additive")
    projections={}
    for label,difference in (("total",delta_total),
                             ("win_source",delta_win),
                             ("wide_source",delta_wide)):
        projections[label]=decompose_edges(difference,w)
    node_total=projections["total"]["node_pred"]
    node_win=projections["win_source"]["node_pred"]
    node_wide=projections["wide_source"]["node_pred"]
    dyad_total=projections["total"]["dyadic_residual"]
    dyad_win=projections["win_source"]["dyadic_residual"]
    dyad_wide=projections["wide_source"]["dyadic_residual"]
    node_error=max(abs(node_total[e]-node_win[e]-node_wide[e]) for e in keys)
    dyad_error=max(abs(dyad_total[e]-dyad_win[e]-dyad_wide[e]) for e in keys)
    if max(node_error,dyad_error)>1e-10:
        raise ValueError("fixed_weight_node_projection_not_linear")
    vt=weighted_cov(delta_total,delta_total,w)
    if vt<=1e-18:
        raise ValueError("no_observed_price_change")
    # Cov(total, source) / Var(total) is the centered variance share.
    # May be negative if two streams oppose each other.
    variance_sources={
        "win_source_covariance_share_of_total_logratio_change":
            weighted_cov(delta_win,delta_total,w)/vt,
        "wide_source_covariance_share_of_total_logratio_change":
            weighted_cov(delta_wide,delta_total,w)/vt,
        "win_source_standalone_change_sd":
            math.sqrt(max(0.,weighted_cov(delta_win,delta_win,w))),
        "wide_source_standalone_change_sd":
            math.sqrt(max(0.,weighted_cov(delta_wide,delta_wide,w))),
        "total_change_sd":math.sqrt(vt),
        "win_vs_wide_source_change_correlation":
            (weighted_cov(delta_win,delta_wide,w) /
             math.sqrt(weighted_cov(delta_win,delta_win,w)*
                       weighted_cov(delta_wide,delta_wide,w))),
    }
    if abs(sum(v for k,v in variance_sources.items() if "share_of_total" in k)-1)>1e-10:
        raise ValueError("two_source_covariance_shares_not_complete")
    projections_info={
        label:{
            "node_explained_R2_of_source_delta":
                obj["R2_node_vs_constant"],
            "node_delta_rms":math.sqrt(
                math.fsum(w[e]*obj["node_pred"][e]**2 for e in keys)
                /math.fsum(w.values())),
            "dyad_delta_rms":obj["weighted_residual_rms"],
        } for label,obj in projections.items()
    }
    cross_corr={}
    for name,state in states.items():
        nod=state["node"]["node_effect"]
        cross_corr[name]={
            "horse_node_corr_with_late_synchronized":corr(
                [nod[k] for k in sorted(nod)],
                [late["node"]["node_effect"][k] for k in sorted(nod)]
            ),
            "dyad_corr_with_late_synchronized":corr(
                [state["node"]["dyadic_residual"][e] for e in keys],
                [late["node"]["dyadic_residual"][e] for e in keys],
            ),
            "observed_both_market_feeds_in_archive":
                name in ("early_win_early_wide","late_win_late_wide"),
            "win_from_time":SOURCES[name][0],
            "wide_from_time":SOURCES[name][1],
        }
    win0=price_distribution(early_market,"win")
    win1=price_distribution(late_market,"win")
    wide0=price_distribution(early_market,"wide")
    wide1=price_distribution(late_market,"wide")
    def effective(d):return 1/math.fsum(v*v for v in d.values())
    return {
        "schema_version":1,"status":STATUS,
        "race_id":RACE_ID,"horse_count":len(win0),"pair_count":len(wide0),
        "early_win_wide_update_gap_seconds":
            early_market["source_win_wide_update_gap_seconds"],
        "later_win_wide_update_gap_seconds":
            late_market["source_win_wide_update_gap_seconds"],
        "early_checked_jst":early_market["receipt_jst"],
        "late_checked_jst":late_market["receipt_jst"],
        "source_updates_first":early_market["source_updated_jst"],
        "source_updates_second":late_market["source_updated_jst"],
        "mixed_states_are_algebraic_counterfactual_combinations_not_joint_observations":True,
        "max_total_equals_win_plus_wide_delta_error":maximum,
        "max_fixed_weight_node_delta_additivity_error":node_error,
        "max_fixed_weight_pair_residual_additivity_error":dyad_error,
        "source_price_change_covariance_partition":variance_sources,
        "source_delta_node_vs_dyad_components":projections_info,
        "four_combinations_relative_to_later_state":cross_corr,
        "effective_market_support_at_each_saved_time":{
            "win_inverse_odds":{
                "earlier":effective(win0),"later":effective(win1),
                "jensen_shannon_divergence_nats":js_divergence(win0,win1),
            },
            "wide_inverse_geometric_midpoint_odds":{
                "earlier":effective(wide0),"later":effective(wide1),
                "jensen_shannon_divergence_nats":js_divergence(wide0,wide1),
            },
        },
        "separate_source_updates_not_separately_randomized":True,
        "cannot_infer_market_voter_learning_or_threshold":True,
        "cannot_infer_horse_behavior_kinship_or_genomic_causality":True,
        "two_archived_price_states_of_ONE_race_only":True,
        "not_racing_outcome_or_betting_return_model":True,
        "interpretation":"Arithmetic source-channel attribution of a price-ratio difference. The share decomposition is a weighted covariance identity, not an intervention or causal attribution.",
    }


def run_analysis()->dict:
    hashes={}
    a=read_market_snapshot(read_json(EARLY,hashes))
    b=read_market_snapshot(read_json(LATE,hashes))
    r=effect_splits(a,b)
    r["source_file_sha256"]=dict(sorted(hashes.items()))
    return r


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    try:
        result=run_analysis()
    except (ValueError,TypeError,KeyError,OSError,ZeroDivisionError,OverflowError) as exc:
        p.error(str(exc))
    txt=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n"
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(txt,encoding="utf-8")
    else:
        print(txt,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
