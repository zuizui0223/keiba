"""Fictional-only tests: 2026 day-lagged source-C history, no target leakage."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2026_day_rolling import (
    history_before_day, transient_source_c_history, relevant_old_history,
    predictions_for_history
)
from ecology_japan_2022_independent_forward import make_common_features


def old_data():
    d=[]
    specs=[("h1","s1","d1"),("h2","s1","d2"),("h3","s3","d3"),
           ("h4","s4","d4")]
    for year in (2018,2019,2020):
        for h,s,dam in specs:
            d.append({
                "horse":h,"sire_id":s,"dam_id":dam,
                "day":pd.Timestamp(year,4,2),"year":year,
                "surface":"turf","distance":1600,"stratum":"turf:4",
                "circuit":"JRA","race":f"r-{year}-{h}",
                "y":0.3 if h=="h1" else 0.8
            })
    return pd.DataFrame(d)


def target():
    return pd.DataFrame([{
        "horse":"h1","sire_id":"s1","dam_id":"d1",
        "day":pd.Timestamp("2026-02-03"),"year":2026,
        "surface":"turf","distance":1600,"stratum":"turf:4",
        "circuit":"JRA","race":"new-r1","y":0.5
    }])


def C_history():
    d=[]
    for day in ("2025-05-10","2026-02-02","2026-02-03","2026-02-04"):
        for h,rank in [("h1",1),("h2",2)]:
            d.append({
                "horse":h,"sire_id":"s1",
                "dam_id":"d1" if h=="h1" else "d2",
                "day":pd.Timestamp(day),"year":int(day[:4]),
                "surface":"turf","distance":1600,"stratum":"turf:4",
                "circuit":"JRA","race":"r"+day,"y":float(rank-1)
            })
    return pd.DataFrame(d)


class DayLaggedTests(unittest.TestCase):
    def test_excludes_same_day_and_future_races_even_if_loaded(self):
        h=history_before_day(old_data(),C_history(),pd.Timestamp("2026-02-03"),mode="prior_day")
        self.assertEqual(int(h.day.ge(pd.Timestamp("2026-02-03")).sum()),0)
        self.assertEqual(int(h.day.eq(pd.Timestamp("2026-02-02")).sum()),2)

    def test_pre2026_static_stop(self):
        h=history_before_day(old_data(),C_history(),pd.Timestamp("2026-02-03"),mode="through2025")
        self.assertEqual(int(h.year.eq(2026).sum()),0)
        self.assertEqual(int(h.year.eq(2025).sum()),2)

    def test_stale_equals_old(self):
        a=old_data()
        b=history_before_day(a,C_history(),pd.Timestamp("2026-02-03"),mode="stale")
        pd.testing.assert_frame_equal(a,b)

    def test_no_same_day_result_in_feature_vector(self):
        a=old_data()
        c=C_history()
        t=target()
        h=history_before_day(a,c,t.day.min(),mode="prior_day")
        f1=make_common_features(h,t)
        c.loc[c.day.ge(pd.Timestamp("2026-02-03")),"y"]=0.95
        h2=history_before_day(a,c,t.day.min(),mode="prior_day")
        f2=make_common_features(h2,t)
        pd.testing.assert_frame_equal(f1,f2)

    def test_reduced_focal_and_family_history_feature_parity(self):
        a=old_data()
        t=target()
        b,qa=relevant_old_history(a,t)
        self.assertTrue(qa["all_original_feature_columns_exactly_reproduced"])
        self.assertFalse(b.horse.eq("h3").any())
        self.assertFalse(b.horse.eq("h4").any())
        pd.testing.assert_frame_equal(make_common_features(a,t),make_common_features(b,t))

    def test_future_history_rejected_if_full_sample_contaminated(self):
        a=old_data()
        a.loc[0,"day"]=pd.Timestamp("2026-03-01")
        with self.assertRaisesRegex(ValueError,"SAME_DAY_OR_FUTURE"):
            history_before_day(a,C_history(),pd.Timestamp("2026-02-03"),mode="stale")

    def test_unknown_mode_is_hard_hold(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_DAY_LAG_MODE"):
            history_before_day(old_data(),C_history(),pd.Timestamp("2026-02-03"),mode="see_future")

    def test_source_c_historical_own_and_relative_rows_are_typed(self):
        C=pd.DataFrame([
            dict(race_key="2025-05-10|東京|1",normalized_name="horse a",
                 day=pd.Timestamp("2025-05-10"),year=2025,venue="東京",
                 surf="turf",distance=1600,rank=1),
            dict(race_key="2025-05-10|東京|1",normalized_name="horse b",
                 day=pd.Timestamp("2025-05-10"),year=2025,venue="東京",
                 surf="turf",distance=1600,rank=2),
        ])
        src,_=transient_source_c_history(C,{"horse a":"h1","horse b":"h2"},old_data())
        self.assertEqual(len(src),2)
        self.assertSetEqual(set(src.sire_id),{"s1"})
        self.assertEqual(sorted(src.y.tolist()),[0.0,1.0])

    def test_unconfirmed_public_name_cannot_contribute_history(self):
        C=pd.DataFrame([
            dict(race_key="2025-05-10|東京|1",normalized_name="horse a",
                 day=pd.Timestamp("2025-05-10"),year=2025,venue="東京",
                 surf="turf",distance=1600,rank=1),
            dict(race_key="2025-05-10|東京|1",normalized_name="unverified",
                 day=pd.Timestamp("2025-05-10"),year=2025,venue="東京",
                 surf="turf",distance=1600,rank=2),
        ])
        src,_=transient_source_c_history(C,{"horse a":"h1"},old_data())
        self.assertEqual(len(src),1)
        self.assertEqual(src.horse.iloc[0],"h1")


if __name__=="__main__":
    unittest.main()
