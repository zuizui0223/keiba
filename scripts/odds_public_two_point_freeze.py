#!/usr/bin/env python3
"""Freeze a real prestart *market-quote baseline* from two public win-odds panels.

This module is stdlib-only. The full market panel remains LOCAL/PRIVATE.
Only a SHA256 of the complete frozen predictions may be posted to GitHub
before race start; the post-race result is never read by freeze().
Publishing a comment does NOT validate quote accuracy, model calibration,
or a formal v3.1 holdout.

Comparison fixed before 2026-10-25 Kyoto 11R:
 M0 market_only: PL with normalized inverse LATEST quotes,
 M1 smooth_momentum: fixed positive beta=0.25 on log latest/earlier q,
 M2 threshold_10x_momentum: same beta only where earlier odds>=10.

No information from WIDE is used. The earlier snapshot is an ARCHIVED
intermediate quote, NOT certified opening odds. Do not cherry-pick among
models postrace: M0 vs M1 on winner logloss is primary comparison;
M2 is explicitly exploratory threshold sensitivity.

Input JSON schema KEIBA_TWO_PUBLIC_WIN_QUOTE_PANEL_V1:
  race_id, post_jst, provider,
  sources=[{quote_at_jst,source_url,win_odds_by_horse_number:{str(num):odds}}]
Sources must be chronological, same 5-30 complete horses, at least 10min
before post. This does not fetch prices or proprietary JRA-VAN data.

CLI:
 python scripts/odds_public_two_point_freeze.py freeze --source private/quotes.json --output private/freeze.json
 python scripts/odds_public_two_point_freeze.py score --freeze private/freeze.json --result private/jra_result.json --output private/score.json

Result schema KEIBA_JRA_TOP3_POSTRACE_V1:
  race_id, top3_horse_numbers, verified_at_jst, official_results_url
"""
from __future__ import annotations
import argparse
from datetime import datetime,timedelta
from hashlib import sha256
from itertools import permutations,combinations
import json, math
from pathlib import Path
from statistics import mean
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

INPUT_SCHEMA = "KEIBA_TWO_PUBLIC_WIN_QUOTE_PANEL_V1"
FREEZE_SCHEMA = "KEIBA_TWO_POINT_PRESTART_WIN_PL_FREEZE_V1"
RESULT_SCHEMA = "KEIBA_JRA_TOP3_POSTRACE_V1"
STATUS = "MARKET_ONLY_PROSPECTIVE_SHA_CONTENT_NOT_PROVEN_RECEIVED_UNTIL_GITHUB_COMMENT"
MODELS = (
    ("M0_market_only",0.0,None),
    ("M1_smooth_beta025",0.25,None),
    ("M2_initial_10x_beta025",0.25,10.0),
)
PRIMARY = "winner_log_loss_M1_minus_M0"
SECONDARY = "top3_brier_M1_minus_M0"
EXPLORATORY = "trio_log_loss_M1_minus_M0"

def aware(x):
    if not isinstance(x,str):raise ValueError("HOLD_NAIVE_OR_MISSING_TIMESTAMP")
    t=datetime.fromisoformat(x.replace("Z","+00:00"))
    if t.tzinfo is None or t.utcoffset() is None:raise ValueError("HOLD_NAIVE_OR_MISSING_TIMESTAMP")
    return t

def canonical(v):
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")

def seal(payload):
    return sha256(canonical(payload)).hexdigest()

def normalize(w):
    if not w or any(v<=0 or not math.isfinite(v) for v in w.values()):
        raise ValueError("HOLD_BAD_WIN_WEIGHT")
    z=sum(w.values())
    return {i:v/z for i,v in sorted(w.items())}

