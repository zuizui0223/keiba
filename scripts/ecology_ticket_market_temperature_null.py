#!/usr/bin/env python3
"""Research-only negative control: nonlinear win-market strength transformation.

Question: does a global monotone change in the contrast among favorite and
longshot win strengths reproduce apparent horse-node structure in wide prices?

For beta>0, transform s_i -> s_i**beta, derive the *joint* PL top-3
distribution and its wide 3-place marginals p_beta(ij). All quoted price
comparisons use q_ij=3*(1/geom_mean_wide_odds_ij)/sum(1/odds).
We model r_ij=log(q_ij / p_beta=1_ij) as
  c_beta + log(p_beta_ij / p_beta=1_ij).
c_beta is a fitted common price offset; β is a single race-level scalar.
The offset is essential: raw quote normalization has a race-constant
factor (including the omitted held-out pair). With an intercept, exact
leave-one-edge-out residuals are invariant to that normalization, avoiding
hidden leakage from normalized quote boards.

Confront this strict 1-parameter temperature model with:
  A: weighted node a_i+a_j (n horse-level parameters)
  B: temperature beta + intercept
  C: temperature beta + horse-node residual (exploratory nested LOO)
Use exactly the same edge weights, target, races, and excluded edge. The
heldout edge's own price cannot enter β selection, intercept or node fit.

No actual votes, market time trajectory, pedigree, genome, interactions,
ROI or prospective race prediction are inferred from these 9 cross-sections.
"""
from __future__ import annotations

import argparse
from itertools import permutations
import json
import math
from pathlib import Path

try:
    from scripts.ecology_ticket_information_graph import (
        _solve, graph_inputs, decompose_edges, leave_one_pair_out_predictability
    )
    from scripts.ticket_type_historical_audit import (
        ROOT, SOURCE_DATE, TARGET_RACES, market_race, read_json,
    )
    from scripts.ticket_wide_second_day import (
        SECOND_DATE, SAVED_SNAPSHOT_PATH, eligible_four_market_only,
    )
except (ImportError, ModuleNotFoundError):
    from ecology_ticket_information_graph import (
        _solve, graph_inputs, decompose_edges, leave_one_pair_out_predictability
    )
    from ticket_type_historical_audit import (
        ROOT, SOURCE_DATE, TARGET_RACES, market_race, read_json,
    )
    from ticket_wide_second_day import (
        DATE as SECOND_DATE, SAVED_SNAPSHOT_PATH, eligible_four_market_only,
    )

# A priori fixed, deliberately low-dimensional temperature family:
# beta<1 flattens favorite–longshot contrast, beta>1 sharpens it.
BETA_GRID = tuple(round(0.5 + i * 0.05, 2) for i in range(31))
LABEL = "SAME_NINE_ARCHIVED_RACES_EXPLORATORY_NEGATIVE_CONTROL"


def pl_wide_marginal(strengths: dict[int, float], beta: float) -> dict[tuple[int,int], float]:
    """Direct normalized top-3 PL marginals, no payout odds or racing results."""
    if (not isinstance(strengths,dict) or not 8 <= len(strengths) <= 18 or
            not isinstance(beta,(int,float)) or isinstance(beta,bool) or
            not math.isfinite(beta) or beta <= 0):
        raise ValueError("invalid_strength_or_monotonic_beta")
    nums=sorted(strengths)
    vals={}
    for i in nums:
        v=strengths[i]
        if (type(i) is not int or not 1<=i<=18 or isinstance(v,bool) or
                not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0):
            raise ValueError("invalid_runner_weight")
        vals[i]=float(v)
    max_strength=max(vals.values())
    weights={i:(v/max_strength)**beta for i,v in vals.items()}
    total=math.fsum(weights.values())
    out={(i,j):0.0 for i in nums for j in nums if i<j}
    sum_events=0.
    for i,j,k in permutations(nums,3):
        wi,wj,wk=weights[i],weights[j],weights[k]
        p=wi/total * wj/(total-wi) * wk/(total-wi-wj)
        if p<=0 or not math.isfinite(p):
            raise ValueError("PL_underflow_or_invalid")
        out[tuple(sorted((i,j)))] += p
        out[tuple(sorted((i,k)))] += p
        out[tuple(sorted((j,k)))] += p
        sum_events+=p
    if not math.isclose(sum_events,1,rel_tol=1e-10,abs_tol=1e-10):
        raise ValueError("PL_joint_not_normalized")
    if not math.isclose(math.fsum(out.values()),3,rel_tol=1e-10,abs_tol=1e-10):
        raise ValueError("PL_wide_not_three_mass")
    return out


