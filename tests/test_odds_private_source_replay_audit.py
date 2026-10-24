#!/usr/bin/env python3
"""Prove exact source bytes recreate every sealed ranking probability pre-result."""
from copy import deepcopy
from hashlib import sha256
import json,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_public_two_point_freeze import INPUT_SCHEMA,freeze,seal
from odds_private_source_replay_audit import STATUS,audit


class SourceReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src={
            "schema":INPUT_SCHEMA,"race_id":"FICTIONAL-2030-KYOTO-11",
            "post_jst":"2030-01-01T15:40:00+09:00",
            "provider":"SYNTHETIC_PUBLIC_TEST",
            "sources":[
                {
                    "quote_at_jst":"2029-12-31T22:57:00+09:00",
                    "source_url":"https://example.test/early",
                    "win_odds_by_horse_number":{
                        str(i):float(1.9+1.6*i) for i in range(1,9)}
                },
                {
                    "quote_at_jst":"2030-01-01T09:23:00+09:00",
                    "source_url":"https://example.test/late",
                    "win_odds_by_horse_number":{
                        str(i):float(1.9+1.8*i) for i in range(1,9)}
                }
            ]
        }
        cls.raw=(json.dumps(cls.src,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
        cls.sha=sha256(cls.raw).hexdigest()
        cls.frozen=freeze(cls.src,source_file_sha=cls.sha,
                          generated_at_jst="2030-01-01T12:00:00+09:00")

    def test_identical_private_source_recreates_every_model(self):
        result=audit(self.raw,self.frozen,
                     expected_sha=self.frozen["seal_sha256_of_payload"],
                     expected_source_sha=self.sha)
        self.assertEqual(result["status"],STATUS)
        self.assertEqual(result["full_horse_count"],8)
        self.assertEqual(result["full_unordered_top3_combination_count"],56)
        self.assertEqual(result["model_names_in_original_precommit_order"],[
            "M0_market_only","M1_smooth_beta025","M2_initial_10x_beta025"])
        self.assertTrue(result["all_three_joint_rank_distributions_identically_recomputed"])
        self.assertFalse(result["official_result_read_before_or_during_replay"])
        self.assertFalse(result["raw_odds_or_individual_probability_values_exported"])
        self.assertFalse(result["GitHub_server_prestart_evidence_fetched"])
        self.assertTrue(result["does_not_promote_to_formal_v31_holdout"])

    def test_source_raw_bytes_sha_is_not_just_normalized_json(self):
        amended=self.raw+b" "
        self.assertEqual(json.loads(amended),self.src)
        with self.assertRaisesRegex(ValueError,"HOLD_PRECOMMITTED_PRIVATE_SOURCE_SHA_CHANGED"):
            audit(amended,self.frozen,expected_source_sha=self.sha)
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_SOURCE_SHA_NOT_LINKED"):
            audit(amended,self.frozen)

    def test_tampering_precommit_or_registered_coefficients_causes_hold(self):
        with self.assertRaisesRegex(ValueError,"HOLD_PRECOMMITTED_FORECAST_SHA_CHANGED"):
            audit(self.raw,self.frozen,expected_sha="a"*64)
        data=deepcopy(self.frozen)
        data["payload"]["models"][1]["beta"]=.33
        data["seal_sha256_of_payload"]=seal(data["payload"])
        with self.assertRaisesRegex(ValueError,"HOLD_FORECAST_NOT_REPRODUCIBLE"):
            audit(self.raw,data)

    def test_tampered_top3_probability_with_resealed_digest_still_fails(self):
        data=deepcopy(self.frozen)
        data["payload"]["predictions"]["M2_initial_10x_beta025"][
            "top3"][0]["p"]+=.015
        data["seal_sha256_of_payload"]=seal(data["payload"])
        with self.assertRaisesRegex(ValueError,"HOLD_FORECAST_NOT_REPRODUCIBLE"):
            audit(self.raw,data)

    def test_race_roster_or_quote_values_changed_even_same_schema_hold(self):
        src=deepcopy(self.src)
        src["sources"][0]["win_odds_by_horse_number"]["1"]=12.5
        edited=(json.dumps(src,ensure_ascii=False,indent=2)+"\n").encode()
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_SOURCE_SHA_NOT_LINKED"):
            audit(edited,self.frozen)

    def test_output_contains_aggregates_and_no_raw_provider_odds(self):
        q=audit(self.raw,self.frozen)
        j=json.dumps(q,ensure_ascii=False)
        self.assertNotIn("win_odds_by_horse_number",j)
        self.assertNotIn("predictions",q)
        self.assertNotIn("model_valuation",q)
        self.assertTrue(q["all_models_recreated_by_same_precommitted_formula"])
        self.assertEqual(q["source_raw_file_sha256"],self.sha)


if __name__=="__main__":
    unittest.main()
