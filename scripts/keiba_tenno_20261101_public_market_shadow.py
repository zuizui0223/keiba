#!/usr/bin/env python3
"""2026-11-01 Tenno Sho Autumn: dated prestart public-price research preview.

This is a SOURCE-DECLARED Oct31 17:00 quote table from a public report,
NOT a licensed JRA-VAN original-file receipt or an authenticated complete
multi-timestamp WIN/WIDE feed. This branch and its GitHub Actions creation
occur before the scheduled Nov1 15:40 post, but do not claim the PR22/30
prospective SHA-only source-receipt gate or an out-of-sample trained model.

Outputs:
  M0: normalize the inverses of all 17 single-WIN quoted payout odds.
  Coherent Plackett-Luce win, top3, first-two, both-top3 and trio events.
  Physical/societal SENSITIVITIES: same prestart price proxy -> PR17
  nonlocal interacting horse SDE / factorized PDE -> PR19 smooth bettor
  response with hypothetical 1/3/5 information-arrival rounds.

Ratings from the JRA Oct26 PRE-rating table are supplied as transparent
prestart covariates. A missing rating for #10 is NOT a measured rating;
the rating-only toy prior uses fixed neutral imputation 115 for sensitivity
only, with NO training/calibration and NO claim of true independent horse
ability. The forecast preference/market baseline is M0, not this toy.

Source-published clock 2026-10-31 17:00 (independently reported by an
editorial site) is not the exact local URL fetch time. Whole ticket pools,
real WIDE prices, market participant behavior, vote sizes, actual horse GPS,
future q2, podium, payout/returns are NOT consumed and not inferred.
"""
from __future__ import annotations
import argparse
from datetime import datetime
from itertools import combinations
import json
import math
from pathlib import Path

import numpy as np

from odds_coherent_hierarchy_rank_bridge import joint_rank_probability
from keiba_nonlocal_horse_pde_bettor_bridge import (
    finish_pair,pde_density_and_agent_check,
)
from keiba_endogenous_threshold_null_bridge import voter_path

RACE="2026-11-01|東京|11R|天皇賞(秋)"
RACE_LOCAL_POST="2026-11-01T15:40:00+09:00"
MARKET_SOURCE_REPORTED_CLOCK="2026-10-31T17:00:00+09:00"
SOURCE_ODDS_URL="https://keiba-times.com/tennosho-aki-2026-zenjitsu-odds/"
SOURCE_JRA_CARD_URL="https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0105202604111120261101%2FA6"
SOURCE_JRA_RATINGS_URL="https://www.jra.go.jp/datafile/ranking/g1/2026/akiten.html"
SOURCE_JRA_COURSE_URL="https://www.jra.go.jp/keiba/baba/"
STATUS="EXPLORATORY_PRESTART_PUBLIC_QUOTE_M0_NOT_INDEPENDENT_ASOF_ATTESTED"
PRESTART_ONLY=True
ASSUMED_HORSE_CROWD=2.0
VOTER_DURATION_HOURS=0.25
MARKET_MODEL="normalized_inverse_win_payout_odds_with_PL_ranking"
PRIMARY_TICKETS=((1,7),(1,17),(7,17),(3,7),(7,11))
TRIOS=((1,3,7),(1,7,11),(1,7,17),(3,7,17))
# Official runner numbers and 2026 best performance PRE-ratings, published
# before this race; source records are not a speed measure or physical GPS.
# No numeric rating was reported for #10 in the current-year rating table.
FIELD=(
    (1,"クロワデュノール",2.5,122),
    (2,"エルトンバローズ",224.3,115),
    (3,"レガレイラ",9.8,104),
    (4,"レディネス",49.7,112),
    (5,"シャンパンカラー",170.8,113),
    (6,"セイウンハーデス",27.2,116),
    (7,"マスカレードボール",2.4,122),
    (8,"ジュンブロッサム",235.9,107),
    (9,"ホウオウビスケッツ",65.9,114),
    (10,"ネブラディスク",46.9,None),
    (11,"シェイクユアハート",11.9,117),
    (12,"コスモキュランダ",110.4,118),
    (13,"リアライズシリウス",36.5,117),
    (14,"タガノデュード",121.3,117),
    (15,"サクラファレル",104.6,112),
    (16,"ジョバンニ",58.0,116),
    (17,"ダノンデサイル",11.4,118),
)


def _field():
    if (len(FIELD)!=17 or [r[0] for r in FIELD]!=list(range(1,18))
            or len({x[1] for x in FIELD})!=17
            or any(type(x[2]) not in (float,int) or not math.isfinite(x[2])
                   or x[2]<=1 for x in FIELD)):
        raise ValueError("HOLD_TENNO_INVALID_FULL_FIELD_PUBLIC_SOURCE")
    rating_missing=[x[0] for x in FIELD if x[3] is None]
    if rating_missing!=[10]:
        raise ValueError("HOLD_TENNO_JRA_RATINGS_SOURCE_INCOMPLETE_OR_CHANGED")
    updated=datetime.fromisoformat(MARKET_SOURCE_REPORTED_CLOCK)
    race=datetime.fromisoformat(RACE_LOCAL_POST)
    if (updated.tzinfo is None or race.tzinfo is None or
            not updated<race):
        raise ValueError("HOLD_TENNO_QUOTE_SOURCE_AFTER_RACE")
    return {x[0]:x[2] for x in FIELD}


