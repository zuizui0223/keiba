#!/usr/bin/env python3
"""Recreate 2026-10-25 pre-race gamma-shadow probabilities and SHA from private odds.

No historical JRA outcomes are read here. Training gamma values were fixed
before this one target race's start, from retrospective two-date evidence.
This experimental clock is only WEB-PAGE RETRIEVAL, not independently verified
per-market source publication; do not score in the formal cohort.
The original 10/24 M0/M1/M2 SHA remains untouched.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime,timedelta
import hashlib
from itertools import permutations
import json
import math
from pathlib import Path

RACE_ID="2026-10-25-KYOTO-11"
POST="2026-10-25T15:40:00+09:00"
SOURCE_SCHEMA="KEIBA_KIKKA_LOCAL_PRICE_VECTOR_V1"
GAMMA_WIN=1.85
GAMMA_TOP3=1.70
HIST_SHA = {
  "kyoto_20261012_r8":"65fa640d6a07b7d94eb6e2904f6cc73f07a96448",
  "kyoto_20261012_r9":"be94d8b01a2b67287958598842cc724029f45e89",
  "kyoto_20261012_r10":"cdf8f36a073f68d351417d0046f5ab5c1ccc2be3",
  "kyoto_20261012_r11":"751734355c67149b39cd1ebaf9682aac24f352e5",
  "kyoto_20261012_r12":"6da13808c7b2a9c716a74b1c41d2c08296318c09",
  "kyoto_20261012_official":"fdcc70b78c64a50b8a0f566868b38b69ce2c6ff8",
  "race_20261018_nine_odds":"8a7d37f02a40e7c6f93d6ee428089cd5c84e59df",
  "race_20261018_nine_official":"ca5c9ac0d38e66d927c68786f7793b59c67035ce",
}


def canonical_bytes(doc):
    return json.dumps(doc, ensure_ascii=False, sort_keys=True,
                      separators=(",",":")).encode("utf-8")


def sha256(doc):
    return hashlib.sha256(canonical_bytes(doc)).hexdigest()


def source_validation(s):
    if s.get("schema")!=SOURCE_SCHEMA or s.get("race_id")!=RACE_ID:
        raise ValueError("HOLD_RACE_SOURCE_SCHEMA")
    if s.get("source_url")!="https://sports.yahoo.co.jp/keiba/race/odds/tfw/2608040911?ninki=1":
        raise ValueError("HOLD_UNIDENTIFIED_SOURCE")
    if s.get("provider_publication_clock_verified") is not False:
        raise ValueError("HOLD_UNVERIFIED_CLOCK_FLAG_MUST_BE_EXPLICIT")
    clock=datetime.fromisoformat(s["source_page_retrieved_at_jst"])
    post=datetime.fromisoformat(POST)
    if clock.utcoffset() is None or not clock < post-timedelta(minutes=10):
        raise ValueError("HOLD_NOT_PROVEN_PRE_START")
    if any(k in s for k in ("outcome", "finish", "winner", "official_result")):
        raise ValueError("HOLD_RESULT_LEAKAGE")
    raw=s.get("odds_by_number",{})
    if s.get("runner_count")!=18 or set(raw)!={str(i) for i in range(1,19)}:
        raise ValueError("HOLD_NOT_COMPLETE_18_HORSES")
    o={}
    for k,v in raw.items():
        if type(v) not in (int,float) or not math.isfinite(v) or v<=1:
            raise ValueError("HOLD_INVALID_INTERMEDIATE_WIN_ODDS")
        o[int(k)]=float(v)
    return o


def exact_model(odds,gamma):
    numbers=sorted(odds)
    w={i:odds[i]**(-gamma) for i in numbers}
    z=sum(w.values())
    p={i:w[i]/z for i in numbers}
    top2=defaultdict(float)
    top3=defaultdict(float)
    trios=defaultdict(float)
    total=0.0
    for a,b,c in permutations(numbers,3):
        m=p[a]*p[b]/(1-p[a])*p[c]/(1-p[a]-p[b])
        total+=m
        for j in (a,b):top2[j]+=m
        for j in (a,b,c):top3[j]+=m
        trios[tuple(sorted((a,b,c)))]+=m
    if (not math.isclose(sum(p.values()),1,abs_tol=1e-10)
            or not math.isclose(total,1,abs_tol=1e-10)
            or not math.isclose(sum(top2.values()),2,abs_tol=1e-10)
            or not math.isclose(sum(top3.values()),3,abs_tol=1e-10)
            or not math.isclose(sum(trios.values()),1,abs_tol=1e-10)
            or len(trios)!=816):
        raise AssertionError("HOLD_RANK_PROBABILITY_MASS")
    return {"gamma":gamma,
       "win":[{"number":i,"p":p[i]} for i in numbers],
       "top2":[{"number":i,"p":top2[i]} for i in numbers],
       "top3":[{"number":i,"p":top3[i]} for i in numbers],
       "unordered_trio":[{"numbers":list(k),"p":val} for k,val in sorted(trios.items())]}


def build(source):
    odds=source_validation(source)
    payload={
      "schema":"KEIBA_KIKKA_MARKET_SHARPNESS_TWO_DAY_EXPERIMENTAL_SHADOW_V1",
      "status":"EXPLORATORY_FORWARD_SHADOW_UNCALIBRATED_NOT_AN_OFFICIAL_HOLDOUT",
      "race_id":RACE_ID,
      "post_jst":POST,
      "source_page_retrieved_at_jst":source["source_page_retrieved_at_jst"],
      "source_private_json_sha256":sha256(source),
      "training_origin":"2026-10-12 5 races; 2026-10-18 9 races; 2 independent meeting dates",
      "training_source_git_blobs":HIST_SHA,
      "gamma_grid":{"min":0.50,"max":2.30,"step":0.05},
      "objective_win":"winner categorical logloss; race-equal 14 historical starts",
      "objective_top3":"per-race mean per-horse Top3 Brier; race-equal 14 historical starts",
      "chosen_gamma_win":GAMMA_WIN,
      "chosen_gamma_top3":GAMMA_TOP3,
      "no_2026_10_25_outcome_used":True,
      "scored_models":{
        "market_gamma1":exact_model(odds,1.0),
        "historic14_gamma185_winner":exact_model(odds,GAMMA_WIN),
        "historic14_gamma170_top3":exact_model(odds,GAMMA_TOP3),
      },
      "limits":[
        "Two dates only, historical source cohort selected retrospectively, no true calibration.",
        "Original 10/24 SHA-sealed M0 M1 M2 remains independent and unchanged.",
        "Price page capture clock is not provider-timestamp verified; ineligible for formal timestamp-gated cohort.",
        "3000m G1 conditions may be out-of-distribution from historical 14 starts.",
        "No real ABM horse-pace/weather/pollinator-style analogue parameters calibrated; no betting ROI claim.",
      ]
    }
    return payload


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--private-source",type=Path,required=True)
    ap.add_argument("--private-payload",type=Path,required=True)
    ap.add_argument("--verify-sha",help="Expected immutable prior SHA; fail if source changed")
    a=ap.parse_args()
    source=json.loads(a.private_source.read_text(encoding="utf8"))
    data=build(source)
    seal=sha256(data)
    if a.verify_sha and seal!=a.verify_sha:
        raise SystemExit("HOLD_SHA_MISMATCH")
    a.private_payload.parent.mkdir(parents=True,exist_ok=True)
    a.private_payload.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({
        "status":data["status"],
        "source_sha256":sha256(source),
        "payload_sha256":seal,
        "models":list(data["scored_models"]),
        "per_model_trio_count":816,
    },ensure_ascii=False))


if __name__=="__main__":main()
