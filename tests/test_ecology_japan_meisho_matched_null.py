"""Deterministic tests for real-source Meisho selection falsification.

Fixtures are invented horse identities. These tests are NOT actual genomic
Meisho estimates, regardless of a planted paternal signal.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from hashlib import sha256

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_meisho_matched_null import analyze,descriptor


def make_fixture(n_controls:int=7) -> dict:
    boxes={
        "S0":{"生":"1995年","国":"米国"},
    }
    for i in range(n_controls):
        boxes[f"SC{i}"]={"生":"1995年","国":"米国"}
    for i in range(3):
        boxes[f"メイショウ架空{i}"]={
            "父":"[[S0]]",
            "国":"日本","生":"2015年"
        }
    for i in range(n_controls):
        boxes[f"対照架空{i}"]={
            "父":f"[[SC{i}]]",
            "国":"日本","生":"2015年"
        }
    return boxes


class MeishoMatchedNullTests(unittest.TestCase):
    def test_exact_stratification_and_observed_relatives(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"input.json"
            src.write_text(json.dumps(make_fixture(),ensure_ascii=False),encoding="utf-8")
            expected=sha256(src.read_bytes()).hexdigest()
            report=analyze(src,n_random=39,expected_sha=expected)
        self.assertEqual(report["status"],
                         "SOURCE_CONDITIONAL_REAL_MEISHO_NAME_GROUP_MATCHED_PEDIGREE_DIAGNOSTIC")
        self.assertEqual(report["selection_and_support"]["named_meisho_articles"],3)
        self.assertEqual(report["selection_and_support"]["matched_strata_count"],1)
        observed=report["results"]["both_available_parents"]["observed"]
        self.assertEqual(observed["pairs"],3)
        self.assertEqual(observed["positive_known_path_pairs"],3)
        self.assertAlmostEqual(observed["mean_partial_A"],0.25)
        controls=report["results"]["both_available_parents"]["positive_known_path_pairs_matched_reference"]
        self.assertEqual(controls["random_set_mean"],0.0)
        self.assertEqual(controls["fraction_random_sets_at_least_observed"],0.0)
        self.assertTrue(controls["descriptive_diagnostic_NOT_a_genetic_p_value"])
        self.assertTrue(report["expected_sha_matches"])
        self.assertNotIn("架空",str(report))

    def test_mismatched_source_sha_is_hold_before_data_model(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"input.json"
            src.write_text(json.dumps(make_fixture(),ensure_ascii=False))
            report=analyze(src,n_random=19,expected_sha="0"*64)
        self.assertEqual(report["status"],
                         "HOLD_SOURCE_SHA_CHANGED_CANNOT_COMPARE_FIXED_BASELINE")
        self.assertFalse(report["matched_analysis_performed"])

    def test_drifted_reference_is_reported_but_new_source_can_be_evaluated(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"input.json"
            src.write_text(json.dumps(make_fixture(),ensure_ascii=False))
            report=analyze(src,n_random=19,reference_sha="0"*64)
        self.assertEqual(report["status"],
                         "SOURCE_CONDITIONAL_REAL_MEISHO_NAME_GROUP_MATCHED_PEDIGREE_DIAGNOSTIC")
        self.assertFalse(report["matches_historical_reference_sha"])
        self.assertIsNone(report["expected_sha_matches"])
        self.assertEqual(report["random_control_groups"],19)

    def test_insufficient_comparable_control_horses(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"input.json"
            src.write_text(json.dumps(make_fixture(n_controls=2),ensure_ascii=False))
            report=analyze(src,n_random=19)
        self.assertEqual(report["status"],
                         "HOLD_INSUFFICIENT_EXACT_BIRTH_DECADE_AND_PARENTS_MATCHING_SUPPORT")
        self.assertEqual(len(report["audit"]["insufficient_strata"]),1)
        self.assertTrue(report["biology_or_heritability_NOT_tested"])
        self.assertNotIn("results",report)

    def test_unsupported_random_count_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"input.json"
            src.write_text("{}")
            with self.assertRaisesRegex(ValueError,"PERMUTATION_COUNT"):
                analyze(src,n_random=5)


if __name__=="__main__":
    unittest.main()
