"""Tests for source-A historical age/sex/recency features (fictional horses)."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2022_strong_portable_baseline import (
    old_metadata, extra_features, ADDED_FEATURES, STRONG_KIN, STRONG_NO_KIN
)

def old_mock():
    return pd.DataFrame([
        {"horse":"x","year":2018,"day":pd.Timestamp("2018-03-01"),
         "y":0.4,"circuit":"JRA","race":"r1"},
        {"horse":"x","year":2019,"day":pd.Timestamp("2019-03-01"),
         "y":0.3,"circuit":"JRA","race":"r2"},
        {"horse":"z","year":2019,"day":pd.Timestamp("2019-02-01"),
         "y":0.7,"circuit":"NAR","race":"r3"},
    ])

def target():
    return pd.DataFrame([
        {"horse":"x","year":2022,"day":pd.Timestamp("2022-01-01"),"y":0.2},
        {"horse":"z","year":2022,"day":pd.Timestamp("2022-01-01"),"y":0.6},
        {"horse":"u","year":2022,"day":pd.Timestamp("2022-01-01"),"y":0.5},
    ])

def source():
    return pd.DataFrame([
        {"horse_id":"x","date":"2018-03-01","age":"3","sex":"牡"},
        {"horse_id":"x","date":"2019-03-01","age":"4","sex":"牡"},
        {"horse_id":"z","date":"2019-02-01","age":"5","sex":"牝"},
        {"horse_id":"x","date":"2023-02-01","age":"8","sex":"牝"},
    ])

class StrongPortableTests(unittest.TestCase):
    def test_only_pre2022_sourceA_metadata(self):
        m=old_metadata(source())
        self.assertEqual(len(m),3)
        self.assertTrue(m.day.lt(pd.Timestamp("2022-01-01")).all())
        self.assertEqual(int(m.loc[m.horse.eq("x"),"birthyear"].iloc[0]),2015)

    def test_age_sex_unknown_and_old_start_gap(self):
        x,qa=extra_features(old_mock(),target(),old_metadata(source()))
        self.assertEqual(list(x.columns),list(ADDED_FEATURES))
        self.assertEqual(x.loc[0,"age_from_pre2022_year"],7)
        self.assertEqual(x.loc[0,"age_available"],1)
        self.assertEqual(x.loc[0,"sex_female"],0)
        self.assertEqual(x.loc[1,"sex_female"],1)
        self.assertEqual(x.loc[2,"sex_unknown"],1)
        self.assertEqual(x.loc[2,"age_available"],0)
        self.assertTrue((x.loc[[0,1],"log_days_since_last"]>0).all())
        self.assertTrue(qa["no_future_sourceB_outcome_or_race_class_in_features"])

    def test_future_metadata_cannot_affect_focal_features(self):
        m=old_metadata(source())
        f=target()
        x,_=extra_features(old_mock(),f,m)
        m2=pd.concat([m,pd.DataFrame([{
            "horse":"x","day":pd.Timestamp("2022-01-02"),
            "year":2022., "birthyear":1999., "sex_code":2
        }])],ignore_index=True)
        y,_=extra_features(old_mock(),f,m2)
        pd.testing.assert_frame_equal(x,y)

    def test_future_outcome_changes_no_predictors(self):
        m=old_metadata(source())
        f=target()
        a,_=extra_features(old_mock(),f,m)
        f.loc[0,"y"]=.999
        b,_=extra_features(old_mock(),f,m)
        pd.testing.assert_frame_equal(a,b)

    def test_age_conflict_does_not_silently_select_value(self):
        m=old_metadata(source())
        m.loc[m.horse.eq("x") & m.day.eq(pd.Timestamp("2019-03-01")),"birthyear"]=2017.
        f=target()
        x,_=extra_features(old_mock(),f,m)
        self.assertEqual(x.loc[0,"age_conflict"],1)
        self.assertEqual(x.loc[0,"age_available"],0)
        self.assertEqual(x.loc[0,"age_from_pre2022_year"],5.0)

    def test_same_cutoff_year_ordering_rejects_future_history(self):
        h=old_mock()
        h.loc[0,"day"]=pd.Timestamp("2022-01-02")
        with self.assertRaisesRegex(ValueError,"TEMPORAL_HISTORY"):
            extra_features(h,target(),old_metadata(source()))

    def test_all_numeric_finite_and_unknown_safe(self):
        x,_=extra_features(old_mock(),target(),old_metadata(source()))
        self.assertTrue(np.isfinite(x.to_numpy(float)).all())

    def test_expanded_baseline_has_exact_same_incremental_family_columns(self):
        self.assertEqual(set(STRONG_KIN)-set(STRONG_NO_KIN),
                         {"sire_kin_history","dam_kin_history",
                          "log_sire_relative_count","log_dam_relative_count"})

if __name__=="__main__":
    unittest.main()
