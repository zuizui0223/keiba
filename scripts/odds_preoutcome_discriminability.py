#!/usr/bin/env python3
"""Pre-outcome identifiability audit for a SEALED public two-point WIN model.

Only reads the old immutable PRIVATE probability freeze; NEVER reads
official results, target payouts or any postrace files. No coefficient
learning, re-fitting, feature selection or threshold search.

The uncertainty of a SINGLE race can be described before it occurs:
- TV(P0,P1) and KL(P0||P1) for winning horse and unordered top3 trio.
- Range of realized win-logloss contrasts among all possible winners.
- Baseline model probability mass of winners that would favor M1.
- Expected Top3 Brier contrast if either fully specified ranking
  distribution were the reference. The true data-generating
  distribution is unknown. These are not evidence of calibration.

The true 2026-10-25 Kikka freeze is not checked into the repo; pass
the private file with --freeze from the user's secure environment.
Output is strictly aggregated: no source odds, per-horse probabilities
or any of the 816 underlying trio probabilities are exported.

Run:
 python scripts/odds_preoutcome_discriminability.py \
   --freeze private/prestart_20261025_kikka11_market_only_vs_path_freeze.json \
   --output private/preoutcome-discriminability.json
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json
import math
from pathlib import Path

from odds_public_two_point_freeze import MODELS, verify_freeze

STATUS = "PREOUTCOME_ONLY_FROZEN_MODEL_SEPARATION_NOT_RESULT_OR_VALIDATION"
MEASURES = ("win", "top3", "trio")
BASE = "M0_market_only"
MAIN = "M1_smooth_beta025"
EXPL = "M2_initial_10x_beta025"


def _validated_distributions(p):
    ids = p.get("roster_horse_numbers")
    if (not isinstance(ids,list) or not 5<=len(ids)<=30
            or any(type(i) is not int or i <= 0 for i in ids)
            or ids!=sorted(set(ids))):
        raise ValueError("HOLD_BAD_SEALED_RACE_ROSTER")
    all_trios=set(combinations(ids,3))
    expected_names={model[0] for model in MODELS}
    predictions=p.get("predictions")
    if not isinstance(predictions,dict) or set(predictions)!=expected_names:
        raise ValueError("HOLD_SEALED_MODEL_PROBABILITIES_MISSING")
    out={}
    for name, raw in predictions.items():
        if set(raw)!=set(MEASURES):
            raise ValueError("HOLD_MISSING_FORECAST_EVENT_TYPE")
        win={}
        top={}
        trio={}
        for entry in raw["win"]:
            k=entry.get("number")
            if k in win or type(k) is not int:raise ValueError("HOLD_DUPLICATE_WIN_HORSE")
            win[k]=entry.get("p")
        for entry in raw["top3"]:
            k=entry.get("number")
            if k in top or type(k) is not int:raise ValueError("HOLD_DUPLICATE_TOP3_HORSE")
            top[k]=entry.get("p")
        for entry in raw["trio"]:
            k=entry.get("horse_numbers")
            if not isinstance(k,list):
                raise ValueError("HOLD_INVALID_TRIO_PAIR")
            key=tuple(k)
            if key in trio:raise ValueError("HOLD_DUPLICATE_TRIO")
            trio[key]=entry.get("p")
        if set(win)!=set(ids) or set(top)!=set(ids) or set(trio)!=all_trios:
            raise ValueError("HOLD_INCOMPLETE_FROZEN_EVENT_UNIVERSE")
        if any(type(q) not in (int,float) or not math.isfinite(q)
               or not 0<q<=1 for q in
               list(win.values())+list(top.values())+list(trio.values())):
            raise ValueError("HOLD_NONPOSITIVE_OR_NONFINITE_PROBABILITY")
        if (not math.isclose(sum(win.values()),1,abs_tol=1e-9)
                or not math.isclose(sum(top.values()),3,abs_tol=1e-9)
                or not math.isclose(sum(trio.values()),1,abs_tol=1e-9)):
            raise ValueError("HOLD_INCOHERENT_FROZEN_PROBABILITY_MASS")
        for i in ids:
            if not math.isclose(sum(q for key,q in trio.items() if i in key),
                                top[i],abs_tol=1e-8):
                raise ValueError("HOLD_TOP3_AND_TRIO_MARGINALS_DISAGREE")
            if win[i]>top[i]+1e-10:
                raise ValueError("HOLD_WIN_MASS_EXCEEDS_TOP3_INCLUSION")
        out[name]={"win":win,"top3":top,"trio":trio}
    return out


def _tv(a,b):
    if set(a)!=set(b):raise ValueError("HOLD_DISTRIBUTION_SUPPORT_MISMATCH")
    return .5*sum(abs(a[k]-b[k]) for k in a)


def _kl(a,b):
    if set(a)!=set(b):raise ValueError("HOLD_DISTRIBUTION_SUPPORT_MISMATCH")
    return sum(a[k]*math.log(a[k]/b[k]) for k in a)


def _two_point_contrast(baseline, model):
    win0,win1 = baseline["win"],model["win"]
    trio0,trio1 = baseline["trio"],model["trio"]
    top0,top1=baseline["top3"],model["top3"]
    winner_d={i:math.log(win0[i]/win1[i]) for i in win0}
    trio_d={t:math.log(trio0[t]/trio1[t]) for t in trio0}
    n=len(win0)
    top_brier_diff={}
    for triple in trio0:
        s=set(triple)
        first=sum((top0[i]-int(i in s))**2 for i in top0)/n
        second=sum((top1[i]-int(i in s))**2 for i in top1)/n
        top_brier_diff[triple]=second-first
    m0_expected=sum(trio0[t]*d for t,d in top_brier_diff.items())
    m1_expected=sum(trio1[t]*d for t,d in top_brier_diff.items())
    squared_diff=sum((top1[i]-top0[i])**2 for i in top0)/n
    if not(math.isclose(m0_expected,squared_diff,abs_tol=1e-11) and
           math.isclose(m1_expected,-squared_diff,abs_tol=1e-11)):
        raise ValueError("HOLD_PROPER_BRIER_EXPECTATION_IDENTITY")
    KL01=_kl(win0,win1)
    KL10=_kl(win1,win0)
    return {
        "winning_horse": {
            "categorical_distribution_TV_pp":100*_tv(win0,win1),
            "KL_baseline_to_candidate_nats":KL01,
            "KL_candidate_to_baseline_nats":KL10,
            "min_possible_winner_logloss_candidate_minus_baseline":
                min(winner_d.values()),
            "max_possible_winner_logloss_candidate_minus_baseline":
                max(winner_d.values()),
            "possible_winner_count_candidate_better":
                sum(d<0 for d in winner_d.values()),
            "total_possible_winner_count":len(winner_d),
            "baseline_probability_mass_of_winner_cases_favoring_candidate":
                sum(win0[k] for k,d in winner_d.items() if d<0),
            "expected_logloss_candidate_minus_baseline_if_baseline_true":
                KL01,
            "expected_logloss_candidate_minus_baseline_if_candidate_true":
                -KL10,
        },
        "top3_horse_binary_brier": {
            "half_L1_distance_in_expected_top3_inclusions":
                _tv(top0,top1),
            "mean_squared_change_in_top3_marginals":
                squared_diff,
            "minimum_possible_top3_Brier_difference":
                min(top_brier_diff.values()),
            "maximum_possible_top3_Brier_difference":
                max(top_brier_diff.values()),
            "expected_Brier_delta_if_baseline_true":m0_expected,
            "expected_Brier_delta_if_candidate_true":m1_expected,
            "baseline_probability_mass_of_trios_favoring_candidate":
                sum(trio0[t] for t,d in top_brier_diff.items() if d<0),
        },
        "trio_event": {
            "unordered_top3_combination_count":len(trio0),
            "trio_distribution_TV_pp":100*_tv(trio0,trio1),
            "KL_baseline_to_candidate_nats":_kl(trio0,trio1),
            "KL_candidate_to_baseline_nats":_kl(trio1,trio0),
            "min_possible_trio_logloss_candidate_minus_baseline":
                min(trio_d.values()),
            "max_possible_trio_logloss_candidate_minus_baseline":
                max(trio_d.values()),
            "baseline_probability_mass_of_trios_favoring_candidate":
                sum(trio0[t] for t,d in trio_d.items() if d<0),
        },
        "probability_forecasts_previously_sealed_not_reoptimized":True,
    }


def audit(frozen,*,expected_seal=None):
    payload=verify_freeze(frozen)
    digest=frozen["seal_sha256_of_payload"]
    if expected_seal is not None and digest != expected_seal:
        raise ValueError("HOLD_SHA_NOT_THE_PRECOMMITTED_DIGEST")
    if payload.get("outcome_loaded_before_freeze") is not False:
        raise ValueError("HOLD_OUTCOME_MAY_HAVE_ENTERED_PRESTART_FORECAST")
    if payload["predeclared_primary_contrast"]!="winner_log_loss_M1_minus_M0":
        raise ValueError("HOLD_PRIMARY_CONTRAST_CHANGED")
    distributions=_validated_distributions(payload)
    return {
        "status":STATUS,
        "race_id":payload["race_id"],
        "scheduled_post_jst":payload["post_jst"],
        "freeze_seal_sha256":digest,
        "source_private_input_sha256":payload["source_private_input_sha256"],
        "official_result_used":False,
        "no_future_result_or_next_market_file_read":True,
        "model_coefficients_chosen_or_retrained_now":False,
        "fixed_primary":"M1 winner logloss minus M0 winner logloss",
        "comparison":{
            MAIN:_two_point_contrast(distributions[BASE],distributions[MAIN]),
            EXPL:_two_point_contrast(distributions[BASE],distributions[EXPL]),
        },
        "limitations":[
            "All separation measures depend on previously sealed model probabilities, not realized win/place outcomes.",
            "Kullback-Leibler divergences express expected logscore differences under assumed reference models; neither reference is known true.",
            "The pre-race analysis was constructed after the original GitHub SHA comment; unchanged predictions permit this diagnostic but it is not an independently precommitted PRIMARY score.",
            "A tiny expected difference in one race cannot identify market path-value or an initial-odds 10x threshold.",
            "This artifact includes aggregate distances only, not restricted source quotes or per-horse and per-trio probability arrays.",
            "This script never promotes one market shadow race to the existing frozen v3.1 holdout.",
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--expected-seal")
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    f=json.loads(args.freeze.read_text(encoding="utf-8"))
    report=audit(f,expected_seal=args.expected_seal)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "race_id":report["race_id"],
        "primary_market_vs_smooth_model_separation":{
            "win_TV_pp":report["comparison"][MAIN]["winning_horse"][
                "categorical_distribution_TV_pp"],
            "trio_TV_pp":report["comparison"][MAIN]["trio_event"][
                "trio_distribution_TV_pp"],
            "expected_winner_KL_nats":report["comparison"][MAIN][
                "winning_horse"]["KL_baseline_to_candidate_nats"],
        },
        "no_result_used":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
