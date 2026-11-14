"""Synthetic pedigree tests: removing maternal links must not create relatedness."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_wikipedia_parent_ablation import analyze,compare,strip_sex
from ecology_japan_wikipedia_large import prepare_infoboxes,PREFIX


def families():
    return {
        "S":{"生":"1990年","国":"アメリカ"},
        "T":{"生":"1990年","国":"日本"},
        "D":{"生":"1993年","国":"日本"},
        "E":{"生":"1993年","国":"日本"},
        "メイショウA":{"父":"[[S]]","母":"[[D]]","生":"2002年","国":"日本"},
        "メイショウB":{"父":"[[S]]","母":"[[E]]","生":"2003年","国":"日本"},
        "C":{"父":"[[T]]","母":"[[D]]","生":"2003年","国":"アメリカ"},
        "メイショウD":{"父":"[[S]]","母":"[[D]]","生":"2004年","国":"日本"},
    }


class PedigreeParentAblationTests(unittest.TestCase):
    def test_paternal_and_maternal_paths_are_noncausal_information_ablation(self):
        full,meta,_=prepare_infoboxes(families())
        sire=strip_sex(full,"sire")
        dam=strip_sex(full,"dam")
        horses=sorted(full.recorded)
        r=compare(full,sire,dam,horses)
        self.assertEqual(r["same_target_pairs"],28)
        self.assertGreater(r["counts"]["path_lost_if_mother_removed"],0)
        self.assertGreater(r["counts"]["A_increases_from_mother_links"],0)
        a,b,c,d=[PREFIX+x for x in ("メイショウA","メイショウB","C","メイショウD")]
        self.assertAlmostEqual(full.a(a,b),0.25)
        self.assertAlmostEqual(sire.a(a,b),0.25)
        self.assertAlmostEqual(dam.a(a,b),0)
        self.assertAlmostEqual(full.a(a,c),0.25)
        self.assertAlmostEqual(sire.a(a,c),0)
        self.assertAlmostEqual(dam.a(a,c),0.25)
        self.assertAlmostEqual(full.a(a,d),0.5)
        self.assertAlmostEqual(sire.a(a,d),0.25)
        self.assertAlmostEqual(dam.a(a,d),0.25)
        self.assertTrue(r["per_pair_genealogical_monotonicity_pass"])
        self.assertTrue(r["no_underlying_genetic_paternal_maternal_variance_estimated"])

    def test_paired_input_sha_and_real_data_scope_flag(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"fixture.json"
            path.write_text(json.dumps(families(),ensure_ascii=False),encoding="utf-8")
            from hashlib import sha256
            digest=sha256(path.read_bytes()).hexdigest()
            result=analyze(path,expected_source_sha=digest)
        self.assertTrue(result["matches_previous_source_sha"])
        self.assertEqual(result["source_horses"],8)
        self.assertEqual(result["cohorts"]["all_language_articles"]["same_target_pairs"],28)
        self.assertEqual(result["cohorts"]["meisho_named_articles"]["same_target_pairs"],3)
        self.assertGreater(result["source_dam_links"],0)
        decade=result["parent_data_completeness_by_foal_decade"]
        self.assertEqual(decade["2000s"]["meisho_name"],3)
        self.assertEqual(decade["2000s"]["both_parents"],4)
        self.assertIn("NOT_NATIONAL",result["status"])

    def test_budget_and_unknown_sex_rejected(self):
        full,_,_=prepare_infoboxes(families())
        a=strip_sex(full,"sire")
        b=strip_sex(full,"dam")
        r=compare(full,a,b,sorted(full.recorded),max_pairs=3)
        self.assertEqual(r["status"],"HOLD_PAIR_BUDGET")
        with self.assertRaisesRegex(ValueError,"INVALID_PARENT"):
            strip_sex(full,"unknown")


if __name__=="__main__":
    unittest.main()
