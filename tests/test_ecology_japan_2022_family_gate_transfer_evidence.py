"""Source-locked actual aggregate safety checks, no original racing records."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
NOW=ROOT/"docs/evidence/japan-2022-trained-kin-gate-2023-24-transfer-20261118.json"
PRIOR=ROOT/"docs/evidence/japan-2022-24-posthoc-kin-information-moderators-20261118.json"


class ActualSource2022GateTransferEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=json.loads(NOW.read_text(encoding="utf-8"))
        cls.prior=json.loads(PRIOR.read_text(encoding="utf-8"))

    def test_original_same_strict_cohort_and_stale_2018_21_fitted_scores(self):
        q=self.q["source_locked_population"]
        p=self.prior["locked_strict_sample"]
        self.assertEqual([q["strict_starts"],q["horse_ID_candidates"],q["complete_races"]],
                         [244147,12887,35333])
        self.assertEqual((p["starts"],p["horses"],p["races"]),
                         (244147,12887,35333))
        self.assertEqual(q["model_training_years"],"2018-2021")
        self.assertFalse(q["official_JRA_NAR_identity_certified"])

    def test_one_2022_selected_gate_and_no_later_labels_for_fit(self):
        q=self.q["choice_from_already_inspected_2022"]
        self.assertEqual(q["candidate_rules"],14)
        self.assertEqual(q["selected"],
                         "own_upto_8to15__peer_from_one_recorded_peer")
        self.assertTrue(q["only_2022_labels_used_for_rule_selection"])
        self.assertTrue(q["later_year_labels_not_used_for_fit"])
        self.assertFalse(q["actual_future_prospective_confirmation"])

    def test_no_target_years_omitted_in_order_to_make_improvement_positive(self):
        years=self.q["calendar_scores"]
        self.assertEqual([x["year"] for x in years],["2022","2023","2024"])
        self.assertEqual(sum(x["starts"] for x in years),244147)
        self.assertEqual([x["starts"] for x in years],
                         [120381,80939,42827])
        self.assertLess(years[0]["gate"],years[0]["M2"])
        self.assertGreater(years[1]["gate"],years[1]["M2"])
        self.assertGreater(years[2]["gate"],years[2]["M2"])

    def test_2024_old_models_and_gate_all_lose_to_midpoint(self):
        y=self.q["calendar_scores"][2]
        self.assertLess(y["M0"],min(y["M1"],y["M2"],y["gate"]))
        self.assertGreater(y["improvement_vs_M1"],0)
        self.assertLess(y["improvement_vs_M0"],0)
        self.assertLess(y["improvement_vs_M2"],0)

    def test_2023_2024_pooled_neg_vs_always_kin_even_if_better_than_M1(self):
        q=self.q["unchanged_gate_combined_2023_2024"]
        self.assertEqual(q["starts"],123766)
        self.assertLess(q["rmse_M2"],q["rmse_gate"])
        self.assertLess(q["rmse_gate"],q["rmse_M1"])
        self.assertLess(q["improvement_M2_minus_gate"],0)
        self.assertGreater(q["improvement_M1_minus_gate"],0)
        self.assertLess(max(q["horse_CI95_M2_minus_gate"]),0)
        self.assertLess(max(q["day_CI95_M2_minus_gate"]),0)

    def test_2022_restricted_selection_fraction_changes_by_year(self):
        s=self.q["calendar_scores"]
        self.assertTrue(all(0<x["selected_fraction"]<1 for x in s))
        self.assertGreater(s[2]["selected_fraction"],s[1]["selected_fraction"])
        self.assertGreater(s[1]["selected_fraction"],s[0]["selected_fraction"])
        self.assertEqual([x["selected_M2_starts"] for x in s],[57914,44667,25612])

    def test_degradation_not_passed_off_as_heritability_market_or_future_result(self):
        e=self.q["negative_and_HOLD"]
        for key in (
            "historical_gate_does_not_beat_always_M2_in_2023",
            "historical_gate_does_not_beat_always_M2_in_2024",
            "gate_2024_worse_than_fixed_midpoint",
            "yearly_direction_not_stable",
            "earlier_outcome_inspection_makes_all_followups_posthoc",
            "market_odds_trajectory_missing",
            "genomic_G_ID_link_missing",
            "breeding_stable_shared_environment_not_identified",
            "source_originals_individual_racehorse_rows_not_uploaded",
        ):
            self.assertTrue(e[key],key)
        self.assertEqual(e["real_2027_pre_race_pledges"],0)

    def test_original_source_SHA_and_successful_complete_race_execution(self):
        e=self.q["evidence_run"]
        self.assertEqual(e["id"],44289780591)
        self.assertEqual(e["status"],"success")
        self.assertEqual(e["artifact_id"],14419759987)
        self.assertEqual(e["sourceA_SHA256"],
                         self.prior["empirical_action_run_source"]["source_A_sha256"])
        self.assertEqual(e["sourceB_SHA256"],
                         self.prior["empirical_action_run_source"]["source_B_sha256"])


if __name__=="__main__":
    unittest.main()
