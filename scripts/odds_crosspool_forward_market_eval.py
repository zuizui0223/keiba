#!/usr/bin/env python3
"""Future-date-blocked WIN–WIDE lead/lag *market quote* benchmark.

Only prestart, FULL runner WIN vectors and FULL WIDE pair vectors
with verified published timestamps are valid. This does NOT fetch
or redistribute JRA-VAN/JRA data. Data must be locally authorized
and normalized; an operator attestation does not prove legal rights.

Target: next normalized inverse displayed WIN quotes, not race winner.
Every coefficient, including odds-band thresholds, is selected solely
on earlier race *dates*. At least 60 races across >=8 dates are required.

The built-in fixtures use fabricated markets with PL-based pair prices
and independent Gaussian updates. They are NOT observed horse races.

Run:
 python scripts/odds_crosspool_forward_market_eval.py --demo-synthetic \
     --output tmp/odds-crosspool-forward-demo.json
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import random
from statistics import mean

from odds_cross_pool_global_async import relative_pair_indices
from odds_pair_hierarchy_decomposition import complete_graph_decompose
from odds_r8_next_win_market_forecast import win_proxy, construct_advance_forecast
from shuka2026_odds_information_hierarchy import pl_pair_top3_index

SCHEMA="AUTHORIZED_WIN_WIDE_FUTURE_MARKET_PANEL_V1"
STATUS_HOLD="HOLD_INSUFFICIENT_VERIFIED_MULTI_DATE_NEXT_MARKET_COHORT"
STATUS_SYN="SYNTHETIC_ONLY_FUTURE_MARKET_COEFFICIENT_LEARNING_DEMO"
STATUS_LOCAL="LOCAL_SELF_ATTESTED_HISTORICAL_MARKET_QUOTE_EXPLORATION_ONLY"
COEFF_GRID=(-.5,0.0,.25,.5,1.0)
ODDS_BANDS=(5.0,10.0,20.0,50.0)


def _time(x):
    if not isinstance(x,str):
        raise ValueError("HOLD_QUOTE_TIME_TYPE")
    t=datetime.fromisoformat(x)
    if t.utcoffset() is None:
        raise ValueError("HOLD_QUOTE_TIMEZONE")
    return t


def _check_market(s,kind,start,*,base_provider=None):
    if s.get("market")!=kind or s.get("provider_time_verified") is not True:
        raise ValueError("HOLD_WRONG_BET_TYPE_OR_UNVERIFIED_SOURCE_CLOCK")
    ts=_time(s["source_update_time"])
    rx=_time(s["received_at"])
    if not ts<=rx<start-timedelta(minutes=10):
        raise ValueError("HOLD_QUOTE_NOT_AVAILABLE_BEFORE_FIXED_DECISION_TIME")
    provider=s.get("provider")
    if not isinstance(provider,str) or not provider:
        raise ValueError("HOLD_UNKNOWN_PROVIDER")
    if base_provider is not None and provider!=base_provider:
        raise ValueError("HOLD_PROVIDER_SWITCH_IN_MATCHED_MARKET")
    return ts,rx,provider


def _wide_rows(s, ids):
    pairs={}
    for row in s.get("pairs",[]):
        selection=row.get("selection")
        if not (isinstance(selection,list) and len(selection)==2 and
                type(selection[0]) is int and type(selection[1]) is int and
                selection[0]!=selection[1]):
            raise ValueError("HOLD_MALFORMED_WIDE_SELECTION")
        key=tuple(sorted(selection))
        price=row.get("low")
        if (type(price) not in (int,float) or not math.isfinite(price)
            or price<=1 or key in pairs):
            raise ValueError("HOLD_DUPLICATE_INVALID_WIDE_PRICE")
        pairs[key]=float(price)
    if len(pairs)!=len(ids)*(len(ids)-1)//2 or any(
            i not in ids or j not in ids for i,j in pairs):
        raise ValueError("HOLD_INCOMPLETE_WIDE_PAIR_GRID")
    return pairs


def prepare_feature_before_future(r):
    """Only pretarget snapshots are read; no official race outcomes."""
    race_id=r.get("race_id")
    if not isinstance(race_id,str) or not race_id:
        raise ValueError("HOLD_RACE_ID")
    start=_time(r["post_jst"])
    early,mid,wide=(r["early_win"],r["mid_win"],r["mid_wide"])
    t0,_,provider=_check_market(early,"win",start)
    t1,mid_rx,_=_check_market(mid,"win",start,base_provider=provider)
    tw,wide_rx,_=_check_market(wide,"wide",start,base_provider=provider)
    if not (t0<t1==tw and wide_rx<start):
        raise ValueError("HOLD_NOT_PRESTART_MATCHED_TIME_WIN_WIDE")
    e=early["odds"]
    m=mid["odds"]
    if not isinstance(e,dict) or set(e)!=set(m) or len(e)<5:
        raise ValueError("HOLD_CHANGED_OR_INCOMPLETE_WIN_ROSTER")
    try:
        early_odds={int(k):v for k,v in e.items()}
        mid_odds={int(k):v for k,v in m.items()}
    except (TypeError,ValueError):
        raise ValueError("HOLD_BAD_HORSE_NUMBER")
    if len(early_odds)!=len(e) or len(mid_odds)!=len(m):
        raise ValueError("HOLD_DUPLICATE_NUMERIC_HORSE_IDS")
    q0,q1=win_proxy(early_odds),win_proxy(mid_odds)
    if set(q0)!=set(q1):
        raise ValueError("HOLD_INCONSISTENT_WIN_HORSE_IDS")
    wide_odds=_wide_rows(wide,set(q1))
    index=relative_pair_indices({
        "label":"mid_only","win":mid_odds,"wide":wide_odds})
    fit=complete_graph_decompose(index["pair_residual"])
    if fit["status"]!="COMPLETE_GRAPH_HORSE_ADDITIVE_DESCRIPTIVE_DECOMPOSITION":
        raise ValueError("HOLD_INCOMPLETE_GRAPH_FIT")
    return {
        "id":race_id,"date":start.date().isoformat(),
        "start_time":start.isoformat(),
        "latest_win_timestamp":t1.isoformat(),
        "feature_receipt":max(mid_rx,wide_rx).isoformat(),
        "provider":provider,
        "n_horses":len(q1),
        "last_market_q":q1,
        "earlier_market_q":q0,
        "early_displayed_win_odds":early_odds,
        "wide_extra_horse_node":fit["node_effects"],
        "prior_earlier_minutes":(t1-t0).total_seconds()/60,
        "comparison_horizon_minutes_in_advance":None,
    }


def prepare_target_for_scoring(r,f):
    """Targets cannot influence construction or selection of future predictors."""
    start=_time(r["post_jst"])
    target=r["target_win"]
    t2,rx,_=_check_market(target,"win",start,base_provider=f["provider"])
    t1=_time(f["latest_win_timestamp"])
    horizon=(t2-t1).total_seconds()/60
    if not (10 <= horizon <= 30 and _time(f["feature_receipt"])<t2):
        raise ValueError("HOLD_TARGET_NOT_A_LATER_SOURCE_PUBLISHED_QUOTE")
    try:
        odds={int(k):v for k,v in target["odds"].items()}
    except (TypeError,ValueError):
        raise ValueError("HOLD_BAD_TARGET_PRICE_IDS")
    q=win_proxy(odds)
    if set(q)!=set(f["last_market_q"]) or len(q)!=f["n_horses"]:
        raise ValueError("HOLD_TARGET_RUNNER_ROSTER_MISMATCH")
    return q,horizon


def _forecast(feature, *, b_momentum=1.0,b_node=0,threshold=None,
              shuffled_node=None):
    f={**feature}
    if shuffled_node is not None:
        f["wide_extra_horse_node"]=shuffled_node
    if threshold is not None:
        f["wide_extra_horse_node"]={
            i:node if f["early_displayed_win_odds"][i]>=threshold else 0.0
            for i,node in f["wide_extra_horse_node"].items()
        }
    return construct_advance_forecast(
        f,beta_momentum=b_momentum,beta_node=b_node)


def _KL(actual,pred):
    return sum(actual[i]*math.log(actual[i]/pred[i]) for i in actual)


def _distance(actual,pred):
    return {
        "market_index_KL":_KL(actual,pred),
        "market_index_TV_pp":50*sum(abs(actual[i]-pred[i]) for i in actual),
    }


def _average_forecast(rows,*,bm=1.0,bn=0.0,threshold=None,which="market_index_KL"):
    return mean(_distance(y,_forecast(f,b_momentum=bm,b_node=bn,threshold=threshold))[which]
                for f,y in rows)


def _fold_train(rows):
    candidate_sm=[(b,None) for b in COEFF_GRID]
    candidate_bands=[
        (b,t) for b in COEFF_GRID for t in ODDS_BANDS if
        sum(sum(o>=t for o in f["early_displayed_win_odds"].values())
            for f,_ in rows)>=10]
    if not candidate_bands:
        raise ValueError("HOLD_TRAIN_HAS_NO_SUPER_THRESHOLD_WIN_PRICE_EXAMPLES")
    def best(candidates):
        outcomes=[(
            _average_forecast(rows,bm=1.0,bn=bn,threshold=t),
            bn,t) for bn,t in candidates]
        return min(outcomes,key=lambda z:(z[0],abs(z[1]),-1 if z[2] is None else z[2]))
    return {
        "smooth":best(candidate_sm),
        "threshold":best(candidate_bands),
    }


def evaluate(data, *, seed=20261023):
    if data.get("schema")!=SCHEMA:
        raise ValueError("HOLD_UNKNOWN_CROSSPOOL_PANEL_SCHEMA")
    origin=data.get("provenance")
    if origin not in ("synthetic","authorized_local_operator"):
        raise ValueError("HOLD_UNVERIFIED_MARKET_DATA_LICENSE_OR_ORIGIN")
    if origin=="authorized_local_operator" and data.get("license_self_attested") is not True:
        raise ValueError("HOLD_SOURCE_LICENSE_SELF_ATTESTATION_MISSING")
    if data.get("raw_records_redistributable") is not False:
        raise ValueError("HOLD_NO_SOURCE_RIGHTS_FOR_RAW_REDISTRIBUTION")
    races=data.get("races")
    if not isinstance(races,list) or not races:
        raise ValueError("HOLD_NO_MULTI_RACE_PANEL")
    ids=[r.get("race_id") for r in races]
    if len(set(ids))!=len(ids):
        raise ValueError("HOLD_DUPLICATE_RACE_ID")
    # All source features are prepared independent of targets. Only after
    # the feature set is fully created do we attach target quote distributions.
    features=[prepare_feature_before_future(r) for r in races]
    pairs=[]
    for r,feature in zip(races,features):
        target,horizon=prepare_target_for_scoring(r,feature)
        f={**feature,"comparison_horizon_minutes_in_advance":horizon}
        pairs.append((f,target))
    pairs.sort(key=lambda p:(p[0]["date"],p[0]["id"]))
    dates=sorted({f["date"] for f,_ in pairs})
    if len(pairs)<60 or len(dates)<8:
        return {
            "status":STATUS_HOLD,
            "actual_distinct_races":len(pairs),
            "distinct_meeting_dates":len(dates),
            "engineering_min_races":60,"engineering_min_dates":8,
            "disclaimer":"Coverage requirement, not a statistically powered proof of market lead-lag."
        }
    tcut=min(len(dates)-3,max(5,int(len(dates)*.7)))
    train_days=set(dates[:tcut])
    train=[p for p in pairs if p[0]["date"] in train_days]
    future=[p for p in pairs if p[0]["date"] not in train_days]
    if len(train)<35 or len(future)<12:
        return {"status":STATUS_HOLD,"training_races":len(train),
                "future_races":len(future)}
    selected=_fold_train(train)
    chosen={
        "current_win_quote_only":(0,0,None),
        "elapsed_time_momentum_only":(1,0,None),
        "train_selected_wide_horse_node":(1,selected["smooth"][1],None),
        "train_selected_threshold_wide_node":(
            1,selected["threshold"][1],selected["threshold"][2])
    }
    rows=[]
    rng=random.Random(seed)
    for f,target in future:
        score={name:_distance(target,_forecast(
            f,b_momentum=bm,b_node=bn,threshold=threshold))
               for name,(bm,bn,threshold) in chosen.items()}
        nodes=f["wide_extra_horse_node"]
        members=sorted(nodes)
        shuffled=[nodes[k] for k in members]
        rng.shuffle(shuffled)
        p=_forecast(f,b_momentum=1,b_node=selected["smooth"][1],
                    shuffled_node=dict(zip(members,shuffled)))
        score["negative_control_shuffled_WIDE_nodes"]=_distance(target,p)
        rows.append({"race_id":f["id"],"date":f["date"],"score":score})
    metrics=("market_index_KL","market_index_TV_pp")
    means={
        model:{metric:mean(r["score"][model][metric] for r in rows)
               for metric in metrics} for model in rows[0]["score"]
    }
    days_future=sorted({r["date"] for r in rows})
    byday={
        day:{model:{metric:mean(r["score"][model][metric] for r in rows
                                      if r["date"]==day)
                    for metric in metrics} for model in means}
        for day in days_future
    }
    aggregate_byday={
        model:{metric:mean(byday[day][model][metric] for day in days_future)
               for metric in metrics} for model in means
    }
    return {
        "status":STATUS_SYN if origin=="synthetic" else STATUS_LOCAL,
        "not_a_race_winner_probability_score":True,
        "real_market_source_license_legal_verification_performed":False,
        "train_max_date":max(train_days),
        "future_min_date":min(days_future),
        "train_race_count":len(train),"future_race_count":len(future),
        "train_meeting_days":len(train_days),"future_meeting_days":len(days_future),
        "training_only_selected":{
            name:{"market_index_KL_train":v[0],"wide_node_beta":v[1],
                  "earlier_win_odds_threshold":v[2]}
            for name,v in selected.items()
        },
        "future_equal_race_market_price_index_scores":means,
        "future_equal_meeting_day_market_price_index_scores":aggregate_byday,
        "future_race_unit_anonymous_checks":[{
            "race_id":r["race_id"],"date":r["date"],
            "market_index_KL_by_model":{m:s["market_index_KL"]
                                        for m,s in r["score"].items()}
        } for r in rows],
        "limitations":[
            "Test target is the NEXT quote-derived win market share index, not actual winner/Top3.",
            "The raw price vectors were verified against their own input provenance flags only, not independently licensed.",
            "No real market results are acquired or simulated fixtures promoted to evidence.",
            "All coefficients and thresholds selected on earlier meeting dates only; future cannot tune them.",
            "Cross-market source update minute matches are not atomic bettor transaction times.",
            "The 60-race/8-day thresholds are software support gates not a statistical power demonstration.",
            "No JRA-VAN raw market data are copied to GitHub and no economic returns are predicted.",
        ],
    }


def synthetic_panel(*, seed=20261023, dates=15, races_per_day=6,
                    horses=11, planted_wide_beta=0.0,
                    planted_initial_odds_threshold=None):
    """Fabricated PL-price WIDE node effects leading future synthetic win shares."""
    if dates<8 or horses<8 or races_per_day<2:
        raise ValueError("HOLD_SYNTHETIC_GENERATOR_TOO_FEW_RACES")
    rng=random.Random(seed)
    start=datetime.fromisoformat("2026-01-01T14:00:00+09:00")
    rows=[]
    for day in range(dates):
        for k in range(races_per_day):
            post=start+timedelta(days=day,minutes=15*k)
            t0=post-timedelta(minutes=125)
            t1=post-timedelta(minutes=60)
            t2=post-timedelta(minutes=42)
            def softmax(w):
                e=[math.exp(v-max(w)) for v in w]
                return [v/sum(e) for v in e]
            q0=softmax([rng.gauss(0,.9) for _ in range(horses)])
            q1=softmax([math.log(q0[i])+rng.gauss(0,.18)
                        for i in range(horses)])
            node=[rng.gauss(0,.32) for _ in range(horses)]
            mid_odds={i+1:1/q1[i] for i in range(horses)}
            modeled=pl_pair_top3_index(mid_odds)
            pairs=[]
            for (i,j),p in modeled.items():
                pair_w=p*math.exp(node[i-1]+node[j-1])
                pairs.append({"selection":[i,j],"low":1/pair_w})
            # Source-generated independent middle-range noise, not a learned mechanism.
            future=softmax([
                math.log(q1[i])+
                (18/65)*math.log(q1[i]/q0[i])+
                planted_wide_beta*(node[i] if
                    planted_initial_odds_threshold is None or
                    1/q0[i]>=planted_initial_odds_threshold else 0)+
                rng.gauss(0,.045)
                for i in range(horses)
            ])
            def snap(kind,t,odds):
                return {
                    "market":kind,"provider":"FICTIONAL_IDENTICAL_PROVIDER",
                    "provider_time_verified":True,
                    "source_update_time":t.isoformat(),
                    "received_at":(t+timedelta(seconds=15)).isoformat(),
                    "odds":{str(i+1):float(v) for i,v in enumerate(odds)}
                }
            a=snap("win",t0,[1/x for x in q0])
            b=snap("win",t1,[1/x for x in q1])
            c=snap("win",t2,[1/x for x in future])
            wide={
                "market":"wide","provider":"FICTIONAL_IDENTICAL_PROVIDER",
                "provider_time_verified":True,
                "source_update_time":t1.isoformat(),
                "received_at":(t1+timedelta(seconds=17)).isoformat(),
                "pairs":pairs
            }
            rows.append({
                "race_id":f"FICTITIOUS-WIN-WIDE-{day:03d}-{k:02d}",
                "post_jst":post.isoformat(),
                "early_win":a,"mid_win":b,"mid_wide":wide,"target_win":c,
            })
    return {
        "schema":SCHEMA, "provenance":"synthetic",
        "raw_records_redistributable":False,
        "generation_note":"Fictitious odds and market structure with PL pair-price tilts and artificial future win signals.",
        "planted_wide_beta":planted_wide_beta,
        "planted_initial_odds_threshold":planted_initial_odds_threshold,
        "races":rows
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path)
    p.add_argument("--demo-synthetic",action="store_true")
    p.add_argument("--output",type=Path,
                   default=Path("tmp/odds-crosspool-future-market.json"))
    args=p.parse_args()
    if bool(args.input)==args.demo_synthetic:
        raise ValueError("Provide exactly one of --input or --demo-synthetic")
    if args.demo_synthetic:
        cases={
            "null_no_extra_WIDE_information":0.0,
            "positive_half_strength_WIDE_signal":0.5,
        }
        result={k:evaluate(synthetic_panel(planted_wide_beta=b))
                for k,b in cases.items()}
        output={
            "status":"COMPARATIVE_SYNTHETIC_ONLY_NO_REAL_RACE_MARKET_FORECAST",
            "cases":result,"no_real_JRA_market_quotes_used":True}
    else:
        output=evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    def concise(result):
        if result["status"]==STATUS_HOLD:
            return result
        return {
            "status":result["status"],
            "train":result["train_race_count"],"future":result["future_race_count"],
            "chosen":result["training_only_selected"],
            "scores":result["future_equal_race_market_price_index_scores"],
            "future_date_averages":result["future_equal_meeting_day_market_price_index_scores"],
            "real_race_winner_prediction":"NOT_EVALUATED"
        }
    print(json.dumps({
        "status":output.get("status"),
        "cases":{k:concise(v) for k,v in output["cases"].items()}
        if "cases" in output else concise(output),
    },ensure_ascii=False))


if __name__=="__main__":
    main()
