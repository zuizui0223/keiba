"""FICTIONAL ONLY: prospective 2027 frozen-denominator/rank-completion bounds.

No real JRA horses, official data access, licensed schedule, market quotes,
registered pedigrees or actual 2027 forecast is used.
"""
from __future__ import annotations

import copy
from datetime import datetime
import itertools
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ecology_japan_2027_point_in_time_ledger import (
    freeze, score, canonical_bytes, digest_bytes
)
from ecology_japan_2027_denominator_rank_bounds import (
    audit_universe, _race_permutation_extrema, STATUS,
)
from test_ecology_japan_2027_point_in_time_ledger import (
    fictional, completed_results, fake_sha, ASOF, CLOCK
)


def snapshot():
    entries,parents,history,model=fictional()
    private,commit=freeze(entries,parents,history,model,
                          asof=ASOF,clock=CLOCK,source_sha=fake_sha())
    results=completed_results(entries)
    races={}
    for e in entries:
        races[e["race_id"]]=e["race_start_at_jst"]
    eligible=[{
        "race_id":rid,
        "race_start_at_jst":day,
        "eligibility_known_at_jst":"2027-01-08T18:00:00+09:00"
    } for rid,day in sorted(races.items())]
    return private,commit,results,eligible


class FrozenDenominatorTests(unittest.TestCase):
    def setUp(self):
        self.private,self.manifest,self.complete,self.eligible=snapshot()

    def audit(self, outcomes=None, expected=None):
        return audit_universe(
            self.private,self.manifest,
            self.complete if outcomes is None else outcomes,
            expected_races=self.eligible if expected is None else expected
        )

    def test_fully_observed_bounds_collapse_to_original_full_horse_equal_mse(self):
        o=self.audit()
        prev=score(self.private,self.manifest,self.complete)
        self.assertEqual(o["status"],STATUS)
        self.assertEqual(o["frozen_races"],2)
        self.assertEqual(o["frozen_starts"],6)
        self.assertEqual(o["frozen_unique_horses"],3)
        self.assertEqual(o["result_availability_counts_races"]["complete_classified_race"],2)
        self.assertEqual(o["source_eligible_race_universe_coverage"][
            "eligible_races_without_a_frozen_prediction"],0)
        for left,right in (("M1","M2"),("M0","M2")):
            b=o["MSE_gain_bounds"][f"{left}_minus_{right}_full_frozen_population_MSE"]
            self.assertEqual(b["status"],"FULLY_CLASSIFIED_FROZEN_BUNDLE_MSE_ALREADY_OBSERVED")
            self.assertAlmostEqual(
                b["min_feasible_MSE_difference"],b["max_feasible_MSE_difference"],places=12)
            self.assertAlmostEqual(
                b["min_feasible_MSE_difference"],
                prev["RMSE_equal_horse_weight"][left]**2-
                prev["RMSE_equal_horse_weight"][right]**2,places=12)
        self.assertFalse(o["actual_external_Github_pre_race_attestation_verified_by_this_tool"])

    def test_missing_second_race_produces_nontrivial_possible_rank_bounds(self):
        first=self.eligible[0]["race_id"]
        published=[x for x in self.complete if x["race_id"]==first]
        o=self.audit(published)
        self.assertEqual(o["result_availability_counts_races"]["complete_classified_race"],1)
        self.assertEqual(o["result_availability_counts_races"]["no_reported_result"],1)
        b=o["MSE_gain_bounds"]["M1_minus_M2_full_frozen_population_MSE"]
        self.assertEqual(b["status"],"HYPOTHETICAL_ALL_MISSING_RACES_FINISH_CLASSIFIED")
        self.assertLess(b["min_feasible_MSE_difference"],
                        b["max_feasible_MSE_difference"])
        self.assertTrue(b["missing_partial_result_rows_not_used_to_narrow_bounds"])
        self.assertTrue(o["original_scorer_scored_only_conditional_not_a_population_estimate"])

    def test_partial_result_reports_do_not_become_fabricated_complete_rank(self):
        first=self.eligible[0]["race_id"]
        part=[x for x in self.complete if x["race_id"]==first][:2]
        o=self.audit(part)
        self.assertGreater(o["result_availability_counts_races"]["partially_reported_result"],0)
        self.assertEqual(
            o["reported_partial_race_rank_values_ignored_for_conservative_bounds"],1)
        self.assertEqual(o["result_availability_counts_races"]["complete_classified_race"],0)
        self.assertIn("HYPOTHETICAL",o["MSE_gain_bounds"][
            "M1_minus_M2_full_frozen_population_MSE"]["status"])

    def test_dnf_quarantined_as_undefined_not_imputed_rank(self):
        r=copy.deepcopy(self.complete)
        r[0]["finish_status"]="DNF"
        r[0]["finish_rank"]=""
        o=self.audit(r)
        self.assertEqual(o["result_availability_counts_races"][
            "undefined_rank_target_or_source_conflict"],1)
        self.assertEqual(o["MSE_gain_bounds"][
            "M1_minus_M2_full_frozen_population_MSE"]["status"],
            "HOLD_PREDICTED_RACE_WITH_UNDEFINED_NORMALIZED_RANK_TARGET")
        self.assertIsNone(o["MSE_gain_bounds"][
            "M1_minus_M2_full_frozen_population_MSE"]["min_feasible_MSE_difference"])
        self.assertTrue(o["unknown_DNF_or_cancelled_finish_rank_is_NOT_imputed"])

    def test_missing_eligible_race_has_no_universe_wide_gain_bound(self):
        other={
            "race_id":"JRA:FICTIONAL_NO_FORECAST",
            "race_start_at_jst":"2027-01-11T14:00:00+09:00",
            "eligibility_known_at_jst":"2027-01-08T18:00:00+09:00"
        }
        o=self.audit(expected=self.eligible+[other])
        cov=o["source_eligible_race_universe_coverage"]
        self.assertEqual(cov["eligible_races_declared"],3)
        self.assertEqual(cov["eligible_races_without_a_frozen_prediction"],1)
        self.assertEqual(cov["status"],"HOLD_PREDECLARED_RACES_WITHOUT_FORECAST")
        self.assertIsNone(o["MSE_gain_bounds"][
            "M1_minus_M2_full_frozen_population_MSE"]["min_feasible_MSE_difference"])
        self.assertNotIn("FICTIONAL_NO_FORECAST",json.dumps(o))

    def test_no_supplied_universe_never_certifies_complete_JRA_coverage(self):
        o=audit_universe(self.private,self.manifest,self.complete)
        cov=o["source_eligible_race_universe_coverage"]
        self.assertEqual(cov["status"],"HOLD_NO_SEPARATE_PRETARGET_RACE_UNIVERSE")
        self.assertFalse(cov["provided_source_eligible_race_universe"])
        self.assertFalse(cov["official_jra_nar_schedule_completeness_independently_certified"])
        self.assertTrue(o["source_scope"].startswith("ONE_LOCALLY_FROZEN"))

    def test_supplied_schedule_known_after_asof_is_not_prior_commitment(self):
        bad=copy.deepcopy(self.eligible)
        bad[0]["eligibility_known_at_jst"]="2027-01-08T20:00:00+09:00"
        with self.assertRaisesRegex(ValueError,"TARGET_UNIVERSE_DUPLICATE_LATE"):
            self.audit(expected=bad)

    def test_frozen_forecast_outside_declared_schedule_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORECAST_OUTSIDE_DECLARED"):
            self.audit(expected=self.eligible[:1])

    def test_schedule_start_mismatch_is_not_silent(self):
        bad=copy.deepcopy(self.eligible)
        bad[0]["race_start_at_jst"]="2027-01-09T18:00:00+09:00"
        with self.assertRaisesRegex(ValueError,"START_NOT_IN_PRETARGET_UNIVERSE"):
            self.audit(expected=bad)

    def test_immutable_private_prediction_digest_must_match_aggregate_manifest(self):
        q=copy.deepcopy(self.private)
        q["predictions"][0]["M2"]=.999
        with self.assertRaisesRegex(ValueError,"DIGEST_MISMATCH"):
            audit_universe(q,self.manifest,self.complete,expected_races=self.eligible)

    def test_no_result_also_has_hypothetical_envelope_no_imputed_y(self):
        o=self.audit([])
        self.assertEqual(o["original_local_scorer_status"],
                         "HOLD_NO_FULLY_PUBLISHED_COMPLETE_RACES")
        self.assertEqual(o["result_availability_counts_races"]["no_reported_result"],2)
        self.assertEqual(o["result_availability_counts_frozen_starts"]["no_reported_result"],6)
        self.assertEqual(o["MSE_gain_bounds"][
            "M0_minus_M2_full_frozen_population_MSE"]["status"],
            "HYPOTHETICAL_ALL_MISSING_RACES_FINISH_CLASSIFIED")

    def test_permutation_bounds_sharp_for_all_three_classified_finishing_positions(self):
        race=self.eligible[0]["race_id"]
        ps=[x for x in self.private["predictions"] if x["race_id"]==race]
        weights={x["horse_id"]:1/3 for x in ps}
        a,b=_race_permutation_extrema(ps,weights,base="M1")
        values=[
            sum(weights[x["horse_id"]]*(
                (rank-float(x["M1"]))**2-(rank-float(x["M2"]))**2
            ) for x,rank in zip(ps,p))
            for p in itertools.permutations((0.0,0.5,1.0))
        ]
        self.assertAlmostEqual(a,min(values),places=12)
        self.assertAlmostEqual(b,max(values),places=12)

    def test_single_race_closure_does_not_change_frozen_horse_denominator(self):
        first=self.eligible[0]["race_id"]
        observed=[x for x in self.complete if x["race_id"]==first]
        o=self.audit(observed)
        self.assertEqual(o["frozen_unique_horses"],3)
        self.assertEqual(o["frozen_starts"],6)
        self.assertEqual(o["result_availability_counts_frozen_starts"][
            "complete_classified_race"],3)
        self.assertEqual(o["result_availability_counts_frozen_starts"][
            "no_reported_result"],3)

    def test_no_identifiers_or_private_predictions_returned(self):
        o=self.audit(self.complete)
        s=json.dumps(o,ensure_ascii=False)
        for x in ("H:111","H:112","H:113","JRA:FAKE20270109",
                  "B:FAKE7","private_horse_level_predictions"):
            self.assertNotIn(x,s)
        self.assertTrue(o["privacy_no_horse_race_identifiers_or_individual_predictions_exported"])
        self.assertTrue(o["no_real_2027_model_effect_established_by_software_test"])
        self.assertFalse(o["licensed_official_race_universe_and_JRA_IDs_verified_by_this_tool"])


if __name__=="__main__":
    unittest.main()
