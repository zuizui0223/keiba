"""Fictional negative controls: exact history-year + same-stratum start-depth.

All identifiers, parentage and target ranks in this test suite are invented.
"""
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ecology_japan_balanced_parent_history as balanced
import ecology_japan_time_depth_nonkin_match as match
from test_ecology_japan_unrelated_peer_control import example


def _fixture():
    h,t=example()
    source=balanced.prepare_peer_block(h,t,cutoff_year=2022)
    return h,t,source


def brute(history,target,k,seed,side,cutoff=2022):
    data=history.groupby(["horse","stratum"],sort=True).agg(
        sire=("sire_id","first"),dam=("dam_id","first"),
        score=("y","mean"),last=("day","max"),starts=("y","size")
    ).reset_index()
    data["score"]-=.5
    data["year"]=data["last"].dt.year
    data["bin"]=data["starts"].apply(match._bin)
    name="sire" if side==0 else "dam"
    true=[r for r in data.itertuples(index=False) if
          r.stratum==target.stratum and
          getattr(r,name)==getattr(target,"sire_id" if side==0 else "dam_id") and
          r.horse!=target.horse]
    priority=lambda x:hashlib.sha256(json.dumps(
        ["keiba-equal-peer-v1",seed,cutoff,x.stratum,x.horse],
        ensure_ascii=False,separators=(",",":")).encode()).digest()
    true=sorted(true,key=lambda r:(priority(r),r.horse))[:k]
    assert len(true)==k
    chosen=[]
    for year,binname in sorted(set((r.year,r.bin) for r in true)):
        need=sum((r.year,r.bin)==(year,binname) for r in true)
        candidates=[r for r in data.itertuples(index=False) if
                    r.stratum==target.stratum and r.year==year and r.bin==binname and
                    pd.notna(r.sire) and pd.notna(r.dam) and r.sire!="" and r.dam!=""]
        candidates=sorted(candidates,key=lambda r:(priority(r),r.horse))
        if not candidates:
            return None
        selected=[]
        start=match._offset(seed,cutoff,target.stratum,target.horse,side,year,binname,len(candidates))
        for j in range(len(candidates)):
            rr=candidates[(start+j)%len(candidates)]
            if rr.horse!=target.horse and rr.sire!=target.sire_id and rr.dam!=target.dam_id:
                selected.append(rr)
                if len(selected)==need:
                    break
        if len(selected)!=need:
            return None
        chosen.extend(selected)
    own=len(history.loc[history.horse.eq(target.horse)])
    return 5/(own+5)*sum(v.score for v in chosen)/(8+k)


class TemporalMatchTests(unittest.TestCase):
    def test_exact_small_case_with_independent_oracle_32_draws_both_sides(self):
        h,t,source=_fixture()
        b=match.prepare_temporal_match(h,t,source,cutoff_year=2022)
        for seed in range(2026112200,2026112232):
            for side in (0,1):
                values,info=match.sample_matched(b,seed=seed,side=side)
                self.assertEqual(info["status"],"OK_EXACT_YEAR_DEPTH_MATCHED_NONKIN")
                self.assertEqual(info["minimum_missing_slots"],0)
                self.assertEqual(info["requested_true_peer_slots"],info["matched_peer_slots"])
                expected=[brute(h,row,int(k),seed,side) for row,k
                          in zip(t.itertuples(index=False),source.k)]
                np.testing.assert_allclose(values,expected,rtol=0,atol=1e-15)

    def test_incorrect_history_year_returns_HOLD_without_other_year_substitution(self):
        h,t,source=_fixture()
        h.loc[h.horse.str.startswith("unrelated"),"day"]=pd.Timestamp("2020-11-01")
        h.loc[h.horse.eq("neutral"),"day"]=pd.Timestamp("2020-11-01")
        source=balanced.prepare_peer_block(h,t,cutoff_year=2022)
        b=match.prepare_temporal_match(h,t,source,cutoff_year=2022)
        for side in (0,1):
            out,info=match.sample_matched(b,seed=2026112200,side=side)
            self.assertIsNone(out)
            self.assertEqual(info["status"],"HOLD_EXACT_YEAR_AND_HISTORY_DEPTH_MATCHING_SUPPORT")
            self.assertGreater(info["minimum_missing_slots"],0)

    def test_unmatched_stratum_starts_category_cannot_borrow_one_start_peers(self):
        h,t,_=_fixture()
        # Two past starts for same-sire and same-dam and full sibling;
        # unrelated candidates have one. No 2-4 count peer to borrow.
        rows=h.loc[h.horse.isin(["same-sire","same-dam","fullsib"])].copy()
        rows["day"]=pd.Timestamp("2021-11-20")
        h=pd.concat([h,rows],ignore_index=True)
        source=balanced.prepare_peer_block(h,t,cutoff_year=2022)
        b=match.prepare_temporal_match(h,t,source,cutoff_year=2022)
        v,info=match.sample_matched(b,seed=2026112200,side=0)
        self.assertIsNone(v)
        self.assertGreater(info["unmatched_selected_peer_bins"]["2-4"],0)

    def test_reordered_starts_do_not_change_any_chosen_candidate_or_score(self):
        h,t,source=_fixture()
        b=match.prepare_temporal_match(h,t,source,cutoff_year=2022)
        x,stat=match.sample_matched(b,seed=2026112201,side=0)
        h2=h.sample(frac=1,random_state=42)
        t2=t.iloc[[1,0,3,1,2]]
        block2=balanced.prepare_peer_block(h2,t2,cutoff_year=2022)
        b2=match.prepare_temporal_match(h2,t2,block2,cutoff_year=2022)
        y,_=match.sample_matched(b2,seed=2026112201,side=0)
        np.testing.assert_allclose(y,x[[1,0,3,1,2]],rtol=0,atol=1e-15)

    def test_wrong_member_context_and_cutoff_are_rejected(self):
        h,t,source=_fixture()
        with self.assertRaises(ValueError):
            match.prepare_temporal_match(h.iloc[1:],t,source,cutoff_year=2022)
        with self.assertRaises(ValueError):
            match.prepare_temporal_match(h,t,source,cutoff_year=2021)
        with self.assertRaises(ValueError):
            match.sample_matched(object(),seed=2026112200,side=0)
        with self.assertRaises(ValueError):
            match.sample_matched(match.prepare_temporal_match(h,t,source,cutoff_year=2022),
                                 seed=2026112200,side=3)

    def test_true_parent_peer_order_and_prior_score_guard(self):
        h,t,source=_fixture()
        b=match.prepare_temporal_match(h,t,source,cutoff_year=2022)
        x,_=match.sample_matched(b,seed=2026112200,side=0)
        self.assertTrue(np.isfinite(x).all())
        self.assertEqual(len(x),len(t))
        self.assertEqual(x[3],0.)
        self.assertNotIn("horse",match.sample_matched(b,seed=2026112200,side=0)[1])

    def test_k_zero_rows_are_preserved_not_counted_as_missing(self):
        h,t,source=_fixture()
        b=match.prepare_temporal_match(h,t,source,cutoff_year=2022)
        x,stats=match.sample_matched(b,seed=2026112200,side=0)
        self.assertEqual(x[2],0.)
        self.assertEqual(x[3],0.)
        self.assertEqual(stats["positive_k_requests"],2)


if __name__=="__main__":
    unittest.main()
