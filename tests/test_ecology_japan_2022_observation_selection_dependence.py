"""Fictional horses only: selection, historical standardization and dependence guards."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_japan_2022_observation_selection_dependence import (
    selection_dependency_audit, STATUS
)


def fiction(n=240, *, group_style="balanced", same_within=False,
            add_day_shock=True, missing_sires=False):
    rows = []
    observed = set()
    for h in range(n):
        b = h % 4
        block = h // 4
        if group_style == "balanced":
            later = (block % 2 == 0)
        elif group_style == "composition":
            later = (block % 5 < (4 if b >= 2 else 1))
        elif group_style == "none":
            later = False
        else:
            raise ValueError("invalid invented group choice")
        horse = f"FICTION:H:{h}"
        if later:
            observed.add(horse)
        for start in range(2):
            day = (h % 25) + 1 + start
            base = (.08 + .04*b
                    + .007 * ((h // 8) % 3 - 1))
            if not same_within:
                base += -.20 if later else 0.0
            if add_day_shock:
                base += .02 if day % 2 == 0 else -.02
            rows.append({
                "horse": horse,
                "race": f"FICTION:R:{h}:{start}",
                "day": pd.Timestamp("2022-03-01") + pd.Timedelta(days=day),
                "own_bin": ("0-3", "4-7", "8-15", "16+")[b],
                "sire_id": "" if missing_sires and h%11==0 else f"FICTION:SIRE:{h//4}",
                "gain": base,
            })
    return pd.DataFrame(rows), observed


class SelectionDependenceTests(unittest.TestCase):
    def test_existing_unadjusted_and_new_standardized_have_same_direction(self):
        p, later = fiction()
        r = selection_dependency_audit(p, later, sire_draws=199)
        self.assertEqual(r["status"], STATUS)
        self.assertEqual(r["2022_horses"], 240)
        self.assertEqual(r["2022_starts"], 480)
        self.assertEqual(r["with_2024_observed_record"],120)
        self.assertAlmostEqual(r["unadjusted_future_observed_minus_unobserved"], -.20, delta=.025)
        self.assertAlmostEqual(r["2022_historical_own_count_bin_standardized_gap"], -.20, delta=.025)
        self.assertTrue(r["composition_plus_within_equals_unadjusted_exact"])
        self.assertEqual(r["unadjusted_horse_by_2022_day"]["two_way_status"],
                         "POSTHOC_HORSE_BY_CALENDAR_DAY_CR0_SENSITIVITY")
        self.assertEqual(r["recorded_sire_group_resampling"]["recorded_sire_plus_missing_singleton_clusters"],60)

    def test_history_bin_composition_able_to_create_unadjusted_gap(self):
        p, later = fiction(n=600, group_style="composition",same_within=True,add_day_shock=False)
        r = selection_dependency_audit(p,later,sire_draws=99,min_group=10)
        self.assertGreater(abs(r["unadjusted_future_observed_minus_unobserved"]),.015)
        self.assertAlmostEqual(r["2022_historical_own_count_bin_standardized_gap"],0,delta=.004)
        self.assertAlmostEqual(r["four_2021_history_bin_composition_component"],
                               r["unadjusted_future_observed_minus_unobserved"],delta=.004)
        self.assertAlmostEqual(r["within_2021_history_bin_component_at_future_observed_shares"],0,delta=.004)

    def test_two_way_handles_common_calendar_day_correlation(self):
        p,later=fiction(add_day_shock=True)
        r=selection_dependency_audit(p,later,sire_draws=60)
        a=r["unadjusted_horse_by_2022_day"]
        self.assertTrue(a["calendar_day_clusters"]>=25)
        self.assertTrue(a["horse_day_intersections"]>a["horse_clusters"])
        self.assertGreater(a["two_way_CR0_se"],0)
        self.assertLess(a["two_way_normal_95pct_sensitivity_interval"][0],
                        a["two_way_normal_95pct_sensitivity_interval"][1])
        self.assertGreater(
            a["bonferroni_two_estimands_simultaneous_95pct_interval"][1]-
            a["bonferroni_two_estimands_simultaneous_95pct_interval"][0],
            a["two_way_normal_95pct_sensitivity_interval"][1]-
            a["two_way_normal_95pct_sensitivity_interval"][0])

    def test_sire_cluster_whole_group_resampling_with_unknown_sire_singletons(self):
        p,later=fiction(missing_sires=True)
        r=selection_dependency_audit(p,later,sire_draws=100)
        s=r["recorded_sire_group_resampling"]
        self.assertEqual(s["missing_sire_horses_as_separate_singletons"],22)
        self.assertGreater(s["recorded_sire_plus_missing_singleton_clusters"],60)
        self.assertTrue(s["unstratified_whole_sire_clusters_resampled"])
        self.assertEqual(s["status"],"POSTHOC_SIRE_CLUSTER_SOURCE_A_NOT_GENETIC_CAUSATION")
        self.assertLess(s["unadjusted"]["percentile_95pct_sensitivity_interval"][1],0)

    def test_no_2024_observation_records_returns_hold(self):
        p,later=fiction(group_style="none")
        r=selection_dependency_audit(p,later,sire_draws=50)
        self.assertEqual(r["status"],"HOLD_FUTURE_OBSERVATION_GROUP_SUPPORT")
        self.assertEqual(r["with_2024_observed_record"],0)

    def test_date_not_in_2022_is_rejected(self):
        p,later=fiction()
        p.loc[0,"day"]=pd.Timestamp("2024-01-01")
        with self.assertRaisesRegex(ValueError,"BAD_DATE"):
            selection_dependency_audit(p,later,sire_draws=50)

    def test_conflicting_sire_is_rejected(self):
        p,later=fiction()
        p.loc[0,"sire_id"]="WRONG"
        with self.assertRaisesRegex(ValueError,"SIRE_ID_CONFLICT"):
            selection_dependency_audit(p,later,sire_draws=50)

    def test_same_horse_has_only_one_original_2021_history_bin(self):
        p,later=fiction()
        p.loc[0,"own_bin"]="16+"
        with self.assertRaisesRegex(ValueError,"HISTORICAL_BIN_CONFLICT"):
            selection_dependency_audit(p,later,sire_draws=50)

    def test_duplicate_horse_race_rejected(self):
        p,later=fiction()
        p=pd.concat([p,p.iloc[[0]]],ignore_index=True)
        with self.assertRaisesRegex(ValueError,"DUPLICATED_HORSE_RACE"):
            selection_dependency_audit(p,later,sire_draws=50)

    def test_same_source_race_multiple_date_rejected(self):
        p,later=fiction()
        p.loc[2,"race"]=p.loc[0,"race"]
        with self.assertRaisesRegex(ValueError,"RACE_MULTIPLE_DAYS"):
            selection_dependency_audit(p,later,sire_draws=50)

    def test_source_anchored_expected_result_drift_rejected(self):
        p,later=fiction()
        exp = {
            "n2022": 240, "present2024":120, "absent2024":120,
            "mean_all":0,"mean_present":0,"mean_absent":0,
            "contrast":0,"composition":0,"within":0,
        }
        with self.assertRaisesRegex(ValueError,"PREVIOUS_SOURCE_LOCKED_SELECTION_RESULT_DRIFT"):
            selection_dependency_audit(p,later,expected=exp,sire_draws=50)

    def test_missing_one_bin_outcome_group_returns_hold(self):
        p,later=fiction()
        later={h for h in later if int(h.split(":")[-1])%4!=0}
        r=selection_dependency_audit(p,later,sire_draws=50)
        self.assertEqual(r["status"],"HOLD_MISSING_ONE_OF_FOUR_HISTORICAL_BINS")

    def test_no_private_individual_identifier_in_aggregates(self):
        p,later=fiction()
        r=selection_dependency_audit(p,later,sire_draws=50)
        txt=str(r)
        self.assertNotIn("FICTION:H:",txt)
        self.assertNotIn("FICTION:R:",txt)
        self.assertNotIn("FICTION:SIRE:",txt)
        self.assertTrue(r["no_private_individual_horse_race_sire_date_or_prediction_rows_exported"])
        self.assertTrue(r["not_retirement_mortality_breeding_fitness_or_genetic_selection"])


if __name__ == "__main__":
    unittest.main()
