"""Small REAL source-cited pedigree FACTS tests; NO race outcomes or predictions."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ecology_japan_meisho_audit import summarize

FIXTURE = ROOT / "docs/evidence/japan-meisho-manual-profile-snapshot-20261114.json"


class MeishoRegistryAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_verified_subset_finds_kin_across_names_and_owners(self):
        result = summarize(self.data)
        self.assertEqual(result["status"], "REAL_PUBLIC_PEDIGREE_FACTS_AUDITED_NOT_PREDICTIVE_RESULT")
        counts = result["counts"]
        self.assertEqual(counts["profiles"], 11)
        self.assertEqual(counts["names_with_meisho_prefix"], 9)
        self.assertEqual(counts["other_name_profiles"], 2)
        self.assertEqual(counts["distinct_displayed_owners"], 4)
        self.assertEqual(counts["manually_linked_dams"], 6)
        self.assertEqual(counts["same_dam_different_sire_pairs"], 3)
        self.assertEqual(counts["same_dam_pairs_with_name_prefix_difference"], 1)
        self.assertEqual(counts["same_dam_pairs_with_displayed_owner_difference"], 2)
        self.assertEqual(counts["documented_nonzero_dam_path_pairs"], 13)
        self.assertTrue(counts["owner_disagreement_within_meisho_named_profiles"])
        self.assertFalse(result["real_future_prediction_or_heritability_estimated"])

    def test_concrete_maternal_pairs_have_different_sires(self):
        result = summarize(self.data)
        edges = {
            frozenset(x["pair"]):x for x in result["known_shared_dam_different_sire_examples"]
        }
        self.assertEqual(set(edges), {
            frozenset(("メイショウタバル","メイショウメイスイ")),
            frozenset(("メイショウツバクロ","メイショウカンパク")),
            frozenset(("メイショウハリオ","テーオーロイヤル")),
        })
        self.assertFalse(edges[frozenset(("メイショウハリオ","テーオーロイヤル"))]["same_name_prefix"])
        self.assertAlmostEqual(edges[frozenset(("メイショウタバル","メイショウメイスイ"))]["minimal_pedigree_expected_A"],0.25)
        deep = {
            frozenset(x["pair"]):x["documented_dam_only_A"]
            for x in result["documented_dam_path_relationships"]
        }
        self.assertAlmostEqual(deep[frozenset(("メイショウタバル","メイショウカンパク"))],0.125)
        self.assertAlmostEqual(deep[frozenset(("メイショウツバクロ","メイショウタバル"))],0.5)

    def test_same_prefix_without_known_path_must_not_infer_unrelated(self):
        result = summarize(self.data)
        positives = {frozenset(x["pair"]) for x in result["documented_dam_path_relationships"]}
        self.assertNotIn(frozenset(("メイショウサムソン","メイショウタバル")),positives)
        self.assertTrue(result["unlinked_pairs_are_NOT_classified_as_genetically_unrelated"])

    def test_reject_forged_mother_ids_or_source_urls(self):
        b=deepcopy(self.data)
        b["profiles"][0]["dam_jbis_id"]="0000760084"
        with self.assertRaisesRegex(ValueError,"MOTHER_NAME_AND_ID_DISAGREE"):
            summarize(b)
        c=deepcopy(self.data)
        c["profiles"][0]["profile_url"]="https://fake.example/malicious"
        with self.assertRaisesRegex(ValueError,"SOURCE_URL"):
            summarize(c)

    def test_reject_broken_id_and_duplicate_without_name_based_fallback(self):
        b=deepcopy(self.data)
        b["profiles"][0]["jbis_id"]="メイショウタバル"
        with self.assertRaisesRegex(ValueError,"INVALID_OR_DUPLICATE_JBIS_ID"):
            summarize(b)
        c=deepcopy(self.data)
        c["profiles"].append(deepcopy(c["profiles"][0]))
        with self.assertRaisesRegex(ValueError,"INVALID_OR_DUPLICATE_JBIS_ID"):
            summarize(c)


if __name__=="__main__":
    unittest.main()
