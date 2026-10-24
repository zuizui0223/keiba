#!/usr/bin/env python3
"""Every discrimination metric is computed before any official podium exists."""
from copy import deepcopy
from hashlib import sha256
import json,math
from pathlib import Path
import sys,unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from odds_public_two_point_freeze import INPUT_SCHEMA,freeze,seal
from odds_preoutcome_discriminability import (
    STATUS,MAIN,EXPL,audit,_two_point_contrast,_validated_distributions
)


def fictional_freeze():
    sample={
        "schema":INPUT_SCHEMA,"race_id":"FICTITIOUS-2030-KYOTO-11",
        "post_jst":"2030-01-01T15:40:00+09:00",
        "provider":"FICTIONAL_SOURCE_NOT_JRA",
        "sources":[
            {"quote_at_jst":"2029-12-31T20:00:00+09:00",
             "source_url":"https://example.test/early",
             "win_odds_by_horse_number":{
                 str(i):float(1.5+2.2*i) for i in range(1,9)}},
            {"quote_at_jst":"2030-01-01T08:00:00+09:00",
             "source_url":"https://example.test/late",
             "win_odds_by_horse_number":{
                 str(i):float(1.9+1.7*i) for i in range(1,9)}}
        ]
    }
    return freeze(sample,generated_at_jst="2030-01-01T09:00:00+09:00")


class PreOutcomeSeparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen=fictional_freeze()
        cls.report=audit(cls.frozen)

    def test_joint_market_models_separate_synthetic_without_podium(self):
        v=self.report
        self.assertEqual(v["status"],STATUS)
        self.assertFalse(v["official_result_used"])
        self.assertTrue(v["no_future_result_or_next_market_file_read"])
        self.assertFalse(v["model_coefficients_chosen_or_retrained_now"])
        self.assertEqual(v["fixed_primary"],
                         "M1 winner logloss minus M0 winner logloss")
        self.assertEqual(set(v["comparison"]),{MAIN,EXPL})
        self.assertEqual(v["freeze_seal_sha256"],
                         self.frozen["seal_sha256_of_payload"])
        for compare in v["comparison"].values():
            w=compare["winning_horse"]
            self.assertEqual(w["total_possible_winner_count"],8)
            self.assertEqual(compare["trio_event"][
                "unordered_top3_combination_count"],56)
            self.assertGreater(w["KL_baseline_to_candidate_nats"],0)
            self.assertGreater(w["KL_candidate_to_baseline_nats"],0)
            self.assertGreater(w["categorical_distribution_TV_pp"],0)
            self.assertAlmostEqual(
                w["expected_logloss_candidate_minus_baseline_if_baseline_true"],
                w["KL_baseline_to_candidate_nats"],places=12)
            self.assertAlmostEqual(
                w["expected_logloss_candidate_minus_baseline_if_candidate_true"],
                -w["KL_candidate_to_baseline_nats"],places=12)

    def test_top3_Brier_expected_difference_is_exact_marginal_square_distance(self):
        for model in self.report["comparison"].values():
            z=model["top3_horse_binary_brier"]
            self.assertGreater(z["mean_squared_change_in_top3_marginals"],0)
            self.assertAlmostEqual(
                z["expected_Brier_delta_if_baseline_true"],
                z["mean_squared_change_in_top3_marginals"],places=12)
            self.assertAlmostEqual(
                z["expected_Brier_delta_if_candidate_true"],
                -z["mean_squared_change_in_top3_marginals"],places=12)
            self.assertLess(
                z["minimum_possible_top3_Brier_difference"],0)
            self.assertGreater(
                z["maximum_possible_top3_Brier_difference"],0)

    def test_no_realized_top3_or_per_horse_probability_array_is_exported(self):
        report=self.report
        self.assertNotIn("actual_top3",str(report))
        self.assertNotIn("official_jra_top3",str(report))
        self.assertNotIn("win_odds_by_horse_number",str(report))
        self.assertNotIn("horse_number",json.dumps(report))
        self.assertNotIn("predictions",report)
        for model in report["comparison"].values():
            self.assertTrue(model[
                "probability_forecasts_previously_sealed_not_reoptimized"])

    def test_expected_original_digest_must_match_precommitment(self):
        val=self.frozen["seal_sha256_of_payload"]
        self.assertEqual(audit(self.frozen,expected_seal=val),self.report)
        with self.assertRaisesRegex(ValueError,"HOLD_SHA_NOT_THE_PRECOMMITTED_DIGEST"):
            audit(self.frozen,expected_seal="f"*64)
        damaged=deepcopy(self.frozen)
        damaged["payload"]["models"][1]["beta"]=.99
        with self.assertRaisesRegex(ValueError,"HOLD_SEALED_FORECAST_CONTENT_CHANGED"):
            audit(damaged)

    def test_modified_valid_seal_but_incoherent_trio_probability_rejected(self):
        tampered=deepcopy(self.frozen)
        trio=tampered["payload"]["predictions"][MAIN]["trio"]
        trio[0]["p"]+=.1
        tampered["seal_sha256_of_payload"]=seal(tampered["payload"])
        with self.assertRaisesRegex(ValueError,"HOLD_INCOHERENT_FROZEN_PROBABILITY_MASS"):
            audit(tampered)
        tampered=deepcopy(self.frozen)
        p=tampered["payload"]["predictions"][MAIN]
        p["top3"][0]["p"]+=.05
        p["top3"][1]["p"]-=.05
        tampered["seal_sha256_of_payload"]=seal(tampered["payload"])
        with self.assertRaisesRegex(ValueError,"HOLD_TOP3_AND_TRIO_MARGINALS_DISAGREE"):
            audit(tampered)

    def test_cannot_later_change_registered_primary_even_resealed(self):
        tampered=deepcopy(self.frozen)
        tampered["payload"]["predeclared_primary_contrast"]=(
            "trio_log_loss_M1_minus_M0")
        tampered["seal_sha256_of_payload"]=seal(tampered["payload"])
        with self.assertRaisesRegex(ValueError,"HOLD_PRIMARY_CONTRAST_CHANGED"):
            audit(tampered)

    def test_no_longer_has_any_difference_if_same_models(self):
        predictions=_validated_distributions(self.frozen["payload"])
        base=predictions["M0_market_only"]
        z=_two_point_contrast(base,base)
        self.assertAlmostEqual(z["winning_horse"][
            "categorical_distribution_TV_pp"],0,places=12)
        self.assertAlmostEqual(z["trio_event"][
            "KL_baseline_to_candidate_nats"],0,places=12)
        self.assertAlmostEqual(z["top3_horse_binary_brier"][
            "mean_squared_change_in_top3_marginals"],0,places=12)
        self.assertEqual(z["winning_horse"][
            "possible_winner_count_candidate_better"],0)


if __name__=="__main__":
    unittest.main()
