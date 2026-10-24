#!/usr/bin/env python3
"""2027 external SHA comment is not an approved calendar or scored trial."""
from copy import deepcopy
import json
from pathlib import Path
import sys,unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import odds_2027_provisional_comment_proof as proof

CAL=ROOT/"data/research/jra-graded-2027jan-mar-provisional-calendar.json"
REG=ROOT/"data/research/odds-prequential-2027jan-mar-provisional-registry.json"


class FutureTentativeCommentProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cal=CAL.read_bytes()
        cls.reg=REG.read_bytes()
        events=json.loads(cls.cal)["events"]
        body="\n".join([
            proof.HEADER+"JRA平地GⅠ/GⅡ/GⅢの候補日程と留保",
            f"{proof.CAL_LABEL} {proof._blob(cls.cal)}",
            f"{proof.REG_LABEL} {proof._blob(cls.reg)}",
            "**暫定36件の全競走：候補日・競馬場・暫定格・競走名**",
            *[proof._listed_name(e) for e in events],
            "**日付の資料間不一致** は正式日付確認待ち",
            "これらは正式認可済みの正式日程を意味しない。",
        ])+"\n"
        cls.fake_comment={
            "id":proof.COMMENT_ID,
            "created_at":"2026-10-24T13:52:06Z",
            "updated_at":"2026-10-24T13:52:06Z",
            "body":body,
        }

    def test_offline_fixture_holds_despite_valid_36_slot_shas(self):
        report=proof.inspect_fixture(self.cal,self.reg,self.fake_comment)
        self.assertEqual(report["status"],proof.OFFLINE)
        self.assertFalse(report["external_GitHub_API_trusted"])
        self.assertEqual(report["candidate_2027_flat_graded_races"],36)
        self.assertEqual(report["documented_disputed_date_cases"],4)
        self.assertTrue(report["two_grade_promotions_pending_not_final"])
        self.assertTrue(report["candidate_2027_listed_lines_all_present_once"])
        self.assertEqual(report["server_time_supplied_by_fixture"],
                         "2026-10-24T13:52:06+00:00")
        self.assertTrue(report["official_2027_regulatory_approval_not_proven"])
        self.assertEqual(report["prediction_scores_from_actual_races"],0)

    def test_changed_original_file_bytes_fail_sha_not_reinterpreted_as_valid_revision(self):
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_2027_SUBMITTED_CALENDAR_REGISTRY_HASH_CHANGED"):
            proof.inspect_fixture(self.cal+b" ",self.reg,self.fake_comment)
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_2027_SUBMITTED_CALENDAR_REGISTRY_HASH_CHANGED"):
            proof.inspect_fixture(self.cal,self.reg+b" ",self.fake_comment)

    def test_calendar_item_missing_or_duplicate_in_comment_rejected(self):
        first=json.loads(self.cal)["events"][0]
        line=proof._listed_name(first)
        altered=deepcopy(self.fake_comment)
        altered["body"]=altered["body"].replace(line,"- deleted other 2027 event")
        with self.assertRaisesRegex(ValueError,"HOLD_2027_PROVISIONAL_RACE_MISSING"):
            proof.inspect_fixture(self.cal,self.reg,altered)
        altered=deepcopy(self.fake_comment)
        altered["body"]+=line+"\n"
        with self.assertRaisesRegex(ValueError,"HOLD_2027_PROVISIONAL_RACE_MISSING"):
            proof.inspect_fixture(self.cal,self.reg,altered)

    def test_conflicts_and_promotion_qualifiers_explicitly_written(self):
        cal=json.loads(self.cal)
        disputed=[e for e in cal["events"]
                  if e["alternate_reported_dates_jst"]]
        self.assertEqual(len(disputed),4)
        for e in disputed:
            self.assertIn("確定要照合",proof._listed_name(e))
        for label in ("根岸ステークス","オーシャンステークス"):
            e=next(row for row in cal["events"] if row["race_name_jp"]==label)
            self.assertIn("G2昇格審査待ち",proof._listed_name(e))
        edited=deepcopy(self.fake_comment)
        edited["body"]=edited["body"].replace(
            "これらは正式認可済みの正式日程を意味しない。","")
        with self.assertRaisesRegex(ValueError,"HOLD_COMMENT_REMOVED_UNCERTAINTY"):
            proof.inspect_fixture(self.cal,self.reg,edited)

    def test_unedited_pre_2027_first_race_server_clock_required(self):
        amended=deepcopy(self.fake_comment)
        amended["updated_at"]="2026-10-24T13:53:06Z"
        with self.assertRaisesRegex(ValueError,"HOLD_SUBMITTED_2027_PR_COMMENT_EDITED"):
            proof.inspect_fixture(self.cal,self.reg,amended)
        amended=deepcopy(self.fake_comment)
        amended["created_at"]=amended["updated_at"]="2027-01-04T00:00:00Z"
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_2027_CALENDAR_COMMITTED_AFTER_FIRST_START"):
            proof.inspect_fixture(self.cal,self.reg,amended)

    def test_duplicate_or_missing_SHA_field_rejected(self):
        for label,original in (
            (proof.CAL_LABEL,proof._blob(self.cal)),
            (proof.REG_LABEL,proof._blob(self.reg)),
        ):
            altered=deepcopy(self.fake_comment)
            altered["body"]+=f"{label} {original}\n"
            with self.assertRaisesRegex(ValueError,
                                        "HOLD_COMMITMENT_SHA_FIELD_DUPLICATE_OR_MISSING"):
                proof.inspect_fixture(self.cal,self.reg,altered)

    def test_GitHub_api_unavailable_must_not_claim_proof(self):
        with patch.object(proof.subprocess,"run",side_effect=OSError("unavailable")):
            with self.assertRaisesRegex(ValueError,
                                        "HOLD_GITHUB_SERVER_PRECOMMITMENT_FETCH_FAILED"):
                proof.verify_live(self.cal,self.reg)
        self.assertEqual(
            proof.inspect_fixture(self.cal,self.reg,self.fake_comment)["status"],
            proof.OFFLINE)


if __name__=="__main__":
    unittest.main()
