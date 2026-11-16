"""Synthetic only: source-locked parental placebo controls (no race source rows)."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_japan_2022_independent_forward import (
    FEATURE_KIN, make_common_features
)
from ecology_japan_2022_parent_placebo import (
    profile_history, shuffle_parent_pairs, with_parent_map
)


def mock_history():
    rows = []
    for i in range(8):
        for year in (2018, 2019, 2020):
            rows.append({
                "horse": str(i),
                "stratum": "turf:4" if year != 2019 else "dirt:4",
                "day": pd.Timestamp(year, 1, 3),
                "year": year,
                "y": float((i + year) % 7) / 7,
                "sire_id": "S" + str(i // 2) if i != 7 else "",
                "dam_id": "D" + str(i // 3) if i != 7 else "",
                "surface": "dirt" if year == 2019 else "turf",
                "distance": 1600,
            })
    return pd.DataFrame(rows)


def mock_target(history):
    t = history[history.year == 2020].copy()
    t["day"] = pd.Timestamp("2022-01-10")
    t["year"] = 2022
    return t.reset_index(drop=True)


def dummy_parent_table(n=12):
    return pd.DataFrame({
        "horse": [str(i) for i in range(n)],
        "sire_id": ["S" + str(i // 2) for i in range(n)],
        "dam_id": ["D" + str(i // 2) for i in range(n)],
        "birth_bin": [400] * n,
        "circuit": ["JRA"] * n,
        "sire_known": [True] * n,
        "dam_known": [True] * n,
    })


class ParentPlaceboTests(unittest.TestCase):

    def test_preaggregation_is_exactly_equal_to_original_true_parent_features(self):
        h = mock_history()
        f = mock_target(h)
        base = make_common_features(h, f)
        p = h[["horse", "sire_id", "dam_id"]].drop_duplicates()
        mapping = p.set_index("horse")
        same = with_parent_map(profile_history(h), f, base, mapping)
        for key in FEATURE_KIN:
            np.testing.assert_allclose(
                same[key].to_numpy(float), base[key].to_numpy(float),
                atol=1e-11, rtol=1e-11,
                err_msg=f"Mismatch {key}",
            )

    def test_exact_missingness_and_complete_sire_dam_pair_counts_preserved(self):
        p = dummy_parent_table()
        p.loc[0, ["dam_id", "dam_known"]] = ["", False]
        p.loc[1, ["dam_id", "dam_known"]] = ["", False]
        p.loc[2, ["sire_id", "sire_known"]] = ["", False]
        p.loc[3, ["sire_id", "sire_known"]] = ["", False]
        a, meta = shuffle_parent_pairs(p, 2026111601)
        self.assertEqual(meta["horses_total"], len(p))
        self.assertTrue((a.sire_id.ne("").to_numpy() ==
                         p.sire_known.to_numpy()).all())
        self.assertTrue((a.dam_id.ne("").to_numpy() ==
                         p.dam_known.to_numpy()).all())
        self.assertEqual(
            sorted(zip(a.sire_id, a.dam_id)),
            sorted(zip(p.sire_id, p.dam_id))
        )

    def test_same_seed_reproducible_and_changes_parent_labels(self):
        p = dummy_parent_table()
        x, sx = shuffle_parent_pairs(p, 2026111601)
        y, sy = shuffle_parent_pairs(p, 2026111601)
        pd.testing.assert_frame_equal(x, y)
        self.assertEqual(sx, sy)
        self.assertGreater(sx["fraction_sire_ID_changed"], .2)

    def test_single_horse_cannot_make_own_relative_history(self):
        h = mock_history()
        h = h[h.horse == "0"]
        t = mock_target(h)
        base = make_common_features(h, t)
        parent_map = h[["horse", "sire_id", "dam_id"]].drop_duplicates()
        q = with_parent_map(
            profile_history(h), t, base, parent_map.set_index("horse")
        )
        self.assertEqual(float(q["sire_kin_history"].iloc[0]), 0.0)
        self.assertEqual(float(q["dam_kin_history"].iloc[0]), 0.0)
        self.assertEqual(float(q["log_sire_relative_count"].iloc[0]), 0.0)

    def test_unknown_parent_pairs_do_not_create_artificial_relatives(self):
        h = mock_history().copy()
        h["sire_id"] = ""
        h["dam_id"] = ""
        t = mock_target(h)
        base = make_common_features(h, t)
        mapping = h[["horse", "sire_id", "dam_id"]].drop_duplicates()
        q = with_parent_map(
            profile_history(h), t, base, mapping.set_index("horse")
        )
        self.assertTrue((q["sire_kin_history"] == 0).all())
        self.assertTrue((q["dam_kin_history"] == 0).all())

    def test_missing_horse_mapping_is_hold_not_zero_relation(self):
        h = mock_history()
        t = mock_target(h)
        base = make_common_features(h, t)
        mapping = h[["horse", "sire_id", "dam_id"]].drop_duplicates()
        mapping = mapping[mapping.horse != "0"].set_index("horse")
        with self.assertRaisesRegex(ValueError, "MAPPING_INCOMPLETE"):
            with_parent_map(profile_history(h), t, base, mapping)

    def test_sham_requires_known_valid_columns(self):
        with self.assertRaisesRegex(ValueError, "MISSING_PARENT_SHUFFLE_COLUMNS"):
            shuffle_parent_pairs(
                pd.DataFrame({"horse": ["A"]}), 2026111600
            )


if __name__ == "__main__":
    unittest.main()
