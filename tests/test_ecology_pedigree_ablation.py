"""No real-horse data: lineage ablations and confounding falsification tests."""
from __future__ import annotations
import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_pedigree_forward import Pedigree
from ecology_pedigree_ablation import split_type, audit
from ecology_pedigree_stress import fabricate, run


class KinAblationTests(unittest.TestCase):
    def test_exact_full_and_half_siblings(self):
        ancestors = {
            "S": (None, None), "D": (None, None),
            "S2": (None, None), "D2": (None, None),
            "A": ("S", "D"), "B": ("S", "D"),
            "PAT": ("S", "D2"), "MAT": ("S2", "D"),
            "PARENT_KNOWN_ONLY": ("S", None),
        }
        pedigree = Pedigree(ancestors)
        self.assertEqual(split_type(pedigree, "A", "B"), "full_siblings")
        self.assertEqual(split_type(pedigree, "A", "PAT"), "paternal_half_siblings")
        self.assertEqual(split_type(pedigree, "A", "MAT"), "maternal_half_siblings")
        self.assertEqual(split_type(pedigree, "A", "PARENT_KNOWN_ONLY"),
                         "other_related")

    def test_same_trainer_kin_blocks_cross_trainer_comparator(self):
        with tempfile.TemporaryDirectory() as td:
            x, p = fabricate(Path(td), "shared_trainer_only", 101)
            result = audit(x, p, min_horses=10)
        self.assertEqual(result["status"],
                         "EXPLORATORY_ABLATION_ONLY_NOT_GENETIC_CAUSATION")
        self.assertGreater(result["channels"]["paternal_half_siblings"]["exposed_unique_horses"], 0)
        self.assertEqual(result["channels"]["kin_different_trainer"]["exposed_unique_horses"], 0)
        self.assertGreater(result["channels"]["all_kin"]["exposed_unique_horses"], 0)
        self.assertFalse(result.get("biological_genetic_effect_estimated", False))
        self.assertNotIn("SYNTH-HORSE", str(result))

    def test_cross_trainer_kin_available_under_crossed_management(self):
        with tempfile.TemporaryDirectory() as td:
            x, p = fabricate(Path(td), "family_signal", 101)
            result = audit(x, p, min_horses=10)
        self.assertGreater(result["channels"]["kin_different_trainer"]["exposed_unique_horses"], 0)
        self.assertGreater(result["channels"]["kin_different_breeder"]["exposed_unique_horses"], 0)
        self.assertEqual(result["channels"]["maternal_half_siblings"]["exposed_unique_horses"], 0)

    def test_absent_trainer_column_emits_hold_not_misleading_zero(self):
        with tempfile.TemporaryDirectory() as td:
            x, p = fabricate(Path(td), "family_signal", 101)
            original = list(csv.DictReader(x.open()))
            for row in original:
                row.pop("trainer_id")
            with x.open("w", encoding="utf-8", newline="") as fd:
                writer = csv.DictWriter(fd, fieldnames=list(original[0]))
                writer.writeheader()
                writer.writerows(original)
            result = audit(x, p, min_horses=10)
        self.assertEqual(result["channels"]["kin_different_trainer"]["status"],
                         "HOLD_NO_TRAINER_ID")

    def test_synthetic_shared_trainer_null_can_mimic_genetic_signal(self):
        result = run(seeds=(101, 202))
        self.assertEqual(result["status"], "SYNTHETIC_IDENTIFIABILITY_STRESS_ONLY")
        self.assertFalse(result["biological_genetic_effect_estimated"])
        null = result["scenarios"]["shared_trainer_only"]
        self.assertGreater(null["mean_cold_start_kin_RMSE_gain_seconds"], 0)
        self.assertEqual(null["mean_cross_trainer_kin_exposed_horses"], 0)
        self.assertNotIn("SYNTH-HORSE", str(result))


if __name__ == "__main__":
    unittest.main()
