#!/usr/bin/env python3
"""A result-free, sharp-hypothesis power envelope for TWO SEALED win forecasts.

The real 2026-10-25 Kikka freeze contains actual pre-race M0 (latest
win-odds PL) and M1 (fixed beta=+0.25 path). The user supplies that private
freeze LOCALLY; do not upload individual WIN/TRIO probabilities.

For each possible winner i, the preselected single-race score difference is
  d_i = -log p1_i - [-log p0_i] = log(p0_i/p1_i).
Under the COUNTERFACTUAL sharp reference "M0 is the true win
distribution", E[d]=KL(p0||p1) >= 0. Under the distinct reference
"M1 is exactly true", E[d]=-KL(p1||p0) <= 0.

If arbitrarily many INDEPENDENT IDENTICALLY DISTRIBUTED replicas of
this EXACT SAME race forecast existed, a two-sided normal mean test
with specified type-I error and power would need N races as calculated
below. This is a theoretical distance/power yardstick, NEVER a real
race sample-size requirement: later races have different forecasts,
correlated meeting days, potentially uncalibrated models, and changing
market information.

Power and conditional expected score contrasts must NOT be described
as observed winning probability improvement, as evidence for an odds
threshold, or as prospective validation. No postrace JRA result is read.

CLI:
 python scripts/odds_sharp_reference_power_envelope.py \
    --freeze private/prestart_20261025_kikka11_market_only_vs_path_freeze.json \
    --expected-sha <64-char precommitted forecast digest> \
    --output private/preoutcome-sharp-reference-power.json
"""
from __future__ import annotations

import argparse
from math import erf, exp, isfinite, log, sqrt
from pathlib import Path
import json
import math
from statistics import NormalDist

from odds_public_two_point_freeze import verify_freeze

STATUS = "PREOUTCOME_SHARP_MODEL_REFERENCE_POWER_NOT_EMPIRICAL_RACE_POWER"
MODEL0 = "M0_market_only"
MODEL1 = "M1_smooth_beta025"
ALPHA = .05
TARGET_POWER = .8
MAX_THEORETICAL_REPLICAS = 10_000_000


def cdf(z):
    return .5 * (1+erf(z/sqrt(2)))


def normal_two_sided_power(mu, sigma, n, *, alpha=ALPHA):
    """CLT reference only. n independent, identical replicas of SAME forecast."""
    if not 0<alpha<1 or n<1 or not isfinite(mu) or not isfinite(sigma):
        raise ValueError("HOLD_BAD_NORMAL_POWER_PARAMETERS")
    if sigma < 0:
        raise ValueError("HOLD_NEGATIVE_SCORE_VARIANCE")
    if sigma == 0:
        return 1.0 if mu != 0 else alpha
    zcrit = NormalDist().inv_cdf(1-alpha/2)
    z = (mu/sigma)*sqrt(n)
    return cdf(-zcrit-z)+(1-cdf(zcrit-z))


def minimal_theoretical_replica_count(mu,sigma,*,alpha=ALPHA,
                                      target_power=TARGET_POWER):
    if not 0<target_power<1 or not 0<alpha<1:
        raise ValueError("HOLD_INVALID_POWER_TARGET")
    if abs(mu)<1e-16:
        return None
    lower,upper=1,MAX_THEORETICAL_REPLICAS
    if normal_two_sided_power(mu,sigma,upper,alpha=alpha)<target_power:
        return None
    while lower<upper:
        mid=(lower+upper)//2
        if normal_two_sided_power(mu,sigma,mid,alpha=alpha)>=target_power:
            upper=mid
        else:
            lower=mid+1
    return lower


def _weights(raw):
    if not isinstance(raw,list) or len(raw)<5:
        raise ValueError("HOLD_NO_FROZEN_WIN_MODEL")
    out={}
    for row in raw:
        if not isinstance(row,dict):
            raise ValueError("HOLD_BAD_WIN_PROBABILITY_ITEM")
        i=row.get("number")
        v=row.get("p")
        if (type(i) is not int or i<=0 or type(v) not in (int,float)
                or not isfinite(v) or v<=0 or v>1 or i in out):
            raise ValueError("HOLD_NONPOSITIVE_DUPLICATE_OR_NONFINITE_WIN_PROB")
        out[i]=float(v)
    if not math.isclose(sum(out.values()),1,abs_tol=1e-10):
        raise ValueError("HOLD_WIN_PROBABILITIES_NOT_NORMALIZED")
    return out


def _moment(weights,deltas):
    mu=sum(weights[i]*deltas[i] for i in weights)
    var=sum(weights[i]*(deltas[i]-mu)**2 for i in weights)
    if var<0 and abs(var)<1e-15:
        var=0.0
    if not isfinite(var) or var<0:
        raise ValueError("HOLD_WIN_SCORE_MOMENT_VARIANCE")
    return mu,sqrt(var)


