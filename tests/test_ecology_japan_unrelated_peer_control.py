"""Fictional independent oracle for both-parent-excluding unrelated history."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ecology_japan_2022_24_family_feature_ablation as ablation
import ecology_japan_balanced_parent_history as balanced
import ecology_japan_unrelated_peer_control as control


def example():
    rows = [
        ("focal","dad","mum","turf:4",.1),
        ("same-sire","dad","other1","turf:4",.2),
        ("same-dam","other2","mum","turf:4",.9),
        ("fullsib","dad","mum","turf:4",.3),
        ("neutral","x1","y1","turf:4",.5),
        ("unrelated-a","x2","y2","turf:4",1.),
        ("unrelated-b","x3","y3","turf:4",.4),
        ("unrelated-c","x4","y4","turf:4",.8),
        ("unrelated-d","x5","y5","turf:4",.1),
        ("missing-historical-parent",None,"y6","turf:4",.7),
        ("different-stratum","x7","y7","dirt:4",.2),
        ("not-in-stratum","x8","y8","turf:8",.6),
    ]
    h = pd.DataFrame(rows, columns=["horse","sire_id","dam_id","stratum","y"])
    h["day"] = pd.date_range("2021-01-01", periods=len(h))
    t = pd.DataFrame([
        ("focal","dad","mum","turf:4"),
        ("new","dad","mum","turf:4"),
        ("new-unrelated","x10","y10","turf:4"),
        ("no-peers","unseen-sire","unseen-dam","turf:4"),
    ], columns=["horse","sire_id","dam_id","stratum"])
    t["day"] = pd.date_range("2023-05-01", periods=len(t))
    t["year"] = 2023
    t["surface"] = "turf"
    t["distance"] = 1600.
    return h, t[ablation.CONTEXT]


def oracle(history, target, k, seed, cutoff_year=2022):
    original = history.groupby(["horse","stratum"], sort=True).agg(score=("y","mean"),
                    sire_id=("sire_id","first"),dam_id=("dam_id","first")).reset_index()
    original.score -= .5
    candidates = [r for r in original.itertuples() if
                  r.stratum == target.stratum and r.horse != target.horse and
                  pd.notna(r.sire_id) and pd.notna(r.dam_id) and
                  r.sire_id not in ("", target.sire_id) and r.dam_id not in ("", target.dam_id)]
    if len(candidates) < k:
        raise ValueError("oracle-too-few")
    def digest(r):
        payload = json.dumps(["keiba-equal-peer-v1",int(seed),int(cutoff_year),r.stratum,r.horse],
                             ensure_ascii=False,separators=(",",":")).encode("utf8")
        return hashlib.sha256(payload).digest(), r.horse
    ranked = sorted(candidates, key=digest)  # Wrong order if filtered pre-rotation: fix below.
    # Rotate the WHOLE known-parent historical stratum ranking, then filter relatives.
    candidates_all = [r for r in original.itertuples() if r.stratum == target.stratum
                      and pd.notna(r.sire_id) and pd.notna(r.dam_id)
                      and r.sire_id != "" and r.dam_id != ""]
    full = sorted(candidates_all, key=digest)
    if k == 0:
        return 0.
    payload = json.dumps(["keiba-unrelated-start-v1",int(seed),int(cutoff_year),
                          target.stratum,target.horse], ensure_ascii=False,
                         separators=(",",":")).encode("utf8")
    start = int.from_bytes(hashlib.sha256(payload).digest()[:8],"big") % len(full)
    picked = []
    for j in range(len(full)):
        r = full[(start+j)%len(full)]
        if r.horse != target.horse and r.sire_id != target.sire_id and r.dam_id != target.dam_id:
            picked.append(r)
        if len(picked) == k:
            break
    if len(picked) != k:
        raise ValueError("oracle-too-few")
    own = len(history[history.horse == target.horse])
    return 5/(own+5) * sum(r.score for r in picked)/(8+k)


class UnrelatedControlTests(unittest.TestCase):
    def test_all_32_against_independent_oracle_and_same_k_for_both_parents(self):
        h,t=example()
        base=balanced.prepare_peer_block(h,t,cutoff_year=2022)
        block=control.prepare_unrelated_block(h,t,base,cutoff_year=2022)
        self.assertEqual(base.k.tolist(),[2,3,0,0])
        for seed in range(2026112200,2026112232):
            performance=control.unrelated_performance(block,seed=seed)
            expected=[oracle(h,row,int(k),seed) for row,k in zip(t.itertuples(),base.k)]
            np.testing.assert_allclose(performance.iloc[:,0],expected,atol=1e-15,rtol=0)
            np.testing.assert_array_equal(performance.iloc[:,0],performance.iloc[:,1])

    def test_permutation_target_subset_and_outcome_independence(self):
        h,t=example()
        seed=2026112201
        b=balanced.prepare_peer_block(h,t,cutoff_year=2022)
        baseline=control.unrelated_performance(
            control.prepare_unrelated_block(h,t,b,cutoff_year=2022),seed=seed)
        order=[1,0,3,1,2,0]
        h2=h.sample(frac=1,random_state=8)
        t2=t.iloc[order]
        b2=balanced.prepare_peer_block(h2,t2,cutoff_year=2022)
        result=control.unrelated_performance(
            control.prepare_unrelated_block(h2,t2,b2,cutoff_year=2022),seed=seed)
        pd.testing.assert_frame_equal(result,baseline.iloc[order].reset_index(drop=True))
        h3=h.copy()
        h3.loc[h3.horse.eq("focal"),"y"]=1.
        b3=balanced.prepare_peer_block(h3,t,cutoff_year=2022)
        alt=control.unrelated_performance(
            control.prepare_unrelated_block(h3,t,b3,cutoff_year=2022),seed=seed)
        np.testing.assert_allclose(baseline.loc[0].values,alt.loc[0].values,atol=1e-15,rtol=0)

    def test_known_nonkin_support_exhaustion_is_hard_hold(self):
        h,t=example()
        h.loc[h.horse.str.startswith("unrelated"),"sire_id"]="dad"
        t=t.iloc[[0]]
        b=balanced.prepare_peer_block(h,t,cutoff_year=2022)
        u=control.prepare_unrelated_block(h,t,b,cutoff_year=2022)
        for seed in (2026112200,2026112231):
            with self.assertRaisesRegex(ValueError,"HOLD_TOO_FEW_UNRELATED_PEERS"):
                control.unrelated_performance(u,seed=seed)

    def test_no_unknown_historical_parents_accepted(self):
        h,t=example()
        h.loc[h.horse.eq("neutral"),["sire_id","dam_id"]]=None
        b=balanced.prepare_peer_block(h,t,cutoff_year=2022)
        u=control.prepare_unrelated_block(h,t,b,cutoff_year=2022)
        for seed in (2026112200,2026112219):
            expected=oracle(h,t.iloc[0],int(b.k[0]),seed)
            np.testing.assert_allclose(control.unrelated_performance(u,seed=seed).iloc[0,0],
                                       expected,atol=1e-15,rtol=0)

    def test_refuses_misaligned_history_mappings_and_context(self):
        h,t=example()
        base=balanced.prepare_peer_block(h,t,cutoff_year=2022)
        for source,history,target in [
            (base,h.iloc[1:],t), (base,h,t.iloc[1:]),
            (base,h,t.assign(stratum="dirt:4")), (base,h,t.assign(horse="changed")),
        ]:
            with self.assertRaises(ValueError):
                control.prepare_unrelated_block(history,target,source,cutoff_year=2022)
        with self.assertRaises(ValueError):
            control.prepare_unrelated_block(h,t,object(),cutoff_year=2022)

    def test_no_target_outcome_needed_and_no_prediction_ensemble(self):
        h,t=example()
        self.assertNotIn("y",t)
        base=balanced.prepare_peer_block(h,t,cutoff_year=2022)
        u=control.prepare_unrelated_block(h,t,base,cutoff_year=2022)
        for seed in (2026112200,2026112201):
            self.assertEqual(list(control.unrelated_performance(u,seed=seed)),list(ablation.PERFORMANCE))
        tbad=t.assign(y=1)
        with self.assertRaises(ValueError):
            balanced.prepare_peer_block(h,tbad,cutoff_year=2022)


if __name__=="__main__":
    unittest.main()
