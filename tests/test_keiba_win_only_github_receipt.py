#!/usr/bin/env python3
"""WIN-only PR30 SHA-only proof never borrowed from full-WIDE PR22.

All server API responses in these tests are ARTIFICIAL unittest mocks.
No real SHA comments are posted, and no actual future races are observed.
"""
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
    import keiba_win_only_github_receipt as m
    import keiba_win_only_shadow_lane as lane
    import keiba_operator_winwide_capture as capture
    from test_keiba_operator_winwide_capture import card, win, DATE

POSTED="2026-10-31T02:09:00Z" # 11:09 JST, target starts 11:15 JST


def _make_frozen(*, authorized=True, with_score=False):
    temp=tempfile.TemporaryDirectory()
    p=Path(temp.name)/"private"/"captured"
    c=card()
    for original,clock in ((win(10),"T10:02:00"),
                           (win(11,scale=1.1),"T11:01:00")):
        q=copy.deepcopy(original)
        if authorized:
            q["provenance"]="authorized_private_local_export"
            q["rights_reviewed_by_operator"]=True
        capture.append_capture(p,q,captured_at_jst=DATE+clock+"+09:00")
    if authorized:
        c["provenance"]="authorized_private_local_export"
        c["rights_reviewed_by_operator"]=True
    f=lane.prepare_win_only(p,c,
                            frozen_at_jst=DATE+"T11:03:00+09:00",
                            horse_draws=45,seed=12)
    target=None
    if with_score:
        future=win(11,17,scale=1.3)
        if authorized:
            future["provenance"]="authorized_private_local_export"
            future["rights_reviewed_by_operator"]=True
        capture.append_capture(p,future,
            captured_at_jst=DATE+"T11:18:00+09:00")
        target=lane.score_win_only(p,c,f,
            asof=DATE+"T11:21:00+09:00",
            operator_declares_capture_complete=True)
    return temp,f,target


def _comment(f, *,created=POSTED, user="zuizui0223", cid=34567,
             fixture=False):
    body=m._body(m._claim(f,synthetic_fixture=fixture))
    return {
        "id":cid,
        "body":body,
        "user":{"login":user},
        "created_at":created,
        "updated_at":created,
        "issue_url":"https://api.github.com/repos/zuizui0223/keiba/issues/30",
        "html_url":f"https://github.com/zuizui0223/keiba/pull/30#issuecomment-{cid}",
    }