def audit(frozen, *, expected_seal=None,
          alpha=ALPHA,target_power=TARGET_POWER):
    payload=verify_freeze(frozen)
    if (expected_seal is not None and
            frozen["seal_sha256_of_payload"] != expected_seal):
        raise ValueError("HOLD_NOT_THE_EXTERNALLY_PRECOMMITTED_WIN_FORECAST")
    if payload.get("outcome_loaded_before_freeze") is not False:
        raise ValueError("HOLD_RESULT_ENTERED_PRIOR_TO_MODEL_FREEZE")
    if payload.get("predeclared_primary_contrast") != (
            "winner_log_loss_M1_minus_M0"):
        raise ValueError("HOLD_WINNER_LOGLOSS_IS_NOT_FIXED_PRIMARY")
    preds=payload["predictions"]
    if set(preds)!={"M0_market_only","M1_smooth_beta025",
                   "M2_initial_10x_beta025"}:
        raise ValueError("HOLD_MODEL_UNIVERSE_CHANGED")
    p0=_weights(preds[MODEL0]["win"])
    p1=_weights(preds[MODEL1]["win"])
    if set(p0)!=set(p1) or len(p0)!=len(payload["roster_horse_numbers"]):
        raise ValueError("HOLD_WIN_ROSTER_CHANGED")
    # Realized outcome is NOT loaded. These are the entire finite
    # counterfactual possibilities for the winner.
    d={i:log(p0[i]/p1[i]) for i in p0}
    mu0,sd0=_moment(p0,d)
    mu1,sd1=_moment(p1,d)
    if (mu0 < -1e-11 or mu1 > 1e-11):
        raise ValueError("HOLD_PROPER_LOG_SCORE_KL_IDENTITY")
    if all(abs(v)<1e-14 for v in d.values()):
        status="HOLD_IDENTICAL_FROZEN_WIN_MODELS_CANNOT_DISCRIMINATE"
    else:
        status=STATUS
    regimes={}
    for name,pv,mu,sd in (("M0_is_exact_truth",p0,mu0,sd0),
                          ("M1_is_exact_truth",p1,mu1,sd1)):
        n_req=minimal_theoretical_replica_count(
            mu,sd,alpha=alpha,target_power=target_power)
        regimes[name]={
            "reference_is_sharp_unverified_hypothesis":True,
            "expected_M1_minus_M0_winner_logloss":mu,
            "single_race_M1_minus_M0_logloss_standard_deviation":sd,
            "single_race_sharp_reference_information_to_noise_ratio":
                abs(mu)/sd if sd else None,
            "number_of_identical_independent_replicas_for_CLT_80pct_power":
                n_req if target_power==.8 else None,
            "number_of_identical_independent_replicas_at_requested_power":
                n_req,
            "CLT_power_if_N_20":normal_two_sided_power(
                mu,sd,20,alpha=alpha),
            "CLT_power_if_N_60":normal_two_sided_power(
                mu,sd,60,alpha=alpha),
            "CLT_power_if_N_1000":normal_two_sided_power(
                mu,sd,1000,alpha=alpha),
            "CLT_power_if_N_10000":normal_two_sided_power(
                mu,sd,10000,alpha=alpha),
            "reference_probability_mass_where_M1_winner_score_better":
                sum(pv[i] for i in pv if d[i]<0),
        }
    return {
        "status":status,
        "race_id":payload["race_id"],
        "scheduled_post_jst":payload["post_jst"],
        "frozen_prediction_sha256":frozen["seal_sha256_of_payload"],
        "race_or_result_outcome_was_loaded":False,
        "type_I_error_two_sided_normal_reference":alpha,
        "target_normal_reference_power":target_power,
        "n_win_horses":len(p0),
        "winner_score_contrast":"M1 minus M0 (negative favors M1)",
        "winner_score_min_possible":min(d.values()),
        "winner_score_max_possible":max(d.values()),
        "model_reference_moments":regimes,
        "independence_and_identical_forecast_assumptions_known_false_as_a_description_of_future_races":True,
        "not_a_recommended_number_of_real_races":True,
        "actual_calibration_or_market_advantage_tested":False,
        "source_market_or_future_result_used":False,
        "caveats":[
            "The two sharp hypotheses suppose the respective *forecast* is the true winner distribution; no evidence establishes either.",
            "Future races are not independently identical copies of this sealed odds distribution, and meeting days induce dependence.",
            "These power figures are normal asymptotic thought experiments. They do not determine empirical power for an actual prospective horse-racing cohort.",
            "A beta or threshold chosen using these figures after observing any outcome would invalidate precommitted score selection.",
            "This script does not amend the frozen v3.1 20-race holdout or evaluate wagering ROI.",
        ],
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--freeze",required=True,type=Path)
    ap.add_argument("--expected-sha")
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    f=json.loads(args.freeze.read_text(encoding="utf-8"))
    result=audit(f,expected_seal=args.expected_sha)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "race_id":result["race_id"],
        "n_winners":result["n_win_horses"],
        "two_sharp_reference_80pct_replica_counts":{
            k:v["number_of_identical_independent_replicas_at_requested_power"]
            for k,v in result["model_reference_moments"].items()
        },
        "real_race_sample_size_claim":False,
        "any_postrace_outcome_read":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
