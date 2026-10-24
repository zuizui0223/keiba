#!/usr/bin/env python3
"""Forward multi-race scoring audit with independent prestart GH commitments.

A fixed protocol is loaded from JSON. For each PRIVATE manifest entry,
only independently GitHub-verified SHA comments permit score inclusion.
Both the private frozen forecast and independently verified official JRA
outcome are loaded locally. At no time are provider quote rows or
per-horse probabilities uploaded to GitHub or written into the aggregate
report.

Only the ORIGINAL frozen primary M1−M0 WIN logloss drives the primary
cohort average. Top3 Brier and trio score are secondary/exploratory.
An optional anytime E process is a SEPARATE sharp-null diagnostic:
  E_n = product_r (p_M1(y_r) / p_M0(y_r)).
It is an e-process ONLY IF M0 supplies the exact conditional winner
distribution for every included race (a much stronger assumption than
"no incremental odds-path information"). E>=20 is NOT general proof
that M1 forecasts better or that betting is profitable.

For local coverage planning no result is required:
  python scripts/odds_prequential_cohort.py protocol \
     --output tmp/odds-prequential-cohort-v1.json

After independent future GH commitments and official postrace results:
  python scripts/odds_prequential_cohort.py verify-live \
     --manifest private/manifest.json --output private/cohort-report.json

Fixtures used in unittest MUST remain HOLD and may NEVER emulate
GitHub independence. Zero official future outcomes are claimed now.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
from statistics import mean

from odds_public_two_point_freeze import verify_freeze
from odds_preoutcome_discriminability import audit as separation
from odds_public_comment_attestation import verify_live as verify_comment_live
from odds_public_two_point_freeze import score as score_official

PROTOCOL_SCHEMA="KEIBA_WIN_ODDS_PREQUENTIAL_COHORT_V1"
REPORT_STATUS="EXTERNALLY_PRECOMMITTED_WINNING_LOGLOSS_COHORT_ONLY"
OFFLINE_STATUS="HOLD_UNAUTHENTICATED_LOCAL_COHORT_FIXTURE"
KL_STRATUM_THRESHOLD=.005
SHARP_NULL_EVIDENCE_THRESHOLD=20.
MIN_RACES_FOR_FEASIBILITY=60
MIN_DATES_FOR_FEASIBILITY=8

def protocol():
    return {
        "schema":PROTOCOL_SCHEMA,
        "protocol_version":"v1_no_change_after_first_official_outcome",
        "prospective_window_start":"2026-10-25",
        "prospective_window_end":"2027-03-31",
        "calendar_eligibility":"All JRA officially scheduled G1/G2/G3 races in the date range, all venues. Full graded-calendar denominator separately auditable.",
        "coverage_requirement":"Publish a result-independent status for EVERY race on the official graded calendar, including source missing, exclusion, scratched and unused records.",
        "market_data_requirement":"Two full field public single-WIN odds snapshots from one identified provider, exact same valid horse roster, each published >10min before post and increasing source update times.",
        "minimum_receipt_evidence":"Unedited GitHub comment SHA, independently fetched server created_at before post minus 10min, original forecast SHA and local source SHA match.",
        "fixed_model_M0":"Normalized inverse latest displayed single-WIN odds PL ranking",
        "fixed_model_M1":"M0 plus beta=+0.25 times centered log-relative early-to-late price change",
        "fixed_exploratory_M2":"M1 adjustment only for early displayed single-WIN odds >=10x",
        "primary_metric":"race-equal average M1 minus M0 winner categorical logloss; smaller is better",
        "secondary_metric":"race-equal average M1 minus M0 per-horse Top3 Brier",
        "exploratory_metric":"race-equal average M1 minus M0 unordered trio logloss; M2 threshold scores reported separately",
        "preoutcome_optional_stratum":"KL(M0 winner || M1 winner) >= 0.005 nats; report all-eligible primary regardless of stratum",
        "preoutcome_stratum_threshold_nats":KL_STRATUM_THRESHOLD,
        "fixed_coverage_feasibility_min_races":MIN_RACES_FOR_FEASIBILITY,
        "fixed_coverage_feasibility_min_meeting_dates":MIN_DATES_FOR_FEASIBILITY,
        "analytic_early_stopping":"NO: no termination, coefficient selection or race exclusions based on outcomes",
        "e_process_exploratory":"Cumulative M1/M0 win likelihood ratio, only an anytime test of SHARP conditional-calibration M0 null, NOT no-additional-info null",
        "e_process_sharp_null_reference_threshold":SHARP_NULL_EVIDENCE_THRESHOLD,
        "old_v31_formal_holdout_untouched":True,
        "statistical_inference_not_claimed_at_feasibility_60_8":True,
        "precommitment_not_a_proof_of_market_quote_integrity":True,
    }


def _date(value):
    if not isinstance(value,str):
        raise ValueError("HOLD_MISSING_COHORT_TIMESTAMP")
    d=datetime.fromisoformat(value.replace("Z","+00:00"))
    if d.tzinfo is None or d.utcoffset() is None:
        raise ValueError("HOLD_COHORT_TIMESTAMP_NEEDS_OFFSET")
    return d


def _is_date_in_scope(iso):
    date=iso[:10]
    pp=protocol()
    return pp["prospective_window_start"]<=date<=pp["prospective_window_end"]


def _evaluate_sealed_records(records, *, authenticated=False):
    """For tests: never upgrades caller-supplied JSON to remote-proof status."""
    p=protocol()
    records=sorted(records,key=lambda e:(_date(e["scheduled_post_jst"]),e["race_id"]))
    if len({r["race_id"] for r in records})!=len(records):
        raise ValueError("HOLD_DUPLICATED_RACE_REGISTRATION")
    if len({r["comment_id"] for r in records})!=len(records):
        raise ValueError("HOLD_DUPLICATED_GITHUB_ATTESTATION_REFERENCE")
    output=[]
    running_log_e=0.0
    for r in records:
        if not _is_date_in_scope(r["scheduled_post_jst"]):
            raise ValueError("HOLD_RACE_OUTSIDE_PREDECLARED_STUDY_WINDOW")
        if r.get("JRA_grade") not in ("G1","G2","G3"):
            raise ValueError("HOLD_NOT_ON_PREDECLARED_GRADED_CALENDAR")
        a=r.get("proof")
        scores=r.get("scores")
        if not isinstance(a,dict) or not isinstance(scores,dict):
            raise ValueError("HOLD_INCOMPLETE_REMOTE_PROOF_OR_OFFICIAL_SCORE")
        if (a.get("race_id")!=r["race_id"]
                or a.get("github_comment_id")!=r["comment_id"]
                or a.get("sha256_of_original_frozen_payload")!=r["forecast_sha"]
                or scores.get("race_id")!=r["race_id"]
                or scores.get("freeze_seal")!=r["forecast_sha"]):
            raise ValueError("HOLD_PROOF_SCORE_RACE_OR_SHA_MISMATCH")
        if (not _date(a["server_created_at"]) <
                _date(r["scheduled_post_jst"])):
            raise ValueError("HOLD_GITHUB_PROOF_AFTER_RACE_START")
        if ("winner_log_loss_M1_minus_M0" not in scores
                or "top3_brier_M1_minus_M0" not in scores
                or "trio_log_loss_M1_minus_M0" not in scores):
            raise ValueError("HOLD_FROZEN_PRIMARY_OR_SECONDARY_METRIC_ABSENT")
        win=float(scores["winner_log_loss_M1_minus_M0"])
        top=float(scores["top3_brier_M1_minus_M0"])
        trio=float(scores["trio_log_loss_M1_minus_M0"])
        if not all(math.isfinite(x) for x in (win,top,trio)):
            raise ValueError("HOLD_NONFINITE_COHORT_SCORE")
        kl=float(r.get("preoutcome_KL_M0_to_M1"))
        if not math.isfinite(kl) or kl<0:
            raise ValueError("HOLD_NONFINITE_OR_NEGATIVE_PREOUTCOME_KL")
        # e-factor is M1/M0 for realized winner. The primary
        # score difference is log(P0/P1) by precommitment.
        running_log_e-=win
        output.append({
            "race_id":r["race_id"],
            "race_date":r["scheduled_post_jst"][:10],
            "JRA_grade":r["JRA_grade"],
            "github_comment_id":r["comment_id"],
            "github_server_prestart_sha_created_at":a["server_created_at"],
            "win_logloss_M1_minus_M0":win,
            "top3_brier_M1_minus_M0":top,
            "trio_logloss_M1_minus_M0_exploratory":trio,
            "preoutcome_WIN_KL_M0_to_M1":kl,
            "preoutcome_high_separation":kl>=KL_STRATUM_THRESHOLD,
            "cumulative_log_likelihood_ratio_under_sharp_M0_null":
                running_log_e,
        })
    days=sorted({x["race_date"] for x in output})
    def avg(subset, field):
        return mean(r[field] for r in subset) if subset else None
    subset=[r for r in output if r["preoutcome_high_separation"]]
    group_by_date={
        date:[r for r in output if r["race_date"]==date] for date in days
    }
    # Do not assert statistical significance: grades/dates may cluster,
    # the source coverage calendar is not verified by this tool.
    return {
        "status":(REPORT_STATUS if authenticated else OFFLINE_STATUS),
        "remote_GitHub_comment_verification_was_independently_run":
            authenticated,
        "protocol":p,
        "included_scored_race_count":len(output),
        "independent_meeting_date_count":len(days),
        "coverage_feasibility_threshold_met":
            len(output)>=MIN_RACES_FOR_FEASIBILITY and
            len(days)>=MIN_DATES_FOR_FEASIBILITY,
        "graded_stakes_calendar_denominator_verified":False,
        "primary_race_equal_mean_WIN_logloss_M1_minus_M0":
            avg(output,"win_logloss_M1_minus_M0"),
        "primary_meeting_day_equal_mean_WIN_logloss_M1_minus_M0":(
            mean(avg(v,"win_logloss_M1_minus_M0")
                 for v in group_by_date.values()) if days else None),
        "secondary_race_equal_mean_Top3_Brier_M1_minus_M0":
            avg(output,"top3_brier_M1_minus_M0"),
        "exploratory_race_equal_mean_trio_logloss_M1_minus_M0":
            avg(output,"trio_logloss_M1_minus_M0_exploratory"),
        "high_separation_preoutcome_KL_stratum_race_count":len(subset),
        "high_separation_stratum_race_equal_WIN_delta":
            avg(subset,"win_logloss_M1_minus_M0"),
        "exploratory_sharp_baseline_M0_log_evidence_factor":
            running_log_e,
        "exploratory_sharp_baseline_M0_e_factor":
            math.exp(min(700,running_log_e)),
        "exploratory_sharp_M0_e_factor_over_20":
            running_log_e>=math.log(SHARP_NULL_EVIDENCE_THRESHOLD),
        "e_process_is_only_valid_if_each_frozen_M0_is_exact_conditional_winner_distribution":True,
        "e_value_not_a_test_for_absence_of_incremental_path_information":True,
        "per_race_scored_provenance":output,
        "predeclared_full_calendar_reporting_missing_still_required":True,
        "not_a_real_market_advantage_claim":True,
        "v31_formal_holdout_not_modified":True,
    }


def offline_demo():
    """NEVER calls GitHub and NEVER labels fixtures real trusted evidence."""
    r=[]
    for idx,(date,delta) in enumerate(
            (("2026-10-25",-.02),("2026-11-01",.03),("2026-11-08",-.01))):
        rid=f"FICTITIOUS-{date}-RACE-{idx}"
        seal=f"{idx+1:064x}"
        r.append({
            "race_id":rid,"JRA_grade":"G1" if idx==0 else "G2",
            "scheduled_post_jst":date+"T15:40:00+09:00",
            "comment_id":idx+1000,"forecast_sha":seal,
            "preoutcome_KL_M0_to_M1":.001 if idx==0 else .01,
            "proof":{
                "race_id":rid,"github_comment_id":idx+1000,
                "sha256_of_original_frozen_payload":seal,
                "server_created_at":date+"T09:00:00+09:00",
            },
            "scores":{
                "race_id":rid,"freeze_seal":seal,
                "winner_log_loss_M1_minus_M0":delta,
                "top3_brier_M1_minus_M0":delta/20,
                "trio_log_loss_M1_minus_M0":delta*2,
            },
        })
    return _evaluate_sealed_records(r,authenticated=False)


def verify_live_manifest(manifest):
    """External API verification, not caller-provided 'proof' fields."""
    if manifest.get("schema")!=PROTOCOL_SCHEMA:
        raise ValueError("HOLD_MANIFEST_PROTOCOL_SCHEMA")
    records=manifest.get("entries")
    if not isinstance(records,list) or not records:
        raise ValueError("HOLD_EMPTY_SCORING_MANIFEST")
    evaluated=[]
    for item in records:
        if item.get("status")!="scorable":
            raise ValueError("HOLD_UNRESOLVED_OMISSIONS_MUST_BE_REPORTED_SEPARATELY")
        frozen=json.loads(Path(item["private_freeze_path"]).read_text(
            encoding="utf-8"))
        official=json.loads(Path(item["private_official_top3_path"]).read_text(
            encoding="utf-8"))
        pre=verify_freeze(frozen)
        if (pre["race_id"]!=item["race_id"] or
            frozen["seal_sha256_of_payload"]!=item["forecast_sha"]):
            raise ValueError("HOLD_PRECOMMITTED_MANIFEST_SHA_OR_RACE_CHANGED")
        if pre.get("predeclared_primary_contrast")!=(
                "winner_log_loss_M1_minus_M0"):
            raise ValueError("HOLD_PRIMARY_CHANGED_AFTER_PRECOMMITMENT")
        # A true GH CLI/API server fetch happens EACH time, not fake caller
        # fields. The function checks original comment, unedited timestamp
        # and earliest PR commitment for this race.
        remote=verify_comment_live(frozen,with_result=official,
                                   comment_id=item["comment_id"])
        if not remote.get("GitHub_API_independently_fetched"):
            raise ValueError("HOLD_NO_AUTHENTICATED_SERVER_TIMESTAMP")
        scored=remote["postrace_scores"]
        disc=separation(frozen,expected_seal=item["forecast_sha"])
        if disc["official_result_used"]:
            raise ValueError("HOLD_PREOUTCOME_KL_USED_RESULTS")
        kl=disc["comparison"]["M1_smooth_beta025"]["winning_horse"][
            "KL_baseline_to_candidate_nats"]
        evaluated.append({
            "race_id":item["race_id"],
            "scheduled_post_jst":pre["post_jst"],
            "JRA_grade":item["JRA_grade"],
            "comment_id":item["comment_id"],
            "forecast_sha":item["forecast_sha"],
            "proof":remote,"scores":scored,
            "preoutcome_KL_M0_to_M1":kl,
        })
    return _evaluate_sealed_records(evaluated,authenticated=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="mode",required=True)
    for name in ("protocol","offline-demo","verify-live"):
        parser2=sub.add_parser(name)
        parser2.add_argument("--output",type=Path,required=True)
        if name=="verify-live":
            parser2.add_argument("--manifest",type=Path,required=True)
    args=parser.parse_args()
    if args.mode=="protocol":
        report=protocol()
    elif args.mode=="offline-demo":
        report=offline_demo()
    else:
        report=verify_live_manifest(json.loads(args.manifest.read_text(
            encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":report.get("status",PROTOCOL_SCHEMA),
        "included_races":report.get("included_scored_race_count",0),
        "GitHub_comment_verified":report.get(
            "remote_GitHub_comment_verification_was_independently_run",False),
        "real_market_predictive_advantage_not_established":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
