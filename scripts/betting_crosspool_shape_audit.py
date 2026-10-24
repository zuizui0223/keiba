#!/usr/bin/env python3
"""Pre-start, market-only odds shape and ticket-overlap audit.

All calculations use provided *intermediate* prices, never outcomes.
No forward calibration, positive return or causal information-flow claims.
Public/source quotes are not embedded or re-published in this module.

Expected JSON input:
{
 "race_id":"2026-10-25-KYOTO-11",
 "scheduled_post_jst":"2026-10-25T15:40:00+09:00",
 "markets":{
   "win":{"source_updated_at_jst":"2026-10-25T01:52:00+09:00",
          "provider_url":"...", "rows":[{"number":1,"odds":20.0}, ...]},
   "wide":{"source_updated_at_jst":"...", "provider_url":"...",
           "rows":[{"numbers":[1,2],"odds_low":3.0,"odds_high":3.7},...]},
   "quinella":{"source_updated_at_jst":"...", "provider_url":"...",
               "rows":[{"numbers":[1,2],"odds":5.0},...]},
   "trio":{"source_updated_at_jst":"...", "provider_url":"...",
           "rows":[{"numbers":[1,2,3],"odds":20.0},...]}
 }
}
FULL 18-runner WIN plus all 153 WIDE and QUINELLA quotes required;
TRIO may contain a disclosed top-K sample, never assumed exhaustive.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import hashlib
from itertools import combinations, permutations
import json
import math
from pathlib import Path


def _time(value: str) -> datetime:
    t = datetime.fromisoformat(value)
    if t.utcoffset() is None:
        raise ValueError("HOLD_NAIVE_TIME")
    return t


def _positive(v: object) -> float:
    if isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) or v <= 1:
        raise ValueError("HOLD_INVALID_DECIMAL_ODDS")
    return float(v)


def _key(seq: list[int] | tuple[int, ...], size: int, runners: set[int]) -> tuple[int, ...]:
    if (not isinstance(seq, (list, tuple)) or len(seq) != size
            or any(type(x) is not int or x not in runners for x in seq)
            or len(set(seq)) != size):
        raise ValueError("HOLD_INVALID_EVENT_MEMBERS")
    return tuple(sorted(seq))


def parse_snapshot(data: dict) -> dict:
    """Fails closed on missing runners/markets, post-start odds, duplicate tickets."""
    if not isinstance(data.get("race_id"), str) or not data["race_id"].strip():
        raise ValueError("HOLD_MISSING_RACE_ID")
    post = _time(data["scheduled_post_jst"])
    markets = data["markets"]
    if set(markets) != {"win", "wide", "quinella", "trio"}:
        raise ValueError("HOLD_MISSING_MARKET")
    source_times = {}
    for k, block in markets.items():
        t = _time(block["source_updated_at_jst"])
        if not t <= post - timedelta(minutes=10):
            raise ValueError("HOLD_PRICE_NOT_TEN_MINUTES_BEFORE_START")
        if not str(block.get("provider_url", "")).startswith("https://"):
            raise ValueError("HOLD_NO_PROVIDER_PROVENANCE")
        source_times[k] = t
    horses: dict[int,float] = {}
    for row in markets["win"]["rows"]:
        number = row["number"]
        if type(number) is not int or number < 1 or number > 99 or number in horses:
            raise ValueError("HOLD_DUPLICATE_INVALID_HORSE")
        horses[number] = _positive(row["odds"])
    n = len(horses)
    if n < 4 or n > 30:
        raise ValueError("HOLD_UNEXPECTED_FIELD_SIZE")
    ids = set(horses)
    quotes: dict[str,dict[tuple[int,...],tuple[float,float]]] = {}
    for kind, arity in (("wide", 2), ("quinella",2), ("trio",3)):
        rows = markets[kind]["rows"]
        q = {}
        for row in rows:
            key = _key(row["numbers"], arity, ids)
            if key in q:
                raise ValueError("HOLD_DUPLICATE_TICKET")
            low = _positive(row["odds_low"] if kind=="wide" else row["odds"])
            high = _positive(row["odds_high"] if kind=="wide" else row["odds"])
            if high < low:
                raise ValueError("HOLD_REVERSED_WIDE_PRICE_BAND")
            q[key] = (low,high)
        quotes[kind] = q
    expected_pairs = set(combinations(sorted(ids),2))
    if set(quotes["wide"]) != expected_pairs or set(quotes["quinella"]) != expected_pairs:
        raise ValueError("HOLD_INCOMPLETE_PAIR_MARKETS")
    if not quotes["trio"] or len(quotes["trio"]) > math.comb(n,3):
        raise ValueError("HOLD_INVALID_TRIO_COVERAGE")
    return {
        "race_id": data["race_id"],
        "post": post,
        "horses": horses,
        "quotes": quotes,
        "source_times": source_times,
        "market_window_min": (max(source_times.values())-min(source_times.values())).total_seconds()/60,
        "full_trio_count": math.comb(n,3),
    }


def exact_pl(horses: dict[int,float], gamma: float,
             multiplier: dict[int,float] | None = None) -> dict:
    """Exact *joint* top-three rank distribution; no MC repetitions required."""
    if not isinstance(gamma, (int,float)) or not math.isfinite(gamma) or gamma <= 0:
        raise ValueError("HOLD_INVALID_GAMMA")
    w = {k:v**(-gamma)*float((multiplier or {}).get(k,1.0))
         for k,v in horses.items()}
    if any(not math.isfinite(v) or v <= 0 for v in w.values()):
        raise ValueError("HOLD_INVALID_WEIGHT_SHOCK")
    total = sum(w.values())
    p = {k:v/total for k,v in w.items()}
    top3 = dict.fromkeys(w,0.0)
    wide = dict.fromkeys(combinations(sorted(w),2),0.0)
    quinella = dict.fromkeys(combinations(sorted(w),2),0.0)
    trio = dict.fromkeys(combinations(sorted(w),3),0.0)
    ordered = {}
    for i,j,k in permutations(sorted(w),3):
        prob = p[i]*(p[j]/(1-p[i]))*(p[k]/(1-p[i]-p[j]))
        ordered[(i,j,k)] = prob
        for v in (i,j,k):
            top3[v] += prob
        quinella[tuple(sorted((i,j)))] += prob
        trio[tuple(sorted((i,j,k)))] += prob
        for pair in ((i,j),(i,k),(j,k)):
            wide[tuple(sorted(pair))] += prob
    if (not math.isclose(sum(p.values()),1,abs_tol=1e-11)
            or not math.isclose(sum(ordered.values()),1,abs_tol=1e-11)
            or not math.isclose(sum(top3.values()),3,abs_tol=1e-11)
            or not math.isclose(sum(wide.values()),3,abs_tol=1e-11)
            or not math.isclose(sum(quinella.values()),1,abs_tol=1e-11)
            or not math.isclose(sum(trio.values()),1,abs_tol=1e-11)):
        raise AssertionError("INVALID_PL_MASS")
    return {"win":p,"top3":top3,"wide":wide,"quinella":quinella,"trio":trio,
            "ordered":ordered}


def _ranks(values: list[float]) -> list[float]:
    """Average ranks for ties, with sorting only in the helper."""
    a = sorted(enumerate(values), key=lambda x:x[1])
    out = [0.0]*len(a)
    i=0
    while i<len(a):
        j=i+1
        while j<len(a) and a[j][1]==a[i][1]:
            j+=1
        avg=(i+j-1)/2+1
        for u in range(i,j):
            out[a[u][0]]=avg
        i=j
    return out


def _correlation(x:list[float],y:list[float]) -> float:
    mx=sum(x)/len(x); my=sum(y)/len(y)
    cov=sum((a-mx)*(b-my) for a,b in zip(x,y))
    den=math.sqrt(sum((v-mx)**2 for v in x)*sum((v-my)**2 for v in y))
    return cov/den if den else float("nan")


def wide_market_shape(snapshot: dict, model: dict) -> dict:
    """Compares two probability-normalized *relative indices*, not 153 independent events."""
    quotes = snapshot["quotes"]["wide"]
    keys = sorted(quotes)
    inv = [1/quotes[k][0] for k in keys]
    z = sum(inv)
    observed={k:v/z for k,v in zip(keys,inv)}
    theoretical={k:model["wide"][k]/3 for k in keys}
    tv=sum(abs(observed[k]-theoretical[k]) for k in keys)/2
    spearman=_correlation(_ranks([observed[k] for k in keys]),
                          _ranks([theoretical[k] for k in keys]))
    n=len(snapshot["horses"])
    logres={k:math.log(observed[k]/theoretical[k]) for k in keys}
    mu=sum(logres.values())/len(keys)
    a={}
    for h in snapshot["horses"]:
        incident=[logres[k] for k in keys if h in k]
        assert len(incident)==n-1
        a[h]=(n-1)/(n-2)*(sum(incident)/(n-1)-mu)
    error={k:logres[k]-mu-a[k[0]]-a[k[1]] for k in keys}
    total_ss=sum((v-mu)**2 for v in logres.values())
    residual_ss=sum(e**2 for e in error.values())
    return {
        "total_variation_between_relative_indices":tv,
        "spearman_pair_rank":spearman,
        "additive_horse_node_r2_descriptive":1-residual_ss/total_ss if total_ss else None,
        "note":"Source WIDE lower-odds q=(1/o)/sum(1/o); PL pair q=P(both top3)/3; neither q is a standalone WIDE winning probability.",
        "pair_specific_residuals":error,
    }


def ticket_stress(snapshot:dict,models:dict[str,dict]) -> dict:
    out={}
    for kind in ("wide","quinella","trio"):
        candidates=[]
        for key,(low,high) in snapshot["quotes"][kind].items():
            multipliers={g:low*m[kind][key] for g,m in models.items()}
            candidates.append({
                "members":list(key),
                "model_conditional_gross_multiplier_by_gamma":multipliers,
                "model_only_min_multiplier":min(multipliers.values()),
                "payout_low":low,
                "payout_high":high
            })
        candidates.sort(key=lambda d:-d["model_only_min_multiplier"])
        out[kind]={
            "listed_count":len(candidates),
            "model_positive_under_every_gamma":sum(d["model_only_min_multiplier"]>1 for d in candidates),
            "model_positive_gamma1":sum(d["model_conditional_gross_multiplier_by_gamma"].get("1.0",0)>1 for d in candidates),
            "top_five_model_only":candidates[:5]
        }
    return out


def ticket_hit(top3:tuple[int,int,int],kind:str,members:tuple[int,...]) -> bool:
    if kind == "wide":
        return all(v in top3 for v in members)
    if kind == "quinella":
        return set(members)==set(top3[:2])
    if kind == "trio":
        return set(members)==set(top3)
    raise ValueError("HOLD_UNSUPPORTED_TICKET_KIND")


def portfolio(snapshot:dict, model:dict, entries:list[dict]) -> dict:
    """Price/return arithmetic conditioned on an uncalibrated PL distribution."""
    stake=0
    plan=[]
    for x in entries:
        kind=x["kind"]
        if kind not in snapshot["quotes"]:
            raise ValueError("HOLD_INVALID_TICKET_TYPE")
        key=_key(x["numbers"],2 if kind!="trio" else 3,set(snapshot["horses"]))
        if key not in snapshot["quotes"][kind]:
            raise ValueError("HOLD_NOT_QUOTED")
        amount=x["yen"]
        if type(amount) is not int or amount < 100 or amount%100!=0:
            raise ValueError("HOLD_INVALID_STAKE")
        stake+=amount
        plan.append((kind,key,amount))
    if not plan:
        raise ValueError("HOLD_EMPTY_PORTFOLIO")
    anyhit=nonloss=positive=expected=0.0
    for top3,pr in model["ordered"].items():
        paid=sum(amount*snapshot["quotes"][kind][key][0]
                 for kind,key,amount in plan if ticket_hit(top3,kind,key))
        anyhit+=pr*(paid>0)
        nonloss+=pr*(paid>=stake)
        positive+=pr*(paid>stake)
        expected+=pr*paid
    return {
        "stake_yen":stake,
        "model_prob_any_payout":anyhit,
        "model_prob_nonnegative_net":nonloss,
        "model_prob_positive_net":positive,
        "gross_multiplier_under_fixed_quote":expected/stake,
        "assumption":"No transaction feedback, no odds movement, no empirical probability calibration; not an estimated real profit."
    }


def sensitivity(data:dict, gammas:list[float], plans:dict[str,list[dict]]|None=None) -> dict:
    snap=parse_snapshot(data)
    models={str(float(g)):exact_pl(snap["horses"],float(g)) for g in gammas}
    shapes={g:wide_market_shape(snap,m) for g,m in models.items()}
    scores=ticket_stress(snap,models)
    output={
        "status":"PRE_RACE_EXPLORATORY_MARKET_ONLY_NOT_PROBABILITY_CALIBRATED",
        "race_id":snap["race_id"],
        "provenance":{k:{"url":data["markets"][k]["provider_url"],
                         "source_updated_at_jst":t.isoformat()}
                      for k,t in snap["source_times"].items()},
        "cross_market_update_gap_minutes":snap["market_window_min"],
        "runners":len(snap["horses"]),
        "model_outcome_count":len(next(iter(models.values()))["ordered"]),
        "quoted_pairs_full":len(snap["quotes"]["wide"]),
        "quoted_trios_partial":len(snap["quotes"]["trio"]),
        "possible_trios":snap["full_trio_count"],
        "gamma_stress_not_fitted":gammas,
        "relative_WIDE_shape_by_gamma":{
            g:{k:v for k,v in s.items() if k!="pair_specific_residuals"} for g,s in shapes.items()},
        "model_only_ticket_stress":scores,
        "portfolios":{
            name:{g:portfolio(snap,m,plan) for g,m in models.items()}
            for name,plan in (plans or {}).items()},
        "limitations":[
            "All odds are intermediate, future payouts are not locked.",
            "WIN, WIDE, QUINELLA and TRIO clocks differ, so no synchronous cross-market lead/lag conclusion.",
            "The 153 overlapping WIDE pairs are NOT 153 independent races.",
            "Gamma grid is assumption sensitivity, not fitted win/place probability.",
            "Model-only expected multipliers above one do not establish a positive true expected return.",
            "Only listed TRIO prices are scored; missing combinations are not imputed.",
            "No result data may enter prediction-side computations."
        ]
    }
    return output


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path,required=True,help="Private source-normalized JSON with timestamped quote rows")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--gamma",default="0.75,1.0,1.25")
    p.add_argument("--plans",type=Path,help="Optional JSON mapping plan names to tickets")
    a=p.parse_args()
    gammas=[float(x) for x in a.gamma.split(",")]
    data=json.loads(a.input.read_text(encoding="utf-8"))
    plans=json.loads(a.plans.read_text(encoding="utf-8")) if a.plans else None
    result=sensitivity(data,gammas,plans)
    raw=a.input.read_bytes()
    result["input_local_sha256"]=hashlib.sha256(raw).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("status","runners","model_outcome_count",
                                          "quoted_pairs_full","quoted_trios_partial")},
                     ensure_ascii=False))


if __name__=="__main__":
    main()
