#!/usr/bin/env python3
"""GitHub PR comment server timestamp proof tests; no live GH proof fabricated."""
from copy import deepcopy
from datetime import datetime,timedelta
from pathlib import Path
import json,sys,unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_public_two_point_freeze import (
    INPUT_SCHEMA,RESULT_SCHEMA,freeze,verify_freeze,score,seal
)
import odds_public_comment_attestation as att


def mock_source():
    return {
        "schema":INPUT_SCHEMA,
        "race_id":"2030-01-01-KYOTO-11",
        "post_jst":"2030-01-01T15:40:00+09:00",
        "provider":"SYNTHETIC",
        "sources":[
            {"quote_at_jst":"2029-12-31T20:00:00+09:00",
             "source_url":"https://example.test/race/2030/early",
             "win_odds_by_horse_number":{str(i):1.5+i*2 for i in range(1,9)}},
            {"quote_at_jst":"2030-01-01T09:00:00+09:00",
             "source_url":"https://example.test/race/2030/late",
             "win_odds_by_horse_number":{str(i):1.7+i*1.8 for i in range(1,9)}},
        ]
    }


class GitHubCommentPresealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=mock_source()
        cls.frozen=freeze(cls.source,generated_at_jst="2030-01-01T13:00:00+09:00")
        p=cls.frozen["payload"]
        cls.comment={
            "id":att.COMMENT_ID,
            "created_at":"2030-01-01T04:05:00Z",
            "updated_at":"2030-01-01T04:05:00Z",
            "body":(
                f"{att.HEADER}2030年 菊花賞\n"
                f"- race_id: {p['race_id']}\n"
                f"- freeze_payload_sha256: {cls.frozen['seal_sha256_of_payload']}\n"
                f"- private_source_json_sha256: {p['source_private_input_sha256']}\n"
            )
        }

    def test_freeze_joint_probability_and_no_result_lookahead(self):
        f=self.frozen
        p=verify_freeze(f)
        self.assertEqual(p["race_id"],"2030-01-01-KYOTO-11")
        self.assertTrue(p["outcome_loaded_before_freeze"] is False)
        self.assertEqual(len(p["predictions"]),3)
        for m in p["predictions"].values():
            self.assertAlmostEqual(sum(x["p"] for x in m["win"]),1,places=10)
            self.assertAlmostEqual(sum(x["p"] for x in m["top3"]),3,places=10)
            self.assertAlmostEqual(sum(x["p"] for x in m["trio"]),1,places=10)
        self.assertEqual(p["models"][1]["beta"],0.25)
        self.assertEqual(p["models"][2]["earlier_odds_threshold"],10.0)

    def test_fixture_matches_but_never_fakes_independent_remote_receipt(self):
        x=att.offline_fixture_check(self.frozen,self.comment,[self.comment])
        self.assertEqual(x["status"],att.STATUS_OFFLINE)
        self.assertFalse(x["GitHub_API_independently_fetched"])
        self.assertEqual(x["sha256_of_original_frozen_payload"],
                         self.frozen["seal_sha256_of_payload"])
        self.assertAlmostEqual(x["lead_time_hours"],26+35/60)

    def test_hash_or_source_sha_mismatch_hard_fail(self):
        for key in ("freeze_payload_sha256","private_source_json_sha256"):
            bad=deepcopy(self.comment)
            old=(self.frozen["seal_sha256_of_payload"]
                 if key=="freeze_payload_sha256" else
                 self.frozen["payload"]["source_private_input_sha256"])
            bad["body"]=bad["body"].replace(old,"f"*64)
            with self.assertRaisesRegex(ValueError,"HOLD_SHA_OR_RACE"):
                att.inspect_records(self.frozen,bad,[bad])

    def test_comment_edit_and_late_comment_rejected(self):
        bad=deepcopy(self.comment)
        bad["updated_at"]="2030-01-01T04:06:00Z"
        with self.assertRaisesRegex(ValueError,"HOLD_POSTED_SHA_COMMENT_WAS_EDITED"):
            att.inspect_records(self.frozen,bad,[bad])
        bad=deepcopy(self.comment)
        bad["created_at"]=bad["updated_at"]="2030-01-01T06:35:00Z"
        with self.assertRaisesRegex(ValueError,"HOLD_COMMENT_NOT_SERVER_CREATED_PRESTART"):
            att.inspect_records(self.frozen,bad,[bad])

    def test_prior_failed_or_different_attempt_not_selectively_ignored(self):
        earlier=deepcopy(self.comment)
        earlier["id"]=self.comment["id"]-1
        earlier["created_at"]=earlier["updated_at"]="2030-01-01T04:03:00Z"
        with self.assertRaisesRegex(ValueError,"HOLD_PRIOR_COMMITMENT"):
            att.inspect_records(self.frozen,self.comment,[earlier,self.comment])
        following=deepcopy(self.comment)
        following["id"]=self.comment["id"]+1
        following["created_at"]=following["updated_at"]="2030-01-01T04:06:00Z"
        self.assertEqual(
            att.inspect_records(self.frozen,self.comment,[self.comment,following])["status"],
            att.STATUS)

    def test_duplicate_or_missing_sha_line_rejected(self):
        for suffix in (
            "- freeze_payload_sha256: "+self.frozen["seal_sha256_of_payload"]+"\n",
            "- race_id: "+self.frozen["payload"]["race_id"]+"\n",
        ):
            bad=deepcopy(self.comment)
            bad["body"]+=suffix
            with self.assertRaisesRegex(ValueError,"HOLD_MULTIPLE_OR_MISSING_PRECOMMITMENT"):
                att.inspect_records(self.frozen,bad,[bad])

    def test_unsealed_probability_change_prevents_comment_validation(self):
        altered=deepcopy(self.frozen)
        altered["payload"]["predictions"]["M1_smooth_beta025"]["win"][0]["p"]+=0.005
        with self.assertRaisesRegex(ValueError,"HOLD_SEALED_FORECAST_CONTENT_CHANGED"):
            att.inspect_records(altered,self.comment,[self.comment])

    def test_future_official_result_only_after_post_and_approved_jra(self):
        result={
            "schema":RESULT_SCHEMA,"race_id":self.frozen["payload"]["race_id"],
            "top3_horse_numbers":[2,5,1],
            "verified_at_jst":"2030-01-01T17:00:00+09:00",
            "official_results_url":"https://www.jra.go.jp/JRADB/accessS.html",
        }
        output=score(self.frozen,result)
        self.assertIn("winner_log_loss_M1_minus_M0",output)
        self.assertIn("top3_brier_M1_minus_M0",output)
        self.assertIn("trio_log_loss_M1_minus_M0",output)
        self.assertTrue(output["real_prospective_GitHub_submission_must_be_independently_checked"])
        bad=deepcopy(result)
        bad["verified_at_jst"]="2030-01-01T14:00:00+09:00"
        with self.assertRaisesRegex(ValueError,"HOLD_RESULT_KNOWN_BEFORE_RACE_START"):
            score(self.frozen,bad)

    def test_no_authenticated_GitHub_access_causes_fail_closed(self):
        with patch.object(att,"_gh_api",side_effect=ValueError("HOLD_FAILED_TO_FETCH_GITHUB_SERVER_COMMENT")):
            with self.assertRaisesRegex(ValueError,"HOLD_FAILED_TO_FETCH_GITHUB_SERVER_COMMENT"):
                att.verify_live(self.frozen)

    def test_live_GitHub_API_mock_flow_no_real_attestation_claim(self):
        # Fixtures only: the low-level inspect can be validated, but the
        # actual real-world claim requires a fresh gh api response.
        def fake_gh_api(q):
            if "/issues/comments/" in q:
                return deepcopy(self.comment)
            if "/issues/10/comments" in q:
                return [deepcopy(self.comment)]
            raise AssertionError(q)
        with patch.object(att,"_gh_api",side_effect=fake_gh_api):
            out=att.verify_live(self.frozen)
        self.assertEqual(out["status"],att.STATUS)
        self.assertTrue(out["GitHub_API_independently_fetched"])
        # This is a mocked unit test, not the actual real GitHub API.

if __name__=="__main__":
    unittest.main()
