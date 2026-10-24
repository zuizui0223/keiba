#!/usr/bin/env python3
"""Outcome-free scoring information-power envelope in sharp PL reference worlds."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_public_two_point_freeze import INPUT_SCHEMA,freeze,seal
from odds_preoutcome_discriminability import audit as discriminability
from odds_sharp_reference_power_envelope import (
    STATUS, _weights, _moment, audit, cdf, normal_two_sided_power,
    minimal_theoretical_replica_count
)


def synthetic_snapshot(*,same=False):
    before={str(i):1.5+1.8*i for i in range(1,10)}
    after=(dict(before) if same else
           {str(i):2.0+1.1*i for i in range(1,10)})
    payload={
        "schema":INPUT_SCHEMA, "race_id":"FICTITIOUS-2030-NO-REAL-MARKET",
        "post_jst":"2030-01-01T15:40:00+09:00","provider":"FICTIONAL",
        "sources":[
            {"quote_at_jst":"2029-12-31T21:00:00+09:00",
             "source_url":"https://example.test/early",
             "win_odds_by_horse_number":before},
            {"quote_at_jst":"2030-01-01T09:00:00+09:00",
             "source_url":"https://example.test/late",
             "win_odds_by_horse_number":after},
        ],
    }
    return freeze(payload,generated_at_jst="2030-01-01T11:00:00+09:00")


class SharpReferencePowerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen=synthetic_snapshot()

    def test_preoutcome_KL_and_moment_expectation_are_exactly_consistent(self):
        p=audit(self.frozen)
        d=discriminability(self.frozen)["comparison"]["M1_smooth_beta025"][
            "winning_horse"]
        self.assertEqual(p["status"],STATUS)
        a=p["model_reference_moments"]["M0_is_exact_truth"]
        b=p["model_reference_moments"]["M1_is_exact_truth"]
        self.assertAlmostEqual(a["expected_M1_minus_M0_winner_logloss"],
                               d["KL_baseline_to_candidate_nats"],places=12)
        self.assertAlmostEqual(b["expected_M1_minus_M0_winner_logloss"],
                               -d["KL_candidate_to_baseline_nats"],places=12)
        self.assertGreater(a["expected_M1_minus_M0_winner_logloss"],0)
        self.assertLess(b["expected_M1_minus_M0_winner_logloss"],0)
        self.assertEqual(p["n_win_horses"],9)
        self.assertFalse(p["race_or_result_outcome_was_loaded"])
        self.assertFalse(p["actual_calibration_or_market_advantage_tested"])

    def test_normal_power_is_monotone_and_requires_many_identical_replicas(self):
        x=audit(self.frozen)
        for row in x["model_reference_moments"].values():
            p20=row["CLT_power_if_N_20"]
            p60=row["CLT_power_if_N_60"]
            p1000=row["CLT_power_if_N_1000"]
            n=row["number_of_identical_independent_replicas_at_requested_power"]
            self.assertLess(p20,p60)
            self.assertLess(p60,p1000)
            self.assertGreater(n,100)
            self.assertGreaterEqual(
                normal_two_sided_power(
                    row["expected_M1_minus_M0_winner_logloss"],
                    row["single_race_M1_minus_M0_logloss_standard_deviation"],
                    n),.8)
            self.assertLess(
                normal_two_sided_power(
                    row["expected_M1_minus_M0_winner_logloss"],
                    row["single_race_M1_minus_M0_logloss_standard_deviation"],
                    n-1),.8)
        self.assertTrue(x["not_a_recommended_number_of_real_races"])
        self.assertTrue(x[
            "independence_and_identical_forecast_assumptions_known_false_as_a_description_of_future_races"])

    def test_identical_market_and_path_forecasts_have_no_detectable_separation(self):
        x=audit(synthetic_snapshot(same=True))
        self.assertEqual(x["status"],
                         "HOLD_IDENTICAL_FROZEN_WIN_MODELS_CANNOT_DISCRIMINATE")
        for v in x["model_reference_moments"].values():
            self.assertAlmostEqual(
                v["expected_M1_minus_M0_winner_logloss"],0,places=12)
            self.assertIsNone(
                v["number_of_identical_independent_replicas_at_requested_power"])
        self.assertAlmostEqual(normal_two_sided_power(0,0,100),.05,places=12)

    def test_resealed_modified_model_rejected_against_expected_first_sha(self):
        known=self.frozen["seal_sha256_of_payload"]
        self.assertEqual(audit(self.frozen,expected_seal=known),
                         audit(self.frozen))
        changed=deepcopy(self.frozen)
        changed["payload"]["models"][1]["beta"]=0.75
        changed["seal_sha256_of_payload"]=seal(changed["payload"])
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_NOT_THE_EXTERNALLY_PRECOMMITTED"):
            audit(changed,expected_seal=known)
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_SEALED_FORECAST_CONTENT_CHANGED"):
            audit({**self.frozen,
                   "payload":changed["payload"]},expected_seal=known)

    def test_no_winner_numbers_or_private_individual_probabilities_are_exported(self):
        result=audit(self.frozen)
        self.assertNotIn("predictions",result)
        self.assertNotIn("actual_top3",str(result))
        self.assertNotIn("win_odds_by_horse_number",str(result))
        self.assertNotIn("weights",result)
        self.assertNotIn("horse_number",str(result))
        self.assertTrue(result["source_market_or_future_result_used"] is False)

    def test_invalid_statistical_power_parameters_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"HOLD_BAD_NORMAL"):
            normal_two_sided_power(.01,.05,0)
        with self.assertRaisesRegex(ValueError,"HOLD_NEGATIVE"):
            normal_two_sided_power(.01,-1,20)
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_POWER_TARGET"):
            minimal_theoretical_replica_count(.01,.05,target_power=1)
        self.assertAlmostEqual(cdf(0),.5,places=15)


if __name__=="__main__":
    unittest.main()
