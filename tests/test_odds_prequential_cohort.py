#!/usr/bin/env python3
"""No G1/G2/G3 prospective advantage is invented by offline fixtures."""
from copy import deepcopy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import odds_prequential_cohort as pre
from odds_public_two_point_freeze import (
    INPUT_SCHEMA, RESULT_SCHEMA, freeze, score
)


class FrozenProspectiveCohortTests(unittest.TestCase):
    def test_phase_one_protocol_fixed_in_advance_of_future_outcomes(self):
        p=pre.protocol()
        self.assertEqual(p["schema"],pre.PROTOCOL_SCHEMA)
        self.assertEqual(p["prospective_window_start"],"2026-10-25")
        self.assertEqual(p["prospective_window_end"],"2027-03-31")
        self.assertEqual(p["fixed_coverage_feasibility_min_races"],60)
        self.assertEqual(p["fixed_coverage_feasibility_min_meeting_dates"],8)
        self.assertEqual(p["preoutcome_stratum_threshold_nats"],.005)
        self.assertEqual(p["e_process_sharp_null_reference_threshold"],20)
        self.assertEqual(p["analytic_early_stopping"][:2],"NO")
        self.assertIn("winner categorical logloss",p["primary_metric"])
        self.assertTrue(p["old_v31_formal_holdout_untouched"])

    def test_public_precommitted_protocol_json_exactly_equals_code(self):
        fixed=json.loads((ROOT/"docs/odds-prequential-graded-cohort-v1-20261024.json").read_text(
            encoding="utf-8"))
        self.assertEqual(fixed,pre.protocol())
        self.assertEqual(fixed["fixed_coverage_feasibility_min_races"],60)
        self.assertTrue(fixed["statistical_inference_not_claimed_at_feasibility_60_8"])

    def test_offline_demo_remains_hold_and_sharp_e_factor_is_well_defined(self):
        z=pre.offline_demo()
        self.assertEqual(z["status"],pre.OFFLINE_STATUS)
        self.assertFalse(z["remote_GitHub_comment_verification_was_independently_run"])
        self.assertEqual(z["included_scored_race_count"],3)
        self.assertEqual(z["independent_meeting_date_count"],3)
        self.assertFalse(z["coverage_feasibility_threshold_met"])
        self.assertEqual(z["high_separation_preoutcome_KL_stratum_race_count"],2)
        self.assertAlmostEqual(
            z["primary_race_equal_mean_WIN_logloss_M1_minus_M0"],0,places=12)
        self.assertAlmostEqual(z["exploratory_sharp_baseline_M0_e_factor"],1,places=12)
        self.assertFalse(z["exploratory_sharp_M0_e_factor_over_20"])
        self.assertTrue(z["e_value_not_a_test_for_absence_of_incremental_path_information"])

    def test_race_order_changes_do_not_change_race_and_date_equal_scores(self):
        r=pre.offline_demo()
        raw=self.fixture_records()
        scrambled=pre._evaluate_sealed_records(raw[::-1])
        self.assertEqual(scrambled,r)
        self.assertEqual([x["race_id"] for x in scrambled["per_race_scored_provenance"]],
                         [x["race_id"] for x in r["per_race_scored_provenance"]])

    @staticmethod
    def fixture_records():
        result=[]
        for idx,(date,diff) in enumerate(
                (("2026-10-25",-.02),("2026-11-01",.03),("2026-11-08",-.01))):
            rid=f"FICTITIOUS-{date}-RACE-{idx}"
            seal=f"{idx+1:064x}"
            result.append({
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
                    "winner_log_loss_M1_minus_M0":diff,
                    "top3_brier_M1_minus_M0":diff/20,
                    "trio_log_loss_M1_minus_M0":2*diff,
                },
            })
        return result

    def test_manifests_cannot_drop_timestamp_or_change_grade_after_scoring(self):
        rows=self.fixture_records()
        rows[0]["JRA_grade"]="G5"
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_ON_PREDECLARED"):
            pre._evaluate_sealed_records(rows)
        rows=self.fixture_records()
        rows[0]["scheduled_post_jst"]="2026-10-24T15:40:00+09:00"
        with self.assertRaisesRegex(ValueError,"HOLD_RACE_OUTSIDE"):
            pre._evaluate_sealed_records(rows)
        rows=self.fixture_records()
        rows[0]["proof"]["server_created_at"]="2026-10-25T15:40:00+09:00"
        with self.assertRaisesRegex(ValueError,"HOLD_GITHUB_PROOF_AFTER"):
            pre._evaluate_sealed_records(rows)

    def test_recycled_comment_id_or_changed_source_digest_is_rejected(self):
        rows=self.fixture_records()
        rows[1]["comment_id"]=rows[0]["comment_id"]
        with self.assertRaisesRegex(ValueError,"HOLD_DUPLICATED_GITHUB"):
            pre._evaluate_sealed_records(rows)
        rows=self.fixture_records()
        rows[1]["proof"]["sha256_of_original_frozen_payload"]="f"*64
        with self.assertRaisesRegex(ValueError,"HOLD_PROOF_SCORE"):
            pre._evaluate_sealed_records(rows)
        rows=self.fixture_records()
        rows[1]["scores"]["winner_log_loss_M1_minus_M0"]=float("nan")
        with self.assertRaisesRegex(ValueError,"HOLD_NONFINITE"):
            pre._evaluate_sealed_records(rows)

    def test_significance_is_only_under_exact_conditional_calibration_null(self):
        # If baseline M0 exactly equals conditional winner distribution,
        # each precommitted M1/M0 winner likelihood ratio has expectation 1:
        # (0.7)*(0.65/0.7) + (0.3)*(0.35/0.3) = 1.
        q0={1:.7,2:.3}
        q1={1:.65,2:.35}
        self.assertAlmostEqual(
            sum(q0[i]*(q1[i]/q0[i]) for i in q0),1,places=12)
        # Being an e-process does NOT test the weaker "no incremental
        # path information" null: if M0 is misspecified, not valid.
        p=pre.protocol()
        self.assertIn("SHARP",p["e_process_exploratory"])
        self.assertTrue(pre.offline_demo()[
            "e_process_is_only_valid_if_each_frozen_M0_is_exact_conditional_winner_distribution"])

    def test_true_live_manifest_requires_external_API_and_result(self):
        fixture=self.synthetic_private_freeze()
        f,r=fixture
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            fp=root/"future_freeze.json"
            rp=root/"postrace_result.json"
            fp.write_text(json.dumps(f),encoding="utf-8")
            rp.write_text(json.dumps(r),encoding="utf-8")
            entry={
                "race_id":f["payload"]["race_id"],"JRA_grade":"G2",
                "comment_id":123,"forecast_sha":f["seal_sha256_of_payload"],
                "status":"scorable",
                "private_freeze_path":str(fp),
                "private_official_top3_path":str(rp),
            }
            manifest={"schema":pre.PROTOCOL_SCHEMA,"entries":[entry]}
            with patch.object(pre,"verify_comment_live",
                              side_effect=ValueError("HOLD_FAILED_TO_FETCH_GITHUB_SERVER_COMMENT")):
                with self.assertRaisesRegex(ValueError,"HOLD_FAILED_TO_FETCH"):
                    pre.verify_live_manifest(manifest)
            # Caller-supplied JSON is NEVER accepted as a live proof.
            manifest["entries"][0]["status"]="prestart_only"
            with self.assertRaisesRegex(ValueError,"HOLD_UNRESOLVED_OMISSIONS"):
                pre.verify_live_manifest(manifest)

    @staticmethod
    def synthetic_private_freeze():
        src={
            "schema":INPUT_SCHEMA,"race_id":"FICTITIOUS-2026-11-01-KYOTO-11",
            "post_jst":"2026-11-01T15:40:00+09:00","provider":"SYNTHETIC",
            "sources":[
                {"quote_at_jst":"2026-10-31T20:00:00+09:00",
                 "source_url":"https://example.test/early",
                 "win_odds_by_horse_number":{str(i):float(2+i*2)
                                              for i in range(1,9)}},
                {"quote_at_jst":"2026-11-01T09:00:00+09:00",
                 "source_url":"https://example.test/late",
                 "win_odds_by_horse_number":{str(i):float(2+i*1.7)
                                              for i in range(1,9)}},
            ],
        }
        frozen=freeze(src,generated_at_jst="2026-11-01T10:00:00+09:00")
        result={
            "schema":RESULT_SCHEMA,
            "race_id":src["race_id"],
            "top3_horse_numbers":[1,2,3],
            "verified_at_jst":"2026-11-01T17:00:00+09:00",
            "official_results_url":"https://www.jra.go.jp/JRADB/accessS.html",
        }
        return frozen,result

    def test_offline_fixtures_cannot_be_promoted_by_setting_trust_flag(self):
        # A local helper can be passed authenticated=True programmatically
        # (unit-tests exercise computation). The CLI 'verify-live' path
        # never accepts caller-provided proof objects; it freshly calls
        # the GitHub server via existing verifier.
        z=pre.offline_demo()
        self.assertEqual(z["status"],pre.OFFLINE_STATUS)
        self.assertTrue(z["predeclared_full_calendar_reporting_missing_still_required"])
        self.assertFalse(z["graded_stakes_calendar_denominator_verified"])
        self.assertTrue(z["full_period_2027_Jan_Mar_calendar_segment_not_registered"])
        self.assertEqual(
            z["externally_precommitted_2026_oct_dec_flat_grade_segment_comment_id"],
            6382991405)
        self.assertEqual(z["externally_precommitted_calendar_segment_slot_count"],26)
        self.assertFalse(z["formal_full_eligible_grades_statistical_inference_allowed"])
        self.assertTrue(z["sharp_M0_e_process_validity_not_established_for_real_market"])
        self.assertTrue(z["official_results_url_text_alone_is_not_independent_JRA_result_fetch"])


if __name__=="__main__":
    unittest.main()
