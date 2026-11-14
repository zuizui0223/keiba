"""Evidence-ledger invariants for the actual large article-source analysis.

These are pinned REAL source-conditioned counts, not national population rates.
"""
from __future__ import annotations
import json
from pathlib import Path
import unittest

DATA=Path(__file__).resolve().parents[1]/"docs"/"evidence"/"japan-wikipedia-actual-kinship-20261114.json"

class JapaneseWikipediaLargeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x=json.loads(DATA.read_text(encoding="utf-8"))

    def test_fixed_source_attribution_cannot_disappear(self):
        x=self.x
        self.assertEqual(x["status"],"REAL_SOURCE_CONDITIONAL_ALL_WITHIN_ARTICLE_PAIRS_NOT_FULL_JRA_NAR")
        self.assertEqual(len(x["provenance"]["input_sha256"]),64)
        self.assertIn("CC BY-SA",x["provenance"]["license"])
        self.assertIn("Sheep Meadow Road Games",x["provenance"]["upstream_credit"])
        self.assertTrue(any("not representative" in s or "not all" in s.lower()
                            for s in x["interpretation_limits"]))

    def test_exact_full_and_japan_subsets_reconcile(self):
        for name,item in self.x["subsets"].items():
            n=item["registered_horses"]
            self.assertEqual(item["scored_pairs"],n*(n-1)//2)
            self.assertEqual(item["scored_pairs"],
                             item["nonzero_known_path_pairs"]+item["zero_or_unresolved_path_pairs"])
            self.assertEqual(sum(item["A_bins"].values()),item["nonzero_known_path_pairs"])
            self.assertLessEqual(item["documented_dam_links"],n)
            self.assertLessEqual(item["documented_sire_links"],n)
            self.assertLessEqual(item["both_sire_and_dam"],
                                 min(item["documented_dam_links"],item["documented_sire_links"]))
        all_=self.x["subsets"]["japanese_language_horse_articles"]
        jp=self.x["subsets"]["explicitly_japan_born_according_to_infobox_country"]
        self.assertEqual(all_["registered_horses"],5878)
        self.assertEqual(jp["registered_horses"],3411)
        self.assertGreater(all_["scored_pairs"],jp["scored_pairs"])
        self.assertGreater(all_["nonzero_known_path_pairs"],jp["nonzero_known_path_pairs"])

    def test_meisho_name_sample_not_genetic_family(self):
        a=self.x["subsets"]["japanese_language_horse_articles"]
        n=a["source_meisho_named_articles"]
        self.assertEqual(n,38)
        self.assertLessEqual(a["known_positive_pairs_among_meisho_named"],n*(n-1)//2)
        self.assertLessEqual(a["known_positive_cross_meisho_non_meisho"],
                             n*(a["registered_horses"]-n))


if __name__=="__main__":
    unittest.main()
