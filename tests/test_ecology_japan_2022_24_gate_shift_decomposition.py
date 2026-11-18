"""Fictional algebraic composition/within-bin decomposition, never real horse data."""
from __future__ import annotations
import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2022_24_gate_shift_decomposition import (
    OWN_NAMES, STATUS, EXPECTED_YEAR_SCORES, horse_equal_weights,
    by_own_info_bin, exact_oaxaca, shared_eligible_horse_coverage,
)


def rows(year:int, sizes=(40,40,40,40), *, shift=False):
    """Each invented individual has exactly 4 synthetic race observations."""
    tuples=[]
    p2=[]
    pg=[]
    groups=[]
    for group_i,size in enumerate(sizes):
        for h in range(size):
            for start in range(4):
                tuples.append({
                    "horse":f"SYN:{year}:{group_i}:{h}",
                    "race":f"SYN:R:{year}:{group_i}:{h}:{start}",
                    "day":pd.Timestamp(f"{year}-01-01")+pd.Timedelta(days=h%20),
                    "year":year,
                    "y":0.5,
                })
                # Different baseline advantages by own-coverage group.
                p2.append(0.55+group_i*.08)
                pg.append(.9 if shift and group_i==0 else .5)
                groups.append(OWN_NAMES[group_i])
    return pd.DataFrame(tuples),groups,np.array(p2),np.array(pg)


