#!/usr/bin/env python3
"""2026 original Git blobs immutable, 2027 proposals separated and uncertain."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_multiyear_provisional_coverage import (
    EXPECTED_2026_GIT_BLOB, STATUS, audit_raw, audit_2027, blob_sha,
)

P={
    "calendar_2026":ROOT/"data/research/jra-graded-flat-2026oct25-dec27-calendar.json",
    "registry_2026":ROOT/"data/research/odds-prequential-2026oct24-coverage-registry.json",
    "protocol":ROOT/"docs/odds-prequential-graded-cohort-v1-20261024.json",
    "calendar_2027":ROOT/"data/research/jra-graded-2027jan-mar-provisional-calendar.json",
    "registry_2027":ROOT/"data/research/odds-prequential-2027jan-mar-provisional-registry.json",
}


class TwoYearDenominatorAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw={k: p.read_bytes() for k,p in P.items()}
        cls.future=json.loads(cls.raw["calendar_2027"])
        cls.staged=json.loads(cls.raw["registry_2027"])
        cls.report=audit_raw(*(cls.raw[k] for k in (
            "calendar_2026","registry_2026","protocol",
            "calendar_2027","registry_2027")))

    def test_combined_62_provisional_calendar_slots_no_empirical_scores(self):
        r=self.report
        self.assertEqual(r["status"],STATUS)
        self.assertEqual(r["2026_immutable_flat_graded_slots"],26)
        self.assertEqual(r["2027_Q1_provisional_candidate_slots"],36)
        self.assertEqual(r["preliminary_total_planned_cohort_slots"],62)
        self.assertEqual(r["2027_candidate_race_dates_provisional"],23)
        self.assertEqual(r["2027_month_counts_provisional"],{
            "1":11,"2":12,"3":13})
        self.assertEqual(r["forecast_results_officially_scored_in_this_prestart_cohort"],0)
        self.assertFalse(r["full_study_period_official_grades_and_exact_dates_verified"])
        self.assertTrue(r["software_support_gate_of_60_can_never_be_met_by_calendar_slots_alone"])
        self.assertTrue(r["v31_frozen_holdout_untouched"])

    def test_original_oct_dec_2026_prerecord_and_protocol_are_not_rewritten(self):
        r=self.report
        self.assertTrue(r["original_2026_and_protocol_Git_blobs_unmodified"])
        self.assertEqual(r["externally_precommitted_2026_26_race_list_comment_id"],
                         6382991405)
        for key,expected in EXPECTED_2026_GIT_BLOB.items():
            actual_key={
                "2026_calendar":"calendar_2026",
                "2026_registry":"registry_2026",
                "protocol_v1":"protocol",
            }[key]
            self.assertEqual(blob_sha(self.raw[actual_key]),expected)
        self.assertEqual(
            self.future["separate_from_unmodified_2026_Oct_Dec_precommit"],
            True)

    def test_four_disputed_calendar_days_are_not_silently_declared_final(self):
        a=self.report
        self.assertEqual(a["2027_disputed_exact_date_count"],4)
        self.assertEqual(set(a["2027_disputed_names"]),{
            "フェアリーステークス","フィリーズレビュー",
            "中山牝馬ステークス","フラワーカップ"})
        self.assertTrue(a["2027_calendar_not_certified_final"])
        self.assertTrue(a["JRA_ministry_approval_and_grade_review_still_required"])
        self.assertTrue(all(not e["scheduled_date_fully_verified_from_official_chart"]
                            for e in self.future["events"]))

    def test_2027_pending_promotions_are_g3_not_fabricated_g2(self):
        a=self.report
        self.assertEqual(a["2027_pending_graded_promotion_count"],2)
        self.assertEqual(set(a["2027_pending_graded_promotions"]),{
            "根岸ステークス","オーシャンステークス"})
        self.assertEqual(
            sum(x["provisional_grade"]=="G1" for x in self.future["events"]),2)
        self.assertEqual(
            sum(x["provisional_grade"]=="G2" for x in self.future["events"]),12)
        self.assertEqual(
            sum(x["provisional_grade"]=="G3" for x in self.future["events"]),22)
        y=deepcopy(self.future)
        row=next(e for e in y["events"] if e["race_name_jp"]=="根岸ステークス")
        row["provisional_grade"]="G2"
        with self.assertRaisesRegex(ValueError,"HOLD_PENDING_G2_APPLICATION_IMPROPERLY_FINALIZED"):
            audit_2027(y,self.staged)

    def test_not_allowed_to_backfill_2027_graded_results_or_guessed_post_times(self):
        data=deepcopy(self.future)
        row=data["events"][0]
        row["official_race_id"]="2027-01-04-KYOTO-11"
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_FABRICATED_OFFICIAL_RACE_CLOCK_OR_APPROVAL"):
            audit_2027(data,self.staged)
        staged=deepcopy(self.staged)
        staged["entries"][0]["status"]="preseal_external_proof_verified"
        with self.assertRaisesRegex(ValueError,"HOLD_2027_PROVISIONAL_RACE_FALSE_COMPLETION"):
            audit_2027(self.future,staged)

    def test_2027_missing_double_registered_or_added_events_are_rejected(self):
        st=deepcopy(self.staged)
        st["entries"].pop()
        with self.assertRaisesRegex(ValueError,"HOLD_2027_PROVISIONAL_CANDIDATE_DENOMINATOR_MISSING"):
            audit_2027(self.future,st)
        st=deepcopy(self.staged)
        st["entries"][1]["slot_id"]=st["entries"][0]["slot_id"]
        with self.assertRaisesRegex(ValueError,"HOLD_2027_COVERAGE_SLOT_OMITTED_OR_EXTRA"):
            audit_2027(self.future,st)
        fut=deepcopy(self.future)
        fut["events"][1]["slot_id"]=fut["events"][0]["slot_id"]
        with self.assertRaisesRegex(ValueError,"HOLD_2027_RACE_IDENTITY_CHANGED"):
            audit_2027(fut,self.staged)

    def test_date_conflict_source_alternatives_must_remain_annotated(self):
        for name in ("フェアリーステークス","フィリーズレビュー",
                     "中山牝馬ステークス","フラワーカップ"):
            q=deepcopy(self.future)
            e=next(row for row in q["events"] if row["race_name_jp"]==name)
            self.assertEqual(len(e["alternate_reported_dates_jst"]),1)
            e["alternate_reported_dates_jst"]=[]
            with self.assertRaisesRegex(
                    ValueError,"HOLD_DISPUTED_2027_RACE_SILENTLY_DECLARED_CONFIRMED"):
                audit_2027(q,self.staged)
        f=deepcopy(self.future)
        f["events"][0]["alternate_reported_dates_jst"]=["2027-01-05"]
        with self.assertRaisesRegex(ValueError,"HOLD_NEW_UNDOCUMENTED_AMBIGUOUS_DATE"):
            audit_2027(f,self.staged)

    def test_regulatory_approval_and_provider_provenance_missing_fail(self):
        cal=deepcopy(self.future)
        cal["final_2027_JRA_event_grades_approved"]=True
        with self.assertRaisesRegex(ValueError,"HOLD_2027_GRADE_OR_SCHEDULE_NOT_YET_FINAL"):
            audit_2027(cal,self.staged)
        cal=deepcopy(self.future)
        cal["source_official_provisional_pdf"]="https://example.test/wrong.pdf"
        with self.assertRaisesRegex(ValueError,"HOLD_UNVERIFIED_JRA_2027_PROVISIONAL_SOURCE"):
            audit_2027(cal,self.staged)
        st=deepcopy(self.staged)
        st["full_future_results_scored_count"]=1
        with self.assertRaisesRegex(ValueError,"HOLD_UNATTESTED_2027_RESULTS_MARKED_SCORED"):
            audit_2027(self.future,st)

    def test_2026_original_hash_not_replaced_by_current_2027_staging(self):
        changed=dict(self.raw)
        changed["calendar_2026"]+=b"\n"
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_ORIGINAL_PRECOMMITTED_2026_OR_PROTOCOL_BLOB_MUTATED"):
            audit_raw(*(changed[k] for k in (
                "calendar_2026","registry_2026","protocol",
                "calendar_2027","registry_2027")))
        changed=dict(self.raw)
        changed["protocol"]+=b" "
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_ORIGINAL_PRECOMMITTED_2026_OR_PROTOCOL_BLOB_MUTATED"):
            audit_raw(*(changed[k] for k in (
                "calendar_2026","registry_2026","protocol",
                "calendar_2027","registry_2027")))

    def test_missing_2027_in_past_cohort_does_not_trigger_fake_statistical_advantage(self):
        v=audit_2027(self.future,self.staged)
        self.assertEqual(v["provisional_candidates"],36)
        self.assertFalse(v["full_calendar_certified"])
        self.assertEqual(v["official_race_results_scored"],0)
        self.assertTrue(self.report[
            "no_real_forward_winning_probability_advantage_established"])


if __name__=="__main__":
    unittest.main()
