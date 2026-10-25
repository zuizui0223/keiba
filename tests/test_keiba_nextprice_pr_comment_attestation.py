#!/usr/bin/env python3
"""PR22 SHA comment authentication: reject post-target/edited/duplicates."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
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
    import keiba_nextprice_pr_comment_attestation as m
    import keiba_private_multirace_winwide_shadow as shadow
    from test_keiba_private_multirace_winwide_shadow import (
        source,as_bytes,target)


def fake_freeze(*,authorized=True):
    doc=source()
    if authorized:
        doc["provenance"]="authorized_private_local_export"
        doc["operator_confirmed_research_rights"]=True
    return shadow.freeze_source_bytes(
        as_bytes(doc),horse_draws=45,horse_seed=20261025)


def gh_comment(frozen,*,created="2026-11-07T02:07:30Z",user="zuizui0223",
               cid=111111,fixture=False):
    commitment=m._commitment(frozen,fixture=fixture)
    return {
        "id":cid,
        "user":{"login":user},
        "body":m._comment_body(commitment),
        "created_at":created,
        "updated_at":created,
        "issue_url":"https://api.github.com/repos/zuizui0223/keiba/issues/22",
        "html_url":f"https://github.com/zuizui0223/keiba/pull/22#issuecomment-{cid}",
    }


@unittest.skipIf(np is None,"Requires NumPy in dedicated numerical CI")
class SHAOnlyPRTimestampTest(unittest.TestCase):
    def test_prepare_digest_only_does_not_publish_or_claim_proof(self):
        f=fake_freeze()
        with patch.object(m.subprocess,"run",side_effect=AssertionError(
                   "NO_AUTOMATIC_GITHUB_POST")) as called:
            p=m.prepare_comment(f)
            called.assert_not_called()
        self.assertEqual(p["status"],m.STATUS_PREPARED)
        self.assertTrue(p["requires_explicit_user_action_to_post"])
        self.assertFalse(p["remote_sha_publication_confirmed"])
        self.assertEqual(p["anchor_url"],
                         "https://github.com/zuizui0223/keiba/pull/22")
        self.assertTrue(p["body_to_post_once_in_PR22_comment"].startswith(
                        m.MARKER+"\n"))
        manifest=json.loads(p["body_to_post_once_in_PR22_comment"].split("\n")[1])
        self.assertEqual(manifest["seal_sha256"],
                         f["seal_sha256_of_canonical_payload"])
        self.assertEqual(manifest["model_count"],12)
        for bad in ("candidate_predictions","odds_by_horse_number",
                    "horse_numbers","full_history_before_target",
                    "first_win","middle_win","pairs"):
            self.assertNotIn('"'+bad+'"',p["body_to_post_once_in_PR22_comment"])

    def test_source_receipt_and_github_created_before_target_would_pass_structure(self):
        f=fake_freeze()
        fake=gh_comment(f)
        x=m.inspect_fixture(f,[fake])
        self.assertEqual(x["status"],m.STATUS_LOCAL)
        self.assertFalse(x["external_sha_pre_target_verified"])
        self.assertFalse(x["independent_GitHub_API_fetch_performed"])
        self.assertEqual(x["github_comment_id"],111111)
        self.assertGreater(x["margin_to_market_target_minutes"],0)
        self.assertTrue(x["provider_market_clocks_not_authenticated_by_GitHub_SHA"])
        self.assertTrue(x["actual_target_quote_completeness_not_externally_proven"])

    def test_critical_guard_comment_after_next_quote_but_before_horse_race_fails(self):
        f=fake_freeze()
        for clock in ("2026-11-07T02:18:00Z","2026-11-07T02:19:00Z",
                      "2026-11-07T05:30:00Z"):
            with self.subTest(clock=clock):
                with self.assertRaisesRegex(ValueError,"AFTER_TARGET"):
                    m.inspect_fixture(f,[gh_comment(f,created=clock)])

    def test_sha_comment_cannot_claim_to_precede_local_freeze(self):
        f=fake_freeze()
        with self.assertRaisesRegex(ValueError,"AFTER_TARGET_OR_CLOCK_ORDER"):
            m.inspect_fixture(f,[gh_comment(f,
                                            created="2026-11-07T02:04:59Z")])

    def test_comment_edits_even_with_restored_digest_are_rejected(self):
        f=fake_freeze()
        c=gh_comment(f)
        c["updated_at"]="2026-11-07T02:08:00Z"
        with self.assertRaisesRegex(ValueError,"WAS_EDITED"):
            m.inspect_fixture(f,[c])

    def test_duplicate_or_conflicting_sha_entries_for_same_race_are_rejected(self):
        f=fake_freeze()
        c1=gh_comment(f,cid=1)
        c2=gh_comment(f,cid=2,created="2026-11-07T02:08:00Z")
        with self.assertRaisesRegex(ValueError,"MULTIPLE"):
            m.inspect_fixture(f,[c1,c2])
        # A different race's receipt is allowed in the shared PR thread.
        c3=copy.deepcopy(c2)
        other=json.loads(c3["body"].split("\n")[1])
        other["race_id"]="SYN_OTHER_RACE"
        c3["body"]=m._comment_body(other)
        x=m.inspect_fixture(f,[c1,c3])
        self.assertEqual(x["github_comment_id"],1)
        malformed=copy.deepcopy(c2)
        malformed["body"]=m.MARKER+'\n{"race_id":"SYN_RACE_20261107_07","seal_sha256":"bad"}\n'
        # Malformed attempt remains visibly associated with this race.
        with self.assertRaisesRegex(ValueError,"MULTIPLE"):
            m.inspect_fixture(f,[c1,malformed])

    def test_wrong_author_wrong_pr_extra_comment_content_rejected(self):
        f=fake_freeze()
        for item,needle in (
            ({"user":{"login":"not_owner"}},"AUTHOR"),
            ({"issue_url":"https://api.github.com/repos/zuizui0223/keiba/issues/21"},"WRONG_ISSUE"),
            ({"body":gh_comment(f)["body"]+"I bet on 9"},"BODY"),
            ({"html_url":"https://github.com/zuizui0223/keiba/pull/21#issuecomment-111111"},"WRONG_ISSUE"),
        ):
            c=gh_comment(f)
            c.update(item)
            with self.subTest(needle=needle):
                with self.assertRaisesRegex(ValueError,needle):
                    m.inspect_fixture(f,[c])

    def test_tampered_seal_and_synthetic_replay_not_authorized_live(self):
        f=fake_freeze()
        with self.assertRaisesRegex(ValueError,"NOT_AN_AUTHORIZED"):
            m.prepare_comment(fake_freeze(authorized=False))
        demo=fake_freeze(authorized=False)
        proof=m.inspect_fixture(demo,[gh_comment(demo,fixture=True)])
        self.assertEqual(proof["status"],m.STATUS_LOCAL)
        f["payload"]["candidate_predictions"]["mid_WIN_persistence"][0]["p"]+=.003
        with self.assertRaisesRegex(ValueError,"HASH_OR_SCHEMA"):
            m.prepare_comment(f)

    def test_independent_Github_cli_failure_is_fail_closed_not_offline_promotion(self):
        f=fake_freeze()
        with patch.object(m,"_gh_json",side_effect=ValueError(
                "HOLD_NO_GITHUB_CLI")):
            with self.assertRaisesRegex(ValueError,"HOLD_NO_GITHUB_CLI"):
                m.verify_live(f)
        with patch.object(m,"_gh_json",return_value=[]):
            with self.assertRaisesRegex(ValueError,"NO_GITHUB"):
                m.verify_live(f)

    def test_pagination_rejects_duplicate_comment_id_and_incomplete_page(self):
        c=gh_comment(fake_freeze())
        with patch.object(m,"_gh_json",return_value=[c,c]):
            with self.assertRaisesRegex(ValueError,"DUPLICATE"):
                m._fetch_all_comments()
        with patch.object(m,"_gh_json",return_value={"bad":"response"}):
            with self.assertRaisesRegex(ValueError,"API_COLLECTION"):
                m._fetch_all_comments()

    def test_proof_cannot_be_bound_to_different_later_market_score(self):
        f=fake_freeze()
        score=shadow.score_target(f,target(source()))
        fake_local=m.inspect_fixture(f,[gh_comment(f)])
        with self.assertRaisesRegex(ValueError,"NOT_INDEPENDENTLY"):
            m.bind_scored_next_market_to_proof(fake_local,score)
        # A structurally matched object can be fabricated in a test.
        # Only the verify-live CLI may publicly assert GitHub REST proof.
        synthetic=copy.deepcopy(fake_local)
        synthetic.update({
            "status":m.STATUS_REMOTE,
            "independent_GitHub_API_fetch_performed":True,
            "external_sha_pre_target_verified":True})
        bind=m.bind_scored_next_market_to_proof(synthetic,score)
        self.assertFalse(bind["later_price_capture_completeness_independently_verified"])
        self.assertFalse(bind["source_receipts_independently_verified"])
        other=copy.deepcopy(score)
        other["sealed_prediction_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"DO_NOT_MATCH"):
            m.bind_scored_next_market_to_proof(synthetic,other)


if __name__=="__main__":
    unittest.main()