@unittest.skipIf(np is None,"Real horse math requires NumPy for synthetic fixture")
class DedicatedWinOnlyReceiptTest(unittest.TestCase):
    def setUp(self):
        self.temp,self.frozen,self.target=_make_frozen(with_score=True)
        self.addCleanup(self.temp.cleanup)

    def test_prepared_body_has_no_public_original_prices_or_model_vectors(self):
        with patch.object(m,"_gh_json",side_effect=AssertionError(
                "PREPARE MUST NOT CALL OR POST GITHUB")) as mocked:
            p=m.prepare(self.frozen)
            mocked.assert_not_called()
        self.assertEqual(p["status"],m.STATUS_PREPARED)
        self.assertFalse(p["created_GitHub_comment"])
        self.assertFalse(p["external_timestamp_proven"])
        self.assertEqual(p["post_to_existing_PR_once_URL"],
                         "https://github.com/zuizui0223/keiba/pull/30")
        body=p["sha_only_comment_body_NOT_POSTED"]
        self.assertTrue(body.startswith(m.MARKER+"\n"))
        claim=json.loads(body.split("\n",1)[1])
        self.assertEqual(claim["research_lane"],"SECONDARY_WIN_ONLY_NOT_WIDE")
        self.assertEqual(claim["fixed_candidate_count"],6)
        self.assertEqual(claim["anchor_pull_request"],30)
        self.assertEqual(claim["model_SHA256"],
                         self.frozen["seal_sha256_of_canonical_payload"])
        for private in ("horse_numbers","odds_by_horse_number",
                        "fixed_next_quote_model_indices",
                        "final_card_SHA256","original_local_capture_chain_prefix_SHA256"):
            self.assertNotIn('"'+private+'"',body)

    def test_offline_arbitrary_comment_claim_cannot_become_server_proof(self):
        x=m.inspect_fixture(self.frozen,[_comment(self.frozen)])
        self.assertEqual(x["status"],m.STATUS_FIXTURE)
        self.assertFalse(x["server_time_pre_next_WIN_target_verified"])
        self.assertFalse(x["live_GitHub_API_comment_GET_performed"])
        self.assertGreater(x["minutes_between_GitHub_SHA_and_target_start"],0)
        self.assertTrue(x["full_target_stream_not_independently_certified"])
        with self.assertRaisesRegex(ValueError,"NEVER_LIVE_VERIFIED"):
            m.attach_locally_scored_target(x,self.target)

    def test_comment_after_q2_target_is_invalid_even_if_before_race(self):
        for when in ("2026-10-31T02:15:00Z",
                     "2026-10-31T02:16:00Z",
                     "2026-10-31T04:00:00Z"):
            with self.subTest(when=when):
                with self.assertRaisesRegex(ValueError,"LATE_VS_NEXT_PRICE"):
                    m.inspect_fixture(self.frozen,[_comment(
                        self.frozen,created=when)])

    def test_comment_before_private_freeze_is_impossible(self):
        with self.assertRaisesRegex(ValueError,"LATE_VS_NEXT_PRICE"):
            m.inspect_fixture(self.frozen,[_comment(
                self.frozen,created="2026-10-31T02:00:00Z")])

    def test_edited_comment_is_never_accepted_as_first_sha(self):
        c=_comment(self.frozen)
        c["updated_at"]="2026-10-31T02:10:00Z"
        with self.assertRaisesRegex(ValueError,"COMMENT_EDITED"):
            m.inspect_fixture(self.frozen,[c])

    def test_duplicate_or_malformed_same_race_comment_is_rejected(self):
        first=_comment(self.frozen,cid=55)
        second=_comment(self.frozen,cid=56)
        with self.assertRaisesRegex(ValueError,"MULTIPLE"):
            m.inspect_fixture(self.frozen,[first,second])
        malformed=copy.deepcopy(second)
        malformed["body"]=m.MARKER+"\n"+json.dumps({
            "race_id":self.frozen["payload"]["race_id"],"model_SHA256":"f"*64})
        with self.assertRaisesRegex(ValueError,"MULTIPLE"):
            m.inspect_fixture(self.frozen,[first,malformed])
        other=copy.deepcopy(second)
        claim=json.loads(other["body"].split("\n")[1])
        claim["race_id"]="A_DIFFERENT_REGISTERED_RACE"
        other["body"]=m._body(claim)
        check=m.inspect_fixture(self.frozen,[first,other])
        self.assertEqual(check["github_comment_id"],55)

    def test_wrong_author_pr_or_noncanonical_public_body_rejected(self):
        probes=[
            ({"user":{"login":"another_owner"}},"UNTRUSTED_AUTHOR"),
            ({"issue_url":"https://api.github.com/repos/zuizui0223/keiba/issues/22"},"UNTRUSTED_AUTHOR"),
            ({"html_url":"https://github.com/zuizui0223/keiba/pull/22#issuecomment-34567"},"UNTRUSTED_AUTHOR"),
            ({"body":_comment(self.frozen)["body"]+"\nEDITED PRIVATE PRICES"},"NOT_CANONICAL"),
        ]
        for val,match in probes:
            c=_comment(self.frozen)
            c.update(val)
            with self.subTest(val=val):
                with self.assertRaisesRegex(ValueError,match):
                    m.inspect_fixture(self.frozen,[c])

    def test_win_only_claim_refuses_synthetic_and_does_not_alias_PR22(self):
        temp,f,_=_make_frozen(authorized=False)
        self.addCleanup(temp.cleanup)
        with self.assertRaisesRegex(ValueError,"UNAUTHORIZED_OR_SYNTHETIC"):
            m.prepare(f)
        fake=m.inspect_fixture(f,[_comment(f,fixture=True)])
        self.assertEqual(fake["status"],m.STATUS_FIXTURE)
        self.assertNotEqual(m.MARKER,
            "KEIBA_SHA_ONLY_NEXT_MARKET_PR_COMMENT_V1")
        self.assertNotEqual(m.ANCHOR_PR,22)

    def test_code_fingerprint_changes_fail_before_public_claim(self):
        mutated=copy.deepcopy(self.frozen)
        mutated["payload"]["model_code_content_SHA256"][
            lane.CODE_FILES[0]]="e"*64
        from odds_shadow_freeze_score import _seal
        mutated["seal_sha256_of_canonical_payload"]=_seal(mutated["payload"])
        with self.assertRaisesRegex(ValueError,"CODE_CHANGED"):
            m.prepare(mutated)

    def test_no_Github_API_is_fail_closed(self):
        with patch.object(m,"_gh_json",side_effect=ValueError(
                "HOLD_CANNOT_FETCH_GITHUB_SERVER_COMMENTS")):
            with self.assertRaisesRegex(ValueError,"CANNOT_FETCH"):
                m.verify_live(self.frozen)
        with patch.object(m,"_gh_json",return_value=[]):
            with self.assertRaisesRegex(ValueError,"ZERO_OR_MULTIPLE"):
                m.verify_live(self.frozen)

    def test_list_and_single_GitHub_API_must_agree(self):
        c=_comment(self.frozen)
        def get(uri):
            if "comments?" in uri:
                return [c]
            return c
        with patch.object(m,"_gh_json",side_effect=get) as mocked:
            proof=m.verify_live(self.frozen)
        self.assertTrue(mocked.call_count>=2)
        self.assertEqual(proof["status"],m.STATUS_REMOTE)
        self.assertTrue(proof["server_time_pre_next_WIN_target_verified"])
        self.assertFalse(proof[
            "true_captured_source_and_target_integrity_independently_proven"])
        # The mock above is a UNIT TEST, not an actual GitHub source.
        broken=copy.deepcopy(c)
        broken["body"]="NOT_THE_SAME_SHA"
        def disagree(uri):
            return [c] if "comments?" in uri else broken
        with patch.object(m,"_gh_json",side_effect=disagree):
            with self.assertRaisesRegex(ValueError,"DETAIL_VS_LISTING"):
                m.verify_live(self.frozen)

    def test_pagination_fails_closed_on_duplicate_or_malformed_comment(self):
        c=_comment(self.frozen)
        with patch.object(m,"_gh_json",return_value=[c,c]):
            with self.assertRaisesRegex(ValueError,"COMMENT_ID_DUPLICATED"):
                m._get_all_comments()
        with patch.object(m,"_gh_json",return_value={"wrong":"shape"}):
            with self.assertRaisesRegex(ValueError,"UNEXPECTED_SHAPE"):
                m._get_all_comments()

    def test_locally_scored_quote_can_only_match_same_frozen_sha_target_window(self):
        c=_comment(self.frozen)
        def api(uri):
            return [c] if "comments?" in uri else c
        with patch.object(m,"_gh_json",side_effect=api):
            # Remote receipt here is a TEST MOCK; no real market proof.
            proof=m.verify_live(self.frozen)
        envelope=m.attach_locally_scored_target(proof,self.target)
        self.assertEqual(envelope["status"],m.STATUS_SCORED)
        self.assertEqual(envelope["new_independently_verified_JRA_market_trials"],0)
        self.assertFalse(envelope[
            "independently_authenticated_WIN_source_and_complete_q2"])
        other=copy.deepcopy(self.target)
        other["local_frozen_model_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"SHA_RACE_OR_STATUS_MISMATCH"):
            m.attach_locally_scored_target(proof,other)
        wrong=copy.deepcopy(self.target)
        wrong["source_target_published"]="2026-10-31T11:14:00+09:00"
        with self.assertRaisesRegex(ValueError,"TARGET_CLOCK_CHANGED"):
            m.attach_locally_scored_target(proof,wrong)


if __name__=="__main__":
    unittest.main()
