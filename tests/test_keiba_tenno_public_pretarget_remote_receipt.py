#!/usr/bin/env python3
"""All comment responses in this module are synthetic mocks, NOT real proof."""
from __future__ import annotations
import copy
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
try:
    import numpy as np
except ModuleNotFoundError:
    np=None
if np is not None:
    import keiba_tenno_public_pretarget_future_shadow as m
    import keiba_tenno_public_pretarget_remote_receipt as v
    import keiba_operator_winwide_capture as cap


@unittest.skipIf(np is None,"Parents require NumPy")
class PublicNewsGithubCommitmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if np is not None:cls.frozen=m.freeze()

    def comment(self,at="2026-10-31T14:00:00Z",cid=48001,
                author="zuizui0223",edited=None):
        return {
            "id":cid,
            "body":v._body(v._claim(self.frozen)),
            "created_at":at,
            "updated_at":edited or at,
            "user":{"login":author},
            "issue_url":"https://api.github.com/repos/zuizui0223/keiba/issues/41",
            "html_url":f"https://github.com/zuizui0223/keiba/pull/41#issuecomment-{cid}",
        }

    def test_prepare_comment_sha_only_without_Github_post_or_betting(self):
        with patch.object(v,"_gh_json",
                          side_effect=AssertionError("NO_FETCH_DURING_PREPARE")) as api:
            p=v.prepare(self.frozen)
            api.assert_not_called()
        self.assertEqual(p["status"],v.STATUS_PREPARED)
        self.assertFalse(p["created_comment"])
        self.assertTrue(p["requires_explicit_operator_POST"])
        self.assertTrue(p["sha_only_comment_BODY_not_posted"].startswith(v.MARKER))
        self.assertEqual(p["sha256"],
                         self.frozen["sha256_of_canonical_frozen_payload"])
        for secret in ('"horse_numbers"','"odds_by_horse_number"',
                       '"frozen_price_index_forecasts"'):
            self.assertNotIn(secret,p["sha_only_comment_BODY_not_posted"])
        self.assertEqual(p["anchor_PR_to_post_once"],
                         "https://github.com/zuizui0223/keiba/pull/41")

    def test_fake_comment_only_structural_not_live(self):
        d=v.inspect_fixture(self.frozen,[self.comment()])
        self.assertEqual(d["status"],v.STATUS_FIXTURE)
        self.assertFalse(d["real_GitHub_server_comment_verified"])
        with self.assertRaisesRegex(ValueError,"NO_LIVE_REMOTE_SHA"):
            v.attach_local_score(d,{})

    def test_wrong_edited_author_and_late_or_early_comment_rejected(self):
        cases=[
            (self.comment(author="untrusted"),"WRONG_OWNER"),
            (self.comment(edited="2026-10-31T14:05:00Z"),"WAS_EDITED"),
            (self.comment(at="2026-11-01T05:45:00Z"),"NOT_BEFORE_TARGET"),
            (self.comment(at="2026-10-31T07:00:00Z"),"NOT_BEFORE_TARGET"),
        ]
        for c,code in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(ValueError,code):
                    v.inspect_fixture(self.frozen,[c])

    def test_duplicate_or_modified_sha_comment_rejected(self):
        with self.assertRaisesRegex(ValueError,
                                    "ZERO_OR_MULTIPLE_SHA_ATTEMPTS"):
            v.inspect_fixture(self.frozen,[self.comment(),self.comment(cid=48002)])
        wrong=copy.deepcopy(self.comment())
        wrong["body"]=wrong["body"].replace(
            self.frozen["sha256_of_canonical_frozen_payload"],"f"*64)
        with self.assertRaisesRegex(ValueError,"WRONG_OWNER_TARGET_OR_PUBLIC_SHA_COMMENT"):
            v.inspect_fixture(self.frozen,[wrong])
        p=copy.deepcopy(self.comment())
        p["issue_url"]=p["issue_url"].replace("/41","/30")
        with self.assertRaisesRegex(ValueError,"WRONG_OWNER_TARGET_OR_PUBLIC_SHA_COMMENT"):
            v.inspect_fixture(self.frozen,[p])

    def test_live_Github_list_and_detail_mocks_are_read_twice(self):
        c=self.comment()
        calls=[]
        def get(uri):
            calls.append(uri)
            if uri.endswith("/issues/comments/48001"):
                return c
            if "/issues/41/comments?" in uri:
                return [c]
            raise AssertionError("unexpected API "+uri)
        with patch.object(v,"_gh_json",side_effect=get):
            p=v.verify_live(self.frozen)
        self.assertEqual(p["status"],v.STATUS_REMOTE)
        self.assertTrue(p["real_GitHub_server_comment_verified"])
        self.assertTrue(p["SHA_existed_before_new_market_target_start"])
        self.assertTrue(p["original_JRA_provider_published_clock_unverified"])
        self.assertTrue(p["actual_target_quote_and_rights_not_verified"])
        self.assertEqual(p["new_formal_PR30_or_PR37_11model_prospective_trials"],0)
        self.assertEqual(len(calls),2)

    def test_live_remote_detail_disagree_and_empty_history_HOLD(self):
        with patch.object(v,"_gh_json",return_value=[]):
            with self.assertRaisesRegex(ValueError,
                                        "ZERO_OR_MULTIPLE_SHA_ATTEMPTS"):
                v.verify_live(self.frozen)
        original=self.comment()
        bad=copy.deepcopy(original)
        bad["body"]+="\nedit"
        with patch.object(v,"_gh_json",side_effect=lambda uri:
                          bad if uri.endswith("/issues/comments/48001") else
                          [original]):
            with self.assertRaisesRegex(ValueError,
                                        "LIST_AND_DETAIL_DISAGREE"):
                v.verify_live(self.frozen)

    def test_only_same_SHA_and_target_window_can_bind_local_result(self):
        c=self.comment()
        with patch.object(v,"_gh_json",side_effect=lambda uri:
                          c if uri.endswith("/issues/comments/48001") else [c]):
            proof=v.verify_live(self.frozen)
        data={
            "schema":m.SCORE_SCHEMA,
            "status":m.SCORED_STATUS,
            "registered_slot_id":m.SLOT,
            "original_pretarget_public_forecast_sha256":
                self.frozen["sha256_of_canonical_frozen_payload"],
            "observed_eligible_next_win_targets":1,
            "new_independently_verified_JRA_market_trial":False,
            "selected_first_eligible_full_WIN_published":
                "2026-11-01T14:50:00+09:00",
            "selected_full_WIN_locally_received":
                "2026-11-01T14:51:00+09:00",
            "target_price_index_TV_KL_by_all_four_fixed_models":{},
        }
        bound=v.attach_local_score(proof,data)
        self.assertEqual(bound["status"],v.STATUS_LOCALLY_SCORED)
        self.assertFalse(bound["original_live_JRA_target_receipt_independently_authenticated"])
        self.assertEqual(bound["formal_11_horse_ABM_PDE_bettor_future_trials"],0)
        for key,val in (
            ("registered_slot_id","fake"),
            ("original_pretarget_public_forecast_sha256","f"*64),
            ("observed_eligible_next_win_targets",2),
        ):
            bad=copy.deepcopy(data);bad[key]=val
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError,
                                            "LOCAL_Q2_NOT_MATCHING_PUBLIC_SHA"):
                    v.attach_local_score(proof,bad)
        late=copy.deepcopy(data)
        late["selected_first_eligible_full_WIN_published"] = \
            "2026-11-01T15:06:00+09:00"
        with self.assertRaisesRegex(ValueError,"COMMENT_TOO_LATE_VS_Q2"):
            v.attach_local_score(proof,late)


if __name__=="__main__":
    unittest.main()
