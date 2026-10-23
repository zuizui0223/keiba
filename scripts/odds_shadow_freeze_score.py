#!/usr/bin/env python3
"""Two-phase, source-time-gated future WIN/WIDE market shadow freeze and score.

This tool CAN prepare a prospective SHADOW forecast if used before
the race with independent remote timestamp attestation. It CANNOT
prove this occurred merely from self-reported local timestamps or
canonical SHA hashes. The output never claims a formal prospective
holdout unless independently verified by an external timestamp record.
This is separate from v3.1 / 20-race formal holdout.

The source input is a PRIVATE already-authorized normalized JSON
snapshot, NOT JRA-VAN binary and NOT a downloader. Do not put provider
raw odds or restricted original price rows into public GitHub.

In a pre-result session:
  python scripts/odds_shadow_freeze_score.py freeze \
    --source private/authorized_snapshot.json --output private/freeze.json

After independently obtaining the official result:
  python scripts/odds_shadow_freeze_score.py score \
    --freeze private/freeze.json --result private/result.json \
    --output private/score.json

Safe synthetic demonstration (never a real horse-race validation):
  python scripts/odds_shadow_freeze_score.py demo \
    --freeze-out tmp/synthetic-market-freeze.json \
    --score-out tmp/synthetic-market-score.json
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path
from urllib.parse import urlparse

from odds_coherent_hierarchy_rank_bridge import joint_rank_probability
from odds_cross_pool_global_async import relative_pair_indices
from odds_pair_hierarchy_decomposition import complete_graph_decompose

SOURCE_SCHEMA = "KEIBA_PRIVATE_WIN_WIDE_SNAPSHOT_V1"
FREEZE_SCHEMA = "KEIBA_UNATTESTED_WIN_WIDE_SHADOW_FREEZE_V1"
OFFICIAL_SCHEMA = "KEIBA_INDEPENDENT_OFFICIAL_TOP3_V1"
STATUS_SHADOW = "LOCAL_SHADOW_NOT_FORMAL_UNLESS_REMOTE_PRESTART_ATTESTED"
SCORING_STATUS = "SHADOW_POSTRACE_SCORE_NOT_V31_OR_CONFIRMED_PROSPECTIVE"


def _aware(ts):
    if not isinstance(ts, str):
        raise ValueError("HOLD_TIMESTAMP_NOT_STRING")
    dt = datetime.fromisoformat(ts)
    if dt.utcoffset() is None:
        raise ValueError("HOLD_NAIVE_CLOCK_NOT_ALLOWED")
    return dt


def _canonical(value) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",",":"),
        allow_nan=False).encode("utf-8")


def _seal(value) -> str:
    return sha256(_canonical(value)).hexdigest()


def _normalized_odds(quoted: dict):
    if not isinstance(quoted, dict) or not 5 <= len(quoted) <= 30:
        raise ValueError("HOLD_INCOMPLETE_FULL_WIN_ROSTER")
    odds = {}
    for k, v in quoted.items():
        if (not isinstance(k, str) or not k.isdecimal()
                or str(int(k)) != k or int(k) <= 0
                or type(v) not in (float, int)
                or not math.isfinite(v) or v <= 1):
            raise ValueError("HOLD_INVALID_WIN_QUOTE")
        odds[int(k)] = float(v)
    if len(odds) != len(quoted):
        raise ValueError("HOLD_DUPLICATE_HORSE_NUMBER")
    return odds


def _wide_prices(rows, ids):
    out = {}
    if not isinstance(rows, list):
        raise ValueError("HOLD_MISSING_FULL_WIDE_ROWS")
    for r in rows:
        pair = r["selection"]
        if (not isinstance(pair, list) or len(pair) != 2
                or any(type(i) is not int or i not in ids for i in pair)
                or pair[0] == pair[1]):
            raise ValueError("HOLD_WIDE_PAIR_SELECTION_INVALID")
        k = tuple(sorted(pair))
        low, high = r["odds_low"], r["odds_high"]
        if (k in out or type(low) not in (float, int)
                or type(high) not in (float, int)
                or not math.isfinite(low) or not math.isfinite(high)
                or not 1 < low <= high):
            raise ValueError("HOLD_INVALID_OR_DUPLICATE_WIDE_PRICE")
        out[k] = float(low)
    if set(out) != set(combinations(sorted(ids),2)):
        raise ValueError("HOLD_NOT_ALL_PAIRS_AVAILABLE")
    return out


def _models(models):
    if not isinstance(models, list) or len(models) != 2:
        raise ValueError("HOLD_TWO_FIXED_MODEL_SPECIFICATIONS_REQUIRED")
    names = [m.get("name") for m in models]
    if names != ["win_PL_baseline", "predeclared_hierarchy"]:
        raise ValueError("HOLD_MODEL_NAMES_OR_ORDER_CHANGED")
    for model in models:
        if (type(model.get("beta_horse")) not in (int,float)
                or type(model.get("beta_pair")) not in (int,float)
                or not math.isfinite(model["beta_horse"])
                or not math.isfinite(model["beta_pair"])
                or max(abs(model["beta_horse"]),abs(model["beta_pair"])) > 2):
            raise ValueError("HOLD_NONFINITE_OR_UNBOUNDED_MODEL_COEFFICIENTS")
    if (models[0]["beta_horse"] != 0
            or models[0]["beta_pair"] != 0):
        raise ValueError("HOLD_BASELINE_MUST_BE_EXACT_MARKET_PL")
    return models


def _market_clock(snapshot, source, *, market):
    if (snapshot.get("market") != market
            or snapshot.get("source_clock_verified") is not True
            or snapshot.get("provider") != source):
        raise ValueError("HOLD_MISMATCHED_MARKET_PROVENANCE")
    published = _aware(snapshot.get("source_updated_at_jst"))
    received = _aware(snapshot.get("received_at_jst"))
    if published > received:
        raise ValueError("HOLD_MARKET_PUBLISHED_AFTER_RECEIPT")
    return published, received


def _validate_snapshot(doc):
    if doc.get("schema") != SOURCE_SCHEMA:
        raise ValueError("HOLD_WRONG_PRIVATE_SOURCE_SCHEMA")
    provenance = doc.get("provenance")
    if provenance not in ("synthetic","authorized_local_normalized_market"):
        raise ValueError("HOLD_SOURCE_OR_LICENSE_STATUS_UNKNOWN")
    if doc.get("raw_provider_rows_redistributable") is not False:
        raise ValueError("HOLD_PUBLIC_RAW_ODDS_EXPORT_NOT_SUPPORTED")
    if (provenance != "synthetic"
            and doc.get("operator_confirmed_research_rights") is not True):
        raise ValueError("HOLD_LOCAL_RESEARCH_RIGHTS_NOT_ATTESTED")
    race = doc.get("race_id")
    if not isinstance(race,str) or not race:
        raise ValueError("HOLD_UNKNOWN_RACE_ID")
    provider=doc.get("provider")
    if not isinstance(provider,str) or not provider:
        raise ValueError("HOLD_MISSING_MARKET_PROVIDER")
    start = _aware(doc.get("scheduled_post_jst"))
    models = _models(doc.get("models"))
    lock = _aware(doc.get("coefficient_lock_at_jst"))
    freeze = _aware(doc.get("prediction_recorded_at_jst"))
    win_source = doc["win"]
    wide_source = doc["wide"]
    tw,rw = _market_clock(win_source, provider, market="win")
    tp,rp = _market_clock(wide_source, provider, market="wide")
    # These must be independently captured BEFORE locking the forecast;
    # both may come from separate pages with only minute-granularity clocks.
    if (not lock <= min(tw,tp)
            or not max(rw,rp) <= freeze
            or not freeze < start-timedelta(minutes=10)
            or tw != tp):
        raise ValueError("HOLD_NOT_EARLY_ENOUGH_OR_NOT_SAME_UPDATE_MINUTE")
    if doc.get("trained_last_official_result_verified_at_jst") is not None:
        available = _aware(doc["trained_last_official_result_verified_at_jst"])
        if not available < lock:
            raise ValueError("HOLD_TRAINING_RESULT_KNOWN_AFTER_MODEL_COEFFICIENT_LOCK")
    odds = _normalized_odds(win_source["odds_by_horse_number"])
    wide = _wide_prices(wide_source["pairs"], set(odds))
    if len(wide) != len(odds)*(len(odds)-1)//2:
        raise ValueError("HOLD_INCOMPLETE_WIDE_GRID")
    return {
        "provenance":provenance,"race":race,"start":start,
        "freeze":freeze,"lock":lock,"market_updated":tw,"last_received":max(rw,rp),
        "provider":provider,"odds":odds,"wide":wide,"models":models,
    }


def _compressed_probabilities(fitted):
    ids=fitted["horse_numbers"]
    return {
        "win": [{"n":i,"p":fitted["win"][i]} for i in ids],
        "top3": [{"n":i,"p":fitted["top3"][i]} for i in ids],
        "trio": [{"numbers":list(k),"p":v}
                 for k,v in fitted["unordered_top3_trio"].items()],
    }


def build_freeze(source, *, source_sha256="no_external_file_demo"):
    """Hash protects local byte equality, not historical publication time."""
    x = _validate_snapshot(source)
    residual=relative_pair_indices({
        "label":"source_prestart", "win":x["odds"],"wide":x["wide"]})
    graph=complete_graph_decompose(residual["pair_residual"])
    if graph["status"]!="COMPLETE_GRAPH_HORSE_ADDITIVE_DESCRIPTIVE_DECOMPOSITION":
        raise ValueError("HOLD_NO_COMPLETE_GRAPH")
    candidates={}
    for model in x["models"]:
        predicted=joint_rank_probability(
            x["odds"],graph["node_effects"],graph["pair_model_residuals"],
            beta_horse=model["beta_horse"],beta_pair=model["beta_pair"])
        candidates[model["name"]]=_compressed_probabilities(predicted)
    payload = {
        "status":STATUS_SHADOW, "schema":FREEZE_SCHEMA,
        "race_id":x["race"], "scheduled_post_jst":x["start"].isoformat(),
        "local_prediction_recorded_at_jst":x["freeze"].isoformat(),
        "model_coefficient_lock_at_jst":x["lock"].isoformat(),
        "source_quote_updated_at_jst":x["market_updated"].isoformat(),
        "last_source_received_at_jst":x["last_received"].isoformat(),
        "source_raw_sha256_local_only":source_sha256,
        "source_provenance":x["provenance"],
        "source_market_provider":x["provider"],
        "confidence_attestation": "LOCAL_TIME_AND_SHA_ONLY_NOT_TRUSTED_REMOTE_PROOF",
        "all_price_features_available_before_freeze":True,
        "coefficients_frozen_before_current_source_market_update":True,
        "source_wide_pair_events_overlap_and_market_index_is_not_true_probability":True,
        "predeclared_primary_metric":"win_categorical_log_loss",
        "predeclared_secondary_metric":"top3_binary_brier_mean_horse",
        "predeclared_exploratory_metric":"trio_categorical_log_loss",
        "horse_count":len(x["odds"]),
        "model_coefficients":{
            model["name"]: {
                "beta_horse":model["beta_horse"],
                "beta_pair":model["beta_pair"],
            } for model in x["models"]
        },
        "predicted_probabilities":candidates,
        "no_actual_result_loaded":True,
        "v31_frozen_holdout_untouched":True,
    }
    return {"seal_sha256_of_canonical_payload":_seal(payload),
            "payload":payload}


def verify_seal(freeze):
    if not isinstance(freeze,dict) or not isinstance(freeze.get("payload"),dict):
        raise ValueError("HOLD_FREEZE_PAYLOAD_NOT_FOUND")
    payload=freeze["payload"]
    if (payload.get("schema")!=FREEZE_SCHEMA or
            payload.get("status")!=STATUS_SHADOW or
            _seal(payload)!=freeze.get("seal_sha256_of_canonical_payload")):
        raise ValueError("HOLD_FREEZE_DIGEST_OR_SCHEMA_CHANGED")
    return payload


def _check_probs(probs, actual):
    ids=[r["n"] for r in probs["win"]]
    top_ids=[r["n"] for r in probs["top3"]]
    if (len(ids)<5 or ids!=sorted(set(ids)) or ids!=top_ids
            or not set(actual).issubset(ids)):
        raise ValueError("HOLD_PROBABILITY_RUNNER_ROSTER_MISMATCH")
    predwin={r["n"]:r["p"] for r in probs["win"]}
    predtop={r["n"]:r["p"] for r in probs["top3"]}
    ptrio={}
    for r in probs["trio"]:
        key=tuple(r["numbers"])
        if (len(key)!=3 or key!=tuple(sorted(set(key)))
                or not set(key).issubset(ids) or key in ptrio):
            raise ValueError("HOLD_INVALID_TRIO_PROBABILITY_KEY")
        ptrio[key]=r["p"]
    if set(ptrio)!=set(combinations(ids,3)):
        raise ValueError("HOLD_TRIO_PROBABILITIES_INCOMPLETE")
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<0
           for v in [*predwin.values(),*predtop.values(),*ptrio.values()]):
        raise ValueError("HOLD_INVALID_NONFINITE_PROBABILITY")
    if (not math.isclose(sum(predwin.values()),1,abs_tol=1e-8)
            or not math.isclose(sum(predtop.values()),3,abs_tol=1e-8)
            or not math.isclose(sum(ptrio.values()),1,abs_tol=1e-8)):
        raise ValueError("HOLD_INCOHERENT_PROBABILITY_MASS")
    for i in ids:
        if not math.isclose(
                sum(v for k,v in ptrio.items() if i in k),
                predtop[i],abs_tol=1e-8):
            raise ValueError("HOLD_TRIO_TOP3_MARGINAL_DISAGREES")
        if predwin[i] > predtop[i]+1e-8:
            raise ValueError("HOLD_WIN_GREATER_THAN_TOP3")
    return predwin,predtop,ptrio


def score_sealed(freeze, official):
    p=verify_seal(freeze)
    if official.get("schema")!=OFFICIAL_SCHEMA:
        raise ValueError("HOLD_OFFICIAL_RESULT_SCHEMA")
    if official.get("race_id")!=p["race_id"]:
        raise ValueError("HOLD_WRONG_OFFICIAL_RACE")
    if (p["source_provenance"]=="synthetic") != (
            official.get("provenance")=="synthetic"):
        raise ValueError("HOLD_REAL_AND_SYNTHETIC_RESULT_MIX")
    if official.get("provenance")=="synthetic":
        if official.get("source_type")!="FICTITIOUS_OUTCOME":
            raise ValueError("HOLD_FAKE_OUTCOME_SOURCE")
    else:
        url=urlparse(official.get("official_results_url",""))
        if (official.get("source_type")!="JRA_official"
                or url.scheme!="https"
                or url.hostname not in
                   ("www.jra.go.jp","app.jra.jp","jra.jp")):
            raise ValueError("HOLD_OFFICIAL_URL_UNVERIFIED")
    post = _aware(p["scheduled_post_jst"])
    freeze_clock=_aware(p["local_prediction_recorded_at_jst"])
    verified=_aware(official.get("independently_verified_at_jst"))
    if not (freeze_clock < post < verified):
        raise ValueError("HOLD_INVALID_PRESTART_FREEZE_OR_POSTRACE_VERIFY")
    podium=official.get("top3_horse_numbers")
    if (not isinstance(podium,list) or len(podium)!=3
            or len(set(podium))!=3 or
            any(type(x) is not int for x in podium)):
        raise ValueError("HOLD_INVALID_OFFICIAL_PODIUM")
    scores={}
    for label,pred in p["predicted_probabilities"].items():
        win,top,trio=_check_probs(pred,podium)
        reality=set(podium)
        clip=1e-12
        scores[label]={
            "win_categorical_log_loss":-math.log(max(clip,win[podium[0]])),
            "top3_binary_brier_mean_horse":sum(
                (v-(1 if i in reality else 0))**2 for i,v in top.items()
            )/len(top),
            "trio_categorical_log_loss":-math.log(
                max(clip,trio[tuple(sorted(podium))])),
        }
    if set(scores)!={"win_PL_baseline","predeclared_hierarchy"}:
        raise ValueError("HOLD_FIXED_TWO_MODEL_PAIR_CHANGED")
    base=scores["win_PL_baseline"]
    cand=scores["predeclared_hierarchy"]
    keys=("win_categorical_log_loss","top3_binary_brier_mean_horse",
          "trio_categorical_log_loss")
    return {
        "status":SCORING_STATUS,
        "race_id":p["race_id"],
        "source_kind":p["source_provenance"],
        "freeze_payload_sha256":freeze["seal_sha256_of_canonical_payload"],
        "official_result_verified_at_jst":verified.isoformat(),
        "actual_top3_horse_numbers":podium,
        "frozen_models_scores":scores,
        "preselected_hierarchy_minus_PL_lower_is_better":{
            metric:cand[metric]-base[metric] for metric in keys},
        "formal_prospective_status":
            "HOLD_INDEPENDENT_REMOTE_PRESTART_TIMESTAMP_ATTESTATION_NOT_VERIFIED",
        "cannot_append_to_frozen_v31_formal_ledger":True,
        "unverified_local_clock_not_external_evidence":True,
        "real_historical_or_synthetic_performance_not_prospectively_confirmed":True,
    }


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path, value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(
        json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",
        encoding="utf-8")


def synthetic_demo():
    from shuka2026_odds_information_hierarchy import pl_pair_top3_index
    odds={i:2.0+1.2*i for i in range(1,9)}
    model=pl_pair_top3_index(odds)
    wide=[
        {"selection":list(pair), "odds_low":1.1+1/p*0.13,
         "odds_high":1.3+1/p*0.14}
        for pair,p in model.items()
    ]
    src={
        "schema":SOURCE_SCHEMA,
        "provenance":"synthetic",
        "raw_provider_rows_redistributable":False,
        "race_id":"FICTITIOUS-2030-01-01-01",
        "provider":"FICTITIOUS_PROVIDER",
        "scheduled_post_jst":"2030-01-01T14:00:00+09:00",
        "coefficient_lock_at_jst":"2029-12-30T10:00:00+09:00",
        "prediction_recorded_at_jst":"2030-01-01T13:31:00+09:00",
        "trained_last_official_result_verified_at_jst":None,
        "models":[
            {"name":"win_PL_baseline","beta_horse":0.0,"beta_pair":0.0},
            {"name":"predeclared_hierarchy","beta_horse":-0.25,
             "beta_pair":0.25},
        ],
        "win":{
            "market":"win","provider":"FICTITIOUS_PROVIDER",
            "source_clock_verified":True,
            "source_updated_at_jst":"2030-01-01T13:29:00+09:00",
            "received_at_jst":"2030-01-01T13:30:03+09:00",
            "odds_by_horse_number":{str(i):v for i,v in odds.items()},
        },
        "wide":{
            "market":"wide","provider":"FICTITIOUS_PROVIDER",
            "source_clock_verified":True,
            "source_updated_at_jst":"2030-01-01T13:29:00+09:00",
            "received_at_jst":"2030-01-01T13:30:05+09:00",
            "pairs":wide,
        },
    }
    result={
        "schema":OFFICIAL_SCHEMA,
        "race_id":src["race_id"],
        "provenance":"synthetic",
        "source_type":"FICTITIOUS_OUTCOME",
        "independently_verified_at_jst":"2030-01-01T15:00:00+09:00",
        "top3_horse_numbers":[2,5,1],
    }
    return src,result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="mode",required=True)
    f=sub.add_parser("freeze")
    f.add_argument("--source",type=Path,required=True)
    f.add_argument("--output",type=Path,required=True)
    s=sub.add_parser("score")
    s.add_argument("--freeze",type=Path,required=True)
    s.add_argument("--result",type=Path,required=True)
    s.add_argument("--output",type=Path,required=True)
    d=sub.add_parser("demo")
    d.add_argument("--freeze-out",type=Path,required=True)
    d.add_argument("--score-out",type=Path,required=True)
    args=p.parse_args()
    if args.mode=="freeze":
        raw=args.source.read_bytes()
        frozen=build_freeze(json.loads(raw.decode("utf-8")),
                            source_sha256=sha256(raw).hexdigest())
        _write(args.output,frozen)
        print(json.dumps({"status":STATUS_SHADOW,
                          "seal":frozen["seal_sha256_of_canonical_payload"],
                          "external_timestamp_attestation_verified":False}))
    elif args.mode=="score":
        scored=score_sealed(_read(args.freeze),_read(args.result))
        _write(args.output,scored)
        print(json.dumps({
            "status":scored["status"],
            "metric_deltas":scored["preselected_hierarchy_minus_PL_lower_is_better"],
            "formal_prospective_status":scored["formal_prospective_status"]}))
    else:
        source,observed=synthetic_demo()
        frozen=build_freeze(source)
        scored=score_sealed(frozen,observed)
        _write(args.freeze_out,frozen)
        _write(args.score_out,scored)
        print(json.dumps({
            "status":"SYNTHETIC_UNATTESTED_FREEZE_SCORE_DEMO_ONLY",
            "race":scored["race_id"],
            "models":list(scored["frozen_models_scores"]),
            "metric_deltas":scored["preselected_hierarchy_minus_PL_lower_is_better"],
            "external_timestamp_attestation_verified":False,
        }))


if __name__=="__main__":
    main()
