#!/usr/bin/env python3
"""Research-only flexible smooth global favorite-longshot price null.

Unlike the PL temperature family, this null directly fits the *price*
discrepancy for each wide pair with one shared polynomial function of
both horses' observed win-market strengths:

  y_ij = c + sum_{k=1..D} b_k (L_k(z_i) + L_k(z_j)) + error_ij
  z_i = (log(s_i) - mean(log s)) / max |log(s) - mean(log s)|

L_1..L_4 are Legendre polynomials, which span all polynomials <=4,
and c absorbs the odds-board normalization and common payout margin.

This is intentionally NOT a coherent joint probability model; it is
a conservative *descriptive price transformation* negative control.
No horse-specific free parameters are allowed. D=1,2,3,4 reported
without choosing the best model from observed results.

Weighted least squares and exact per-edge PRESS scores hold out each
pair at fit time; no quotation for the held-out edge is used except
its target at scoring. The global q normalization adds a constant to
every y_ij and cannot induce held-out skill with a fitted intercept.

The archive contains 9 races on 2 dates, not horse genotype, voting
volume, market time trajectories or new-date prediction evidence.
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json
import math
from pathlib import Path

try:
    from scripts.ecology_ticket_information_graph import (
        _solve, graph_inputs, leave_one_pair_out_predictability,
    )
    from scripts.ticket_type_historical_audit import (
        SOURCE_DATE, TARGET_RACES, market_race, read_json,
    )
    from scripts.ticket_wide_second_day import (
        DATE as SECOND_DATE, SAVED_SNAPSHOT_PATH, eligible_four_market_only,
    )
except (ImportError, ModuleNotFoundError):
    from ecology_ticket_information_graph import (
        _solve, graph_inputs, leave_one_pair_out_predictability,
    )
    from ticket_type_historical_audit import (
        SOURCE_DATE, TARGET_RACES, market_race, read_json,
    )
    from ticket_wide_second_day import (
        DATE as SECOND_DATE, SAVED_SNAPSHOT_PATH, eligible_four_market_only,
    )

DEGREES = (1, 2, 3, 4)
STATUS = "EMPIRICAL_SMOOTH_GLOBAL_PRICE_BIAS_CONTROL_NINE_RACES_RETROSPECTIVE"


def legendre(z:float,degree:int)->float:
    if degree == 1:return z
    if degree == 2:return (3*z*z - 1)/2
    if degree == 3:return (5*z*z*z - 3*z)/2
    if degree == 4:return (35*z**4 -30*z*z+3)/8
    raise ValueError("unsupported_smooth_basis_degree")


def feature_map(strengths:dict[int,float], degree:int)->dict[tuple[int,int],tuple]:
    if type(degree) is not int or degree not in DEGREES or not 8<=len(strengths)<=18:
        raise ValueError("unsupported_polynomial_graph")
    logs={}
    for horse,weight in strengths.items():
        if (type(horse) is not int or isinstance(weight,bool)
                or not isinstance(weight,(float,int))
                or not math.isfinite(weight) or weight<=0):
            raise ValueError("bad_strength")
        logs[horse]=math.log(weight)
    mean=math.fsum(logs.values())/len(logs)
    contrast={i:v-mean for i,v in logs.items()}
    scale=max(abs(x) for x in contrast.values())
    if scale<=1e-12:
        raise ValueError("no_stable_strength_contrast")
    z={i:v/scale for i,v in contrast.items()}
    edges={}
    for i,j in combinations(sorted(strengths),2):
        edges[i,j]=tuple(
            [1.] + [legendre(z[i],k)+legendre(z[j],k) for k in range(1,degree+1)]
        )
    return edges


def weighted_linear_edge_cv(values:dict, weights:dict,
                            features:dict)->dict:
    """Exact weighted OLS LOOCV. β and intercept refit without tested edge."""
    if not values or set(values)!=set(weights) or set(values)!=set(features):
        raise ValueError("wrong_edge_support")
    n=len(next(iter(features.values())))
    mat=[[0.]*n for _ in range(n)]
    vec=[0.]*n
    total=math.fsum(weights.values())
    if n<2 or n>5 or len(values)<n+6 or total<=0:
        raise ValueError("unsupported_polynomial_design")
    obsmean=math.fsum(weights[e]*values[e] for e in values)/total
    train_sst=math.fsum(weights[e]*(values[e]-obsmean)**2 for e in values)
    if train_sst<=1e-20:
        raise ValueError("no_price_response_variation")
    for edge,y in values.items():
        w=weights[edge]
        x=features[edge]
        if len(x)!=n or not math.isfinite(w) or w<=0 or not math.isfinite(y):
            raise ValueError("nonfinite_graph_regression")
        for a in range(n):
            vec[a]+=w*x[a]*y
            for b in range(n):
                mat[a][b]+=w*x[a]*x[b]
    coeff=_solve(mat,vec)
    total_y=math.fsum(weights[e]*values[e] for e in values)
    residual={}
    for edge,y in values.items():
        residual[edge]=y-math.fsum(coeff[j]*features[edge][j] for j in range(n))
    in_sse=math.fsum(weights[e]*r*r for e,r in residual.items())
    press=0.
    basepress=0.
    leverage=[]
    for edge,x in features.items():
        w=weights[edge]
        inverse_x=_solve(mat,list(x))
        h=w*math.fsum(x[j]*inverse_x[j] for j in range(n))
        if not 0<=h<1-1e-12:
            raise ValueError("invalid_model_leverage")
        loo=residual[edge]/(1-h)
        press+=w*loo*loo
        baseline=(total_y-w*values[edge])/(total-w)
        basepress+=w*(values[edge]-baseline)**2
        leverage.append(h)
    if basepress<=1e-20:
        raise ValueError("no_heldout_mean_baseline")
    return {
        "degree":n-1,
        "parameter_count":n,
        "in_sample_R2":1-in_sse/train_sst,
        "pair_holdout_R2":1-press/basepress,
        "heldout_weighted_squared_error":press,
        "heldout_null_weighted_squared_error":basepress,
        "max_edge_leverage":max(leverage),
        "mean_edge_leverage":math.fsum(leverage)/len(leverage),
        "fitted_coefficients_are_price_basis_not_horse_effects":True,
    }


def one_race(race_id:str, date:str, strengths:dict, frames:dict,
             wide_quotes:list)->dict:
    y,w,_=graph_inputs(strengths,frames,wide_quotes)
    node=leave_one_pair_out_predictability(y,w)
    fitted={}
    for degree in DEGREES:
        stats=weighted_linear_edge_cv(y,w,feature_map(strengths,degree))
        fitted[f"degree_{degree}"]=stats
    return {
        "race_id":race_id,"date":date,"runner_count":len(strengths),
        "pair_count":len(y),
        "node_pair_holdout_R2":node["leave_one_pair_out_R2_vs_train_edge_mean"],
        "global_smooth_models":fitted,
        "node_minus_degree_4_pair_holdout_R2":
            node["leave_one_pair_out_R2_vs_train_edge_mean"]-
            fitted["degree_4"]["pair_holdout_R2"],
        "not_an_estimate_of_individual_genetic_value":True,
    }


def run_analysis()->dict:
    hashes={}
    rows=[]
    for n in TARGET_RACES:
        r=market_race(n,hashes)
        rows.append(one_race(
            r["race_id"],SOURCE_DATE,
            {i:1/v for i,v in r["win_odds"].items()},
            r["frames"],r["markets"]["wide"],
        ))
    second=read_json(SAVED_SNAPSHOT_PATH,hashes)
    entries,_=eligible_four_market_only(second)
    for r in entries:
        rows.append(one_race(r["race_id"],SECOND_DATE,
                             r["strengths"],r["frames"],r["wide_quotes"]))
    if len(rows)!=9:
        raise ValueError("incorrect_historical_source_universe")
    by_date={}
    for date in (SOURCE_DATE,SECOND_DATE):
        subset=[r for r in rows if r["date"]==date]
        by_date[date]={
            "race_count":len(subset),
            "node_mean_R2":math.fsum(r["node_pair_holdout_R2"] for r in subset)/len(subset),
            **{
                f"degree_{d}_mean_R2":
                    math.fsum(r["global_smooth_models"][f"degree_{d}"]["pair_holdout_R2"]
                             for r in subset)/len(subset)
                for d in DEGREES
            },
            "node_beats_degree_4_count":sum(
                r["node_pair_holdout_R2"] >
                r["global_smooth_models"]["degree_4"]["pair_holdout_R2"]
                for r in subset
            ),
            "number_degree_4_in_sample_better_than_node_oos_NOT_COMPARABLE":None,
        }
    return {
        "schema_version":1,"status":STATUS,
        "observational_dates":2,"races_observed":len(rows),
        "degrees_tested":list(DEGREES),
        "basis":"global Legendre polynomial of normalized log win strength; effects of two horses added plus intercept",
        "edge_validation":"weighted exact same-race leave-one-pair-out, no race outcome used",
        "outcome_labels_used":False,
        "relative_quote_margins_calibrated":False,
        "same_horse_cross_date_repeatability_identified":False,
        "genomic_A_G_or_biological_individual_trait_identified":False,
        "market_time_series_measured":False,
        "general_nonlinear_pricing_not_excluded":True,
        "by_date":by_date,"races":rows,
        "input_file_sha256":dict(sorted(hashes.items())),
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    try:
        result=run_analysis()
    except (ValueError,KeyError,TypeError,OSError,ZeroDivisionError) as e:
        p.error(str(e))
    output=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(output,encoding="utf-8")
    else:
        print(output,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