class GateShiftDecompositionTests(unittest.TestCase):
    def test_equal_horse_weights_sum_one_even_with_repeated_starts(self):
        w=horse_equal_weights(["H1","H1","H1","H2"])
        self.assertAlmostEqual(w.sum(),1.)
        self.assertAlmostEqual(w[:3].sum(),.5)
        self.assertAlmostEqual(w[3],.5)

    def test_twofold_decomposition_exact_with_only_composition_changed(self):
        base,labels,p2,pg=rows(2022)
        later,l2,p22,pg2=rows(2024,sizes=(80,40,40,40))
        a=by_own_info_bin(base,labels,p2,pg)
        b=by_own_info_bin(later,l2,p22,pg2)
        d=exact_oaxaca(a,b)
        self.assertEqual(d["status"],
            "EXACT_ALGEBRAIC_DESCRIPTIVE_STANDARDIZATION_NOT_CAUSAL")
        self.assertAlmostEqual(d["within_bin_prediction_effect_change_at_later_weights"],0,places=12)
        self.assertNotAlmostEqual(d["composition_change_using_2022_bin_effects"],0,places=7)
        self.assertAlmostEqual(
            d["MSE_advantage_change_from_2022"],
            d["composition_change_using_2022_bin_effects"],places=12)
        self.assertTrue(d["composition_plus_within_equals_total"])
        self.assertTrue(d["MSE_NOT_RMSE_additivity"])

    def test_twofold_decomposition_exact_with_only_conditional_change(self):
        base,labels,p2,pg=rows(2022)
        later,l2,p22,pg2=rows(2024,shift=True)
        a=by_own_info_bin(base,labels,p2,pg)
        b=by_own_info_bin(later,l2,p22,pg2)
        d=exact_oaxaca(a,b)
        self.assertAlmostEqual(d["composition_change_using_2022_bin_effects"],0,places=12)
        self.assertLess(d["within_bin_prediction_effect_change_at_later_weights"],0)
        self.assertAlmostEqual(
            d["MSE_advantage_change_from_2022"],
            d["within_bin_prediction_effect_change_at_later_weights"],places=12)

    def test_mixed_composition_conditional_change_sums_to_total(self):
        base,labels,p2,pg=rows(2022)
        later,l2,p22,pg2=rows(2024,sizes=(80,40,60,40),shift=True)
        a=by_own_info_bin(base,labels,p2,pg)
        b=by_own_info_bin(later,l2,p22,pg2)
        d=exact_oaxaca(a,b)
        self.assertAlmostEqual(
            d["MSE_advantage_change_from_2022"],
            d["composition_change_using_2022_bin_effects"]+
            d["within_bin_prediction_effect_change_at_later_weights"],
            places=12)
        self.assertNotAlmostEqual(
            d["composition_change_using_2022_bin_effects"],0,places=7)
        self.assertNotAlmostEqual(
            d["within_bin_prediction_effect_change_at_later_weights"],0,places=7)

    def test_sparse_own_bin_holds_not_fabricates_decomposition(self):
        base,labels,p2,pg=rows(2022)
        later,l2,p22,pg2=rows(2024,sizes=(5,40,40,40))
        a=by_own_info_bin(base,labels,p2,pg)
        b=by_own_info_bin(later,l2,p22,pg2)
        self.assertFalse(b["all_predeclared_bins_standardizable"])
        self.assertEqual(exact_oaxaca(a,b)["status"],
                         "HOLD_NO_FULL_OWN_BIN_OVERLAP_FOR_DECOMPOSITION")

    def test_unrecognized_own_bin_not_silent_negative_category(self):
        t,labels,p2,pg=rows(2022)
        labels[0]="official_first_start"
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_OWN_HISTORY_BIN"):
            by_own_info_bin(t,labels,p2,pg)

    def test_invalid_prediction_or_source_probability_rejected(self):
        t,labels,p2,pg=rows(2022)
        pg[0]=np.nan
        with self.assertRaisesRegex(ValueError,"NONFINITE"):
            by_own_info_bin(t,labels,p2,pg)
        pg[0]=1.2
        with self.assertRaisesRegex(ValueError,"NONFINITE_OR_OUT_OF_BOUNDS"):
            by_own_info_bin(t,labels,p2,pg)

    def test_observed_horse_participation_not_called_survival(self):
        t22,_,_,_=rows(2022)
        t23,_,_,_=rows(2023)
        t24,_,_,_=rows(2024)
        q=shared_eligible_horse_coverage(
            {"2022":t22,"2023":t23,"2024":t24})
        self.assertEqual(q["status"],
            "OBSERVED_COHORT_PARTICIPATION_OVERLAP_NOT_SURVIVAL_OR_BREEDING")
        self.assertEqual(q["pairs"]["2022_to_2024"]["same_candidate_horse_in_both_years"],0)

    def test_same_horse_paired_year_change_cannot_be_population_turnover_only(self):
        from ecology_japan_2022_24_gate_shift_decomposition import (
            matched_horse_risk_change
        )
        a,ba,m2a,ga=rows(2022)
        b,bb,m2b,gb=rows(2024,shift=True)
        # Force exact same fictional horse identities in both years.
        b["horse"]=b.horse.str.replace(":2024:",":2022:",regex=False)
        q=matched_horse_risk_change(
            {"t":a,"p2":m2a,"pg":ga,"ownbin":ba,"selected":np.ones(len(a),bool)},
            {"t":b,"p2":m2b,"pg":gb,"ownbin":bb,"selected":np.ones(len(b),bool)})
        self.assertEqual(q["matched_horses"],160)
        self.assertLess(q["same_horse_year_average_MSE_advantage_change"],0)
        self.assertLess(max(q["paired_horse_oneway_399_resampling_95pct"]),0)
        self.assertEqual(q["by_pre2022_focal_own_history_bin"]["16+"]["matched_horses"],40)
        self.assertTrue(q["observed_yearly_race_context_and_horse_age_not_held_fixed"])
        self.assertTrue(q["race_day_two_way_dependence_not_modeled"])

    def test_matched_horse_history_bin_changed_between_years_holds(self):
        from ecology_japan_2022_24_gate_shift_decomposition import (
            matched_horse_risk_change
        )
        a,ba,m2a,ga=rows(2022)
        b,bb,m2b,gb=rows(2024)
        b["horse"]=b.horse.str.replace(":2024:",":2022:",regex=False)
        bb[0]="16+"
        with self.assertRaisesRegex(ValueError,"BIN_CHANGED_WITHIN_HORSE"):
            matched_horse_risk_change(
                {"t":a,"p2":m2a,"pg":ga,"ownbin":ba,"selected":np.ones(len(a),bool)},
                {"t":b,"p2":m2b,"pg":gb,"ownbin":bb,"selected":np.ones(len(b),bool)})

    def test_historical_reference_scores_preserved_as_original_results(self):
        self.assertTrue(STATUS.startswith("POSTHOC_"))
        self.assertTrue(
            EXPECTED_YEAR_SCORES["2022"]["gate"]<
            EXPECTED_YEAR_SCORES["2022"]["M2"])
        self.assertTrue(
            EXPECTED_YEAR_SCORES["2024"]["gate"]>
            EXPECTED_YEAR_SCORES["2024"]["M2"])
        self.assertTrue(
            EXPECTED_YEAR_SCORES["2024"]["gate"]>
            EXPECTED_YEAR_SCORES["2024"]["M0"])


if __name__=="__main__":
    unittest.main()
