"""Synthetic only: dated source-A own/other-parent information coverage and HOLDs."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2022_2024_kin_information_moderators import (
    STATUS,age_bin,count_bin,peer_last_day_excluding_self,
    fixed_sourceA_context,group_score,
    OWN_NAMES,KIN_NAMES
)


def old_future():
    base=[]
    for horse,sire,dam,dates,performance in (
        ("A","S","DA",("2020-11-01","2021-12-01"),.2),
        ("B","S","DB",("2020-11-01","2021-12-15"),.7),
        ("C","T","DC",("2020-11-01","2021-12-10"),.4)
    ):
        for i,day in enumerate(dates):
            base.append({
                "horse":horse,"sire_id":sire,"dam_id":dam,
                "day":pd.Timestamp(day),"year":int(day[:4]),
                "surface":"turf","distance":1600,"stratum":"turf:4",
                "y":performance +.02*i,"race":"old_"+horse+str(i),
            })
    old=pd.DataFrame(base)
    t=pd.DataFrame([{
        "horse":h,"sire_id":sire,"dam_id":dam,
        "day":pd.Timestamp("2022-01-03"),"year":2022,
        "surface":"turf","distance":1600,"stratum":"turf:4",
        "y":.5,"race":"target-"+h,
    } for h,sire,dam in (("A","S","DA"),("B","S","DB"),("C","T","DC"))])
    return old,t


class KinshipInformationModeratorTests(unittest.TestCase):
    def test_predeclared_own_bins(self):
        self.assertEqual(count_bin([0,1,3,4,7,8,15,16,100],"own").tolist(),
                         ["0-3","0-3","0-3","4-7","4-7",
                          "8-15","8-15","16+","16+"])
        self.assertEqual(tuple(OWN_NAMES),("0-3","4-7","8-15","16+"))

    def test_predeclared_kin_bins(self):
        self.assertEqual(
            count_bin([0,1,2,4,5,20],"family").tolist(),
            ["no_recorded_peer","one_recorded_peer","2-4_peers",
             "2-4_peers","5+_peers","5+_peers"])

    def test_age_bin_exact_boundary_and_missing(self):
        self.assertEqual(age_bin([0,365,366,1095,1096,9999,np.nan]).tolist(),
            ["0-365d","0-365d","366-1095d","366-1095d",
             "1096+d","1096+d","NO_RECORDED_DATE"])

    def test_focal_horse_is_excluded_as_parent_peer(self):
        old,t=old_future()
        q=peer_last_day_excluding_self(old,t,"sire_id")
        self.assertEqual(q.iloc[0],pd.Timestamp("2021-12-15"))
        self.assertEqual(q.iloc[1],pd.Timestamp("2021-12-01"))
        self.assertTrue(pd.isna(q.iloc[2]))

    def test_two_event_identity_can_have_zero_eligible_old_history(self):
        old,t=old_future()
        # D could have a valid two-date raw-source A/B identity witness but
        # no race rows surviving this specific source-A eligibility filter.
        # Its parent proxy still exists and must NOT be thrown away.
        d=t.iloc[0].copy()
        d["horse"]="D"
        d["dam_id"]="DD"
        d["race"]="target-D"
        t=pd.concat([t,pd.DataFrame([d])],ignore_index=True)
        ctx,qa=fixed_sourceA_context(old,t)
        self.assertEqual(ctx["own_record_count_bin"].iloc[-1],"0-3")
        self.assertEqual(ctx["sourceA_own_record_age_bin"].iloc[-1],
                         "NO_RECORDED_DATE")
        self.assertEqual(ctx["other_same_parent_horse_count_bin"].iloc[-1],
                         "2-4_peers")
        self.assertEqual(qa["focal_rows_with_zero_eligible_A_history"],1)
        self.assertTrue(qa[
            "raw_cross_source_identity_two_events_NOT_guaranteed_eligible_model_history"])

    def test_unmatched_dam_record_is_not_pseudo_relative(self):
        old,t=old_future()
        q=peer_last_day_excluding_self(old,t,"dam_id")
        self.assertTrue(q.isna().all())

    def test_historical_pretarget_own_and_parent_support(self):
        old,t=old_future()
        ctx,qa=fixed_sourceA_context(old,t)
        self.assertEqual(len(ctx),3)
        self.assertEqual(set(ctx["own_record_count_bin"]),{"0-3"})
        self.assertEqual(ctx["other_same_parent_horse_count_bin"].tolist(),
                         ["one_recorded_peer","one_recorded_peer","no_recorded_peer"])
        self.assertEqual(ctx["sourceA_other_same_parent_record_age_bin"].tolist(),
                         ["0-365d","0-365d","NO_RECORDED_DATE"])
        self.assertEqual(qa["focal_rows_with_any_peer_history"],2)
        self.assertEqual(qa["focal_rows_with_zero_peer_history"],1)
        self.assertTrue(qa["last_other_horse_excludes_focal"])

    def test_same_parent_different_race_context_does_not_count(self):
        old,t=old_future()
        old.loc[old.horse.eq("B"),"stratum"]="dirt:4"
        old.loc[old.horse.eq("B"),"surface"]="dirt"
        ctx,qa=fixed_sourceA_context(old,t)
        self.assertEqual(ctx["other_same_parent_horse_count_bin"].iloc[0],
                         "no_recorded_peer")
        self.assertEqual(ctx["other_same_parent_horse_count_bin"].iloc[1],
                         "one_recorded_peer")

    def test_unknown_parent_column_rejected(self):
        old,t=old_future()
        with self.assertRaisesRegex(ValueError,"UNKNOWN_PARENT"):
            peer_last_day_excluding_self(old,t,"race")

    def test_future_source_A_history_rejected_before_moderating(self):
        old,t=old_future()
        old.loc[0,"day"]=pd.Timestamp("2022-01-04")
        with self.assertRaisesRegex(ValueError,"NEWER_RESULTS"):
            fixed_sourceA_context(old,t)

    def test_invalid_negative_counts_and_lags_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID_RECORD_COUNT"):
            count_bin([-1],"own")
        with self.assertRaisesRegex(ValueError,"NEGATIVE_TIME_LAG"):
            age_bin([-1])
        with self.assertRaisesRegex(ValueError,"INVALID_MODERATOR_BIN"):
            count_bin([1],"rider")

    def test_small_subgroup_holds_and_never_assigns_significance(self):
        _,t=old_future()
        result=group_score(t,[.4,.4,.4],[.5,.5,.5],np.ones(3,bool))
        self.assertEqual(result["status"],
                         "HOLD_POSTHOC_SUBGROUP_INSUFFICIENT_SUPPORT")
        self.assertNotIn("M0_minus_kin_gain",result)

    def test_large_synthetic_subgroup_equal_horse_aggregation(self):
        rows=[]
        for i in range(160):
            rows.append({
                "horse":"H"+str(i%40),
                "race":"R"+str(i),
                "day":pd.Timestamp("2022-01-01")+pd.Timedelta(days=i%20),
                "year":2022,"y":float((i%5)/5)
            })
        t=pd.DataFrame(rows)
        p0=np.full(len(t),.5)
        p1=t.y.to_numpy(float)*.5+.25
        score=group_score(t,p0,p1,np.ones(len(t),bool),boot=40)
        self.assertEqual(score["status"],
                         "POSTHOC_SUBGROUP_DESCRIPTIVE_NOT_GENERALIZED")
        self.assertGreater(score["M0_minus_kin_gain"],0)
        self.assertGreater(score["MSE_no_kin_minus_family"],0)
        self.assertEqual(score["single_way_horse_and_race_day_199_bootstrap"][
            "horse"]["bootstrap_draws"],40)

    def test_no_horse_ids_in_returned_hypothetical_aggregate(self):
        old,t=old_future()
        _,qa=fixed_sourceA_context(old,t)
        self.assertNotIn("horse",str(qa).lower().replace("other_horse",""))
        self.assertNotIn("target-A",str(qa))

if __name__=="__main__":
    unittest.main()
