"""Invented horses only: model-switch exposure and conditional gain arithmetic."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_japan_2022_gate_exposure_selection import (
    audit_switches, STATUS,
)


def make_case(n=240, *, gate_mode="split", all_model_predictions_equal=False):
    rows=[]
    m1=[]
    m2=[]
    y=[]
    family=[]
    yr23=set()
    yr24=set()
    for h in range(n):
        horse=f"FICTIONAL:H:{h}"
        later=(h//4)%2==0
        if later: yr24.add(horse)
        if (h//8)%3 != 0: yr23.add(horse)
        for k in range(2):
            day=pd.Timestamp("2022-01-01")+pd.Timedelta(days=h%48+k)
            rows.append({
                "horse":horse,"race":f"FICTIONAL:R:{h}:{k}",
                "day":day,"gain":0.0,
                "own_bin":("0-3","4-7","8-15","16+")[h%4],
                "sire_id":f"FICTIONAL:SIRE:{h//4}"
            })
            y.append(.5)
            m2.append(.55)
            m1.append(.55 if all_model_predictions_equal else
                      (.48 if later else .58))
            if gate_mode=="all_family":choose=True
            elif gate_mode=="all_own":choose=False
            elif gate_mode=="split":
                # more M1 exposure in future-observed horses, but both groups
                # have at least one active switch.
                choose=(k==1 and not later)
            else: raise ValueError("bad invented mode")
            family.append(choose)
    return (pd.DataFrame(rows),yr23,yr24,np.array(family,bool),
            np.array(m1),np.array(m2),np.array(y))


def evaluate(data, **kwargs):
    panel, h23, h24, family, m1, m2, y = data
    return audit_switches(
        panel,h23,h24,
        chosen_family=family,frozen_m1=m1,frozen_m2=m2,y=y,
        draws=49,source_lock=False,benchmark=False,**kwargs
    )


class ModelSwitchExposureTests(unittest.TestCase):
    def test_exact_composition_and_within_gain_components_for_both_scopes(self):
        z=evaluate(make_case())
        self.assertEqual(z["status"],STATUS)
        self.assertEqual(z["source_population_2022_horses"],240)
        self.assertEqual(z["source_population_2022_starts"],480)
        self.assertEqual(set(z["reported_scopes"]),{"all_2022","2023_recorded_2022"})
        for v in z["reported_scopes"].values():
            self.assertEqual(v["status"],STATUS)
            self.assertTrue(v["exposure_plus_conditional_exactly_equals_original_MG_gap"])
            self.assertAlmostEqual(
                v["exposure_composition_component_at_not_recorded_conditional_gain"]+
                v["within_active_switch_gain_component_at_recorded_activation_share"],
                v["MG_minus_M2_2024_recorded_vs_unrecorded_gap"],places=12
            )
            self.assertGreater(v["M1_activation_rate_group_difference"],0)
            self.assertEqual(v["sire_bootstrap_status"],
                             "POSTHOC_WHOLE_RECORDED_SIRE_CLUSTER_SENSITIVITY")
            self.assertEqual(v["sire_resamples_requested"],49)
            self.assertIn("frozen_M1_vs_M2_all_starts_gap",
                          v["sire_cluster_999_draw_95pct_sensitivity"])

    def test_gate_exposure_standardized_on_pre2022_horse_history(self):
        z=evaluate(make_case())
        a=z["reported_scopes"]["all_2022"]["pre2022_own_history_bin_exposure_adjustment"]
        self.assertEqual(a["status"],
                         "POSTHOC_PRE2022_HISTORY_BIN_COMPOSITION_AND_WITHIN_EXPOSURE")
        self.assertAlmostEqual(
            a["pre2022_own_bin_composition_component"]+
            a["within_pre2022_own_bin_M1_selection_component"],
            z["reported_scopes"]["all_2022"]["M1_activation_rate_group_difference"],
            places=12)
        self.assertAlmostEqual(a["pre2022_own_bin_composition_component"],0,places=12)
        self.assertAlmostEqual(
            a["M1_selection_gap_standardized_to_all_pre2022_own_bin_mix"],.5,places=12)
        self.assertEqual(a["sire_bootstrap_status"],
            "POSTHOC_WHOLE_SIRE_CLUSTER_HISTORY_ADJUSTED_EXPOSURE_SENSITIVITY")
        self.assertIn("fixed_all_2022_ownbin_standardized_M1_selection_gap",
                      a["sire_bootstrap_95pct"])

    def test_sparse_pre2022_history_cell_holds_instead_of_zero_imputation(self):
        p,a,b,g,m1,m2,y=make_case()
        b={horse for horse in b if int(horse.split(":")[-1])%4!=0}
        z=audit_switches(p,a,b,chosen_family=g,frozen_m1=m1,frozen_m2=m2,
                         y=y,draws=49,benchmark=False)
        q=z["reported_scopes"]["all_2022"]["pre2022_own_history_bin_exposure_adjustment"]
        self.assertEqual(q["status"],"HOLD_SPARSE_PRE2022_HISTORY_BIN_EXPOSURE")
        self.assertIn("0-3",q["unsupported_bins"])
        self.assertNotIn("M1_selection_gap_standardized_to_all_pre2022_own_bin_mix",q)

    def test_2022_chosen_family_everywhere_holds_without_fabricating_active_gain(self):
        z=evaluate(make_case(gate_mode="all_family"))
        for v in z["reported_scopes"].values():
            self.assertEqual(v["status"],"HOLD_INFORMATION_SWITCH_EXPOSURE_ZERO_IN_GROUP")
            self.assertNotIn("within_active_switch_gain_component_at_recorded_activation_share",v)
            self.assertEqual(v["2024_recorded"]["horse_equal_MG_over_M2_MSE_gain"],0)

    def test_all_own_switch_recovers_raw_frozen_model_comparison(self):
        z=evaluate(make_case(gate_mode="all_own"))
        for v in z["reported_scopes"].values():
            self.assertAlmostEqual(v["M1_activation_rate_group_difference"],0)
            self.assertAlmostEqual(
                v["MG_minus_M2_2024_recorded_vs_unrecorded_gap"],
                v["frozen_M1_minus_M2_full_2022_recorded_vs_unrecorded_gap"]
            )
            self.assertAlmostEqual(
                v["exposure_composition_component_at_not_recorded_conditional_gain"],0)

    def test_identical_frozen_models_force_zero_mse_difference(self):
        z=evaluate(make_case(all_model_predictions_equal=True))
        for v in z["reported_scopes"].values():
            self.assertAlmostEqual(v["MG_minus_M2_2024_recorded_vs_unrecorded_gap"],0)
            self.assertAlmostEqual(
                v["frozen_M1_minus_M2_full_2022_recorded_vs_unrecorded_gap"],0)

    def test_out_of_bounds_predictions_fail_closed(self):
        p,a,b,g,m1,m2,y=make_case()
        m1[0]=1.3
        with self.assertRaisesRegex(ValueError,"INVALID_NORMALIZED_PREDICTIONS"):
            audit_switches(p,a,b,chosen_family=g,frozen_m1=m1,
                           frozen_m2=m2,y=y,draws=49,benchmark=False)

    def test_wrong_row_vector_length_fails_closed(self):
        p,a,b,g,m1,m2,y=make_case()
        with self.assertRaisesRegex(ValueError,"VECTOR_LENGTHS"):
            audit_switches(p,a,b,chosen_family=g,frozen_m1=m1[:-1],
                           frozen_m2=m2,y=y,draws=49,benchmark=False)

    def test_real_source_count_gate_rejects_invented_population(self):
        p,a,b,g,m1,m2,y=make_case()
        with self.assertRaisesRegex(ValueError,"IDENTICAL_COHORT_LOCK"):
            audit_switches(p,a,b,chosen_family=g,frozen_m1=m1,
                           frozen_m2=m2,y=y,draws=49,source_lock=True,benchmark=False)

    def test_sire_support_is_guarded(self):
        z=evaluate(make_case(),min_sires=100)
        self.assertEqual(
            z["reported_scopes"]["all_2022"]["sire_bootstrap_status"],
            "HOLD_TOO_FEW_SIRE_CLUSTERS_OR_DRAWS"
        )

    def test_no_individual_identifiers_in_aggregate(self):
        z=evaluate(make_case())
        s=str(z)
        self.assertNotIn("FICTIONAL:H:",s)
        self.assertNotIn("FICTIONAL:SIRE:",s)
        self.assertNotIn("FICTIONAL:R:",s)
        self.assertTrue(z["no_individual_source_horse_sire_race_day_or_predictions_exported"])
        self.assertTrue(z["information_switch_identity_not_mechanism_of_biological_aging_or_genetic_selection"])


if __name__=="__main__":
    unittest.main()
