#!/usr/bin/env python3
"""All GitHub API responses here are artificial mocks; no real SHA is posted."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
if np is not None:
    import keiba_win_only_regime_sidecar_receipt as m
    import keiba_win_only_regime_sidecar as b
    import keiba_win_only_shadow_lane as original
    import keiba_operator_winwide_capture as capture
    from test_keiba_operator_winwide_capture import card,win,DATE

PARENT_POST="2026-10-31T02:09:00Z" # 11:09 JST
SIDECAR_POST="2026-10-31T02:10:00Z" # 11:10 JST


@unittest.skipIf(np is None,"Original linked horse model requires NumPy")
class BPlusDualGitHubSHAOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if np is None:
            return
        cls.temp=tempfile.TemporaryDirectory()
        cls.ledger=Path(cls.temp.name)/"private"/"source"
        cls.card=card()
        cls.card["provenance"]="authorized_private_local_export"
        cls.card["rights_reviewed_by_operator"]=True
        for source,t in ((win(10),"T10:02:00"),(win(11,scale=1.1),"T11:01:00")):
            s=copy.deepcopy(source)
            s["provenance"]="authorized_private_local_export"
            s["rights_reviewed_by_operator"]=True
            capture.append_capture(cls.ledger,s,
                captured_at_jst=DATE+t+"+09:00")
        cls.parent=original.prepare_win_only(
            cls.ledger,cls.card,
            frozen_at_jst=DATE+"T11:03:00+09:00",
            horse_draws=45,seed=14)
        cls.sidecar=b.freeze_companion(
            cls.ledger,cls.card,cls.parent,
            freeze_at_jst=DATE+"T11:04:00+09:00")
        next_source=copy.deepcopy(win(11,17,scale=1.2))
        next_source["provenance"]="authorized_private_local_export"
        next_source["rights_reviewed_by_operator"]=True
        capture.append_capture(cls.ledger,next_source,
            captured_at_jst=DATE+"T11:18:00+09:00")
        cls.score=b.score_companion(
            cls.ledger,cls.card,cls.parent,cls.sidecar,
            asof=DATE+"T11:21:00+09:00",
            operator_declares_capture_complete=True)

    @classmethod
    def tearDownClass(cls):
        if np is not None:
            cls.temp.cleanup()

    def comment(self,*,when=SIDECAR_POST,who="zuizui0223",cid=1234,
                edited=None):
        claim=m._claim(self.parent,self.sidecar,fixture=True)
        return {
            "id":cid,
            "body":m._body(claim),
            "user":{"login":who},
            "created_at":when,
            "updated_at":edited or when,
            "issue_url":"https://api.github.com/repos/zuizui0223/keiba/issues/37",
            "html_url":f"https://github.com/zuizui0223/keiba/pull/37#issuecomment-{cid}",
        }

    def parent_mock_proof(self,*,when=PARENT_POST,sha=None):
        return {
            "status":m.parent_proof.STATUS_REMOTE,
            "live_GitHub_API_comment_GET_performed":True,
            "server_time_pre_next_WIN_target_verified":True,
            "race_id":self.parent["payload"]["race_id"],
            "frozen_model_SHA256":
                sha or self.parent["seal_sha256_of_canonical_payload"],
            "github_server_created_at_claim":when,
            "github_comment_url":"https://github.com/zuizui0223/keiba/pull/30#issuecomment-34567",
        }

    def test_prepare_contains_only_safe_two_model_hashes_no_Github_POST(self):
        with patch.object(m,"_gh_json",
                          side_effect=AssertionError("NO NETWORK IN PREPARE")) as api:
            out=m.prepare(self.parent,self.sidecar)
            api.assert_not_called()
        self.assertEqual(out["status"],m.STATUS_PREPARED)
        self.assertEqual(out["post_once_to_existing_PR37_URL"],
                         "https://github.com/zuizui0223/keiba/pull/37")
        self.assertTrue(out["this_tool_never_posts_GitHub_comment"])
        self.assertFalse(out["actual_GitHub_SHA_timestamp_verified"])
        body=out["sidecar_sha_only_comment_NOT_POSTED"]
        self.assertTrue(body.startswith(m.MARKER+"\n"))
        payload=json.loads(body.split("\n",1)[1])
        self.assertEqual(payload["parent_original_six_model_SHA256"],
                         self.parent["seal_sha256_of_canonical_payload"])
        self.assertEqual(payload["sidecar_five_additional_model_SHA256"],
                         self.sidecar["sidecar_local_SHA256_not_remote_receipt"])
        self.assertEqual(payload["anchor_pull_request"],37)
        self.assertEqual(payload["unchanged_parent_model_count"],6)
        self.assertEqual(payload["added_fixed_candidate_count"],5)
        for private in ("horse_numbers","odds_by_horse_number",
                        "sidecar_price_candidate_indices",
                        "fixed_next_quote_model_indices",
                        "source_url","original_final_card_SHA256"):
            self.assertNotIn('"'+private+'"',body)

    def test_structural_offline_fixture_never_valid_remote_proof(self):
        p=m.inspect_fixture(self.parent,self.sidecar,[self.comment()])
        self.assertEqual(p["status"],m.STATUS_FIXTURE)
        self.assertFalse(p["both_models_externally_pretarget_timewitnessed"])
        self.assertFalse(p["live_GitHub_API_parent_and_sidecar_comment_GET"])
        with self.assertRaisesRegex(ValueError,"NOT_DUAL_LIVE"):
            m.bind_local_score(p,self.score)

    def test_reject_wrong_author_edited_duplicate_wrong_PR_and_late_clock(self):
        for comment,reason in [
            (self.comment(who="wrong-bot"),"WRONG_OWNER"),
            (self.comment(edited="2026-10-31T02:12:00Z"),"EDITED"),
            (self.comment(when="2026-10-31T02:15:00Z"),"NOT_BEFORE_NEXT"),
        ]:
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(ValueError,reason):
                    m.inspect_fixture(self.parent,self.sidecar,[comment])
        c=self.comment()
        c["issue_url"]=c["issue_url"].replace("37","30")
        with self.assertRaisesRegex(ValueError,"WRONG_OWNER"):
            m.inspect_fixture(self.parent,self.sidecar,[c])
        with self.assertRaisesRegex(ValueError,"NO_UNIQUE"):
            m.inspect_fixture(self.parent,self.sidecar,
                              [self.comment(),self.comment(cid=4321)])

    def test_no_parent_REMOTE_comment_or_wrong_sha_fails_closed(self):
        with patch.object(m.parent_proof,"verify_live",
                          side_effect=ValueError("HOLD_NO_PR30_REAL_COMMENT")):
            with self.assertRaisesRegex(ValueError,"NO_PR30"):
                m.verify_live(self.parent,self.sidecar)
        with patch.object(m.parent_proof,"verify_live",
                          return_value=self.parent_mock_proof(sha="f"*64)):
            with self.assertRaisesRegex(ValueError,
                                        "PARENT_PR30_REMOTE_SHA_NOT_VERIFIED"):
                m.verify_live(self.parent,self.sidecar)

    def test_live_API_simulation_requires_parent_and_sidecar_list_detail(self):
        # Both APIs below are unittest MOCKS only, never actual GitHub calls.
        one=self.comment()
        called=[]
        def api(url):
            called.append(url)
            if url.startswith("/repos/zuizui0223/keiba/issues/37/comments?"):
                return [one]
            if url=="/repos/zuizui0223/keiba/issues/comments/1234":
                return one
            raise AssertionError("Unexpected URL "+url)
        with patch.object(m.parent_proof,"verify_live",
                          return_value=self.parent_mock_proof()):
            with patch.object(m,"_gh_json",side_effect=api):
                result=m.verify_live(self.parent,self.sidecar)
        self.assertEqual(result["status"],m.STATUS_REMOTE)
        self.assertTrue(result["both_parent_and_sidecar_SHA_created_before_target"])
        self.assertTrue(result["live_GitHub_API_parent_and_sidecar_comment_GET"])
        self.assertTrue(result["only_DIGEST_timewitnessed_NOT_original_quote_truth"])
        self.assertEqual(len(called),2)
        attached=m.bind_local_score(result,self.score)
        self.assertEqual(attached["status"],m.STATUS_BOUND)
        self.assertTrue(attached["eleven_models_scored_on_one_locally_claimed_q2"])
        self.assertEqual(attached["new_independently_verified_JRA_next_market_trials"],0)

    def test_parent_sha_must_be_public_before_sidecar_sha(self):
        with patch.object(m.parent_proof,"verify_live",
                          return_value=self.parent_mock_proof(
                              when="2026-10-31T02:11:00Z")):
            with patch.object(m,"_gh_json",side_effect=lambda uri:
                [self.comment()] if "/issues/37/comments?" in uri
                else self.comment()):
                with self.assertRaisesRegex(ValueError,
                                            "PARENT_SHA_NOT_POSTED_BEFORE_SIDECAR"):
                    m.verify_live(self.parent,self.sidecar)

    def test_secondary_GitHub_details_cannot_silently_disagree(self):
        wrong=copy.deepcopy(self.comment())
        wrong["body"]+="\nFAKE"
        with patch.object(m.parent_proof,"verify_live",
                          return_value=self.parent_mock_proof()):
            with patch.object(m,"_gh_json",side_effect=lambda uri:
                [self.comment()] if "/issues/37/comments?" in uri
                else wrong):
                with self.assertRaisesRegex(ValueError,
                                            "LIST_VS_DETAIL_CHANGED"):
                    m.verify_live(self.parent,self.sidecar)

    def test_no_stolen_six_sha_or_changed_source_race(self):
        wrong=copy.deepcopy(self.parent)
        wrong["payload"]["race_id"]="changed"
        with self.assertRaisesRegex(ValueError,"SHA_OR_SCHEMA"):
            m.prepare(wrong,self.sidecar)
        corrupt=copy.deepcopy(self.sidecar)
        corrupt["payload"]["parent_original_six_model_freeze_SHA256"]="f"*64
        corrupt["sidecar_local_SHA256_not_remote_receipt"]=b._seal(
            corrupt["payload"])
        with self.assertRaisesRegex(ValueError,"DIFFERENT_RACE_SOURCE_SHA"):
            m.prepare(self.parent,corrupt)

    def test_binded_score_requires_same_both_shas_race_and_window(self):
        with patch.object(m.parent_proof,"verify_live",
                          return_value=self.parent_mock_proof()):
            with patch.object(m,"_gh_json",side_effect=lambda uri:
                [self.comment()] if "/issues/37/comments?" in uri
                else self.comment()):
                proof=m.verify_live(self.parent,self.sidecar)
        for key,val in (
            ("race_id","other"),("parent_original_six_model_SHA256","f"*64),
            ("sidecar_local_SHA256","f"*64),
            ("independent_race_count_not_six_plus_five",3),
        ):
            score=copy.deepcopy(self.score)
            score[key]=val
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError,"NOT_FROM_SAME_DUAL"):
                    m.bind_local_score(proof,score)
        late=copy.deepcopy(self.score)
        late["source_target_published"]=DATE+"T11:23:00+09:00"
        with self.assertRaisesRegex(ValueError,
                                    "LOCAL_Q2_NOT_IN_REMOTE_DECLARED_WINDOW"):
            m.bind_local_score(proof,late)

    def test_unsupported_parent_or_missing_per_page_response_HOLD(self):
        with patch.object(m.parent_proof,"verify_live",
                          return_value=self.parent_mock_proof()):
            with patch.object(m,"_gh_json",return_value=None):
                with self.assertRaisesRegex(ValueError,
                                            "COMMENTS_API_BAD_RESPONSE"):
                    m.verify_live(self.parent,self.sidecar)
        with patch.object(m,"_gh_json",return_value=[
                self.comment(),self.comment()]):
            with self.assertRaisesRegex(ValueError,
                                        "DUPLICATE_OR_INVALID_COMMENT_ID"):
                m._all_sidecar_comments()


if __name__=="__main__":
    unittest.main()
