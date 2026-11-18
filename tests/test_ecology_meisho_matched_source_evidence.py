"""Safeguards for frozen actual Wikipedia Meisho matched-control evidence.

Real source-conditioned ARTICLE sample, NOT JRA/NAR population or genetic
causation. Unit tests protect denominators, drift notes, and citations.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest

PATH=(Path(__file__).resolve().parents[1]/
      "docs/evidence/japan-meisho-coverage-matched-kinship-20261114.json")


class RealMeishoMatchedSourceLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=json.loads(PATH.read_text(encoding="utf-8"))

    def test_denominators_and_drift_are_explicit(self):
        j=self.result
        self.assertEqual(j["status"],
                         "SOURCE_CONDITIONAL_REAL_MEISHO_NAME_GROUP_MATCHED_PEDIGREE_DIAGNOSTIC")
        a=j["selection_and_support"]
        self.assertEqual(a["total_source_articles"],5879)
        self.assertEqual(a["named_meisho_articles"],38)
        self.assertEqual(a["candidate_non_meisho_articles"],5841)
        self.assertEqual(a["matched_strata_count"],10)
        self.assertFalse(a["insufficient_strata"])
        self.assertEqual(j["random_control_groups"],999)
        self.assertFalse(j["matches_historical_reference_sha"])
        self.assertNotEqual(j["source_sha256"],j["historical_reference_source_sha"])
        self.assertEqual(len(j["source_sha256"]),64)

    def test_matched_descriptive_numbers_not_recast_as_genetic_p(self):
        j=self.result
        comp=j["results"]["both_available_parents"]
        controls=comp["mean_partial_A_matched_reference"]
        self.assertEqual(comp["observed"]["pairs"],703)
        self.assertEqual(comp["observed"]["positive_known_path_pairs"],311)
        self.assertEqual(comp["observed"]["A_at_least_0_125_pairs"],10)
        self.assertGreater(controls["random_set_mean"],0)
        self.assertGreaterEqual(controls["random_set_95pct"],
                                comp["observed"]["mean_partial_A"])
        self.assertLessEqual(controls["random_set_5pct"],
                             comp["observed"]["mean_partial_A"])
        self.assertTrue(controls["descriptive_diagnostic_NOT_a_genetic_p_value"])
        self.assertGreater(controls["fraction_random_sets_at_least_observed"],0)
        self.assertLess(controls["fraction_random_sets_at_least_observed"],1)
        self.assertGreater(comp["A_at_least_0_125_pairs_matched_reference"]["random_set_mean"],
                           comp["observed"]["A_at_least_0_125_pairs"])
        self.assertEqual(j["results"]["sire_only"]["observed"]["pairs"],703)

    def test_three_reproductions_are_same_fixed_source(self):
        j=self.result
        r=j["reproduction"]
        self.assertTrue(r["same_source_sha256_on_independent_actions"])
        self.assertEqual(len(r["confirmed_runs"]),3)
        self.assertIn("not biological replication",r["note"])
        self.assertIn("Sheep Meadow Road Games",j["credit"])
        self.assertTrue(j["same_pair_count_all_models"])


if __name__=="__main__":
    unittest.main()
