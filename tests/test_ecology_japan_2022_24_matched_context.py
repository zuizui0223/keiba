"""Only invented horse IDs and synthetic signed MSE differences."""
import sys
import unittest
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_japan_2022_24_matched_context import matched_context_audit, STATUS


def invented(yr, count=50, contexts=("turf:3", "dirt:4"), starts=(1,1),
             values=(.2,.6), prefix="SYN"):
    rows=[]
    for h in range(count):
        for j, context in enumerate(contexts):
            for s in range(starts[j]):
                rows.append({
                    "horse":f"{prefix}:{h}", "race":f"SYN:{yr}:{h}:{j}:{s}",
                    "day":pd.Timestamp(f"{yr}-01-01")+pd.Timedelta(days=h%31),
                    "stratum":context, "gain":values[j]
                })
    return pd.DataFrame(rows)


class MatchedContextTests(unittest.TestCase):
    def test_all_contexts_constant_gain_no_fake_year_drift(self):
        r=matched_context_audit(invented(2022),invented(2024))
        self.assertEqual(r["status"],STATUS)
        self.assertEqual(r["matched_horses_with_at_least_one_common_context"],50)
        self.assertEqual(r["horse_context_pairs_observed_both_years"],100)
        self.assertAlmostEqual(r["paired_same_horse_same_context_2022_mix_standardized_year_change"],0)
        self.assertAlmostEqual(r["common_context_native_mix_year_change"],0)
        self.assertTrue(r["native_mix_decomposition_exact"])

    def test_context_composition_can_create_apparent_drift_without_within_change(self):
        r=matched_context_audit(invented(2022),invented(2024,starts=(3,1)))
        self.assertAlmostEqual(r["paired_same_horse_same_context_2022_mix_standardized_year_change"],0)
        self.assertAlmostEqual(r["2022_reference_within_horse_context_mix_component"],-.1)
        self.assertAlmostEqual(r["within_common_context_component_at_2024_mix"],0)
        self.assertAlmostEqual(r["common_context_native_mix_year_change"],-.1)

    def test_within_context_change_separated_from_composition(self):
        r=matched_context_audit(invented(2022),invented(2024,values=(.1,.5)))
        self.assertAlmostEqual(r["paired_same_horse_same_context_2022_mix_standardized_year_change"],-.1)
        self.assertAlmostEqual(r["2022_reference_within_horse_context_mix_component"],0)
        self.assertAlmostEqual(r["within_common_context_component_at_2024_mix"],-.1)
        self.assertLess(max(r["paired_horse_oneway_399_resampling_95pct"]),0)

    def test_non_overlapping_strata_hold_and_never_invent_pairs(self):
        a=invented(2022,contexts=("turf:3",),starts=(1,),values=(.1,))
        b=invented(2024,contexts=("dirt:3",),starts=(1,),values=(.2,))
        r=matched_context_audit(a,b)
        self.assertTrue(r["status"].startswith("HOLD"))
        self.assertEqual(r["same_candidate_horses_both_years_all_contexts"],50)
        self.assertEqual(r["matched_horses_with_at_least_one_common_context"],0)
        self.assertNotIn("paired_same_horse_same_context_2022_mix_standardized_year_change",r)

    def test_observed_selection_and_unmatched_horses_not_denominator_confused(self):
        r=matched_context_audit(invented(2022),invented(2024,prefix="ANOTHER"))
        self.assertEqual(r["same_candidate_horses_both_years_all_contexts"],0)
        self.assertEqual(r["matched_horses_with_at_least_one_common_context"],0)
        self.assertTrue(r["status"].startswith("HOLD"))

    def test_repeated_same_horse_race_is_rejected(self):
        a=invented(2022)
        a=pd.concat([a,a.iloc[[0]]],ignore_index=True)
        with self.assertRaisesRegex(ValueError,"DUPLICATED_HORSE_RACE"):
            matched_context_audit(a,invented(2024))

    def test_bad_signed_gain_and_missing_date_are_fail_closed(self):
        a=invented(2022); b=invented(2024)
        a.loc[0,"gain"]=float("nan")
        with self.assertRaisesRegex(ValueError,"NONFINITE"):
            matched_context_audit(a,b)
        a.loc[0,"gain"]=1.4
        with self.assertRaisesRegex(ValueError,"OUT_OF_RANGE"):
            matched_context_audit(a,b)
        a.loc[0,"gain"]=0.4
        a.loc[0,"day"]=pd.NaT
        with self.assertRaisesRegex(ValueError,"NONFINITE"):
            matched_context_audit(a,b)

    def test_public_aggregate_has_no_private_observation_ids(self):
        r=matched_context_audit(invented(2022),invented(2024))
        txt=str(r)
        self.assertNotIn("SYN:0",txt)
        self.assertNotIn("SYN:2024",txt)
        self.assertTrue(r["no_individual_horse_ID_race_ID_day_or_gain_exported"])
        self.assertTrue(r["same_coarse_context_NOT_same_rivals_jockey_trainer_going_or_age"])
        self.assertTrue(r["cohort_selected_using_future_year_and_context_overlap"])


if __name__=="__main__":
    unittest.main()
