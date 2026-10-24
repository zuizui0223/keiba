#!/usr/bin/env python3
"""Independent stdlib-only preseal receiver tests: no model or raw odds."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from odds_sha_only_receipt import (
    SCHEMA,REPOSITORY,WORKFLOW_PATH,receive,receive_environment
)


class SHAOnlyReceiptTests(unittest.TestCase):
    @staticmethod
    def good():
        return {
            "repo":REPOSITORY,"run_id":112233,"attempt":1,
            "event":"workflow_dispatch",
            "workflow_ref":f"{REPOSITORY}/{WORKFLOW_PATH}@refs/heads/main",
            "inputs":{
                "race_id":"2026-11-01-KYOTO-11",
                "seal_sha256":"a"*64,
                "scheduled_post_jst":"2026-11-01T15:40:00+09:00",
                "last_source_received_jst":"2026-11-01T15:10:00+09:00",
            }
        }

    def test_exact_four_safe_fields_and_required_source_clock(self):
        x=receive(**self.good())
        self.assertEqual(x["schema"],SCHEMA)
        self.assertEqual(x["run_id"],112233)
        self.assertEqual(x["run_attempt"],1)
        self.assertEqual(x["submitted_commitment_inputs"]["seal_sha256"],"a"*64)
        self.assertEqual(len(x["submitted_commitment_inputs"]),4)
        self.assertTrue(x["contains_only_digest_and_nonsecret_race_time_metadata"])
        self.assertTrue(x["external_created_at_NOT_INCLUDED_MUST_FETCH_GITHUB_API"])
        self.assertTrue(x["local_receipt_alone_does_not_prove_prepost_submission"])
        self.assertEqual(x["artifact_name"],"winwide-sha-commitment-112233")
        self.assertNotIn("odds_by_horse_number",json.dumps(x))
        self.assertNotIn("predicted_probabilities",json.dumps(x))

    def test_dispatch_cannot_be_a_push_or_unsupported_branch(self):
        for name,invalid in (
            ("event","push"),("attempt",2),("run_id",0),
            ("repo","untrusted/repo"),
            ("workflow_ref",f"{REPOSITORY}/{WORKFLOW_PATH}@refs/heads/other")):
            settings=self.good()
            settings[name]=invalid
            with self.assertRaisesRegex(ValueError,"HOLD_DISPATCH_NOT_DEFAULT_BRANCH"):
                receive(**settings)

    def test_only_valid_sha_and_public_race_id(self):
        for key,value in (
            ("seal_sha256","z"*64),
            ("seal_sha256","a"*63),
            ("race_id","2026/11/01 KYOTO"),
            ("race_id","name;cat"),
            ("race_id","🐎"),
        ):
            args=self.good()
            args["inputs"][key]=value
            with self.assertRaisesRegex(ValueError,"HOLD_UNSAFE_RACE_ID_OR_INVALID_SHA"):
                receive(**args)

    def test_no_extra_provider_prices_in_submitted_payload(self):
        args=self.good()
        args["inputs"]["win_odds"]={"1":2.1}
        with self.assertRaisesRegex(ValueError,"HOLD_EXTRA_DISPATCH_INPUT_FIELDS"):
            receive(**args)

    def test_receipt_rejects_ambiguous_or_late_clocks(self):
        args=self.good()
        args["inputs"]["scheduled_post_jst"]="2026-11-01T15:40:00"
        with self.assertRaisesRegex(ValueError,"HOLD_EXPLICIT_TIMEZONE"):
            receive(**args)
        args=self.good()
        args["inputs"]["last_source_received_jst"]="2026-11-01T15:31:00+09:00"
        with self.assertRaisesRegex(ValueError,"HOLD_INPUT_SOURCE_AFTER_PREPOST_CUTOFF"):
            receive(**args)

    def test_true_GitHub_env_shape_matches_normal_call(self):
        d=self.good()
        env={
            "GITHUB_REPOSITORY":d["repo"],
            "GITHUB_RUN_ID":str(d["run_id"]),
            "GITHUB_RUN_ATTEMPT":str(d["attempt"]),
            "GITHUB_EVENT_NAME":d["event"],
            "GITHUB_WORKFLOW_REF":d["workflow_ref"],
            "SEAL_RACE_ID":d["inputs"]["race_id"],
            "SEAL_SHA256":d["inputs"]["seal_sha256"],
            "SEAL_POST_JST":d["inputs"]["scheduled_post_jst"],
            "SEAL_RECEIVED_JST":d["inputs"]["last_source_received_jst"],
        }
        self.assertEqual(receive_environment(env),receive(**d))
        env.pop("SEAL_SHA256")
        with self.assertRaisesRegex(ValueError,"HOLD_MISSING_SHA_ONLY_GITHUB_INPUT"):
            receive_environment(env)

    def test_workflow_only_accepts_four_dispatch_strings_no_raw_data(self):
        workflow=(ROOT/".github/workflows/odds-shadow-attest.yml").read_text(
            encoding="utf-8")
        self.assertIn("on:\n  workflow_dispatch:",workflow)
        self.assertIn("odds-preseal/${{ inputs.race_id }}",workflow)
        self.assertIn("python scripts/odds_sha_only_receipt.py runner",workflow)
        for field in (
            "SEAL_SHA256: ${{ inputs.seal_sha256 }}",
            "SEAL_POST_JST: ${{ inputs.scheduled_post_jst }}",
            "SEAL_RECEIVED_JST: ${{ inputs.last_source_received_jst }}",
        ):
            self.assertIn(field,workflow)
        self.assertNotIn("odds_by_horse_number",workflow)
        self.assertNotIn("predicted_probabilities",workflow)

    def test_only_offline_fixture_no_run_created_at_claim(self):
        sample=receive(**self.good())
        self.assertNotIn("github_server_created_at",sample)
        self.assertNotIn("verified_future_win_rate",sample)
        self.assertNotIn("true_win_odds",sample)


if __name__=="__main__":
    unittest.main()
