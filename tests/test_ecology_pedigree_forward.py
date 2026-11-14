"""Offline, invented pedigree tests. Never substitute these for racehorse findings."""
from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
import random
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_pedigree_forward import (
    Pedigree, asof_pedigree, observations, pedigree_rows, screen,
    training_profile, predict, verify_dates,
)


def write_csv(path, rows, fields):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fictional_cohort(directory, *, pedigree_future=False, reverse_family_effect=False):
    rng = random.Random(612)
    obs, pedigree = [], []
    n_days = 20
    for family in range(6):
        sire = f"FAKE-SIRE-{family}"
        for child in range(10):
            horse = f"FAKE-HORSE-{family}-{child}"
            # 6 train entrants + 2 later in inner validation + 2 only in outer holdout
            entry_day = 0 if child < 6 else (12 if child < 8 else 17)
            dam = f"FAKE-DAM-{family}-{child}"
            pedigree.append({
                "horse_id": horse, "sire_id": sire, "dam_id": dam,
                "known_on": "2031-01-01" if pedigree_future else "1990-01-01",
            })
            horse_noise = rng.gauss(0, 0.025)
            sire_effect = 0.0 if reverse_family_effect else 0.22 * (family - 2.5)
            for day in range(entry_day, n_days):
                dt = date(2026, 1, 1) + timedelta(days=day)
                obs.append({
                    "horse_id": horse, "race_id": f"FAKE-RACE-{day}-{child % 3}",
                    "race_date": dt.isoformat(),
                    "venue": "FAKE-VENUE", "first_marker_m": "150",
                    "distance_m": "1200", "going": "Good",
                    "race_class": "FAKE-CLASS",
                    "early_section_s": f"{10 + sire_effect + horse_noise + rng.gauss(0, 0.07):.6f}",
                })
    path1 = Path(directory) / "fake_sectionals.csv"
    path2 = Path(directory) / "fake_pedigree.csv"
    write_csv(path1, obs, [
        "horse_id", "race_id", "race_date", "venue", "first_marker_m",
        "distance_m", "going", "race_class", "early_section_s",
    ])
    write_csv(path2, pedigree, ["horse_id", "sire_id", "dam_id", "known_on"])
    return path1, path2


class RelatednessAndForwardTests(unittest.TestCase):
    def test_parent_sib_relationships_and_inbreeding(self):
        a = Pedigree({
            "S": (None, None), "D": (None, None), "D2": (None, None),
            "A": ("S", "D"), "B": ("S", "D"),
            "HALF": ("S", "D2"), "INBRED": ("A", "B"),
        })
        self.assertAlmostEqual(a.relationship("A", "S"), 0.5)
        self.assertAlmostEqual(a.relationship("A", "B"), 0.5)
        self.assertAlmostEqual(a.relationship("A", "HALF"), 0.25)
        self.assertAlmostEqual(a.relationship("S", "D"), 0.0)
        self.assertAlmostEqual(a.relationship("INBRED", "INBRED"), 1.25)
        self.assertAlmostEqual(a.relationship("INBRED", "S"),
                               a.relationship("S", "INBRED"))

    def test_loop_and_conflicting_race_id_rejected(self):
        with self.assertRaisesRegex(ValueError, "PEDIGREE_CYCLE"):
            Pedigree({"A": ("B", None), "B": ("A", None)})
        with tempfile.TemporaryDirectory() as td:
            p1, _ = fictional_cohort(td)
            records = list(csv.DictReader(p1.open()))
            other = next(r for r in records if r["horse_id"] != records[0]["horse_id"]
                         and r["race_date"] == records[0]["race_date"])
            other["race_id"] = records[0]["race_id"]
            other["going"] = "Heavy"
            write_csv(p1, records, list(records[0]))
            with self.assertRaisesRegex(ValueError, "RACE_ID_CONTEXT_INCONSISTENT"):
                observations(p1)

    def test_forward_kin_adds_signal_in_cold_start_synthetic(self):
        with tempfile.TemporaryDirectory() as td:
            x, p = fictional_cohort(td)
            result = screen(x, p, permutations=19, min_horses=10)
        self.assertEqual(result["status"],
                         "EXPLORATORY_TIME_FORWARD_ASSOCIATION_NOT_HERITABILITY")
        self.assertGreater(result["tuned_only_on_earlier_dates_lambda"], 0)
        cold = result["rmse_equal_weight_per_horse"]["cold_start_kin_exposed"]
        self.assertGreaterEqual(cold["unique_horses"], 10)
        self.assertGreater(cold["M0_minus_M1_RMSE_gain_s"], 0)
        self.assertTrue(result["not_a_genetic_heritability_or_causal_inference"])
        self.assertNotIn("FAKE-SIRE", str(result))
        self.assertNotIn("FAKE-HORSE", str(result))

    def test_future_ancestry_cannot_contribute_to_test(self):
        with tempfile.TemporaryDirectory() as td:
            x, p = fictional_cohort(td, pedigree_future=True)
            result = screen(x, p, permutations=3, min_horses=10)
        self.assertEqual(result["tuned_only_on_earlier_dates_lambda"], 0.0)
        self.assertEqual(result["related_heldout_scored_horses"], 0)
        self.assertEqual(result["status"], "HOLD_TOO_FEW_RELATED_OUTER_HORSES")
        cohort = result["rmse_equal_weight_per_horse"]["all"]
        self.assertEqual(cohort["M0_RMSE_s"], cohort["M1_RMSE_s"])

    def test_outer_outcomes_cannot_change_pre_cutoff_predictions(self):
        with tempfile.TemporaryDirectory() as td:
            x, p = fictional_cohort(td)
            obs = observations(x)
            _, outer = verify_dates(obs)
            pedigree = asof_pedigree(pedigree_rows(p), outer)
            train = [r for r in obs if r["day"] < outer]
            future = next(r for r in obs if r["day"] >= outer)
            context, history = training_profile(train)
            prediction = predict(future, context, history, pedigree, 1)
            changed = {**future, "y": 200.0}
            prediction_after = predict(changed, context, history, pedigree, 1)
        self.assertAlmostEqual(prediction["base"], prediction_after["base"])
        self.assertAlmostEqual(prediction["kin"], prediction_after["kin"])


if __name__ == "__main__":
    unittest.main()