def nonlinear_curve(strengths:dict[int,float], baseline_wide:dict,
                    *, grid= BETA_GRID)->dict[float,dict]:
    if any(not 0<p<=1 for p in baseline_wide.values()):
        raise ValueError("invalid_PL_reference")
    result={}
    for beta in grid:
        if beta in result:
            raise ValueError("duplicate_beta")
        p=pl_wide_marginal(strengths,beta)
        if set(p)!=set(baseline_wide):
            raise ValueError("temperature_model_support_changed")
        result[beta]={edge:math.log(p[edge]/baseline_wide[edge]) for edge in p}
    return result


def _eval_temperature(y:dict, weights:dict, effects:dict) -> dict:
    if not y or set(y)!=set(weights) or set(y)!=set(effects):
        raise ValueError("edge_support_mismatch")
    mass=math.fsum(weights.values())
    if mass<=0: raise ValueError("zero_edge_mass")
    z={e:y[e]-effects[e] for e in y}
    a=math.fsum(weights[e]*z[e] for e in z)/mass
    sse=math.fsum(weights[e]*(z[e]-a)**2 for e in z)
    return {"intercept":a,"sse":sse}


def _node_fit_omit(y:dict,weights:dict,omit:tuple[int,int]) -> float:
    """Predict omitted edge after fitting n node parameters on OTHER edges."""
    nodes=sorted(set(i for e in y for i in e))
    indices={v:i for i,v in enumerate(nodes)}
    n=len(nodes)
    mat=[[0.]*n for _ in nodes]
    rhs=[0.]*n
    for (i,j),val in y.items():
        if (i,j)==omit:continue
        w=weights[(i,j)]
        a,b=indices[i],indices[j]
        mat[a][a]+=w;mat[b][b]+=w
        mat[a][b]+=w;mat[b][a]+=w
        rhs[a]+=w*val;rhs[b]+=w*val
    coeff=_solve(mat,rhs)
    return coeff[indices[omit[0]]]+coeff[indices[omit[1]]]


