#!/usr/bin/env python3
"""Synthetic comment fixtures NEVER imply verified JRA calendar metadata."""
from copy import deepcopy
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

import odds_graded_calendar_comment_proof as proof

CAL=ROOT/"data/research/jra-graded-flat-2026oct25-dec27-calendar.json"
REG=ROOT/"data/research/odds-prequential-2026oct24-coverage-registry.json"
PROTO=ROOT/"docs/odds-prequential-graded-cohort-v1-20261024.json"


class CalendarCommentProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cal=CAL.read_bytes()
        cls.reg=REG.read_bytes()
        cls.proto=PROTO.read_bytes()
        c=json.loads(cls.cal)
        lines=[
            proof.HEADER+"2026年10月25日〜12月27日のJRA平地GⅠ・GⅡ・GⅢ",
            f"- 対象一覧のGit blob SHA: {proof.git_blob_sha(cls.cal)}",
            f"- 状態台帳のGit blob SHA: {proof.git_blob_sha(cls.reg)}",
            f"- 事前固定モデル・評価規則v1のGit blob SHA: {proof.git_blob_sha(cls.proto)}",
        ]+[f"- {x['scheduled_date_jst']} {x['venue']} {x['grade']} {x['race_name_jp']}"
             for x in c["events"]]
        cls.comment={
            "id":proof.COMMENT_ID,
            "created_at":"2026-10-24T10:15:53Z",
            "updated_at":"2026-10-24T10:15:53Z",
            "body":"\n".join(lines)+"\n",
        }

    def test_all_26_events_and_three_git_blobs_match_offline_fixture(self):
        x=proof.inspect_fixture(self.cal,self.reg,self.proto,self.comment)
        self.assertEqual(x["status"],proof.OFFLINE)
        self.assertFalse(x["external_GitHub_timestamp_independently_verified"])
        self.assertEqual(x["registered_race_slots"],26)
        self.assertEqual(x["registered_distinct_meeting_dates"],20)
        self.assertTrue(x["all_26_calendar_slots_predeclared_in_comment"])
        self.assertEqual(
            x["claimed_server_GitHub_created_at"],
            "2026-10-24T19:15:53+09:00")
        self.assertEqual(x["three_frozen_content_git_blob_SHAs"]["calendar"],
                         proof.git_blob_sha(self.cal))
        self.assertEqual(x["comment_url"],
                         "https://github.com/zuizui0223/keiba/pull/10#issuecomment-6382991405")
        self.assertTrue(x["study_period_end_2027_03_31_not_yet_fully_scheduled"])
        self.assertTrue(x["no_future_winner_or_top3_outcome_used"])

    def test_calendar_change_even_whitespace_invalidates_original_commitment(self):
        for field in ("cal","reg","proto"):
            raw=getattr(self,field)+b" "
            inputs={"cal":self.cal,"reg":self.reg,"proto":self.proto}
            inputs[field]=raw
            with self.assertRaisesRegex(
                    ValueError,"HOLD_PRECOMMITTED_CALENDAR_OR_PROTOCOL_BLOB_CHANGED"):
                proof.inspect_fixture(inputs["cal"],inputs["reg"],
                                      inputs["proto"],self.comment)

    def test_missing_or_duplicated_race_title_fails_despite_matching_blobs(self):
        original=json.loads(self.cal)
        line=original["events"][0]
        full=(f"- {line['scheduled_date_jst']} {line['venue']} "
              f"{line['grade']} {line['race_name_jp']}")
        c=deepcopy(self.comment)
        c["body"]=c["body"].replace(full,"- redacted")
        with self.assertRaisesRegex(ValueError,"HOLD_GITHUB_DENOMINATOR_RACE_MISSING"):
            proof.inspect_fixture(self.cal,self.reg,self.proto,c)
        c=deepcopy(self.comment)
        c["body"]+=full+"\n"
        with self.assertRaisesRegex(ValueError,"HOLD_GITHUB_DENOMINATOR_RACE_MISSING"):
            proof.inspect_fixture(self.cal,self.reg,self.proto,c)

    def test_comment_modified_or_created_after_kikka_cutoff_is_not_precommit(self):
        c=deepcopy(self.comment)
        c["updated_at"]="2026-10-24T10:16:00Z"
        with self.assertRaisesRegex(ValueError,"HOLD_GITHUB_PRECOMMITMENT_COMMENT_EDITED"):
            proof.inspect_fixture(self.cal,self.reg,self.proto,c)
        c=deepcopy(self.comment)
        c["created_at"]=c["updated_at"]="2026-10-25T06:35:00Z"
        with self.assertRaisesRegex(ValueError,"HOLD_GITHUB_PRECOMMITMENT_NOT_BEFORE"):
            proof.inspect_fixture(self.cal,self.reg,self.proto,c)

    def test_disconnected_Github_API_cannot_fabricate_trusted_receipt(self):
        with patch.object(proof.subprocess,"run",side_effect=OSError("No gh")):
            with self.assertRaisesRegex(ValueError,
                                        "HOLD_GITHUB_API_INDEPENDENT_CALENDAR_COMMENT_FETCH_FAILED"):
                proof.verify_live(self.cal,self.reg,self.proto)
        self.assertEqual(
            proof.inspect_fixture(self.cal,self.reg,self.proto,self.comment)["status"],
            proof.OFFLINE)

    def test_duplicate_git_sha_claim_is_rejected(self):
        c=deepcopy(self.comment)
        line=(f"- 対象一覧のGit blob SHA: "
              f"{proof.git_blob_sha(self.cal)}\n")
        c["body"]+=line
        with self.assertRaisesRegex(ValueError,"HOLD_MISSING_OR_DUPLICATE"):
            proof.inspect_fixture(self.cal,self.reg,self.proto,c)


if __name__=="__main__":
    unittest.main()
