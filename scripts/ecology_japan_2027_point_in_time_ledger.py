#!/usr/bin/env python3
"""Prospective JRA-2027 private prediction commitment and outcome scorer.

Two separate commands:
  freeze: ONLY authorized pre-race entrant, pedigree, published-history,
          and previously frozen coefficient files; no target outcomes.
  score:  only an unmodified privately frozen forecast, its already-published
          aggregate commitment and actual later-published complete results.

All run-level horse IDs, race IDs, forecast rows and result rows stay PRIVATE.
A public manifest contains only counts and cryptographic file digests.
No license, trained coefficient file, 2027 target or future race result is
bundled with this repository. CLI uses current actual clock for freeze; the
injected clock in unit tests is explicitly synthetic.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
from pathlib import Path
import random

from ecology_japan_2027_official_knownon_preflight import (
    ENTRY_REQUIRED, PARENT_REQUIRED, HISTORY_REQUIRED,
    local_jst, read_csv, prepare
)

JST_ZONE = timezone(timedelta(hours=9))
SCHEMA = "JRA_2027_H1_PREDICTION_COMMITMENT_V1"
MODEL_SCHEMA = "JRA_2027_H1_FROZEN_LINEAR_MODEL_V1"
OWN = (
    "own_mean", "log_own_count", "context_mean", "log_context_n",
    "last3", "log_days_since_last", "surface_turf", "distance_km",
    "age", "sex_female", "sex_gelding", "sex_unknown",
    "course_mean", "log_course_count",
    "jockey_mean", "log_jockey_count",
    "trainer_mean", "log_trainer_count",
)
KIN = (
    "sire_kin_history", "dam_kin_history",
    "log_sire_relative_count", "log_dam_relative_count",
)
HISTORICAL_INPUT = HISTORY_REQUIRED + (
    "surface", "distance_m", "course_id", "jockey_id", "trainer_id",
)
FROZEN_2027_START = datetime(2027, 1, 1, tzinfo=JST_ZONE)
FROZEN_2027_END = datetime(2027, 7, 1, tzinfo=JST_ZONE)
MIN_ROWS, MIN_HORSES, MIN_RACING_DAYS = 100, 30, 30


def canonical_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(2 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def finite_number(value) -> float:
    if isinstance(value, bool):
        raise ValueError("HOLD_MODEL_NUMERIC_BOOLEAN")
    try:
        out = float(value)
    except (TypeError, ValueError):
        raise ValueError("HOLD_MODEL_NONNUMERIC") from None
    if not math.isfinite(out):
        raise ValueError("HOLD_MODEL_NONFINITE")
    return out


def validate_models(spec: dict, clock: datetime, first_start: datetime):
    if spec.get("schema") != MODEL_SCHEMA:
        raise ValueError("HOLD_UNFROZEN_MODEL_SCHEMA")
    trained = local_jst(spec.get("training_through_jst"))
    frozen = local_jst(spec.get("model_frozen_at_jst"))
    if not trained < frozen <= clock < first_start:
        raise ValueError("HOLD_TRAINING_OR_MODEL_FROZEN_TIMESTAMP")
    if trained >= FROZEN_2027_START:
        raise ValueError("HOLD_2027_LABELS_IN_MODEL_TRAINING")
    models = spec.get("models")
    if not isinstance(models, dict) or set(models) != {"M1", "M2"}:
        raise ValueError("HOLD_EXPECT_M1_M2_WITH_NO_FAMILY_COMPARABLE")
    for name, allowed in (("M1", OWN), ("M2", OWN + KIN)):
        model = models[name]
        if not isinstance(model, dict) or set(model) != {"intercept", "features"}:
            raise ValueError("HOLD_FROZEN_LINEAR_MODEL_FIELDS")
        finite_number(model["intercept"])
        fmap = model["features"]
        if not isinstance(fmap, dict) or set(fmap) != set(allowed):
            raise ValueError("HOLD_MODEL_NOT_SAME_OWN_COVARIATES_PLUS_KIN")
        for feature in allowed:
            z = fmap[feature]
            if not isinstance(z, dict) or set(z) != {"coefficient", "mean", "sd"}:
                raise ValueError("HOLD_INVALID_FROZEN_SCALER")
            vals = {k: finite_number(v) for k, v in z.items()}
            if vals["sd"] <= 0:
                raise ValueError("HOLD_MODEL_SD_NONPOSITIVE")
            if name == "M2" and feature in OWN:
                z0 = models["M1"]["features"][feature]
                if (vals["mean"] != finite_number(z0["mean"])
                        or vals["sd"] != finite_number(z0["sd"])):
                    raise ValueError("HOLD_MODEL_OWN_FEATURE_SCALER_MISMATCH")
    return True


def linear_predict(model: dict, f: dict) -> float:
    y = finite_number(model["intercept"])
    for name, z in model["features"].items():
        y += (finite_number(z["coefficient"])
              * ((f[name] - finite_number(z["mean"])) / finite_number(z["sd"])))
    return min(1.0, max(0.0, y))


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else .5


def asof_features(entry: dict, entry_raw: dict, parents: dict,
                  history_by_horse: dict, all_history: list[dict],
                  asof: datetime):
    """All dated input must already be known at the single forecast cutoff."""
    if not entry["cutoff"] <= asof < entry["start"]:
        raise ValueError("HOLD_ENTRY_NOT_KNOWN_ASOF_OR_RACE_STARTED")
    horse = entry["horse"]
    race = entry["race"]
    own = [
        h for h in history_by_horse.get(horse, [])
        if h["known"] < asof and h["start"] < asof and h["race"] != race
    ]
    own.sort(key=lambda h: (h["start"], h["known"], h["race"]))
    n = len(own)
    mean = _avg([h["y"] for h in own])
    own_shrunk = .5 + n / (n + 5) * (mean - .5)
    surface = entry["surface"]
    bin_ = entry["distance"] // 400
    context = [h for h in own if h["surface"] == surface
               and h["distance"] // 400 == bin_]
    cn = len(context)
    context_shrunk = .5 + cn / (cn + 3) * (_avg([h["y"] for h in context]) - .5)
    recent = _avg([h["y"] for h in own[-3:]])
    if own:
        days = min(3650., max(0., (asof-own[-1]["start"]).total_seconds()/86400.))
    else:
        days = 3650.
    try:
        age = int(entry_raw["age"])
    except (ValueError, TypeError):
        raise ValueError("HOLD_INVALID_ENTERED_AGE") from None
    if not 2 <= age <= 20:
        raise ValueError("HOLD_INVALID_ENTERED_AGE")
    sex = entry_raw["sex"]
    if sex not in ("M", "F", "G", "U"):
        raise ValueError("HOLD_INVALID_PRE_RACE_SEX_CODE")
    f = {
        "own_mean": own_shrunk,
        "log_own_count": math.log1p(n),
        "context_mean": context_shrunk,
        "log_context_n": math.log1p(cn),
        "last3": recent,
        "log_days_since_last": math.log1p(days),
        "surface_turf": float(surface=="turf"),
        "distance_km": entry["distance"] / 1000.,
        "age": float(age),
        "sex_female": float(sex=="F"),
        "sex_gelding": float(sex=="G"),
        "sex_unknown": float(sex=="U"),
    }
    # Competitor-adjusted CONTEXT without using parent identities: pretarget
    # prior JRA course, jockey and trainer records from the same ID namespace.
    # Absent category IDs never create artificial shared groups.
    for field, candidate in (
        ("course", entry_raw["course_id"]),
        ("jockey", entry_raw["jockey_id"]),
        ("trainer", entry_raw["trainer_id"]),
    ):
        values=[h["y"] for h in all_history
                if candidate and h[field+"_id"] == candidate
                and h["known"] < asof and h["start"] < asof
                and h["race"] != race]
        n_group=len(values)
        f[field+"_mean"] = .5 + n_group/(n_group+5)*(_avg(values)-.5)
        f["log_"+field+"_count"] = math.log1p(n_group)
    support = Counter()
    support["own_history_known"] += bool(n)
    support["own_races_prior_to_cutoff"] += n

    for field, label in (("sire", "sire"), ("dam", "dam")):
        parent_id = entry[field]
        relative_means = []
        if parent_id:
            for rel, (sire, dam, parent_known) in parents.items():
                if rel == horse or parent_known >= asof:
                    continue
                matched = (sire == parent_id if field=="sire" else dam == parent_id)
                if not matched:
                    continue
                hh = [
                    h["y"] for h in history_by_horse.get(rel, [])
                    if h["known"] < asof and h["start"] < asof
                    and h["race"] != race
                    and h["surface"] == surface
                    and h["distance"] // 400 == bin_
                ]
                if hh:
                    relative_means.append(_avg(hh))
        n_peer = len(relative_means)
        f[label+"_kin_history"] = ((5/(n+5))
                                  * sum(m - .5 for m in relative_means)
                                  / (8+n_peer))
        f["log_"+label+"_relative_count"] = math.log1p(n_peer)
        support[label+"_other_horse_history_known"] += bool(n_peer)
        support[label+"_other_horse_count"] += n_peer
    if not all(math.isfinite(z) for z in f.values()):
        raise ValueError("HOLD_NONFINITE_PRE_RACE_FEATURE")
    return f, support


def _history_with_conditions(raw_history: list[dict], prepared: list[dict]):
    out = defaultdict(list)
    if len(raw_history) != len(prepared):
        raise ValueError("HOLD_HISTORY_PREPARED_ROW_COUNT")
    for raw, row in zip(raw_history, prepared):
        if raw["surface"] not in ("turf", "dirt"):
            raise ValueError("HOLD_HISTORY_SURFACE_UNVERIFIED")
        try:
            distance = int(raw["distance_m"])
        except (TypeError, ValueError):
            raise ValueError("HOLD_HISTORY_DISTANCE_UNVERIFIED") from None
        if not 600 <= distance <= 4000:
            raise ValueError("HOLD_HISTORY_DISTANCE_UNVERIFIED")
        if row["start"] >= row["known"]:
            # Equal times are not reliable published results.
            raise ValueError("HOLD_RACE_RESULT_PUBLICATION_NOT_AFTER_RACE")
        if any(not raw[field] for field in ("course_id","jockey_id","trainer_id")):
            raise ValueError("HOLD_HISTORIC_CONDITION_OR_JOCKEY_TRAINER_UNCERTIFIED")
        out[row["horse"]].append(dict(
            row,surface=raw["surface"],distance=distance,
            course_id=raw["course_id"],jockey_id=raw["jockey_id"],
            trainer_id=raw["trainer_id"]))
    return out


def freeze(entries: list[dict], pedigree: list[dict], history: list[dict],
           model: dict, *, asof: datetime, clock: datetime,
           source_sha: dict[str,str]):
    """Returns PRIVATE forecast object and PUBLIC aggregate-only commitment."""
    if asof.utcoffset() != timedelta(hours=9) or clock.tzinfo is None:
        raise ValueError("HOLD_ASOF_OR_REAL_CLOCK_WITHOUT_EXPLICIT_TIMEZONE")
    e, parents, hist = prepare(entries,pedigree,history)
    start = min(row["start"] for row in e)
    if not asof <= clock < start:
        raise ValueError("HOLD_NOT_ACTUALLY_FROZEN_BEFORE_FIRST_RACE")
    for row in e:
        if row["cutoff"] > asof:
            raise ValueError("HOLD_ENTRY_NOT_PUBLISHED_AT_ASOF")
        if parents[row["horse"]][2] >= asof:
            raise ValueError("HOLD_PARENT_MASTER_NOT_PUBLISHED_ASOF")
    for h in hist:
        if h["known"] >= asof:
            raise ValueError("HOLD_HISTORICAL_FILE_HAS_POST_ASOF_RESULT")
        if h["start"] >= h["known"]:
            raise ValueError("HOLD_HISTORICAL_PUBLICATION_NOT_AFTER_START")
    validate_models(model, clock, start)
    by_horse = _history_with_conditions(history,hist)
    all_hist = [one for rows in by_horse.values() for one in rows]
    raw_entry = {(x["race_id"],x["horse_id"]):x for x in entries}
    if len(raw_entry) != len(e):
        raise ValueError("HOLD_PRIVATE_FORECAST_DUPLICATE_ENTRY")
    predictions=[]
    supports=Counter()
    for row in sorted(e,key=lambda r:(r["start"],r["race"],r["horse"])):
        feature, support = asof_features(
            row,raw_entry[(row["race"],row["horse"])],parents,by_horse,
            all_hist,asof
        )
        supports.update(support)
        p1=linear_predict(model["models"]["M1"],feature)
        p2=linear_predict(model["models"]["M2"],feature)
        predictions.append({
            "race_id":row["race"],
            "horse_id":row["horse"],
            "race_start_at_jst":row["start"].isoformat(),
            "M0":0.5,"M1":p1,"M2":p2,
        })
    private={
        "schema":SCHEMA,
        "private_horse_level_predictions":True,
        "target_outcomes_included":False,
        "asof_at_jst":asof.isoformat(),
        "frozen_at_utc":clock.astimezone(timezone.utc).isoformat(),
        "model_spec_sha256":source_sha["model"],
        "predictions":predictions,
    }
    private_bytes=canonical_bytes(private)
    manifest={
        "schema":SCHEMA,
        "status":"PRIVATE_PRE_RACE_FORECAST_COMMITTED_UNSCORED",
        "target":"JRA_2027_JAN_JUN_FLAT_ONLY",
        "asof_at_jst":asof.isoformat(),
        "frozen_at_utc":clock.astimezone(timezone.utc).isoformat(),
        "earliest_target_start_at_jst":start.isoformat(),
        "races":len({p["race_id"] for p in predictions}),
        "starts":len(predictions),
        "unique_horses":len({p["horse_id"] for p in predictions}),
        "input_SHA256":dict(source_sha),
        "private_prediction_file_SHA256":digest_bytes(private_bytes),
        "pretarget_support_aggregates":dict(supports),
        "no_2027_target_results_used":True,
        "no_horse_or_race_IDs_in_public_manifest":True,
        "licensed_provider_approval_independently_checked":False,
        "public_git_commit_timestamp_required_before_racing":True,
        "local_timestamp_and_digest_alone_NOT_trusted_external_proof":True,
        "no_genetic_causation_or_profit_inferred":True,
    }
    return private, manifest


def _quantile(values, q):
    v = sorted(values)
    i = (len(v)-1)*q
    lo,hi = math.floor(i),math.ceil(i)
    return v[lo] + (v[hi]-v[lo])*(i-lo)


def _weighted_metrics(rows: list[dict]):
    occurrences=Counter(row["horse_id"] for row in rows)
    sq=[0.,0.,0.]
    weight_sum=0.
    for row in rows:
        w=1/occurrences[row["horse_id"]]
        weight_sum+=w
        for i,k in enumerate(("M0","M1","M2")):
            sq[i]+=w*(row["y"]-row[k])**2
    rms=[math.sqrt(v/weight_sum) for v in sq]
    return dict(zip(("M0","M1","M2"),rms))


def _bootstrap(rows, by, B=399):
    group=defaultdict(list)
    for r in rows:
        k=r["horse_id"] if by=="horse" else r["race_start_at_jst"][:10]
        group[k].append(r)
    if len(group)<20:
        return {"status":"HOLD_FEWER_THAN_20_CLUSTERS",
                "cluster_count":len(group)}
    # Original-sample equal-horse weights, held fixed through one-way
    # cluster-resampling. Sensitivity only, not joint multiway inference.
    freq=Counter(r["horse_id"] for r in rows)
    parts=[]
    for g in group.values():
        sq=[0.,0.,0.]
        wsum=0.
        for r in g:
            w=1/freq[r["horse_id"]]
            wsum+=w
            for i,k in enumerate(("M0","M1","M2")):
                sq[i]+=w*(r["y"]-r[k])**2
        parts.append((*sq,wsum))
    rng=random.Random(20270101)
    draws=[]
    n=len(parts)
    for _ in range(B):
        sums=[0.,0.,0.,0.]
        for _ in range(n):
            k=parts[rng.randrange(n)]
            for i in range(4):
                sums[i]+=k[i]
        a,b,c=[math.sqrt(sums[i]/sums[3]) for i in range(3)]
        draws.append((b-c,a-c))
    return {
        "cluster_count":n,"bootstrap_draws":B,
        "CI95_M1_minus_M2":[_quantile([x[0] for x in draws],q)
                            for q in (.025,.975)],
        "CI95_M0_minus_M2":[_quantile([x[1] for x in draws],q)
                            for q in (.025,.975)],
        "one_way_conditional_resampling_only":True,
    }


def score(private:dict, manifest:dict, final_rows:list[dict]):
    """Results are separate inputs; no re-fitting or post-outcome adjustments."""
    if private.get("schema")!=SCHEMA or manifest.get("schema")!=SCHEMA:
        raise ValueError("HOLD_FORECAST_MANIFEST_SCHEMA")
    if manifest.get("status")!="PRIVATE_PRE_RACE_FORECAST_COMMITTED_UNSCORED":
        raise ValueError("HOLD_FROZEN_MANIFEST_STATUS")
    if digest_bytes(canonical_bytes(private))!=manifest.get(
        "private_prediction_file_SHA256"
    ):
        raise ValueError("HOLD_PRIVATE_FORECAST_DIGEST_MISMATCH")
    if private.get("model_spec_sha256")!=manifest["input_SHA256"]["model"]:
        raise ValueError("HOLD_MODEL_HASH_NOT_SAME_AS_FROZEN_COMMITMENT")
    if (private.get("frozen_at_utc")!=manifest.get("frozen_at_utc")
            or private.get("asof_at_jst")!=manifest.get("asof_at_jst")
            or private.get("target_outcomes_included") is not False):
        raise ValueError("HOLD_FORECAST_MANIFEST_PARITY")
    frozen_at=datetime.fromisoformat(private["frozen_at_utc"])
    asof=local_jst(private["asof_at_jst"])
    preds=private["predictions"]
    if len(preds)!=manifest["starts"]:
        raise ValueError("HOLD_FORECAST_STARTS_CHANGED")
    by_pair={}
    races=defaultdict(dict)
    for p in preds:
        k=(p["race_id"],p["horse_id"])
        if k in by_pair:
            raise ValueError("HOLD_DUPLICATE_FROZEN_FORECAST_HORSE")
        start=local_jst(p["race_start_at_jst"])
        if not asof<=frozen_at<start:
            raise ValueError("HOLD_FORECAST_TIMESTAMP_NOT_BEFORE_RACE")
        if not all(0<=finite_number(p[model])<=1 for model in ("M0","M1","M2")):
            raise ValueError("HOLD_PROBABILITY_RANGE_FOR_RANK_PREDICTION")
        by_pair[k]=p
        races[p["race_id"]][p["horse_id"]]=p
    if (len(races)!=manifest["races"]
            or len({p["horse_id"] for p in preds})!=manifest["unique_horses"]):
        raise ValueError("HOLD_PUBLIC_FORECAST_COUNTS_PARITY")
    results=defaultdict(dict)
    for row in final_rows:
        key=(row["race_id"],row["horse_id"])
        if key not in by_pair:
            raise ValueError("HOLD_OUTCOME_NOT_IN_FROZEN_FORECAST")
        if row["horse_id"] in results[row["race_id"]]:
            raise ValueError("HOLD_DUPLICATE_OFFICIAL_RESULT")
        p=by_pair[key]
        start=local_jst(row["race_start_at_jst"])
        known=local_jst(row["result_known_at_jst"])
        if start != local_jst(p["race_start_at_jst"]) or known<=start:
            raise ValueError("HOLD_RESULT_START_OR_PUBLICATION_CONFLICT")
        if known<=frozen_at:
            raise ValueError("HOLD_RESULT_KNOWN_BEFORE_FORECAST_FROZEN")
        results[row["race_id"]][row["horse_id"]]=row
    complete=[]
    quality=Counter()
    monthly=defaultdict(list)
    for race,pdict in races.items():
        rr=results.get(race,{})
        n=len(pdict)
        if len(rr)!=n:
            quality["pending_or_partially_reported_races"]+=1
            continue
        try:
            ranks=[int(rr[h]["finish_rank"]) for h in pdict]
            sizes=[int(rr[h]["classified_field_size"]) for h in pdict]
        except (KeyError,ValueError,TypeError):
            quality["invalid_or_unclassified_races"]+=1
            continue
        if (any(rr[h]["finish_status"]!="CLASSIFIED" for h in pdict)
                or sorted(ranks)!=list(range(1,n+1))
                or any(sz!=n for sz in sizes)):
            quality["incomplete_tied_dnf_or_denominator_races"]+=1
            continue
        quality["fully_classified_races"]+=1
        for h,rank in zip(pdict,ranks):
            p=pdict[h]
            one=dict(p,y=(rank-1)/(n-1))
            complete.append(one)
            monthly[p["race_start_at_jst"][:7]].append(one)
    if not complete:
        return {
            "status":"HOLD_NO_FULLY_PUBLISHED_COMPLETE_RACES",
            "source_manifest_private_prediction_sha":manifest[
                "private_prediction_file_SHA256"
            ],"race_quality_counts":dict(quality),
            "no_individual_results_exported":True,
        }
    scores=_weighted_metrics(complete)
    distinct_horses=len({row["horse_id"] for row in complete})
    dates=len({row["race_start_at_jst"][:10] for row in complete})
    support=(len(complete)>=MIN_ROWS and distinct_horses>=MIN_HORSES
             and dates>=MIN_RACING_DAYS)
    monthly_scores={}
    for month,v in sorted(monthly.items()):
        if len(v)<30 or len({r["race_id"] for r in v})<10:
            monthly_scores[month]={
                "status":"HOLD_MONTHLY_LOW_SUPPORT",
                "starts":len(v),"races":len({r["race_id"] for r in v}),
            }
        else:
            monthly_scores[month]={"status":"DESCRIPTIVE",
                                   "starts":len(v),"scores":_weighted_metrics(v)}
    return {
        "status":"PROVISIONAL_PROSPECTIVE_2027_AGGREGATE_NOT_INDEPENDENTLY_ATTESTED"
            if support else "HOLD_2027_AGGREGATE_LOW_SUPPORT",
        "frozen_prediction_SHA256":manifest["private_prediction_file_SHA256"],
        "frozen_model_SHA256":manifest["input_SHA256"]["model"],
        "forecast_asof_jst":manifest["asof_at_jst"],
        "forecast_created_at_utc":manifest["frozen_at_utc"],
        "races_scored":quality["fully_classified_races"],
        "races_total_frozen":len(races),
        "starts_scored":len(complete),
        "unique_horses_scored":distinct_horses,
        "calendar_days_scored":dates,
        "race_quality_counts":dict(quality),
        "RMSE_equal_horse_weight":scores,
        "gain_M1_minus_M2":scores["M1"]-scores["M2"],
        "gain_M0_minus_M2":scores["M0"]-scores["M2"],
        "conditional_operational_gain":bool(support and
                scores["M2"]<scores["M1"] and scores["M2"]<scores["M0"]),
        "horse_cluster_bootstrap":_bootstrap(complete,"horse"),
        "race_day_cluster_bootstrap":_bootstrap(complete,"race_day"),
        "monthly_descriptive_scores":monthly_scores,
        "cannot_prove_model_or_manifest_pre_race_Git_commit":True,
        "official_provider_rights_and_IDs_must_be_independently_verified":True,
        "causal_genetic_or_betting_claims_NOT_licensed":True,
        "no_individual_results_exported":True,
    }


def _load_json(path:Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _private_destination(path:Path):
    # Don't accidentally commit licensed individual prediction data to a
    # working repository. The manifest contains only SHA and counts.
    if path.resolve().is_relative_to(Path.cwd().resolve()):
        raise ValueError("HOLD_PRIVATE_FORECAST_PATH_INSIDE_WORKING_REPOSITORY")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest="command",required=True)
    f=sub.add_parser("freeze",help="Private forecast WITHOUT 2027 outcomes")
    f.add_argument("--entries",type=Path,required=True)
    f.add_argument("--parents",type=Path,required=True)
    f.add_argument("--history",type=Path,required=True)
    f.add_argument("--frozen-model",type=Path,required=True)
    f.add_argument("--asof-at-jst",required=True)
    f.add_argument("--private-forecast",type=Path,required=True)
    f.add_argument("--public-commitment",type=Path,required=True)
    s=sub.add_parser("score",help="Read sealed private forecasts + 2027 results")
    s.add_argument("--private-forecast",type=Path,required=True)
    s.add_argument("--public-commitment",type=Path,required=True)
    s.add_argument("--later-results",type=Path,required=True)
    s.add_argument("--aggregate-out",type=Path,required=True)
    args=ap.parse_args()
    if args.command=="freeze":
        _private_destination(args.private_forecast)
        files={"entries":args.entries,"parents":args.parents,
               "history":args.history,"model":args.frozen_model}
        source_sha={k:digest_file(v) for k,v in files.items()}
        private,manifest=freeze(
            read_csv(args.entries,ENTRY_REQUIRED),
            read_csv(args.parents,PARENT_REQUIRED),
            read_csv(args.history,HISTORICAL_INPUT),
            _load_json(args.frozen_model),
            asof=local_jst(args.asof_at_jst),
            clock=datetime.now(timezone.utc),
            source_sha=source_sha,
        )
        args.private_forecast.parent.mkdir(parents=True,exist_ok=True)
        args.private_forecast.write_bytes(canonical_bytes(private))
        args.private_forecast.chmod(0o600)
        args.public_commitment.parent.mkdir(parents=True,exist_ok=True)
        args.public_commitment.write_bytes(canonical_bytes(manifest))
        print(json.dumps(manifest,ensure_ascii=False,indent=2))
    else:
        out=score(_load_json(args.private_forecast),
                  _load_json(args.public_commitment),
                  read_csv(args.later_results,HISTORY_REQUIRED))
        args.aggregate_out.parent.mkdir(parents=True,exist_ok=True)
        args.aggregate_out.write_bytes(canonical_bytes(out))
        print(json.dumps(out,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
