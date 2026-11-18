"""Offline secondary Wikidata source crosscheck tests. No network access."""
from __future__ import annotations

from unittest.mock import patch
from urllib.error import HTTPError
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_wikimedia_parent_crosscheck import (
    parse_parent_claims,parse_pageprops,selection,run,
)


def claim(q):
    return {"rank":"normal","mainsnak":{
        "snaktype":"value","datavalue":{"value":{"entity-type":"item","id":q}}}}
def boxes():
    return {
        "メイショウ甲":{"父":"[[S]]","母":"母甲","生":"2019年","国":"日本"},
        "メイショウ乙":{"父":"[[S]]","母":"母乙","生":"2020年","国":"日本"},
        "普通丙":{"父":"[[S]]","母":"母丙","生":"2021年","国":"日本"},
        "S":{"生":"2005年","国":"アメリカ"},
        "D":{"生":"2010年","国":"日本"},
    }


class WikiWikidataParentTests(unittest.TestCase):
    def test_bounded_sample_prioritizes_meisho_and_missing_mother(self):
        c=selection(boxes(),limit=4)
        self.assertEqual(c[:2],["メイショウ乙","メイショウ甲"] if False else
                         sorted(["メイショウ甲","メイショウ乙"]))
        self.assertEqual(len(c),4)
        with self.assertRaisesRegex(ValueError,"SAMPLE_LIMIT"):
            selection(boxes(),limit=400)

    def test_direct_wikimedia_pages_are_only_accepted_when_exact_qids(self):
        data={"query":{"pages":{"1":{"title":"メイショウ甲","pageprops":{"wikibase_item":"Q101"}},
                                "2":{"title":"メイショウ乙","pageprops":{"wikibase_item":"Q102"}},
                                "3":{"title":"Missing","missing":True}}}}
        self.assertEqual(parse_pageprops(data),
                         {"メイショウ甲":"Q101","メイショウ乙":"Q102"})
        self.assertEqual(parse_parent_claims({"claims":{"P25":[claim("Q300")]}}, "P25"),"Q300")
        x={"claims":{"P25":[claim("Q300"),claim("Q301")]}}
        with self.assertRaisesRegex(ValueError,"MULTIPLE_PARENTS"):
            parse_parent_claims(x,"P25")

    def test_mother_claims_added_with_no_name_join_or_conflation(self):
        def fake_get(endpoint,params):
            if params["action"]=="query":
                names=params["titles"].split("|")
                return {"query":{"pages":{
                    str(i):{"title":t,"pageprops":{"wikibase_item":f"Q{200+i}"}}
                    for i,t in enumerate(names)
                }}}
            names=params["ids"].split("|")
            return {"entities":{
                q:{"claims":{"P22":[claim("Q900")],"P25":[claim("Q800")]}}
                for q in names
            }}
        with patch("ecology_japan_wikimedia_parent_crosscheck.json_get",side_effect=fake_get):
            result=run(boxes(),limit=3,batch=3,max_requests=6)
        self.assertEqual(result["status"],"SECONDARY_WIKIDATA_ACTUAL_PARENT_QIDS_PARTIAL_SAMPLE")
        self.assertEqual(result["sampled_titles"],3)
        self.assertEqual(result["Wikidata_documented_dam_claims"],3)
        self.assertEqual(result["within_same_sample_shared_dam_pairs"],3)
        self.assertGreater(result["additional_parent_claims_where_Wikipedia_infobox_missing"]["wikidata_dam_when_infobox_dam_missing"],0)
        self.assertTrue(result["source_conflicts_do_not_auto_overwrite_official_or_article_parents"])
        self.assertNotIn("Q800",str(result))

    def test_http_429_keeps_hold_not_false_missing_dam(self):
        def fake_get(endpoint,params):
            if params["action"]=="query":
                return {"query":{"pages":{
                    "1":{"title":params["titles"].split("|")[0],"pageprops":{"wikibase_item":"Q101"}}
                }}}
            raise HTTPError("https://www.wikidata.org/w/api.php",429,"slow",{},None)
        with patch("ecology_japan_wikimedia_parent_crosscheck.json_get",side_effect=fake_get):
            result=run(boxes(),limit=1,batch=1,max_requests=2)
        self.assertEqual(result["status"],"HOLD_NO_RETRIEVED_WIKIDATA_PARENT_DATA")
        self.assertEqual(result["requests_sent"],2)
        self.assertEqual(result["Wikidata_documented_dam_claims"],0)
        self.assertIn("HOLD_WIKIDATA_CLAIMS_HTTPError",result["failures"])

if __name__=="__main__":
    unittest.main()
