"""Fictional, direct-filter oracle for the locked equal-peer sampler."""
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ecology_japan_2022_24_family_feature_ablation as original
import ecology_japan_balanced_parent_history as peers


def digest(seed, cutoff, stratum, horse):
    payload = json.dumps(["keiba-equal-peer-v1", seed, cutoff, stratum, horse],
                         ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).digest()


def frames():
    family = [(f"peer-{c}", "s", "d" if c < "d" else f"dam-{c}") for c in "abcdefg"]
    family += [("他|馬", "other", "d"), ("unknown", "", "")]
    rows = [(h, s, d, "turf:4", i / 8) for i, (h, s, d) in enumerate(family)]
    rows += [("peer-a", "s", "d", "dirt:3", .3),
             ("peer-b", "s", "d", "turf:4", .875)]  # b averages to a neutral .5
    h = pd.DataFrame(rows, columns=["horse", "sire_id", "dam_id", "stratum", "y"])
    h["day"] = pd.date_range("2021-01-01", periods=len(h))
    targets = family + [("new", "s", "d"), ("smaller_sire", "other", "d"),
                        ("missing", "s", None), ("same", "other", "dam-g")]
    t = pd.DataFrame(targets, columns=["horse", "sire_id", "dam_id"]).assign(stratum="turf:4")
    t = pd.concat([t, t.iloc[[0]], t.iloc[[0]].assign(stratum="dirt:3")], ignore_index=True)
    t["surface"] = t.stratum.str.split(":").str[0]
    t["distance"] = np.where(t.surface.eq("turf"), 1600, 1200)
    t["day"] = pd.date_range("2024-01-01", periods=len(t))
    t["year"] = 2024
    return h, t[original.CONTEXT]


def oracle(history, target, seed):
    own = sum(history.horse == target.horse)
    pools = []
    for side in ("sire_id", "dam_id"):
        parent = getattr(target, side)
        pool = {}
        for row in history.itertuples():
            if (parent and getattr(row, side) == parent and row.stratum == target.stratum
                    and row.horse != target.horse):
                pool.setdefault(row.horse, []).append(row.y)
        pools.append(pool)
    k = min(map(len, pools))
    sums = []
    for pool in pools:
        ordered = sorted(pool, key=lambda h: (digest(seed, 2022, target.stratum, h), h))
        sums.append(math.fsum(math.fsum(pool[h])/len(pool[h]) - .5 for h in ordered[:k]))
    return [len(pool) for pool in pools], own, [5/(own+5)*s/(8+k) for s in sums]


