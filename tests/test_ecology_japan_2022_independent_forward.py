"""Invented historical/independent-source races; no original runner content."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2022_independent_forward import (
    parse_independent_history,make_common_features,fit_weighted_ridge,
    predict_weighted_ridge,
)


def hf_record(rid="101",rank=2,field=8,distance=1600,surface=1):
    # Original HF source stores 17 values and date is in race table.
    return [rid,"05",.5,0,surface,distance,0,field,3,57,500,0,rank,92,0,32,33.5]


def old():
    data=[]
    for y in (2018,2019,2020,2021):
        for i in range(9):
            data.append({
                "horse":str(i),"day":pd.Timestamp(y,1,1),
                "year":y,"y":(i%3)/3.0,"stratum":"turf:4",
                "sire_id": "S"+str(i//3),
                "dam_id": "D"+str(i),
                "surface":"turf","distance":1600,
            })
    return pd.DataFrame(data)


class IndependentValidationModelTests(unittest.TestCase):
    def test_actual_17_column_history_parses_2022_with_Race_dates(self):
        rec=hf_record()
        rows,qa=parse_independent_history(json.dumps([[rec]]),
            {"101":("2022/01/05",1600,1)})
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["day"],pd.Timestamp("2022-01-05"))
        self.assertEqual(rows[0]["race_id"],"101")
        self.assertAlmostEqual(rows[0]["y"],1/7)
        self.assertEqual(rows[0]["stratum"],"turf:4")
        self.assertEqual(qa["eligible_rows"],1)

    def test_mismatched_source_distance_and_surf_are_not_silently_kept(self):
        rec=hf_record()
        rows,qa=parse_independent_history(json.dumps([[rec]]),
            {"101":("2022/01/05",1800,0)})
        self.assertEqual(rows,[])
        self.assertEqual(qa["source_race_metadata_conflicts"],1)

    def test_invalid_record_field_is_reported_by_exact_column(self):
        x=hf_record()
        x[4]=None
        rows,qa=parse_independent_history(json.dumps([[x]]),
            {"101":("2022/01/05",1600,1)})
        self.assertEqual(rows,[])
        self.assertEqual(qa["invalid_horse_surface"],1)
        y=hf_record()
        rows,qa=parse_independent_history(json.dumps([[y]]),
            {"101":("2022/01/05",1600,None)})
        self.assertEqual(qa["invalid_race_surface"],1)

    def test_unclassified_finisher_and_no_source_race_ref_excluded(self):
        x=hf_record(rank=9,field=8)
        y=hf_record(rid="999")
        rows,qa=parse_independent_history(json.dumps([[x,y]]),
            {"101":("2023/01/01",1600,1)})
        self.assertEqual(rows,[])
        self.assertEqual(qa["invalid_relative_rank_or_field"],1)
        self.assertEqual(qa["missing_race_id_lookup"],1)

    def test_future_target_rank_never_enters_features(self):
        h=old()
        t=pd.DataFrame([{
            "horse":"0","day":pd.Timestamp("2022-01-01"),"year":2022,
            "y":.25,"stratum":"turf:4","sire_id":"S0",
            "dam_id":"D0","surface":"turf","distance":1600,
        }])
        x=make_common_features(h,t)
        t["y"]=.99
        z=make_common_features(h,t)
        pd.testing.assert_frame_equal(x,z)
        self.assertNotIn("y",x.columns)
        self.assertEqual(int(x.iloc[0]["sire_relative_count"]),2)

    def test_actual_kin_and_no_kin_use_identical_training_samples(self):
        h=old()
        t=h[h.year==2021].copy()
        a=make_common_features(h[h.year<2021],t)
        z=fit_weighted_ridge(a,t.y.to_numpy(),t.horse.to_numpy(),
                            ["own_mean","log_own_count","surface_turf"],alpha=100)
        pred=predict_weighted_ridge(z,a)
        self.assertEqual(pred.shape,(len(t),))
        self.assertTrue(np.all((pred>=0)&(pred<=1)))

    def test_empty_reference_cannot_be_treated_as_unrelated(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_EVENT"):
            parse_independent_history(json.dumps([[hf_record()]]),{})


if __name__=="__main__":
    unittest.main()
