#!/usr/bin/env python3
"""Official JRA flat graded calendar denominator — no outcome cherry-picking."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_graded_calendar_coverage import (
    CALENDAR_SCHEMA, REGISTRY_SCHEMA, PROTOCOL_SCHEMA, STATUS,
    audit, validate_calendar,
)

CAL=ROOT/"data/research/jra-graded-flat-2026oct25-dec27-calendar.json"
REG=ROOT/"data/research/odds-prequential-2026oct24-coverage-registry.json"


class GradedCalendarCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(CAL.read_text(encoding="utf-8"))
        cls.r=json.loads(REG.read_text(encoding="utf-8"))
        cls.report=audit(cls.c,cls.r)

    def test_all_26_official_2026_flat_graded_events_registered_not_result_chosen(self):
        a=self.report
        self.assertEqual(a["status"],STATUS)
        self.assertEqual(a["calendar_segment_event_count"],26)
        self.assertEqual(a["calendar_segment_distinct_race_dates"],20)
        self.assertEqual(a["coverage_rows_present"],26)
        self.assertTrue(a["coverage_all_registered_for_segment"])
        self.assertEqual(a["segment_start_jst"],"2026-10-25")
        self.assertEqual(a["segment_end_jst"],"2026-12-27")
        self.assertEqual(a["full_protocol_study_end_jst"],"2027-03-31")
        self.assertFalse(a["full_period_calendar_denominator_verified"])
        self.assertTrue(a["future_2027_Jan_Mar_segment_NOT_REGISTERED"])
        self.assertFalse(a["official_results_used_to_select_race_slots"])
        self.assertEqual(a["actual_forward_graded_stakes_scores_count"],0)

    def test_exactly_one_unverified_kikka_preseal_and_all_future_slots_retained(self):
        a=self.report
        self.assertEqual(a["status_counts"],{
            "preseal_sha_submitted_unverified":1,
            "upcoming_not_due":25,
        })
        self.assertEqual(
            a["registered_local_SHA_submission_count_not_externally_verified"],1)
        self.assertEqual(a["externally_proven_prestart_submissions_count"],0)
        self.assertEqual(a["overdue_pending_unresolved_races"],[])
        head=a["per_slot_coverage"][0]
        self.assertEqual(head["date"],"2026-10-25")
        self.assertEqual(head["grade"],"G1")
        self.assertEqual(head["venue"],"京都")
        self.assertEqual(head["race_name_jp"],"菊花賞")
        self.assertTrue(head["has_only_local_SHA_claim_no_GitHub_proof"])
        self.assertFalse(head["is_eligible_for_actual_prospective_scoring_now"])
        self.assertTrue(all(
            not row["is_eligible_for_actual_prospective_scoring_now"]
            for row in a["per_slot_coverage"]))

    def test_public_calendar_excludes_all_jumping_grades(self):
        c=self.c
        self.assertEqual(c["schema"],CALENDAR_SCHEMA)
        self.assertTrue(c["not_an_externally_signed_official_calendar_snapshot"])
        self.assertFalse(c["calendar_segment_is_entire_study_horizon"])
        self.assertTrue(all(e["grade"] in ("G1","G2","G3")
                            for e in c["events"]))
        self.assertFalse(any(
            "中山大障害" in e["race_name_jp"] or "京都ジャンプ" in e["race_name_jp"]
            for e in c["events"]))
        self.assertEqual(sum(e["grade"]=="G1" for e in c["events"]),10)

    def test_missing_even_one_future_race_blocks_full_denominator(self):
        registry=deepcopy(self.r)
        registry["entries"].pop()
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_CALENDAR_RACES_OMITTED"):
            audit(self.c,registry)
        registry=deepcopy(self.r)
        registry["entries"].append({
            "slot_id":"2026-12-30|中山|NOT_ACTUALLY_ON_CALENDAR",
            "status":"upcoming_not_due"})
        with self.assertRaisesRegex(ValueError,"HOLD_NONCALENDAR_RACE_INSERTED"):
            audit(self.c,registry)

    def test_duplicate_or_ad_hoc_result_exclusion_rejected(self):
        registry=deepcopy(self.r)
        registry["entries"].append(deepcopy(registry["entries"][0]))
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_DUPLICATED_REGISTERED_GRADED_RACE"):
            audit(self.c,registry)
        registry=deepcopy(self.r)
        registry["entries"][0]["status"]="excluded_after_result"
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_UNDECLARED_OUTCOME_DRIVEN_SELECTION_STATUS"):
            audit(self.c,registry)
        registry=deepcopy(self.r)
        registry["entries"][0]["status"]="postrace_scored_provenance_not_independently_checked"
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_SELF_CLAIMED_REMOTE_PROOF"):
            audit(self.c,registry)

    def test_corrupted_or_deleted_seal_does_not_turn_into_completed_validation(self):
        registry=deepcopy(self.r)
        registry["entries"][0]["preseal_digest_sha256"]="x"*64
        with self.assertRaisesRegex(ValueError,"HOLD_SHA_COMMITMENT_CANNOT"):
            audit(self.c,registry)
        registry=deepcopy(self.r)
        registry["entries"][0]["preseal_comment_id"]=None
        with self.assertRaisesRegex(ValueError,"HOLD_SHA_COMMITMENT_CANNOT"):
            audit(self.c,registry)
        registry=deepcopy(self.r)
        registry["entries"][1]["preseal_comment_id"]=42
        with self.assertRaisesRegex(ValueError,"HOLD_UNDECLARED_EARLY_PRESEAL"):
            audit(self.c,registry)

    def test_calendar_horizon_misrepresentation_or_nonflat_grade_rejected(self):
        cal=deepcopy(self.c)
        cal["calendar_segment_is_entire_study_horizon"]=True
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_UNCERTIFIED_COMPLETE_OR_DIFFERENT"):
            validate_calendar(cal)
        cal=deepcopy(self.c)
        cal["events"][0]["grade"]="J-G1"
        with self.assertRaisesRegex(ValueError,"HOLD_NON_FLAT_GRADE"):
            validate_calendar(cal)
        cal=deepcopy(self.c)
        cal["events"][0]["slot_id"]="FICTITIOUS_CHANGED_ID"
        with self.assertRaisesRegex(ValueError,"HOLD_DUPLICATE_OR_MUTATED"):
            validate_calendar(cal)

    def test_due_and_unresolved_sources_cannot_be_hidden_under_not_due(self):
        later=deepcopy(self.r)
        later["declared_as_of_jst"]="2026-12-28T09:00:00+09:00"
        a=audit(self.c,later)
        self.assertEqual(len(a["overdue_pending_unresolved_races"]),25)
        self.assertFalse(a["full_period_calendar_denominator_verified"])
        self.assertEqual(a["actual_forward_graded_stakes_scores_count"],0)

    def test_2027_future_program_must_remain_honest_hold(self):
        x=audit(self.c,self.r)
        self.assertEqual(
            x["official_JRA_public_calendar_source"],
            "https://jra.jp/datafile/seiseki/replay/2026/jyusyo.html")
        self.assertTrue(
            x["calendar_data_transcribed_from_official_site_not_cryptographically_signed"])
        self.assertTrue(x["no_statistical_winner_information_advantage_established"])
        self.assertTrue(x["registry_must_keep_unscored_and_missing_source_races"])


if __name__=="__main__":
    unittest.main()
