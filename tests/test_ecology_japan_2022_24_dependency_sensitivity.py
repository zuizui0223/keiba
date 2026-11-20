"""Fictional only: dependency, multiplicity, date and sire-identity guards."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_japan_2022_24_dependency_sensitivity import (
    dependency_audit, STATUS, _cluster_variance, MULTIPLICITY_CRITICAL_Z
)


def toy(n=120, *, day_pattern=False, parent_pattern=False, missing=False):
    out={}
    for y in (2022,2023,2024):
        rows=[]
        for h in range(n):
            dad=f"FICTIONAL:SIRE:{h//2}"
            if missing and h%11==0:
                dad=""
            for stratum in ("turf:3","dirt:4"):
                for start in range(2):
                    day_idx = h % 40
                    parity = 1.0 if (day_idx%2) else -1.0
                    dayshock = 0.06*parity if day_pattern else 0.
                    sire = 0.07*(1 if (h//2)%2 else -1) if parent_pattern else 0.
                    score = (.10 if y==2022 else
                             .11 if y==2023 else .12+dayshock+sire)
                    rows.append({
                        "horse":f"FICTIONAL:HORSE:{h}",
                        "race":f"FICTIONAL:R:{y}:{day_idx}:{stratum}:{start}:{h}",
                        "day":pd.Timestamp(year=y, month=4, day=1)+pd.Timedelta(days=day_idx),
                        "stratum":stratum,
                        "gain":score,
                        "own_bin":("0-3","4-7","8-15","16+")[h%4],
                        "sire_id":dad,
                    })
        out[y]=pd.DataFrame(rows)
    return out


class DependenceTests(unittest.TestCase):
    def test_matched_fixed_cohort_and_telescoping(self):
        r=dependency_audit(toy(),draws=100)
        self.assertEqual(r["status"],STATUS)
        self.assertEqual(r["balanced_horses"],120)
        self.assertEqual(r["balanced_context_cells"],240)
        self.assertEqual(r["race_starts_by_year"],{"2022":480,"2023":480,"2024":480})
        self.assertAlmostEqual(r["results"]["2022_to_2023"]["point_change_MSE_MG_vs_M2"],.01)
        self.assertAlmostEqual(r["results"]["2023_to_2024"]["point_change_MSE_MG_vs_M2"],.01)
        self.assertAlmostEqual(r["results"]["2022_to_2024"]["point_change_MSE_MG_vs_M2"],.02)
        self.assertTrue(r["full_three_year_old_differences_preserved"])

    def test_no_fabricated_two_way_interval_for_zero_variance(self):
        r=dependency_audit(toy(),draws=100)
        v=r["results"]["2023_to_2024"]
        self.assertEqual(v["two_way_status"],"HOLD_NONPOSITIVE_TWO_WAY_SANDWICH_VARIANCE")
        self.assertNotIn("two_way_normal_95pct_sensitivity_interval",v)
        self.assertAlmostEqual(v["horse_CR0_se"],0,places=12)

    def test_calendar_date_shock_changes_dependence_uncertainty(self):
        r=dependency_audit(toy(day_pattern=True),draws=100)
        v=r["results"]["2023_to_2024"]
        self.assertEqual(v["matched_calendar_days"],80)
        self.assertEqual(v["matched_horses"],120)
        self.assertEqual(v["two_way_status"],"POSTHOC_TWO_WAY_HORSE_AND_CALENDAR_DAY_SANDWICH")
        self.assertGreater(v["two_way_horse_date_CR0_se"],0)
        self.assertGreater(v["two_way_horse_date_CR0_se"],v["horse_CR0_se"])
        lo,hi=v["bonferroni_3contrasts_normal_familywise_95pct_interval"]
        self.assertLess(lo,hi)
        self.assertGreater(MULTIPLICITY_CRITICAL_Z,2.3)

    def test_sire_cluster_resamples_whole_paternal_groups(self):
        r=dependency_audit(toy(parent_pattern=True),draws=199)
        v=r["results"]["2023_to_2024"]
        self.assertEqual(v["sire_clusters_recorded_plus_unresolved_singletons"],60)
        self.assertEqual(v["unresolved_sire_horses_as_individual_singletons"],0)
        self.assertEqual(v["largest_observed_paternal_group_horses"],2)
        self.assertEqual(v["sire_cluster_bootstrap_status"],
                         "POSTHOC_RECORDED_SIRE_CLUSTER_WITH_UNKNOWN_SINGLETONS")
        self.assertGreater(v["sire_cluster_95pct_percentile_sensitivity_interval"][1],
                           v["sire_cluster_95pct_percentile_sensitivity_interval"][0])

    def test_unknown_sire_does_not_group_unrelated_horses(self):
        r=dependency_audit(toy(missing=True),draws=50)
        v=r["results"]["2023_to_2024"]
        self.assertEqual(v["unresolved_sire_horses_as_individual_singletons"],11)
        self.assertGreater(v["sire_clusters_recorded_plus_unresolved_singletons"],60)

    def test_absent_sire_source_holds(self):
        p=toy()
        p[2023]=p[2023].drop(columns="sire_id")
        with self.assertRaisesRegex(ValueError,"SIRE_SOURCE_A_PARENT_ID_ABSENT"):
            dependency_audit(p,draws=50)

    def test_sire_identity_conflict_cross_year_holds(self):
        p=toy()
        p[2024].loc[p[2024].horse.eq("FICTIONAL:HORSE:1"),"sire_id"]="WRONG"
        with self.assertRaisesRegex(ValueError,"SIRE_CHANGED_WITHIN_HORSE"):
            dependency_audit(p,draws=50)

    def test_date_cluster_count_fail_closed(self):
        p=toy()
        for y in p:
            p[y]["day"]=pd.Timestamp(year=y,month=5,day=1)
        r=dependency_audit(p,draws=50)
        self.assertEqual(r["results"]["2023_to_2024"]["two_way_status"],
                         "HOLD_TOO_FEW_DEPENDENCE_CLUSTERS")

    def test_invalid_cross_race_day_date_holds(self):
        p=toy()
        p[2024].loc[[0,4],"race"]="FICTIONAL:DUPLICATE:RACE"
        p[2024].loc[0,"day"]=pd.Timestamp("2024-04-05")
        p[2024].loc[4,"day"]=pd.Timestamp("2024-04-07")
        with self.assertRaisesRegex(ValueError,"RACE_MULTIPLE_CALENDAR_DAYS"):
            dependency_audit(p,draws=50)

    def test_contrast_has_no_private_source_ids_or_deltas(self):
        r=dependency_audit(toy(),draws=50)
        self.assertNotIn("FICTIONAL:HORSE:",str(r))
        self.assertNotIn("FICTIONAL:SIRE:",str(r))
        self.assertTrue(r["no_sire_horse_day_race_or_individual_effects_exported"])
        self.assertTrue(r["three_previously_examined_contrasts_bonferroni_corrected"])

    def test_inclusion_exclusion_group_sums(self):
        a=pd.DataFrame({
            "horse":["a","a","b","b"],
            "day":pd.to_datetime(["2023-01-01","2023-01-02","2023-01-01","2023-01-02"]),
            "q":[.1,-.1,-.2,.2]})
        nh,vh=_cluster_variance(a,["horse"])
        nd,vd=_cluster_variance(a,["day"])
        nhd,vhd=_cluster_variance(a,["horse","day"])
        self.assertEqual((nh,nd,nhd),(2,2,4))
        self.assertAlmostEqual(vh,0)
        self.assertAlmostEqual(vd,0.04)
        self.assertAlmostEqual(vhd,4/3*.1)
        
if __name__=="__main__":
    unittest.main()
