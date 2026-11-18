"""Source-pinned 2022-24 strictly post-hoc ecological moderation evidence gates."""
from __future__ import annotations
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"docs/evidence/japan-2022-24-posthoc-kin-information-moderators-20261118.json"
PRIOR=ROOT/"docs/evidence/japan-2022-2024-joint-strict-strong-20261116.json"


class EmpiricalModeratorEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.source=json.loads(PRIOR.read_text(encoding="utf-8"))

    def test_old_evaluation_population_parity_is_not_a_new_test(self):
        f=self.audit["locked_strict_sample"]
        o=self.source["analysis_from_actual_successful_job_stdout"]["strict_strong"]
        self.assertEqual([f["horses"],f["starts"],f["races"]],
                         [12887,244147,35333])
        self.assertEqual([int(o["unique_horses"]),int(o["rows"]),int(o["races"])],
                         [12887,244147,35333])
        self.assertAlmostEqual(f["M1_own_strong_rmse"],o["RMSE_portable_no_kin"])
        self.assertAlmostEqual(f["M2_own_plus_recorded_parent_other_horse_rmse"],
                               o["RMSE_portable_kin"])

    def test_no_group_was_silently_dropped_to_obtain_positive_pattern(self):
        d=self.audit["own_record_count_2021_source_A_bins"]
        self.assertEqual(sum(x["starts"] for x in d.values()),244147)
        self.assertTrue(d["0-3"]["gain_M1_minus_M2"]>
                        d["4-7"]["gain_M1_minus_M2"]>
                        d["8-15"]["gain_M1_minus_M2"]>
                        d["16+"]["gain_M1_minus_M2"])
        self.assertLess(d["16+"]["gain_M1_minus_M2"],0)

    def test_2024_reverse_of_low_to_high_moderation_is_retained(self):
        year=self.audit["year_by_own_history_M1_minus_M2"]
        self.assertGreater(year["2022"]["0-3"],year["2022"]["16+"])
        self.assertLess(year["2024"]["0-3"],year["2024"]["16+"])
        self.assertTrue(self.audit["locked_strict_sample"][
            "results_2024_family_failed_vs_midpoint"])

    def test_family_source_age_not_assumed_monotonic(self):
        age=self.audit["parent_other_horse_record_age_since_last_old_source_race"]
        self.assertGreater(age["1096_plus_days"]["gain"],
                           age["0_365_days"]["gain"])
        self.assertLess(age["no_recorded_date"]["gain"],0)

    def test_unobserved_peer_model_deterioration_is_not_erased(self):
        p=self.audit["parent_other_horse_eligible_record_count"]
        self.assertLess(p["none"]["gain"],0)
        self.assertLess(p["one"]["gain"],0)
        self.assertGreater(p["two_four"]["gain"],0)
        self.assertEqual(sum(x["starts"] for x in p.values()),244147)

    def test_missing_eligible_history_not_an_official_debut(self):
        q=self.audit["original_history_source_coverage"]
        self.assertEqual(q["sourceA_focal_rows_with_one_eligible_race"],956)
        self.assertEqual(q["sourceA_focal_rows_with_zero_eligible_races"],0)
        self.assertEqual(q["median_focal_recorded_prior_starts"],14)

    def test_initial_ci_alias_failure_honestly_recorded(self):
        e=self.audit["empirical_action_run_source"]
        self.assertEqual(e["first_complete_aggregate_produced_in_run"],44284912350)
        self.assertEqual(e["first_aggregate_artifact_id"],14419480112)
        self.assertEqual(e["full_workflow_initial_conclusion"],"failure")
        self.assertIn("strict_sample_QA",e["initial_failure_reason"])

    def test_posthoc_and_genetic_and_unlicensed_source_holds(self):
        self.assertTrue(self.audit["only_existing_real_2022_2024_source_outcomes"])
        self.assertTrue(self.audit["no_individual_horse_ids_names_results_or_race_rows_exported"])
        self.assertTrue(self.audit["genome_G_A_full_pedigree_market_time_series_not_joined"])
        self.assertFalse(self.audit["real_2027_future_prospective_validation_done"])
        self.assertFalse(self.audit["empirical_action_run_source"][
            "actual_official_registered_ID_master_joined"])
        self.assertEqual(len(self.audit["critical_negative_results"]),7)


if __name__=="__main__":
    unittest.main()