def compare_models(values:dict,weights:dict,curve:dict)->dict:
    """Nested leave-one-edge-out: β and all coefficients use training edges."""
    if not curve or set(values)!=set(weights) or len(values)<28:
        raise ValueError("invalid_edges")
    for beta,effects in curve.items():
        if set(effects)!=set(values):
            raise ValueError("nonlinear_model_edges_missing")
    keys=sorted(values)
    total_w=math.fsum(weights.values())
    total_y=math.fsum(weights[e]*values[e] for e in keys)
    temperature_fit={}
    for beta,effects in curve.items():
        temperature_fit[beta]=_eval_temperature(values,weights,effects)
    best_beta=min(temperature_fit,key=lambda x:(temperature_fit[x]["sse"],abs(x-1),x))
    ybar=total_y/total_w
    constant_sse=math.fsum(weights[e]*(values[e]-ybar)**2 for e in keys)
    fit_sse=temperature_fit[best_beta]["sse"]
    node=decompose_edges(values,weights)
    node_loo=leave_one_pair_out_predictability(values,weights)
    baseline_cv=0.
    temp_cv=0.
    temp_node_cv=0.
    node_cv=0.
    beta_cv=[]
    for omit in keys:
        train_mass=total_w-weights[omit]
        train_mean=(total_y-weights[omit]*values[omit])/train_mass
        baseline_cv+=weights[omit]*(values[omit]-train_mean)**2
        best=None
        for beta,effects in curve.items():
            fit=_eval_temperature(
                {e:values[e] for e in keys if e!=omit},
                {e:weights[e] for e in keys if e!=omit},
                {e:effects[e] for e in keys if e!=omit},
            )
            candidate=(fit["sse"],abs(beta-1),beta)
            if best is None or candidate<best[0]:
                best=(candidate,beta,fit["intercept"])
        _,beta,a=best
        beta_cv.append(beta)
        effects=curve[beta]
        estimate=a+effects[omit]
        temp_cv+=weights[omit]*(values[omit]-estimate)**2
        adjusted={e:values[e]-effects[e] for e in keys}
        node_prediction=effects[omit]+_node_fit_omit(adjusted,weights,omit)
        temp_node_cv+=weights[omit]*(values[omit]-node_prediction)**2
        node_prediction_only=node["node_pred"][omit] + (
            node["dyadic_residual"][omit] /
            (1. - _leverage(weights,omit))
        ) if False else None  # computed directly via the existing PRESS oracle
    node_cv=node_loo["press_error_weighted_mean"] * total_w
    if baseline_cv<=1e-20 or constant_sse<=1e-20:
        raise ValueError("constant_price_graph_no_R2")
    return {
        "beta_in_sample":best_beta,
        "beta_in_sample_at_grid_boundary":best_beta in (min(curve),max(curve)),
        "beta_excluded_pair_median":sorted(beta_cv)[len(beta_cv)//2],
        "beta_excluded_pair_minmax":[min(beta_cv),max(beta_cv)],
        "node_in_sample_R2":node["R2_node_vs_constant"],
        "temperature_in_sample_R2":1-fit_sse/constant_sse,
        "node_heldout_edge_R2":1-node_cv/baseline_cv,
        "temperature_heldout_edge_R2":1-temp_cv/baseline_cv,
        "temperature_plus_node_heldout_edge_R2":1-temp_node_cv/baseline_cv,
        "node_heldout_sse":node_cv,
        "temperature_heldout_sse":temp_cv,
        "temperature_plus_node_heldout_sse":temp_node_cv,
        "edge_constant_heldout_sse":baseline_cv,
        "temperature_plus_node_vs_temperature_heldout_delta_R2":
            (temp_cv-temp_node_cv)/baseline_cv,
        "node_vs_temperature_heldout_delta_R2":
            (temp_cv-node_cv)/baseline_cv,
        "same_race_pairs_only":True,
        "actual_future_2026_11_23_odds_trajectories_used":False,
        "biological_individual_trait_identified":False,
    }


def one_race(race_id:str, date:str, strengths:dict, frames:dict, quotes:list)->dict:
    deviations,weights,base=graph_inputs(strengths,frames,quotes)
    beta=nonlinear_curve(strengths,base["wide"])
    comparison=compare_models(deviations,weights,beta)
    return {
        "race_id":race_id,"race_date":date,
        "runner_count":len(strengths),"complete_pair_count":len(deviations),
        **comparison
    }


def run_analysis()->dict:
    hashes={}
    races=[]
    for n in TARGET_RACES:
        snapshot=market_race(n,hashes)
        records={i:1./v for i,v in snapshot["win_odds"].items()}
        races.append(one_race(snapshot["race_id"],SOURCE_DATE,records,
                              snapshot["frames"],snapshot["markets"]["wide"]))
    raw18=read_json(SAVED_SNAPSHOT_PATH,hashes)
    eligible,coverage=eligible_four_market_only(raw18)
    for row in eligible:
        races.append(one_race(row["race_id"],SECOND_DATE,row["strengths"],
                              row["frames"],row["wide_quotes"]))
    if len(races)!=9:
        raise ValueError("wrong_historical_race_count")
    metrics=("node_in_sample_R2","temperature_in_sample_R2",
             "node_heldout_edge_R2","temperature_heldout_edge_R2",
             "temperature_plus_node_heldout_edge_R2",
             "temperature_plus_node_vs_temperature_heldout_delta_R2",
             "node_vs_temperature_heldout_delta_R2")
    groups={}
    for date in (SOURCE_DATE,SECOND_DATE):
        group=[row for row in races if row["race_date"]==date]
        groups[date]={
            "race_count":len(group),
            **{"mean_"+col:math.fsum(x[col] for x in group)/len(group) for col in metrics},
            "node_heldout_beats_temperature_count":sum(
                x["node_heldout_edge_R2"]>x["temperature_heldout_edge_R2"]
                for x in group),
            "temperature_plus_node_improves_on_temperature_count":sum(
                x["temperature_plus_node_vs_temperature_heldout_delta_R2"]>0
                for x in group),
            "beta_boundary_count":sum(x["beta_in_sample_at_grid_boundary"] for x in group),
        }
    return {
        "schema_version":1,
        "status":LABEL,
        "goal":"Reject simple global favorite-longshot temperature explanation before interpreting node price structure as individual-specific",
        "observational_design":"nine complete cross-sectional win+wide markets, two already-inspected historical calendar days",
        "strict_race_level_independent_validation":False,
        "beta_grid":list(BETA_GRID),
        "beta_family":"strictly positive s_i ** beta then coherent PL top3 wide marginals",
        "intercept_fit":"weighted common logquote offset (removes takeout and normalization constant)",
        "edge_holdout":"per-edge beta chosen and intercept/node refit on other same-race pairs; all models use identical weights and exclusions",
        "outcome_labels_used":False,
        "true_pairwise_market_probability":False,
        "voter_behavior_or_biological_interaction_identified":False,
        "same_horse_kinship_genome_join_available":False,
        "input_file_sha256":dict(sorted(hashes.items())),
        "groups":groups,
        "races":races,
        "limitations":"The input wide-price proxy may be biased by takeout, ranges and popularity; the global beta class is only one nonlinear pricing control; held-out pairs share horses and same race; two days insufficient for market-general claim.",
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    try:
        result=run_analysis()
    except (ValueError,TypeError,KeyError,ZeroDivisionError,OSError) as exc:
        p.error(str(exc))
    body=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(body,encoding="utf-8")
    else:
        print(body,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
