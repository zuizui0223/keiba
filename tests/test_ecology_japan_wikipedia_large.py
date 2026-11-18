"""Licensed-source Wikipedia pedigree parsing, quality and exact-A tests.

All fixtures are invented to avoid presenting code tests as real equine results.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_wikipedia_large import (
    prepare_infoboxes,canonical_title,analyze,all_pairs,PREFIX,
)


def fake():
    return {
        "メイショウA":{"父":"[[S]]","母":"[[D]]","国":"日本","生":"2004年1月1日","性":"牝"},
        "メイショウB":{"父":"[[S]]","母":"[[D2]]","国":"{{JPN}}","生":"2005年1月1日"},
        "C":{"父":"[[T]]","母":"[[D]]","国":"アメリカ","生":"2005年1月1日"},
        "S":{"国":"アメリカ","生":"1994年1月1日","性":"牡"},
        "D":{"国":"日本","生":"1997年1月1日","性":"牝"},
        "D2":{"国":"日本","生":"1997年1月1日","性":"牝"},
        "T":{"国":"アメリカ","生":"1994年1月1日","性":"牡"},
    }


class WikipediaPedigreeTests(unittest.TestCase):
    def test_parent_link_not_plain_name_or_multiple_links(self):
        self.assertEqual(canonical_title("[[Sunday Silence|SS]]"),"Sunday Silence")
        self.assertEqual(canonical_title("[[S]]"),"S")
        self.assertEqual(canonical_title("[[S]] + [[T]]"),None)
        self.assertIsNone(canonical_title("サンデーサイレンス"))
        self.assertIsNone(canonical_title("[[Category:Racehorses]]"))

    def test_strict_parent_page_id_and_related_pairs(self):
        ped,meta,_=prepare_infoboxes(fake())
        self.assertEqual(len(ped.recorded),7)
        self.assertAlmostEqual(ped.a(PREFIX+"メイショウA",PREFIX+"メイショウB"),.25)
        self.assertAlmostEqual(ped.a(PREFIX+"メイショウA",PREFIX+"C"),.25)
        self.assertAlmostEqual(ped.a(PREFIX+"メイショウA",PREFIX+"S"),.5)
        self.assertEqual(len(meta["japan_explicit_titles"]),4)
        self.assertEqual(len(meta["meisho_titles"]),2)
        full=all_pairs(ped,sorted(ped.recorded),{
            PREFIX+"メイショウA",PREFIX+"メイショウB"})
        self.assertEqual(full["pairs_scored"],21)
        self.assertGreater(full["documented_nonzero_path_pairs"],0)
        self.assertGreater(full["positive_pairs_meisho_to_other"],0)
        self.assertTrue(full["full_all_pairs_run_without_exporting_raw_wikipedia_articles"])

    def test_zero_path_means_unknown_not_unrelated(self):
        ped,meta,_=prepare_infoboxes(fake())
        self.assertEqual(ped.a(PREFIX+"S",PREFIX+"T"),0)
        report=all_pairs(ped,sorted(ped.recorded),set())
        self.assertGreater(report["pairs_without_known_path_not_unrelated"],0)
        self.assertEqual(all_pairs(ped,sorted(ped.recorded),set(),max_pairs=1)["status"],
                         "HOLD_ALL_PAIR_BUDGET_EXCEEDED")

    def test_impossible_ages_and_invalid_parent_identity(self):
        data=fake()
        data["メイショウA"]["父"]="[[S]]"
        data["S"]["生"]="2010年"
        ped,meta,_=prepare_infoboxes(data)
        self.assertEqual(ped.recorded[PREFIX+"メイショウA"][0],None)
        self.assertEqual(meta["link_rejections"]["父_implausible_parent_age"],2)
        data["C"]["母"]="[[C]]"
        ped,meta,_=prepare_infoboxes(data)
        self.assertEqual(ped.recorded[PREFIX+"C"][1],None)
        self.assertEqual(meta["link_rejections"]["母_self_parent"],1)

    def test_file_end_to_end_not_heritable_genetic_effect(self):
        with tempfile.TemporaryDirectory() as td:
            raw=Path(td)/"raw.json"
            raw.write_text(json.dumps(fake(),ensure_ascii=False),encoding="utf-8")
            result=analyze(raw,max_pairs=100)
        self.assertEqual(result["status"],
                         "REAL_JA_WIKIPEDIA_INFOBOXES_ANALYZED_NOT_ALL_JAPANESE_RACEHORSES")
        self.assertTrue(result["not_jra_or_nar_population"])
        self.assertEqual(result["data_quality"]["total_wikipedia_article_infoboxes"],7)
        self.assertEqual(result["all_japanese_language_articles"]["all_pairs"]["pairs_scored"],21)
        self.assertEqual(result["meisho_name_not_an_owner_or_bloodline"]["named_articles_total"],2)
        self.assertEqual(result["meisho_name_not_an_owner_or_bloodline"]["within_meisho_all_pairs"]["pairs_scored"],1)
        self.assertEqual(result["meisho_name_not_an_owner_or_bloodline"]["within_meisho_all_pairs"]["documented_nonzero_path_pairs"],1)
        self.assertTrue("0.25<=A<0.5" in result["meisho_name_not_an_owner_or_bloodline"]["within_meisho_all_pairs"]["partial_A_predeclared_bins"])
        self.assertTrue(result["unknown_parent_article_is_assumed_unrelated_FOUNDER_for_partial_A_only"])


if __name__=="__main__":
    unittest.main()
