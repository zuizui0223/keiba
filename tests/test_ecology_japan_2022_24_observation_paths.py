"""Synthetic-only tests of 2023/2024 source-record paths and opportunity bias."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2022_24_observation_paths import (
    analyze_paths, _opportunity_standardization, EXPECTED_STATES, STATUS
)


def invented(means=(.03,.01,-.01,-.02), counts=(160,180,40,260),
             *, same_signal=False, single_2022_start=False):
    """Every individual appears in 2022; all later states are recorded flags."""
    names=("neither","2023_only","2024_only","both")
    rows=[];ids23=set();ids24=set()
    start_id=0
    for state, count, mean in zip(names,counts,means):
        for k in range(count):
            i = start_id+k
            horse=f"FICT:H:{i}"
            if state in ("2023_only","both"):
                ids23.add(horse)
            if state in ("2024_only","both"):
                ids24.add(horse)
            month=1+(i%12)
            start_count=1 if single_2022_start else (2 if i%3 else 6)
            for start in range(start_count):
                when=pd.Timestamp(year=2022, month=month,
                                  day=1+((i//12+start)%26))
                rows.append({
                    "horse":horse, "race":f"FICT:R:{i}:{start}",
                    "day":when,"gain":(.05 if same_signal else mean),
                    "own_bin":("0-3","4-7","8-15","16+")[i%4],
                    "sire_id":f"FICT:SIRE:{i%97}",
                })
        start_id+=count
    return pd.DataFrame(rows),ids23,ids24


class ObservationPathTests(unittest.TestCase):
    def test_all_four_observation_paths_and_exact_marginal_decomposition(self):
        p,a,b=invented()
        q=analyze_paths(p,a,b,sire_draws=35)
        self.assertEqual(q["status"],STATUS)
        self.assertEqual(q["same_source_2022_horses"],640)
        self.assertEqual(q["observed_2023_count"],440)
        self.assertEqual(q["observed_2024_count"],300)
        counts={name:row["2022_horses"]
                for name,row in q["four_source_record_paths"].items()}
        self.assertEqual(counts,dict(zip(
            ("neither_2023_nor_2024","2023_only","2024_only","both_2023_and_2024"),
            (160,180,40,260))))
        self.assertAlmostEqual(
            q["2024_gap_ref_2023_status_composition_MSE_component"]+
            q["2024_gap_within_2023_status_MSE_component"],q["2024_gap"],places=12)
        self.assertEqual(
            q["year_2024_observation_conditioned_on_2023_record"]["2022_horses"],440)
        self.assertEqual(q["year_2024_observation_conditioned_on_2023_record"][
            "with_2024_observed_record"],260)
        self.assertLess(q["2024_gap"],0)

    def test_future_observation_labels_cannot_create_gap_if_2022_losses_identical(self):
        p,a,b=invented(same_signal=True)
        q=analyze_paths(p,a,b,sire_draws=35)
        self.assertAlmostEqual(q["2024_gap"],0,places=12)
        self.assertAlmostEqual(q["2024_gap_within_2023_status_MSE_component"],0,places=12)

    def test_history_2022_observation_timing_and_2022_start_volume_have_guards(self):
        p,a,b=invented()
        q=analyze_paths(p,a,b,sire_draws=35)
        v=q["2022_observation_opportunity_sensitivity"]
        self.assertEqual(len(v),6)
        self.assertTrue(all(z["status"].startswith(("HOLD_","POSTHOC_"))
                            for z in v.values()))
        self.assertTrue(all(z["2022_last_record_and_2022_number_of_starts_are_post_event_observation_proxies"]
                            for z in v.values()))
        self.assertTrue(all(z["target_standardization_to_all_2022_horses_in_this_scope"]
                            for z in v.values()))
        self.assertTrue(q["not_causal_survival_retirement_aging_or_breeding_selection"])

    def test_missing_2022_opportunity_support_holds_instead_of_imputation(self):
        p,a,b=invented(single_2022_start=True)
        q=analyze_paths(p,a,b,sire_draws=35)
        z=q["2022_observation_opportunity_sensitivity"]["all_2022__own_bin__recorded_2022_starts_bin"]
        self.assertEqual(z["planned_nonempty_strata"],4)
        self.assertTrue(z["status"].startswith(("HOLD_","POSTHOC_")))
        self.assertNotIn("genetic_selection_fitness",str(q))

    def test_broader_valid_source_can_contain_2024_races_excluded_by_strict_gate(self):
        p,a,b=invented()
        extra={f"FICT:H:{i}" for i in range(160,170)}
        q=analyze_paths(p,a,b,sire_draws=35,
                        all_valid_2024_source_ids=b|extra)
        z=q["broader_valid_source_vs_strict_2024_record_coverage"]
        groups=z["three_record_coverage_groups"]
        self.assertEqual(groups["strict_2024"]["2022_horses"],300)
        self.assertEqual(groups["2024_valid_joined_source_but_not_strict"]["2022_horses"],10)
        self.assertEqual(groups["no_valid_joined_2024_outcome_in_broader_source"]["2022_horses"],330)
        self.assertTrue(z["absence_of_valid_record_does_not_certify_no_raw_race_or_retirement"])

    def test_broader_source_coverage_must_include_all_strict_source_records(self):
        p,a,b=invented()
        with self.assertRaisesRegex(ValueError,"STRICT_2024_IDS_NOT_IN_BROADER_VALID_SOURCE"):
            analyze_paths(p,a,b,sire_draws=35,all_valid_2024_source_ids=set())

    def test_source_lock_rejects_wrong_four_path_membership(self):
        p,a,b=invented()
        with self.assertRaisesRegex(ValueError,"MEMBERSHIP_CHANGED"):
            analyze_paths(p,a,b,expected_states=EXPECTED_STATES,sire_draws=35)

    def test_illegal_inconsistent_race_day_and_outcome_date_fail_closed(self):
        p,a,b=invented()
        p.loc[0,"day"]=pd.Timestamp("2023-01-01")
        with self.assertRaisesRegex(ValueError,"BAD_DATE"):
            analyze_paths(p,a,b,sire_draws=35)

    def test_neither_false_survival_nor_individual_sire_id_export(self):
        p,a,b=invented()
        q=analyze_paths(p,a,b,sire_draws=35)
        s=str(q)
        self.assertNotIn("FICT:H:",s)
        self.assertNotIn("FICT:R:",s)
        self.assertNotIn("FICT:SIRE:",s)
        self.assertTrue(q["no_private_horse_parent_race_day_or_model_prediction_rows_exported"])
        self.assertTrue(q["year_2023_source_record_not_survival_or_studbook_status"])


if __name__=="__main__":
    unittest.main()
