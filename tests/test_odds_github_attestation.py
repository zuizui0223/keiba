#!/usr/bin/env python3
"""Synthetic SHA-only GitHub attestation fixtures. NO live prestart run exists."""
from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import odds_github_attestation as att
from odds_shadow_freeze_score import synthetic_demo, build_freeze


class GitHubAttestationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source,cls.official=synthetic_demo()
        cls.freeze=build_freeze(cls.source)
        cls.dispatch=att.prepare_dispatch(cls.freeze)
        cls.receipt=att.runner_receipt(
            repo=att.REPOSITORY,run_id=314159,run_attempt=1,
            event="workflow_dispatch",
            workflow_ref=f"{att.REPOSITORY}/{att.WORKFLOW_PATH}@refs/heads/main",
            inputs=att.dispatch_inputs(cls.freeze))
        cls.remote={
            "id":314159,"run_attempt":1,"event":"workflow_dispatch",
            "status":"completed","conclusion":"success","head_branch":"main",
            "repository":{"full_name":att.REPOSITORY},
            "path":f"{att.WORKFLOW_PATH}@refs/heads/main",
            "display_title":f"odds-preseal/{cls.source['race_id']}",
            "created_at":"2030-01-01T04:32:00Z",
            "html_url":f"https://github.com/{att.REPOSITORY}/actions/runs/314159",
        }

    def test_prepared_dispatch_only_has_four_safe_strings(self):
        d=self.dispatch
        self.assertEqual(d["status"],"PREPARED_ONLY_NO_GITHUB_DISPATCH_HAS_OCCURRED")
        self.assertEqual(d["ref"],"main")
        self.assertEqual(d["repo"],att.REPOSITORY)
        self.assertEqual(set(d["inputs"]),{
            "race_id","seal_sha256","scheduled_post_jst","last_source_received_jst"})
        self.assertEqual(len(d["inputs"]["seal_sha256"]),64)
        self.assertNotIn("odds_by_horse_number",str(d))
        self.assertNotIn("predicted_probabilities",str(d))
        self.assertFalse(d["external_prestart_evidence_present"])

    def test_offline_generated_fixture_never_claims_remote_trust(self):
        demo=att.demo()
        self.assertEqual(demo["status"],att.STATUS_OFFLINE)
        self.assertFalse(demo["independent_fetch_performed"])
        self.assertTrue(demo["fixtures_can_be_fabricated_no_remote_evidence"])
        self.assertTrue(demo["trusted_external_claim_limited_to_digest_preexistence"])
        offline=att.inspect_fixture(
            self.freeze,self.receipt,self.remote,[self.remote])
        self.assertEqual(offline["status"],att.STATUS_OFFLINE)
        self.assertAlmostEqual(offline["safe_margin_minutes_from_github_created_to_post"],28)
        self.assertTrue(offline["does_not_append_to_v31_holdout"])

    def test_untrusted_receipt_content_tamper_fails(self):
        for key,bad in (
            ("seal_sha256","a"*64),
            ("race_id","FICTITIOUS-OTHER"),
            ("scheduled_post_jst","2030-01-02T14:00:00+09:00"),
            ("last_source_received_jst","2030-01-01T12:00+09:00"),
        ):
            corrupted=deepcopy(self.receipt)
            corrupted["submitted_commitment_inputs"][key]=bad
            with self.assertRaisesRegex(ValueError,"HOLD_REMOTE_COMMITMENT_INPUT_MISMATCH"):
                att.inspect_fixture(self.freeze,corrupted,self.remote,[self.remote])
        damaged=deepcopy(self.freeze)
        damaged["payload"]["model_coefficients"]["predeclared_hierarchy"][
            "beta_pair"]=.9
        with self.assertRaisesRegex(ValueError,"HOLD_FREEZE_DIGEST"):
            att.inspect_fixture(damaged,self.receipt,self.remote,[self.remote])

    def test_run_not_completed_on_default_branch_is_not_accepted(self):
        for key,bad in (
            ("status","in_progress"),
            ("conclusion","failure"),
            ("event","push"),
            ("head_branch","analysis/odds"),
            ("path",".github/workflows/random.yml@refs/heads/main"),
            ("display_title","odds-preseal/ANOTHER-RACE"),
            ("run_attempt",2),
        ):
            o=deepcopy(self.remote)
            o[key]=bad
            with self.assertRaisesRegex(ValueError,"HOLD_GITHUB_RUN_METADATA"):
                att.inspect_fixture(self.freeze,self.receipt,o,[o])
        o=deepcopy(self.remote)
        o["repository"]["full_name"]="not-this-repository/keiba"
        with self.assertRaisesRegex(ValueError,"HOLD_GITHUB_RUN_METADATA"):
            att.inspect_fixture(self.freeze,self.receipt,o,[o])

    def test_late_server_received_commitment_cannot_be_backdated_by_local_time(self):
        for created in (
            "2030-01-01T03:29:00Z", # before last 13:30:05 JST source receipt
            "2030-01-01T04:30:00Z", # before claimed 13:31 freeze clock
            "2030-01-01T04:51:00Z", # after 13:50 JST prepost cutoff
            "2030-01-01T05:01:00Z", # after the 14:00 post itself
        ):
            o=deepcopy(self.remote)
            o["created_at"]=created
            with self.assertRaisesRegex(ValueError,"HOLD_NOT_GITHUB_SERVER_PRESTART_SHA"):
                att.inspect_fixture(self.freeze,self.receipt,o,[o])

    def test_first_submission_only_prevents_later_cherry_picking(self):
        # Even a previous failed attempt with the same display_title
        # should be counted as an earlier attempt; it is not discardable.
        earlier=deepcopy(self.remote)
        earlier["id"]=314158
        earlier["created_at"]="2030-01-01T04:31:30Z"
        earlier["conclusion"]="failure"
        with self.assertRaisesRegex(ValueError,"HOLD_EARLIER_SAME_RACE"):
            att.inspect_fixture(self.freeze,self.receipt,self.remote,
                                [earlier,self.remote])
        later=deepcopy(self.remote)
        later["id"]=314160
        later["created_at"]="2030-01-01T04:33:00Z"
        valid=att.inspect_fixture(self.freeze,self.receipt,self.remote,
                                  [self.remote,later])
        self.assertEqual(valid["status"],att.STATUS_OFFLINE)
        missing=deepcopy(self.remote)
        missing["id"]=999
        with self.assertRaisesRegex(ValueError,"HOLD_COMMITTED_RUN_ABSENT"):
            att.inspect_fixture(self.freeze,self.receipt,self.remote,[missing])

    def test_runner_must_be_single_default_branch_workflow_dispatch(self):
        args={
            "repo":att.REPOSITORY,
            "run_id":314159,"run_attempt":1,"event":"workflow_dispatch",
            "workflow_ref":f"{att.REPOSITORY}/{att.WORKFLOW_PATH}@refs/heads/main",
            "inputs":att.dispatch_inputs(self.freeze),
        }
        self.assertEqual(att.runner_receipt(**args),self.receipt)
        for k,bad in (("event","push"),("run_attempt",2),
                      ("repo","other/repo"),("run_id",0),
                      ("workflow_ref","other/repo/.github/workflows/odds-shadow-attest.yml@refs/heads/main")):
            invalid={**args,k:bad}
            with self.assertRaisesRegex(ValueError,"HOLD_NOT_DEFAULT_BRANCH"):
                att.runner_receipt(**invalid)
        invalid={**args,"inputs":{**args["inputs"],"seal_sha256":"notSHA"}}
        with self.assertRaisesRegex(ValueError,"HOLD_SHA256"):
            att.runner_receipt(**invalid)

    def test_unsafe_race_ids_rejected_before_dispatch(self):
        for bad in ("..","race\nnew","race; ls","/race","🐎"):
            badfreeze=deepcopy(self.freeze)
            badfreeze["payload"]["race_id"]=bad
            from odds_shadow_freeze_score import _seal
            badfreeze["seal_sha256_of_canonical_payload"]=_seal(
                badfreeze["payload"])
            with self.assertRaisesRegex(ValueError,"HOLD_UNSAFE_OR_INVALID_RACE_ID"):
                att.dispatch_inputs(badfreeze)

    def test_local_only_does_not_impersonate_first_party_timestamps(self):
        data=deepcopy(self.freeze)
        data["payload"]["local_prediction_recorded_at_jst"]="2030-01-01T13:31:00"
        from odds_shadow_freeze_score import _seal
        data["seal_sha256_of_canonical_payload"]=_seal(data["payload"])
        receipt=deepcopy(self.receipt)
        receipt["submitted_commitment_inputs"]["seal_sha256"]=data[
            "seal_sha256_of_canonical_payload"]
        with self.assertRaisesRegex(ValueError,"HOLD_ATTESTATION_TIMEZONE"):
            att.inspect_fixture(data,receipt,self.remote,[self.remote])

    def test_script_cannot_claim_live_without_independent_GH_CLI(self):
        with patch.object(att, "_gh_json", side_effect=ValueError("HOLD_GITHUB_CLI_INDEPENDENT_FETCH_FAILED")):
            with self.assertRaisesRegex(ValueError,"HOLD_GITHUB_CLI_INDEPENDENT_FETCH"):
                att.verify_live(self.freeze,repo=att.REPOSITORY,run_id=314159)


if __name__=="__main__":
    unittest.main()
