"""Synthetic-only 2026 own-vs-family factorial provenance and attenuation tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2026_own_kin_factorial import (
    mix_own_kin, SCENARIOS, KIN_SIGNALS, KIN_COUNTS,
    ORIGINAL_2026, FROZEN_2026_DAY_LAGGED,
)
from ecology_japan_2022_independent_forward import make_common_features
from ecology_japan_2026_day_rolling import history_before_day


def feature_pair():
    # Explicit own-count attenuation 5/(5+n) and unchanged family aggregates.
    # Stale n=2, fresh n=8. 1.5 is a fictional peer mean sum.
    n_old=2.0
    n_new=8.0
    x_old=pd.DataFrame({
        "own_mean":[0.45],
        "log_own_count":[np.log1p(n_old)],
        "sire_kin_history":[5/(5+n_old)*1.5/(8+3)],
        "dam_kin_history":[5/(5+n_old)*(-0.5)/(8+1)],
        "log_sire_relative_count":[np.log1p(3)],
        "log_dam_relative_count":[np.log1p(1)],
        "log_days_since_last":[4.1],
        "sex_unknown":[0.0],
    })
    x_new=pd.DataFrame({
        "own_mean":[0.35],
        "log_own_count":[np.log1p(n_new)],
        "sire_kin_history":[5/(5+n_new)*2.0/(8+4)],
        "dam_kin_history":[5/(5+n_new)*(-0.3)/(8+2)],
        "log_sire_relative_count":[np.log1p(4)],
        "log_dam_relative_count":[np.log1p(2)],
        "log_days_since_last":[2.1],
        "sex_unknown":[0.0],
    })
    return x_old,x_new


class FactorialFourWayTests(unittest.TestCase):
    def test_all_four_factorial_codes_fixed(self):
        self.assertEqual(
            SCENARIOS, {
                "SS":("stale","stale"),"FS":("fresh","stale"),
                "SF":("stale","fresh"),"FF":("fresh","fresh")
            }
        )

    def test_identity_SS_reproduces_stale(self):
        old,new=feature_pair()
        x=mix_own_kin(old,new,own="stale",family="stale")
        pd.testing.assert_frame_equal(x,old)

    def test_identity_FF_reproduces_updated(self):
        old,new=feature_pair()
        x=mix_own_kin(old,new,own="fresh",family="fresh")
        pd.testing.assert_frame_equal(x,new)

    def test_FS_fresh_own_stale_family_rescales_kin_signal(self):
        old,new=feature_pair()
        x=mix_own_kin(old,new,own="fresh",family="stale")
        self.assertAlmostEqual(x.own_mean.iloc[0],new.own_mean.iloc[0])
        self.assertAlmostEqual(x.log_days_since_last.iloc[0],2.1)
        self.assertAlmostEqual(x.sire_kin_history.iloc[0],
                               old.sire_kin_history.iloc[0]*7/13)
        self.assertAlmostEqual(x.dam_kin_history.iloc[0],
                               old.dam_kin_history.iloc[0]*7/13)
        self.assertAlmostEqual(x.log_sire_relative_count.iloc[0],
                               old.log_sire_relative_count.iloc[0])

    def test_SF_stale_own_fresh_family_rescales_kin_signal(self):
        old,new=feature_pair()
        x=mix_own_kin(old,new,own="stale",family="fresh")
        self.assertAlmostEqual(x.own_mean.iloc[0],old.own_mean.iloc[0])
        self.assertAlmostEqual(x.log_days_since_last.iloc[0],4.1)
        self.assertAlmostEqual(x.sire_kin_history.iloc[0],
                               new.sire_kin_history.iloc[0]*13/7)
        self.assertAlmostEqual(x.log_dam_relative_count.iloc[0],
                               new.log_dam_relative_count.iloc[0])

    def test_never_swap_own_info_into_kin_columns_by_accident(self):
        old,new=feature_pair()
        x=mix_own_kin(old,new,own="stale",family="fresh")
        self.assertAlmostEqual(float(x.log_own_count.iloc[0]),
                               float(old.log_own_count.iloc[0]))
        self.assertAlmostEqual(float(x.sex_unknown.iloc[0]),
                               float(old.sex_unknown.iloc[0]))

    def test_unknown_parent_and_zero_kin_always_zero(self):
        old,new=feature_pair()
        old.loc[0,list(KIN_SIGNALS)]=0.0
        old.loc[0,list(KIN_COUNTS)]=0.0
        x=mix_own_kin(old,new,own="fresh",family="stale")
        self.assertEqual(float(x.sire_kin_history.iloc[0]),0.0)
        self.assertEqual(float(x.dam_kin_history.iloc[0]),0.0)
        self.assertEqual(float(x.log_sire_relative_count.iloc[0]),0.0)

    def test_source_schema_mismatch_is_hard_hold(self):
        old,new=feature_pair()
        with self.assertRaisesRegex(ValueError,"SCHEMA_MISMATCH"):
            mix_own_kin(old,new.drop(columns="own_mean"),own="fresh",family="stale")

    def test_invalid_mode_is_hard_hold(self):
        old,new=feature_pair()
        with self.assertRaisesRegex(ValueError,"FRESHNESS_FACTOR"):
            mix_own_kin(old,new,own="today",family="stale")

    def test_different_own_counts_and_real_peer_history(self):
        # Construct 2 distant horses sharing sire. One later race of the focal,
        # while the sibling's own performance stays unchanged.
        old=pd.DataFrame([
            dict(horse="A",day=pd.Timestamp("2019-01-01"),year=2019,
                 y=.2, sire_id="S",dam_id="DA",
                 stratum="turf:4",surface="turf",distance=1600,race="r1"),
            dict(horse="B",day=pd.Timestamp("2019-01-02"),year=2019,
                 y=.8,sire_id="S",dam_id="DB",
                 stratum="turf:4",surface="turf",distance=1600,race="r2"),
        ])
        newer=pd.concat([old,pd.DataFrame([
            dict(horse="A",day=pd.Timestamp("2025-01-01"),year=2025,
                 y=.3,sire_id="S",dam_id="DA",
                 stratum="turf:4",surface="turf",distance=1600,race="r3"),
        ])],ignore_index=True)
        future=pd.DataFrame([
            dict(horse="A",day=pd.Timestamp("2026-01-01"),year=2026,
                 y=.5,sire_id="S",dam_id="DA",
                 stratum="turf:4",surface="turf",distance=1600,race="r4"),
        ])
        a=make_common_features(old,future)
        b=make_common_features(newer,future)
        mixed=mix_own_kin(a,b,own="fresh",family="stale")
        # Same relative B score .8 => residual .3, one peer.
        self.assertAlmostEqual(float(mixed.sire_kin_history.iloc[0]),
                               (5/7)*(.8-.5)/9)
        self.assertAlmostEqual(float(mixed.log_own_count.iloc[0]),
                               np.log(3))

    def test_no_same_day_data_available_for_features(self):
        past=pd.DataFrame([
            dict(horse="A",day=pd.Timestamp("2026-01-01"),year=2026,
                 y=.2,sire_id="S",dam_id="D",
                 stratum="turf:4",surface="turf",distance=1600,race="r1"),
        ])
        modern=pd.concat([past,pd.DataFrame([
            dict(horse="A",day=pd.Timestamp("2026-01-02"),year=2026,
                 y=.99,sire_id="S",dam_id="D",
                 stratum="turf:4",surface="turf",distance=1600,race="r2"),
        ])],ignore_index=True)
        h=history_before_day(past,modern,pd.Timestamp("2026-01-02"),mode="prior_day")
        self.assertTrue(h.day.lt(pd.Timestamp("2026-01-02")).all())

    def test_reference_scores_are_locked_from_previous_real_runs(self):
        self.assertAlmostEqual(ORIGINAL_2026["ordinary"][0],.319681772293503)
        self.assertAlmostEqual(FROZEN_2026_DAY_LAGGED["strong"][1],.274422587127491)


if __name__=="__main__":
    unittest.main()
