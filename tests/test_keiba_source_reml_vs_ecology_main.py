"""Independent numerical equivalence to existing ecology race-fixed REML.

Entire dataset is fabricated 24 horses x 12 original race dates. It uses
the real ecology_rq_race_fixed_icc.race_fixed_reml implementation only
for method comparison, NOT actual Racing Queensland horse observations.
The original REML needs SciPy; scientific CI installs it. Generic CI
skips if unavailable without pretending a full comparison succeeded.
"""
from __future__ import annotations
from pathlib import Path
import math
import sys
import unittest

try:
    import numpy
    import scipy
except ModuleNotFoundError:
    scipy = None

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
if scipy is not None:
    from ecology_rq_race_fixed_icc import race_fixed_reml
    from keiba_source_race_fixed_reml import estimate_race_fixed_reml
    from keiba_race_contrast_trait_posterior import fit_race_contrast_posterior


def prepared_toy_cohort():
    source_system="ARTIFICIAL_RQ_METHOD_EQUIVALENCE_NEVER_REAL_HORSES"
    labels=[f"SYN-{i:02d}" for i in range(24)]
    all_old_rows=[]
    all_new_rows=[]
    for date_idx in range(1,13):
        day=f"2026-10-{date_idx:02d}"
        for i,h in enumerate(labels):
            stable=.47*math.sin(.6*i)+.11*math.cos(.33*i)
            err=.13*math.sin(1.19*i+1.63*date_idx)
            seconds=10.0+.21*math.sin(.9*date_idx)+stable+err
            old={
                "day":day,"race_number":4,
                "horse_id":h,"horse_name":f"TOY_{i}",
                "distance":1400,"first_marker_m":150,
                "first_section_sec":seconds,"class":"TOY_OPEN"
            }
            all_old_rows.append(old)
            new={
                "source_system":source_system,
                "horse_id":h,"race_id":f"{day}-R4",
                "race_day":f"{day}T10:00:00+09:00",
                "received_at":f"{day}T12:00:00+09:00",
                "first_marker_m":150,"distance_m":1400,
                "race_class":"TOY_OPEN",
                "first_section_seconds":seconds,
            }
            all_new_rows.append(new)
    source={
        "schema":"KEIBA_SAME_HORSE_GPS_REPEATABILITY_HISTORY_V1",
        "source_system":source_system,
        "rights_checked_locally":True,
        "authenticated_publisher_clock":True,
        "records":all_new_rows,
    }
    target={
        "source_system":source_system,"horse_ids":labels,
        "asof_jst":"2026-10-26T09:30:00+09:00",
        "initial_market_published_at_jst":"2026-10-26T08:45:00+09:00",
        "initial_market_received_at_jst":"2026-10-26T09:00:00+09:00",
        "first_marker_m":150,"distance_m":1400,
        "race_class":"TOY_OPEN",
    }
    return all_old_rows,source,target


@unittest.skipIf(scipy is None,"Crosscheck requires optional SciPy in dedicated CI")
class RealEcologyImplementationEquivalenceSyntheticTests(unittest.TestCase):
    def test_race_fixed_reml_matches_independent_main_ecology_implementation(self):
        old,source,target=prepared_toy_cohort()
        ecology=race_fixed_reml(old,min_race_telemetry=4)
        integrated=estimate_race_fixed_reml(source,target)
        self.assertEqual(ecology["status"],
                         "EXPLORATORY_RACE_ADJUSTED_GAUSSIAN_ICC_POINT_ONLY")
        self.assertEqual(integrated["n_independent_contrast_dimensions"],
                         12*23)
        self.assertEqual(ecology["race_fixed_effect_contrast_observations"],
                         integrated["n_independent_contrast_dimensions"])
        self.assertEqual(ecology["original_races"],12)
        self.assertEqual(ecology["different_official_HORSES_IDs"],24)
        self.assertAlmostEqual(
            ecology["horse_variance_component_sec_squared"],
            integrated["horse_effect_variance_seconds_squared"],
            delta=2e-6)
        self.assertAlmostEqual(
            ecology["independent_error_variance_component_sec_squared"],
            integrated["independent_absolute_time_error_variance_seconds_squared"],
            delta=2e-6)
        self.assertAlmostEqual(
            ecology["conditional_observational_ICC_point_estimate"],
            integrated["conditional_icc_point"],delta=5e-6)
        self.assertLess(abs(
            ecology["source_variance_ratio_horse_over_residual"]-
            integrated["variance_ratio"])/integrated["variance_ratio"],
            1e-4)

    def test_same_reml_hyperparameters_go_into_full_joint_horse_posterior(self):
        _old,source,target=prepared_toy_cohort()
        independent=estimate_race_fixed_reml(source,target)
        joint=fit_race_contrast_posterior(
            source,target,variance_fit_mode="source_reml")
        self.assertEqual(joint["source_variance_estimation_mode"],"source_reml")
        self.assertTrue(joint["hyperparameters"]
                        ["source_only_orthogonal_race_contrast_reml"])
        self.assertAlmostEqual(
            joint["hyperparameters"]["horse_between_variance_seconds2"],
            independent["horse_effect_variance_seconds_squared"],
            delta=2e-6)
        self.assertAlmostEqual(
            joint["hyperparameters"]["assumed_absolute_time_residual_variance_seconds2"],
            independent["independent_absolute_time_error_variance_seconds_squared"],
            delta=2e-6)
        self.assertEqual(len(joint["mean"]),24)
        self.assertEqual(len(joint["covariance"]),24)
        self.assertGreater(numpy.linalg.eigvalsh(joint["covariance"])[0],0)
        self.assertFalse(joint["not_original_RQ_REML_fit"] is False)


if __name__=="__main__":
    unittest.main()