def _normalized(x):
    p=np.asarray(x,dtype=float)
    if p.ndim!=1 or np.any(p<=0) or not np.all(np.isfinite(p)):
        raise ValueError("HOLD_INVALID_SYNTHETIC_NORMALIZED_HORSE_VECTOR")
    return p/p.sum()


def _rating_prior():
    # Pre-declared sensitivity, NOT a learned predictor. Missing #10 is
    # assigned a NEUTRAL prior value for computation, not a JRA observation.
    ratings=np.asarray([115 if x[3] is None else x[3] for x in FIELD])
    return _normalized(np.exp((ratings-115)/10.0))


def audit(*,horse_draws=150,seed_count=3,seed=20261031,
          include_physical=True):
    odds=_field()
    ids=sorted(odds)
    p0=_normalized([1/odds[i] for i in ids])
    law=joint_rank_probability(
        odds,{i:0.0 for i in ids},
        {pair:0.0 for pair in combinations(ids,2)},
        beta_horse=0.,beta_pair=0.)
    if (not math.isclose(sum(law["win"].values()),1,abs_tol=1e-9)
            or not math.isclose(sum(law["top3"].values()),3,abs_tol=1e-9)
            or not math.isclose(sum(law["both_top3_pair"].values()),
                                3,abs_tol=1e-9)
            or not math.isclose(sum(law["unordered_top3_trio"].values()),
                                1,abs_tol=1e-9)):
        raise ValueError("HOLD_TENNO_COHERENT_JOINT_TICKET_MASS")
    rows=[{
        "horse_number":n,"name":next(x[1] for x in FIELD if x[0]==n),
        "source_reported_single_win_odds":odds[n],
        "market_M0_win_index":law["win"][n],
        "Plackett_Luce_top3_index":law["top3"][n],
        "JRA_2026_best_pre_rating_not_course_specific":
            next(x[3] for x in FIELD if x[0]==n),
    } for n in ids]
    selections={
        "unordered_umaren_probability_index":{
            f"{a}-{b}":law["ordered_firsttwo_exacta"][(a,b)]+
                      law["ordered_firsttwo_exacta"][(b,a)]
            for a,b in PRIMARY_TICKETS},
        "both_top3_wide_event_probability_index":{
            f"{a}-{b}":law["both_top3_pair"][(a,b)]
            for a,b in PRIMARY_TICKETS},
        "unordered_top3_trio_event_probability_index":{
            "-".join(map(str,combo)):law["unordered_top3_trio"][combo]
            for combo in TRIOS},
    }
    report={
        "status":STATUS,
        "race":RACE,
        "post_jst":RACE_LOCAL_POST,
        "full_horse_field":17,
        "source_published_WIN_odds_reported_at_jst":
            MARKET_SOURCE_REPORTED_CLOCK,
        "quote_source_url":SOURCE_ODDS_URL,
        "official_JRA_card_url":SOURCE_JRA_CARD_URL,
        "official_JRA_2026_rating_source_url":SOURCE_JRA_RATINGS_URL,
        "market_index_definition":MARKET_MODEL,
        "sum_inverse_quote_odds_not_true_bet_volume":
            sum(1/x for x in odds.values()),
        "market_implied_proxy_not_calibrated_true_win_probabilities":True,
        "coherent_PL_ticket_events_not_actual_pool_ticket_odds":True,
        "all_horses_source_market_M0_and_top3":rows,
        "selected_coherent_event_indices":selections,
        "real_WIN_snapshot_count":1,
        "independent_asof_authenticated_source_receipts":0,
        "full_same_provider_real_WIDE_grid_received":False,
        "observed_real_market_vote_total":False,
        "actual_JRA_outcome_read":False,
        "predictive_skill_proven_on_new_target":False,
        "preexisting_2026_Kikka_and_v31_ledger_unchanged":True,
        "prediction_eligible_for_PR22_or_PR30_capture_certificate":False,
    }
    if not include_physical:
        report["synthetic_horse_social_sensitivity"]="NOT_RUN"
        return report
    if not 40<=horse_draws<=5000 or not 1<=seed_count<=30:
        raise ValueError("HOLD_TENNO_INVALID_SYNTHETIC_SEED_OR_DRAWS")
    pde=pde_density_and_agent_check(
        p0,strength=ASSUMED_HORSE_CROWD,
        particles=600,duration_s=12.,seed=seed+177)
    if (not pde["nonnegative_density"] or
            abs(pde["min_horse_probability_mass"]-1)>1e-8 or
            abs(pde["max_horse_probability_mass"]-1)>1e-8):
        raise ValueError("HOLD_TENNO_NONLOCAL_PDE_MASS_LEAK")
    sensitivity={}
    for initial_name,prior in (
        ("market_price_q0",p0),
        ("JRA_rating_only_NEUTRAL_missing_imputation_TOY",_rating_prior())
    ):
        per_seed=[]
        for k in range(seed_count):
            this_seed=seed+1009*k
            horse=finish_pair(
                prior,distance_m=2000,draws=horse_draws,seed=this_seed,
                crowd_coefficient=ASSUMED_HORSE_CROWD)
            signal=_normalized(horse["scenarios"]["nonlocal_crowd"]["win"])
            no_crowd=_normalized(horse["scenarios"]["no_crowd"]["win"])
            market={step:voter_path(
                p0,signal,policy="smooth",
                duration_hours=VOTER_DURATION_HOURS,
                arrival=step,seed=this_seed+390)["final"]
                    for step in (1,3,5)}
            before=voter_path(p0,p0,policy="smooth",
                              duration_hours=VOTER_DURATION_HOURS,
                              arrival=5,seed=this_seed+390)["final"]
            if not np.array_equal(market[5],before):
                raise ValueError("HOLD_TENNO_FUTURE_HORSE_SIGNAL_REACHED_PAST_VOTERS")
            per_seed.append({
                "hypothetical_horse_win":signal,
                "hypothetical_no_crowd_horse_win":no_crowd,
                "synthetic_bettors_round1":market[1],
                "synthetic_bettors_round3":market[3],
                "synthetic_bettors_no_signal_round5":market[5],
            })
        summary={}
        for key in per_seed[0]:
            avg=np.mean(np.asarray([x[key] for x in per_seed]),axis=0)
            summary[key]={
                str(n):float(avg[j]) for j,n in enumerate(ids)}
        sensitivity[initial_name]=summary
    report["synthetic_horse_social_sensitivity"]={
        "settings_fixed_hypothetical_not_fitted":{
            "physical_horse_crowd_c_m2ps":ASSUMED_HORSE_CROWD,
            "horse_distance_m":2000,
            "market_voter_duration_hours_fictional":VOTER_DURATION_HOURS,
            "horse_draws_per_seed":horse_draws,
            "same_17_real_horses_reused_under_simulation_seeds":seed_count,
            "rating_only_toy_JRA_missing_10_assumed_neutral_115":True,
            "no_two_real_synchronized_quote_snapshots":True,
        },
        "paired_PDE_and_particle_numeric_check":{
            "nonnegative_density":pde["nonnegative_density"],
            "min_horse_probability_mass":pde["min_horse_probability_mass"],
            "max_horse_probability_mass":pde["max_horse_probability_mass"],
            "max_particle_PDE_CDF_difference_synthetic_only":
                pde["max_KS_particle_to_PDE"],
            "finite_horse_factorized_PDE_NOT_true_GPS_validated":True,
        },
        "averaged_over_synthetic_seeds_not_new_real_races":sensitivity,
    }
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--horse-draws",type=int,default=150)
    p.add_argument("--seeds",type=int,default=3)
    p.add_argument("--market-only",action="store_true")
    p.add_argument("--output",type=Path,default=Path(
        "tmp/20261101-tenno-20261031-public-market-prestart-shadow.json"))
    a=p.parse_args()
    report=audit(horse_draws=a.horse_draws,seed_count=a.seeds,
                 include_physical=not a.market_only)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,
                                   allow_nan=False)+"\n",encoding="utf-8")
    top=sorted(report["all_horses_source_market_M0_and_top3"],
               key=lambda r:-r["market_M0_win_index"])[:7]
    print("TENNO_PRESTART_MARKET_M0_TOP7",
          json.dumps(top,ensure_ascii=False,sort_keys=True))
    print("TENNO_COHERENT_TICKET_MASS",
          json.dumps(report["selected_coherent_event_indices"],
                     sort_keys=True))
    if not a.market_only:
        for prior,summary in report["synthetic_horse_social_sensitivity"][
                "averaged_over_synthetic_seeds_not_new_real_races"].items():
            print("TENNO_HORSE_TO_BETTOR_SENSITIVITY",
                  json.dumps({"source_prior":prior,
                       "hypothetical_horse_win":summary["hypothetical_horse_win"],
                       "synthetic_market_round1":
                           summary["synthetic_bettors_round1"]},
                       sort_keys=True))
        print("TENNO_HORSE_PDE_NUMERIC_ONLY",
              json.dumps(report["synthetic_horse_social_sensitivity"][
                    "paired_PDE_and_particle_numeric_check"],sort_keys=True))
    print("TENNO_OUTCOME_NOT_ACCESSED_AND_REAL_PROSPECTIVE_SOURCE_UNATTESTED",
          report["actual_JRA_outcome_read"],
          report["prediction_eligible_for_PR22_or_PR30_capture_certificate"])


if __name__=="__main__":
    main()