def validate_source(x):
    if x.get("schema") != INPUT_SCHEMA:raise ValueError("HOLD_WRONG_SOURCE_SCHEMA")
    race=x.get("race_id")
    if not isinstance(race,str) or len(race)<5:raise ValueError("HOLD_INVALID_RACE")
    post=aware(x.get("post_jst"))
    provider=x.get("provider")
    if not isinstance(provider,str) or not provider:raise ValueError("HOLD_INVALID_MARKET_PROVIDER")
    sources=x.get("sources")
    if not isinstance(sources,list) or len(sources)!=2:raise ValueError("HOLD_EXACTLY_TWO_SOURCE_TIMES_REQUIRED")
    items=[]
    for source in sources:
        if not isinstance(source,dict):raise ValueError("HOLD_BAD_SOURCE")
        quote_at=aware(source.get("quote_at_jst"))
        u=urlparse(source.get("source_url",""))
        if u.scheme!="https" or not u.hostname:raise ValueError("HOLD_SOURCE_URL_NOT_HTTPS")
        raw=source.get("win_odds_by_horse_number")
        if not isinstance(raw,dict) or not 5<=len(raw)<=30:raise ValueError("HOLD_INCOMPLETE_FIELD")
        odds={}
        for k,o in raw.items():
            if (not isinstance(k,str) or not k.isdecimal() or str(int(k))!=k
                    or int(k)<=0 or type(o) not in (float,int) or not math.isfinite(o) or o<=1):
                raise ValueError("HOLD_MALFORMED_ODDS_OR_HORSE")
            odds[int(k)]=float(o)
        if len(odds)!=len(raw):raise ValueError("HOLD_DUPLICATE_HORSE")
        items.append((quote_at,source["source_url"],odds))
    (t0,url0,o0),(t1,url1,o1)=items
    if not (t0<t1<post-timedelta(minutes=10)):raise ValueError("HOLD_QUOTES_ARE_NOT_TWO_PRESTART_UPDATES")
    if set(o0)!=set(o1):raise ValueError("HOLD_CHANGED_RACE_ROSTER")
    return race,post,provider,items

def make_joint(odds,early,*,beta=0.0,threshold=None):
    q=normalize({i:1/o for i,o in odds.items()})
    q0=normalize({i:1/o for i,o in early.items()})
    # Cohesive ranking weights normalized from market price proxy.
    weights=normalize({i:q[i]*math.exp(beta*math.log(q[i]/q0[i])*
                 (threshold is None or early[i]>=threshold)) for i in q})
    ids=sorted(weights)
    top3={i:0.0 for i in ids}
    trios={k:0.0 for k in combinations(ids,3)}
    W=sum(weights.values())
    for i,j,k in permutations(ids,3):
        pij=weights[i]/W*weights[j]/(W-weights[i])
        p=pij*weights[k]/(W-weights[i]-weights[j])
        for x in (i,j,k):top3[x]+=p
        trios[tuple(sorted((i,j,k)))]+=p
    assert math.isclose(sum(weights.values()),1,abs_tol=1e-10)
    assert math.isclose(sum(top3.values()),3,abs_tol=1e-10)
    assert math.isclose(sum(trios.values()),1,abs_tol=1e-10)
    return {
        "win":[{"number":i,"p":weights[i]} for i in ids],
        "top3":[{"number":i,"p":top3[i]} for i in ids],
        "trio":[{"horse_numbers":list(key),"p":v} for key,v in trios.items()],
    }

def freeze(source,*,generated_at_jst=None,source_file_sha=None):
    race,post,provider,[(t0,url0,o0),(t1,url1,o1)]=validate_source(source)
    generated=aware(generated_at_jst) if generated_at_jst else datetime.now(ZoneInfo("Asia/Tokyo"))
    if not t1<=generated<post-timedelta(minutes=10):
        raise ValueError("HOLD_SNAPSHOT_NOT_FROZEN_PRESTART")
    if source_file_sha is None:source_file_sha=seal(source)
    predicts={}
    for name,beta,threshold in MODELS:
        predicts[name]=make_joint(o1,o0,beta=beta,threshold=threshold)
    payload={
        "schema":FREEZE_SCHEMA,"status":STATUS,
        "race_id":race,"post_jst":post.isoformat(),
        "provider":provider,
        "source_earlier_quote_at_jst":t0.isoformat(),
        "source_later_quote_at_jst":t1.isoformat(),
        "source_urls":[url0,url1],
        "local_freeze_generated_at_jst":generated.isoformat(),
        "source_private_input_sha256":source_file_sha,
        "source_displayed_quotes_are_not_opening_odds":True,
        "non_calibrated_normalized_inverse_odds_market_proxy":True,
        "beta025_and_threshold10_are_predeclared_exploratory_not_trained":True,
        "predeclared_primary_contrast":PRIMARY,
        "predeclared_secondary_contrast":SECONDARY,
        "predeclared_exploratory_contrast":EXPLORATORY,
        "roster_horse_numbers":sorted(o1),
        "models":[{"name":n,"beta":b,"earlier_odds_threshold":t}
                  for n,b,t in MODELS],
        "predictions":predicts,"outcome_loaded_before_freeze":False,
        "not_a_v31_formal_holdout":True,
    }
    return {"seal_sha256_of_payload":seal(payload),"payload":payload}