class SamplerTests(unittest.TestCase):
    def test_golden_hash_and_unicode_encoding(self):
        self.assertEqual(peers.peer_priority(2026112200, 2022, "turf:4", "peer-a").hex(),
                         "6114d9dd86abf438839553522f6e974631e97a4822732a80351ebc8416c76c14")
        self.assertEqual(peers.peer_priority(2026112201, 2022, "芝:4", "馬|a"),
                         digest(2026112201, 2022, "芝:4", "馬|a"))

    def test_all_draws_against_scalar_oracle_and_legacy_smaller_side(self):
        h, t = frames()
        block = peers.prepare_peer_block(h, t, cutoff_year=2022)
        legacy = original.make_common_features(h, t.fillna(""))
        counts = ["sire_relative_count", "dam_relative_count"]
        np.testing.assert_array_equal(block.counts, legacy[counts])
        self.assertEqual(list(block.counts), counts)
        for seed in range(2026112200, 2026112232):
            expect = [oracle(h, r, seed) for r in t.itertuples()]
            perf = peers.balanced_performance(block, seed=seed)
            self.assertEqual(list(perf), list(original.PERFORMANCE))
            self.assertIsInstance(perf.index, pd.RangeIndex)
            np.testing.assert_array_equal(block.counts, [v[0] for v in expect])
            np.testing.assert_array_equal(block.k, [min(v[0]) for v in expect])
            np.testing.assert_array_equal(block.own_counts, [v[1] for v in expect])
            np.testing.assert_allclose(perf, [v[2] for v in expect], rtol=0, atol=1e-15)
            for side, col in zip(counts, original.PERFORMANCE):
                use = block.counts[side] == block.k
                np.testing.assert_allclose(perf.loc[use, col], legacy.loc[use, col], rtol=0, atol=1e-15)

    def test_focal_priority_boundaries_with_identical_k(self):
        h, t = frames()
        # Give each sire-pool horse two outside dam peers, so k=2 at every focal rank.
        h = h[h.horse.isin([f"peer-{c}" for c in "abcdefg"]) & h.stratum.eq("turf:4")].copy()
        h["dam_id"] = "m-" + h.horse
        focal = h.drop_duplicates("horse").copy()
        copies = [focal.assign(horse=focal.horse + tag, sire_id="outside", y=score)
                  for tag, score in [("-1", .2), ("-2", .7)]]
        h = pd.concat([h, *copies], ignore_index=True)
        t = t.iloc[:7].copy()
        t["dam_id"] = "m-" + t.horse
        block = peers.prepare_peer_block(h, t, cutoff_year=2022)
        np.testing.assert_array_equal(block.k, np.full(7, 2))
        seed = 2026112205
        np.testing.assert_allclose(peers.balanced_performance(block, seed=seed),
                                   [oracle(h, r, seed)[2] for r in t.itertuples()], atol=1e-15, rtol=0)

    def test_identical_pools_and_missing_parent_tokens(self):
        h, t = frames()
        h["dam_id"] = h.sire_id
        t["dam_id"] = t.sire_id
        for missing in (None, "  ", "000", "na", "－"):
            t.loc[t.horse.eq("unknown"), ["sire_id", "dam_id"]] = missing
            block = peers.prepare_peer_block(h, t, cutoff_year=2022)
            np.testing.assert_array_equal(block.counts.loc[t.horse.eq("unknown")], [[0, 0]])
            perf = peers.balanced_performance(block, seed=2026112200)
            np.testing.assert_array_equal(perf.iloc[:, 0], perf.iloc[:, 1])

    def test_shuffling_history_and_subsetting_2024_targets_preserves_values(self):
        h, t = frames()
        base = peers.prepare_peer_block(h, t, cutoff_year=2022)
        seed = 2026112211
        baseline = peers.balanced_performance(base, seed=seed)
        rows = [4, 0, len(t)-1, 4, 3, 0]
        subset = t.iloc[rows]
        actual = peers.prepare_peer_block(h.sample(frac=1, random_state=15), subset, cutoff_year=2022)
        pd.testing.assert_frame_equal(peers.balanced_performance(actual, seed=seed),
                                      baseline.iloc[rows].reset_index(drop=True))

    def test_bad_history_context_or_cutoff_rejected(self):
        h, t = frames()
        bad_inputs = [(h, t.assign(y=0)), (h, t.drop(columns="distance")), (h, t.iloc[:0]),
                      (h.iloc[:0], t), (h.assign(y=np.nan), t), (h.assign(y=1.01), t),
                      (h.assign(day=pd.NaT), t), (h.assign(day=20210101), t),
                      (h.assign(day="2022-01-01"), t), (h, t.assign(day="2021-12-31")),
                      (h, t.assign(horse="null")), (h.assign(stratum=" "), t),
                      (h, t.assign(year=2023)), (h, t.assign(dam_id="conflicting")),
                      (pd.concat([h, h.iloc[:1].assign(sire_id=None)]), t)]
        for i, (old, target) in enumerate(bad_inputs):
            with self.subTest(case=i), self.assertRaises(ValueError):
                peers.prepare_peer_block(old, target, cutoff_year=2022)

    def test_replacement_copies_only_performance_and_checks_positional_identity(self):
        h, t = frames()
        base = original.make_common_features(h, t.fillna(""))
        perf = peers.balanced_performance(peers.prepare_peer_block(h, t, cutoff_year=2022), seed=2026112200)
        original_base = base.copy()
        replaced = peers.replace_performance(base, perf)
        other = base.columns.difference(original.PERFORMANCE)
        pd.testing.assert_frame_equal(replaced[other], base[other])
        pd.testing.assert_frame_equal(replaced[list(original.PERFORMANCE)], perf)
        pd.testing.assert_frame_equal(base, original_base)
        for x, p in [(base, perf.iloc[::-1]), (base, perf.iloc[:-1]), (base, perf.assign(extra=1.)),
                     (base, perf.assign(dam_kin_history=np.inf)), (base.assign(own_mean=np.nan), perf),
                     (base.set_axis([0]*len(t)), perf.set_axis([0]*len(t)))]:
            with self.assertRaises(ValueError):
                peers.replace_performance(x, p)

    def test_entirely_unknown_side_including_categorical_history(self):
        h, t = frames()
        h["dam_id"] = pd.Categorical([None] * len(h), categories=["unused"])
        t["dam_id"] = "null"
        block = peers.prepare_peer_block(h, t, cutoff_year=2022)
        np.testing.assert_array_equal(block.counts.dam_relative_count, np.zeros(len(t)))
        np.testing.assert_array_equal(peers.balanced_performance(block, seed=2026112200),
                                      np.zeros((len(t), 2)))

    def test_invalid_optional_history_race_keys_and_invalid_context_are_rejected(self):
        h, t = frames()
        h["race"] = [f"r{i}" for i in range(len(h))]
        bad = [(pd.concat([h, h.iloc[:1]]), t), (h.assign(race="shared-across-days"), t),
               (h.assign(race=None), t), (h, t.assign(distance=np.nan)), (h, t.assign(surface=None))]
        for i, (history, target) in enumerate(bad):
            with self.subTest(case=i), self.assertRaises(ValueError):
                peers.prepare_peer_block(history, target, cutoff_year=2022)

    def test_changing_only_the_focals_historical_scores_never_changes_its_features(self):
        h, t = frames()
        t = t[t.horse.eq("peer-a")]
        old = peers.prepare_peer_block(h, t, cutoff_year=2022)
        h.loc[h.horse.eq("peer-a"), "y"] = 1.
        new = peers.prepare_peer_block(h, t, cutoff_year=2022)
        for seed in range(2026112200, 2026112232):
            np.testing.assert_allclose(peers.balanced_performance(new, seed=seed),
                                       peers.balanced_performance(old, seed=seed), atol=1e-15, rtol=0)


if __name__ == "__main__":
    unittest.main()
