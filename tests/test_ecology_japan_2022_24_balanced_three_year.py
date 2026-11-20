"""Synthetic (fictional) three-year racehorse-context and observation tests."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2022_24_balanced_three_year import (
    balanced_three_year, continuation_selection_2022, STATUS
)


def made(year, n=80, *, strata=("turf:3","dirt:4"), reps=(1,1),
         gain=None, horses=None):
    if horses is None:
        horses=range(n)
    result=[]
    for i in horses:
        for j,stratum in enumerate(strata):
            for s in range(reps[j]):
                result.append({
                    "horse":f"FICTIONAL:H:{i}",
                    "race":f"FICTIONAL:R:{year}:{i}:{j}:{s}",
                    "day":pd.Timestamp(year=year,month=5,day=(i%20)+1),
                    "stratum":stratum,
                    "own_bin":("0-3","4-7","8-15","16+")[i%4],
                    "gain":float(gain(i,j) if callable(gain) else (gain if gain is not None else (.1+.2*j))),
                })
    return pd.DataFrame(result)


def panels():
    return {year:made(year) for year in (2022,2023,2024)}


class BalancedThreeYearTests(unittest.TestCase):
    def test_exact_three_year_telescoping_and_paired_horse_interval(self):
        p={
            2022:made(2022,gain=lambda h,j:.1+.1*j),
            2023:made(2023,gain=lambda h,j:.2+.1*j),
            2024:made(2024,gain=lambda h,j:.35+.1*j),
        }
        r=balanced_three_year(p)
        self.assertEqual(r["status"],STATUS)
        self.assertEqual(r["balanced_horses_same_context_all_three_years"],80)
        self.assertAlmostEqual(r["same_horse_context_year_difference"]["2022_to_2023"],.1)
        self.assertAlmostEqual(r["same_horse_context_year_difference"]["2023_to_2024"],.15)
        self.assertAlmostEqual(r["same_horse_context_year_difference"]["2022_to_2024"],.25)
        self.assertTrue(r["balanced_2022_to_2024_difference_equals_sum_of_two_steps"])
        self.assertGreater(min(r["paired_horse_399_resampling_95pct_sensitivity_intervals"]["2022_to_2024"]),0)

    def test_context_mix_changes_dont_imply_year_drift(self):
        p={2022:made(2022,reps=(1,3)),2023:made(2023,reps=(3,1)),
           2024:made(2024,reps=(1,1))}
        r=balanced_three_year(p)
        self.assertAlmostEqual(r["same_horse_context_year_difference"]["2022_to_2023"],0)
        self.assertAlmostEqual(r["same_horse_context_year_difference"]["2023_to_2024"],0)
        self.assertEqual(r["balanced_horse_context_cells"],160)

    def test_balanced_requires_identical_horses_all_three(self):
        p={2022:made(2022,horses=range(80)),2023:made(2023,horses=range(40,120)),
           2024:made(2024,horses=range(20,100))}
        r=balanced_three_year(p)
        self.assertEqual(r["balanced_horses_same_context_all_three_years"],40)
        self.assertEqual(r["horses_observed_2022_and_2024_any_context"],60)
        self.assertTrue(r["horses_only_selected_after_observing_all_three_years"])

    def test_same_horses_but_no_same_context_in_middle_year_hold(self):
        p={2022:made(2022,strata=("turf:3",),reps=(1,)),
           2023:made(2023,strata=("dirt:3",),reps=(1,)),
           2024:made(2024,strata=("turf:3",),reps=(1,))}
        r=balanced_three_year(p)
        self.assertEqual(r["status"],"HOLD_BALANCED_THREE_YEAR_COMMON_CONTEXT_SUPPORT")
        self.assertEqual(r["horses_observed_all_three_years_any_context"],80)
        self.assertEqual(r["balanced_horses_same_context_all_three_years"],0)
        self.assertNotIn("same_horse_context_year_difference",r)

    def test_non_monotonic_realizable_with_three_years(self):
        p={2022:made(2022,gain=.3),2023:made(2023,gain=.1),2024:made(2024,gain=.2)}
        r=balanced_three_year(p)
        self.assertAlmostEqual(r["same_horse_context_year_difference"]["2022_to_2023"],-.2)
        self.assertAlmostEqual(r["same_horse_context_year_difference"]["2023_to_2024"],.1)
        self.assertAlmostEqual(r["same_horse_context_year_difference"]["2022_to_2024"],-.1)
        self.assertAlmostEqual(r["within_horse_first_versus_second_year_difference_sign_reversals_fraction"],1.0)

    def test_future_observation_2022_selection_exact_history_decomposition(self):
        p={
            2022:made(2022,n=320,gain=lambda h,j:.2 if h%8<4 else -.1),
            2023:made(2023,n=320),
            2024:made(2024,horses=[i for i in range(320) if i%8<4])
        }
        r=continuation_selection_2022(p)
        self.assertEqual(r["2022_horses"],320)
        self.assertEqual(r["2022_horses_observed_again_in_2024"],160)
        self.assertAlmostEqual(r["2022_future_participation_selection_contrast_later_minus_not"],.3)
        self.assertTrue(r["composition_plus_within_exact"])
        self.assertAlmostEqual(r["2022_own_info_bin_composition_component"],0)
        self.assertAlmostEqual(r["within_2022_own_info_bin_participation_selection_component"],.3)
        self.assertGreater(min(r["horse_group_stratified_399_bootstrap_95pct"]),0)

    def test_own_history_mix_only_selection_can_mimic_information_bias(self):
        p={
            2022:made(2022,n=400,gain=lambda h,j:.1*(h%4)),
            2023:made(2023,n=400),
            2024:made(2024,horses=[i for i in range(400) if i%4 in (2,3)]),
        }
        r=continuation_selection_2022(p)
        self.assertAlmostEqual(r["2022_future_participation_selection_contrast_later_minus_not"],.2)
        self.assertEqual(r["2022_own_info_bin_full_standardization_status"],
                         "HOLD_SPARSE_OR_MISSING_2022_OWN_INFO_BIN")
        self.assertTrue(r["source_2024_records_missing_do_NOT_mean_dead_or_retired"])

    def test_future_none_observed_holds(self):
        p={2022:made(2022),2023:made(2023),
           2024:made(2024,horses=range(100,180))}
        r=continuation_selection_2022(p)
        self.assertTrue(r["status"].startswith("HOLD_"))
        self.assertEqual(r["2022_horses_observed_again_in_2024"],0)

    def test_missing_history_bin_and_invalid_year_raise(self):
        p=panels()
        p[2023].loc[0,"own_bin"]="not-an-official-maiden"
        with self.assertRaisesRegex(ValueError,"UNKNOWN_FROZEN_OWN_HISTORY_BIN"):
            balanced_three_year(p)
        p=panels()
        p[2023].loc[0,"day"]=pd.Timestamp("2024-05-01")
        with self.assertRaisesRegex(ValueError,"INCORRECT_SOURCE_OUTCOME_YEAR"):
            balanced_three_year(p)

    def test_inconsistent_pre2022_history_and_duplicate_horse_race_raise(self):
        p=panels()
        p[2024].loc[0,"own_bin"]="16+" if p[2024].loc[0,"own_bin"]!="16+" else "0-3"
        with self.assertRaisesRegex(ValueError,"BIN_NOT_STABLE_WITHIN_YEAR"):
            balanced_three_year(p)
        p=panels()
        p[2024]=pd.concat([p[2024],p[2024].iloc[[0]]],ignore_index=True)
        with self.assertRaisesRegex(ValueError,"DUPLICATED_HORSE_RACE"):
            balanced_three_year(p)

    def test_aggregate_privacy_no_individual_IDs(self):
        p=panels()
        r=balanced_three_year(p)
        s=continuation_selection_2022(p)
        self.assertNotIn("FICTIONAL:",str(r))
        self.assertNotIn("FICTIONAL:",str(s))
        self.assertTrue(r["source_horse_race_or_individual_gain_values_never_exported"])
        self.assertTrue(s["no_source_horse_IDs_individual_predictions_or_rows_exported"])


if __name__ == "__main__":
    unittest.main()