def verify_freeze(frozen):
    p=frozen.get("payload",{})
    if p.get("schema")!=FREEZE_SCHEMA or seal(p)!=frozen.get("seal_sha256_of_payload"):
        raise ValueError("HOLD_SEALED_FORECAST_CONTENT_CHANGED")
    if [m.get("name") for m in p.get("models",[])]!=[m[0] for m in MODELS]:
        raise ValueError("HOLD_FORECAST_MODELS_CHANGED")
    return p

def score(frozen,result):
    p=verify_freeze(frozen)
    if result.get("schema")!=RESULT_SCHEMA or result.get("race_id")!=p["race_id"]:
        raise ValueError("HOLD_INDEPENDENT_RESULT_RACE_MISMATCH")
    post=aware(p["post_jst"])
    verified=aware(result.get("verified_at_jst"))
    if verified<=post:raise ValueError("HOLD_RESULT_KNOWN_BEFORE_RACE_START")
    u=urlparse(result.get("official_results_url",""))
    if u.scheme!="https" or u.hostname not in ("www.jra.go.jp","jra.go.jp","app.jra.jp"):
        raise ValueError("HOLD_RESULT_MUST_BE_INDEPENDENT_JRA_OFFICIAL")
    podium=result.get("top3_horse_numbers")
    if not isinstance(podium,list) or len(podium)!=3 or len(set(podium))!=3 or not all(type(i)==int for i in podium):
        raise ValueError("HOLD_INVALID_RESULT_PODIUM")
    if not set(podium).issubset(p["roster_horse_numbers"]):raise ValueError("HOLD_RESULT_OUTSIDE_FROZEN_ROSTER")
    report={}
    true_set=set(podium)
    for name,_,_ in MODELS:
        forecast=p["predictions"][name]
        win={v["number"]:v["p"] for v in forecast["win"]}
        place={v["number"]:v["p"] for v in forecast["top3"]}
        trio={tuple(v["horse_numbers"]):v["p"] for v in forecast["trio"]}
        if not math.isclose(sum(win.values()),1,abs_tol=1e-8) or not math.isclose(sum(place.values()),3,abs_tol=1e-8) or not math.isclose(sum(trio.values()),1,abs_tol=1e-8):
            raise ValueError("HOLD_INCOHERENT_SCORE_FORECAST")
        report[name]={
            "winner_log_loss":-math.log(win[podium[0]]),
            "top3_brier":mean((prob-int(i in true_set))**2 for i,prob in place.items()),
            "trio_log_loss":-math.log(trio[tuple(sorted(podium))]),
        }
    base=report["M0_market_only"]
    model=report["M1_smooth_beta025"]
    threshold=report["M2_initial_10x_beta025"]
    return {
        "status":"POSTRACE_SCORE_OF_PRESEALED_MARKET_PROXY_NOT_CERTIFIED_GITHUB_PROOF",
        "race_id":p["race_id"],
        "freeze_seal":frozen["seal_sha256_of_payload"],
        "observed_podium":podium,
        "scores_by_model":report,
        PRIMARY:model["winner_log_loss"]-base["winner_log_loss"],
        SECONDARY:model["top3_brier"]-base["top3_brier"],
        EXPLORATORY:model["trio_log_loss"]-base["trio_log_loss"],
        "exploratory_threshold_winner_delta":threshold["winner_log_loss"]-base["winner_log_loss"],
        "no_new_model_selection_or_real_return_claim":True,
        "real_prospective_GitHub_submission_must_be_independently_checked":True,
    }

def main():
    a=argparse.ArgumentParser(description=__doc__)
    sub=a.add_subparsers(dest="cmd",required=True)
    f=sub.add_parser("freeze")
    f.add_argument("--source",type=Path,required=True)
    f.add_argument("--output",type=Path,required=True)
    c=sub.add_parser("score")
    c.add_argument("--freeze",type=Path,required=True)
    c.add_argument("--result",type=Path,required=True)
    c.add_argument("--output",type=Path,required=True)
    args=a.parse_args()
    if args.cmd=="freeze":
        raw=args.source.read_bytes()
        output=freeze(json.loads(raw.decode("utf-8")),source_file_sha=sha256(raw).hexdigest())
    else:
        output=score(json.loads(args.freeze.read_text(encoding="utf-8")),
                     json.loads(args.result.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":output["payload"]["status"] if args.cmd=="freeze" else output["status"],
        "race_id":output["payload"]["race_id"] if args.cmd=="freeze" else output["race_id"],
        "seal":output["seal_sha256_of_payload"] if args.cmd=="freeze" else output["freeze_seal"],
        "outcome_used":args.cmd=="score",
    },ensure_ascii=False))

if __name__=="__main__":
    main()
