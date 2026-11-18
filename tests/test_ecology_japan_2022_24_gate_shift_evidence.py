"""Preserve signed empirical participant-selection vs same-horse year changes."""
import json
import math
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PROVENANCE=ROOT/"docs/evidence/japan-2022-24-gate-shift-composition-paired-20261118.json"
OLDER=ROOT/"docs/evidence/japan-2022-trained-kin-gate-2023-24-transfer-20261118.json"


class GateShiftActualAggregateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=json.loads(PROVENANCE.read_text(encoding="utf-8"))
        cls.old=json.loads(OLDER.read_text(encoding="utf-8"))

    def test_population_and_original_both_source_sha_parity(self):
        q=self.q["source"]
        self.assertEqual((q["strict_starts"],q["horse_candidates"],q["strict_races"]),
                         (244147,12887,35333))
        self.assertEqual(q["SHA_A"],self.old["evidence_run"]["sourceA_SHA256"])
        self.assertEqual(q["SHA_B"],self.old["evidence_run"]["sourceB_SHA256"])
        self.assertEqual(q["original_2022_gate"],
            self.old["choice_from_already_inspected_2022"]["selected"])

    def test_real_action_success_and_no_horse_level_source_redistribution(self):
        self.assertEqual(self.q["successful_run"]["id"],44294790802)
        self.assertEqual(self.q["successful_run"]["conclusion"],"success")
        self.assertEqual(self.q["successful_run"]["artifact_id"],14422134348)
        self.assertTrue(self.q["successful_run"]["all_passed"])
        self.assertTrue(self.q["holds"]["no_private_ID_names_individual_races_or_genotypes_uploaded"])

    def test_fixed_2022_gate_positive_and_both_later_years_negative(self):
        x=self.q["MSE_advantage_gate_over_M2"]
        self.assertGreater(x["2022"],0)
        self.assertLess(x["2023"],0)
        self.assertLess(x["2024"],x["2023"])

    def test_exact_2022_reference_MSE_not_RMSE_decomposition(self):
        q=self.q["four_focal_history_bin_standardization"]
        original=self.q["MSE_advantage_gate_over_M2"]
        for year in ("2023","2024"):
            d=q["2022_to_"+year]
            self.assertAlmostEqual(
                d["total"],d["composition"]+d["within"],places=13)
            self.assertAlmostEqual(
                d["total"],original[year]-original["2022"],places=13)
            self.assertAlmostEqual(
                d["composition_fraction"]+d["within_fraction"],1,places=12)
        self.assertLess(q["2022_to_2024"]["composition_fraction"],0.06)
        self.assertGreater(q["2022_to_2024"]["within_fraction"],0.94)
        self.assertGreater(q["2022_to_2024"]["bin_16plus_signed_total_fraction"],.85)
        self.assertTrue(q["MSE_not_RMSE_exact_reconstruction_passed"])

    def test_matched_horse_year_change_not_a_new_independent_significance_claim(self):
        q=self.q["same_horse_year_pair"]["2022_to_2024"]
        self.assertEqual((q["matched"],q["later_year_horse_candidates"]),(5163,5225))
        self.assertGreater(q["later_horse_fraction_also_2022"],.98)
        self.assertLess(q["first_year_advantage"],0)
        self.assertLess(q["later_advantage"],q["first_year_advantage"])
        self.assertLess(q["oneway_bootstrap_95pct"][0],0)
        self.assertGreater(q["oneway_bootstrap_95pct"][1],0)
        self.assertTrue(self.q["holds"]["same_horse_bootstrap_2024_interval_includes_zero"])

    def test_exact_participant_selection_and_paired_change_sum(self):
        d=self.q["participation_selection_three_term"]
        self.assertAlmostEqual(
            d["total"],
            d["later_participating_subset_baseline_2022_difference"]+
            d["same_horse_year_change"]+
            d["later_full_vs_matched_residual"],places=13)
        self.assertGreater(d["signed_fractions"][0],.42)
        self.assertGreater(d["signed_fractions"][1],.57)
        self.assertLess(d["signed_fractions"][2],.001)
        self.assertTrue(d["three_components_exactly_sum_to_total"])

    def test_2024_midpoint_loss_and_causal_genetic_market_hold_unchanged(self):
        h=self.q["holds"]
        for x in (
            "gate_and_always_M2_lost_to_midpoint_in_2024",
            "posthoc_after_all_years_inspected",
            "selected_later_participants_NOT_biological_survival",
            "within_bin_and_within_horse_NOT_causal_age_environment_effect",
            "no_linked_kinship_A_genomic_G_MSTN",
            "no_market_time_series_or_betting_profit_evidence",
        ):
            self.assertTrue(h[x],x)
        self.assertEqual(h["actual_prospective_2027_pledge_count"],0)


if __name__=="__main__":
    unittest.main()
