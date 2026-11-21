"""Fictional 2022 horses: six observation-opportunity specifications and cluster guards."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2022_opportunity_cluster_inference import (
    evaluate_opportunity, STATUS, SPECIFICATIONS, EXPECTED_POINT,
)


def invented(each=50, selected2023=.84, *, base_on_opportunity=False):
    # 4 historical bins x 2 final half-year bins x 2 2022 starts bins
    # x both future source-presence values. Purely fictional identifiers.
    records=[]
    h23,h24=set(),set()
    k=0
    for ib,b in enumerate(("0-3","4-7","8-15","16+")):
        for im,half in enumerate(("Jan-Jun","Jul-Dec")):
            for ins,start_bin in enumerate(("1-4","5+")):
                for flag in (False,True):
                    for j in range(each):
                        horse=f"FICTIONAL:HORSE:{k}"
                        if flag: h24.add(horse)
                        if j < int(each*selected2023): h23.add(horse)
                        sire=f"FICTIONAL:SIRE:{k%151}"
                        nstarts=2 if start_bin=="1-4" else 5
                        gain=(.025 * (ib-1.5) + .010*im
                              + .014*ins + (-.030 if flag else .030)
                              if not base_on_opportunity
                              else .025*(ib-1.5)+.010*im+.014*ins)
                        for st in range(nstarts):
                            when=pd.Timestamp(
                                year=2022,month=4 if im==0 else 10,
                                day=1+((j*7+st+ib*3)%26))
                            # Distinct race identifiers, each horse×event
                            # signed normalized-MSE difference stays in [-1,1].
                            records.append({
                                "horse":horse,
                                "race":f"FICTIONAL:R:{k}:{st}",
                                "day":when,"sire_id":sire,"own_bin":b,
                                "gain":gain+(.006 if when.day%2 else -.006),
                            })
                        k+=1
    return pd.DataFrame(records),h23,h24


class OpportunityClusterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p,cls.ids23,cls.ids24=invented()

    def test_same_six_prespecified_specs_both_full_and_2023_scope(self):
        z=evaluate_opportunity(self.p,self.ids23,self.ids24,draws=50)
        self.assertEqual(z["status"],STATUS)
        self.assertEqual(z["2022_horses"],1600)
        self.assertEqual(z["2024_observed_horses"],800)
        self.assertEqual(len(z["results"]),6)
        for item in z["results"].values():
            self.assertEqual(item["status"],
                             "POSTHOC_ALL_2022_OPPORTUNITY_STANDARDIZED_ASSOCIATION")
            self.assertEqual(item["two_way_status"],
                             "POSTHOC_TWO_WAY_HORSE_DATE_LINEARIZED_CR0")
            self.assertLess(item["standardized_2022_MSE_gain_present_minus_absent"],0)
            self.assertEqual(item["sire_status"],
                             "POSTHOC_ENTIRE_RECORDED_SIRE_CLUSTER_RESAMPLING")
            self.assertTrue(item["year2022_target_mix_held_fixed_within_scope"])

    def test_bonferroni_six_spec_interval_wider_than_95pct(self):
        z=evaluate_opportunity(self.p,self.ids23,self.ids24,draws=40)
        q=z["results"]["all_2022__own_bin__last_2022_half"]
        ordinary=q["two_way_95pct_sensitivity_interval"]
        corrected=q["six_opportunity_specs_bonferroni_95pct_interval"]
        self.assertLess(corrected[0],ordinary[0])
        self.assertGreater(corrected[1],ordinary[1])
        self.assertTrue(z["six_preselected_opportunity_specifications_familywise_test"])

    def test_if_future_labels_no_additional_signal_standardized_gap_zero(self):
        p,a,b=invented(base_on_opportunity=True)
        z=evaluate_opportunity(p,a,b,draws=40)
        for x in z["results"].values():
            self.assertAlmostEqual(
                x["standardized_2022_MSE_gain_present_minus_absent"],0,places=10)

    def test_sparse_2023_subcohort_holds_without_imputing(self):
        p,ids23,ids24=invented(each=50, selected2023=.24)
        z=evaluate_opportunity(p,ids23,ids24,draws=35)
        self.assertTrue(z["results"]["observed_2023__own_bin__last_2022_half"][
            "status"].startswith("HOLD_"))
        self.assertNotIn("sire_95pct_percentile_sensitivity_interval",
                         z["results"]["observed_2023__own_bin__last_2022_half"])

    def test_real_cohort_count_gate_not_satisfied_by_fiction(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_LOCKED_2022_HORSE_START"):
            evaluate_opportunity(self.p,self.ids23,self.ids24,draws=35,source_lock=True)

    def test_incorrect_2022_event_date_rejected(self):
        p=self.p.copy()
        p.loc[0,"day"]=pd.Timestamp("2023-01-01")
        with self.assertRaisesRegex(ValueError,"BAD_DATE"):
            evaluate_opportunity(p,self.ids23,self.ids24,draws=35)

    def test_output_never_exports_private_horse_or_sire_id(self):
        z=evaluate_opportunity(self.p,self.ids23,self.ids24,draws=35)
        txt=str(z)
        self.assertNotIn("FICTIONAL:HORSE:",txt)
        self.assertNotIn("FICTIONAL:SIRE:",txt)
        self.assertNotIn("FICTIONAL:R:",txt)
        self.assertTrue(z["no_sire_horse_race_day_individual_predictions_or_residuals_exported"])

    def test_no_fabricated_genetic_causation_or_race_known_on(self):
        z=evaluate_opportunity(self.p,self.ids23,self.ids24,draws=35)
        self.assertTrue(z["year_2022_last_record_and_2022_starts_not_known_on_earlier_races"])
        self.assertTrue(z["year_2024_record_absence_not_retirement_death_or_breeding_fitness"])
        self.assertTrue(z["original_MG_selected_on_2022_outcomes_and_all_results_posthoc"])


if __name__=="__main__":
    unittest.main()
