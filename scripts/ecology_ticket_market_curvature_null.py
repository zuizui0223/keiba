#!/usr/bin/env python3
"""Second nonlinear negative control: 2-parameter *monotone* market curvature.

For log s_i = x_i + mean(log s), let L=max_i |x_i| and
  log s_i' = beta * x_i + gamma * x_i^2 / L
where beta in [.5,2.0], gamma in [-.15,0,.15].
The derivative beta+2gamma*x/L is >= .2, hence the new strength order
is strictly monotonic. (beta=1,gamma=0) is the exact original win PL.
The resulting top-three joint PL gives a coherent wide pair marginal.

One holdout pair is excluded from choosing (beta,gamma), common offset,
and any additional horse-node coefficients. Entire-graph normalization
adds the same constant to all edges and is absorbed by the fitted offset
or nodes; no heldout outcome data used.

All comparisons are same-race price-graph diagnostics, not independent
race-level performance or biological/causal interaction estimates.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

try:
    from scripts.ecology_ticket_information_graph import (
        graph_inputs, decompose_edges, leave_one_pair_out_predictability
    )
    from scripts.ecology_ticket_market_temperature_null import (
        pl_wide_marginal, nonlinear_curve, compare_models,
        _eval_temperature, _node_fit_omit, BETA_GRID,
    )
    from scripts.ticket_type_historical_audit import (
        ROOT, SOURCE_DATE, TARGET_RACES, market_race, read_json,
    )
    from scripts.ticket_wide_second_day import (
        DATE as SECOND_DATE, SAVED_SNAPSHOT_PATH, eligible_four_market_only,
    )
except (ImportError, ModuleNotFoundError):
    from ecology_ticket_information_graph import (
        graph_inputs, decompose_edges, leave_one_pair_out_predictability
    )
    from ecology_ticket_market_temperature_null import (
        pl_wide_marginal, nonlinear_curve, compare_models,
        _eval_temperature, _node_fit_omit, BETA_GRID,
    )
    from ticket_type_historical_audit import (
        ROOT, SOURCE_DATE, TARGET_RACES, market_race, read_json,
    )
    from ticket_wide_second_day import (
        DATE as SECOND_DATE, SAVED_SNAPSHOT_PATH, eligible_four_market_only,
    )

GAMMA_GRID = (-0.15, 0.0, 0.15)
PRIMARY_STATUS = "EXPLORATORY_CURVED_MONOTONE_FAVORITE_LONGSHOT_NULL_NO_CAUSAL_EFFECT"


def transformed_strengths(strengths: dict[int,float], beta:float,
                          gamma:float)->dict[int,float]:
    if not (0 < beta and abs(gamma)<=.25 and beta>2*abs(gamma)):
        raise ValueError("non_monotone_market_control")
    if not 8<=len(strengths)<=18 or any(
        not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or v<=0
        for v in strengths.values()
    ):
        raise ValueError("invalid_baseline_strengths")
    logs={i:math.log(v) for i,v in strengths.items()}
    ave=math.fsum(logs.values())/len(logs)
    centered={i:x-ave for i,x in logs.items()}
    scale=max(abs(x) for x in centered.values())
    if scale<1e-12:
        raise ValueError("no_strength_contrast")
    curve={i:beta*x+gamma*(x*x/scale) for i,x in centered.items()}
    peak=max(curve.values())
    out={i:math.exp(x-peak) for i,x in curve.items()}
    if any(x<=0 for x in out.values()):
        raise ValueError("curvature_underflow")
    return out


def curvature_curve(strengths:dict, baseline_wide:dict,
                    *, beta_grid=BETA_GRID,gamma_grid=GAMMA_GRID)->dict:
    out={}
    for beta in beta_grid:
        for gamma in gamma_grid:
            key=(beta,gamma)
            transformed=transformed_strengths(strengths,beta,gamma)
            p=pl_wide_marginal(transformed,1.0)
            if set(p)!=set(baseline_wide):
                raise ValueError("curvature_pl_support_changed")
            out[key]={e:math.log(p[e]/baseline_wide[e]) for e in p}
    return out


def compare_curve_models(values:dict, weights:dict, curve:dict,
                         one_param:dict)->dict:
    """2-parameter heldout refits vs 1-param temp and horse-only LOO."""
    if not curve or not one_param or set(values)!=set(weights):
        raise ValueError("empty_or_incompatible_market_curve")
    all_edges=sorted(values)
    all_w=math.fsum(weights.values())
    all_y=math.fsum(weights[e]*values[e] for e in all_edges)
    fit={}
    for key,u in curve.items():
        if set(u)!=set(values):
            raise ValueError("curved_edge_support_changed")
        fit[key]=_eval_temperature(values,weights,u)
    best_key=min(fit,key=lambda k:(fit[k]["sse"],abs(k[1]),abs(k[0]-1),k[0],k[1]))
    ymean=all_y/all_w
    sst=math.fsum(weights[e]*(values[e]-ymean)**2 for e in all_edges)
    if sst<=1e-20:
        raise ValueError("no_variable_price_data")
    node=decompose_edges(values,weights)
    node_loo=leave_one_pair_out_predictability(values,weights)
    simple=compare_models(values,weights,one_param)
    curve_press=0.
    curved_node_press=0.
    null_press=0.
    selected=[]
    for omit in all_edges:
        wt=weights[omit]
        train={e:values[e] for e in all_edges if e!=omit}
        trainw={e:weights[e] for e in all_edges if e!=omit}
        mean_without=(all_y-wt*values[omit])/(all_w-wt)
        null_press+=wt*(values[omit]-mean_without)**2
        chosen=None
        for key,u in curve.items():
            model=_eval_temperature(train,trainw,{e:u[e] for e in train})
            candidate=(model["sse"],abs(key[1]),abs(key[0]-1),key[0],key[1])
            if chosen is None or candidate<chosen[0]:
                chosen=(candidate,key,model["intercept"])
        _,best,offset=chosen
        selected.append(best)
        u=curve[best]
        forecast=offset+u[omit]
        curve_press+=wt*(values[omit]-forecast)**2
        node_delta=_node_fit_omit({e:values[e]-u[e] for e in values},weights,omit)
        combined=u[omit]+node_delta
        curved_node_press+=wt*(values[omit]-combined)**2
    if null_press<=1e-20:
        raise ValueError("no_valid_LOO_constant")
    curved_R2=1-curve_press/null_press
    combined_R2=1-curved_node_press/null_press
    if not math.isclose(simple["edge_constant_heldout_sse"],null_press,rel_tol=1e-10,abs_tol=1e-10):
        raise ValueError("heldout_null_baseline_changed")
    if not math.isclose(simple["node_heldout_sse"],node_loo["press_error_weighted_mean"]*all_w,rel_tol=1e-10,abs_tol=1e-10):
        raise ValueError("node_LOO_not_reproduced")
    return {
        "two_parameter_beta_gamma_in_sample":list(best_key),
        "two_parameter_beta_gamma_cv_median":list(sorted(selected)[len(selected)//2]),
        "two_parameter_in_sample_R2":1-fit[best_key]["sse"]/sst,
        "two_parameter_heldout_R2":curved_R2,
        "two_parameter_plus_node_heldout_R2":combined_R2,
        "one_parameter_heldout_R2":simple["temperature_heldout_edge_R2"],
        "horse_node_only_heldout_R2":simple["node_heldout_edge_R2"],
        "node_minus_two_parameter_heldout_R2":
            simple["node_heldout_edge_R2"]-curved_R2,
        "node_added_after_two_parameter_heldout_delta_R2":
            combined_R2-curved_R2,
        "curve_vs_one_parameter_delta_R2":
            curved_R2-simple["temperature_heldout_edge_R2"],
        "heldout_pairs_share_other_pairs_same_race":True,
        "has_true_market_voter_time_series":False,
        "no_race_outcome_labels_used":True,
    }


def one_race(race_id:str,date:str,strengths:dict,frames:dict,quotes:list)->dict:
    observed,weights,pl=graph_inputs(strengths,frames,quotes)
    curve=curvature_curve(strengths,pl["wide"])
    original=nonlinear_curve(strengths,pl["wide"])
    return {
        "race_id":race_id,"race_date":date,"runner_count":len(strengths),
        "complete_pair_count":len(observed),
        **compare_curve_models(observed,weights,curve,original),
    }


def run_analysis()->dict:
    hashes={}
    rows=[]
    for n in TARGET_RACES:
        r=market_race(n,hashes)
        rows.append(one_race(r["race_id"],SOURCE_DATE,
                             {i:1/v for i,v in r["win_odds"].items()},
                             r["frames"],r["markets"]["wide"]))
    source=read_json(SAVED_SNAPSHOT_PATH,hashes)
    eligible,coverage=eligible_four_market_only(source)
    for r in eligible:
        rows.append(one_race(r["race_id"],SECOND_DATE,
                             r["strengths"],r["frames"],r["wide_quotes"]))
    if len(rows)!=9:
        raise ValueError("not_nine_original_races")
    fields=("one_parameter_heldout_R2","two_parameter_heldout_R2",
            "horse_node_only_heldout_R2","two_parameter_plus_node_heldout_R2",
            "node_minus_two_parameter_heldout_R2",
            "node_added_after_two_parameter_heldout_delta_R2")
    grouped={}
    for date in (SOURCE_DATE,SECOND_DATE):
        subset=[r for r in rows if r["race_date"]==date]
        grouped[date]={
            "race_count":len(subset),
            **{"mean_"+k:math.fsum(r[k] for r in subset)/len(subset) for k in fields},
            "node_beats_two_parameter_count":sum(
                r["horse_node_only_heldout_R2"]>r["two_parameter_heldout_R2"]
                for r in subset),
            "extra_node_after_curvature_improves_count":sum(
                r["node_added_after_two_parameter_heldout_delta_R2"]>0
                for r in subset),
        }
    return {
        "schema_version":1,"status":PRIMARY_STATUS,
        "observed_races":9,"independent_calendar_dates":2,
        "beta_grid":list(BETA_GRID),
        "gamma_grid":list(GAMMA_GRID),
        "strictly_monotone_transformation":True,
        "transformation":"center log s, scaled quadratic gamma and beta: exp(beta*x+gamma*x**2/maxabs(x))",
        "benchmark":"same edge-LOO with nuisance offset; β and γ selected within training pair set",
        "outcome_labels_used":False,
        "causal_biological_individuality_identified":False,
        "market_social_contagion_identified":False,
        "future_market_validation":False,
        "many_other_nonlinear_price_models_remain_untested":True,
        "by_date":grouped,"races":rows,
        "input_file_sha256":dict(sorted(hashes.items())),
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    try:
        data=run_analysis()
    except (ValueError,TypeError,KeyError,OSError,ZeroDivisionError) as exc:
        p.error(str(exc))
    result=json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(result,encoding="utf-8")
    else:
        print(result,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
