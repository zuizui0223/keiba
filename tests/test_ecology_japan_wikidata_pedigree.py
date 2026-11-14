"""Completely offline tests of scoped Wikidata-QID source handling."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_wikidata_pedigree import (
    normalize, ancestor_query, source_report,
)


def b(q):
    return {"type":"uri","value":"http://www.wikidata.org/entity/"+q}


class JapaneseWikidataPilotTests(unittest.TestCase):
    def test_qid_only_parent_and_conflicts_rejected(self):
        a=normalize([
            {"horse":b("Q100"),"father":b("Q1"),"mother":b("Q2")},
            {"horse":b("Q101"),"father":b("Q1")},
        ])
        self.assertEqual(a["Q100"]["sire_id"],"Q1")
        self.assertEqual(a["Q101"]["dam_id"],"")
        with self.assertRaisesRegex(ValueError,"CONFLICTING_PARENTS"):
            normalize([
                {"horse":b("Q100"),"father":b("Q1")},
                {"horse":b("Q100"),"father":b("Q3")},
            ])
        with self.assertRaisesRegex(ValueError,"NON_QID"):
            normalize([{"horse":{"value":"https://evil.invalid/horse"}}])

    def test_small_secondary_source_produces_measured_partial_pedigree_counts(self):
        def data(query):
            if "ORDER BY ?horse" in query:
                return [
                    {"horse":b("Q101"),"father":b("Q201"),"mother":b("Q301")},
                    {"horse":b("Q102"),"father":b("Q201"),"mother":b("Q302")},
                    {"horse":b("Q103"),"father":b("Q202"),"mother":b("Q301")},
                ]
            self.assertIn("VALUES ?horse",query)
            return [{"horse":b(q)} for q in ("Q201","Q202","Q301","Q302")]
        with patch("ecology_japan_wikidata_pedigree.source_get",side_effect=data):
            output=source_report(max_targets=10,ancestor_generations=2,max_requests=10)
        self.assertEqual(output["status"],
                         "REAL_CC0_WIKIDATA_SECONDARY_PEDIGREE_SUBSET_NOT_JAPAN_COMPLETE")
        c=output["known_parentage"]
        self.assertEqual(c["target_horses"],3)
        self.assertEqual(c["pedigree_record_rows"],7)
        self.assertEqual(c["confirmed_paternal_half_pairs_both_dams_known_distinct"],1)
        self.assertEqual(c["confirmed_maternal_half_pairs_both_sires_known_distinct"],1)
        self.assertTrue(output["ancestry_complete_to_requested_depth"])
        self.assertFalse(output["seed_hits_limit"])
        self.assertEqual(output["exact_A_pair_check_first_100_QIDs"]["queries"],3)

    def test_failed_ancestor_fetch_preserves_direct_parentage(self):
        from urllib.error import HTTPError
        def data(q):
            if "ORDER BY ?horse" in q:
                return [
                    {"horse":b("Q101"),"father":b("Q201")},
                    {"horse":b("Q102"),"father":b("Q201")},
                ]
            raise HTTPError("https://query.wikidata.org/sparql",429,"limited",{},None)
        with patch("ecology_japan_wikidata_pedigree.source_get",side_effect=data):
            result=source_report(max_targets=10,ancestor_generations=3,max_requests=5)
        self.assertEqual(result["status"],
                         "REAL_CC0_WIKIDATA_SECONDARY_PEDIGREE_SUBSET_ANCESTOR_HOLD")
        self.assertEqual(result["ancestor_fetch_error"]["http_status_code"],429)
        self.assertEqual(result["known_parentage"]["target_horses"],2)
        self.assertEqual(result["known_parentage"]["shared_sire_target_pairs_including_unknown_other_parent"],1)
        self.assertEqual(result["exact_A_pair_check_first_100_QIDs"]["positive_documented_path_pairs"],1)
        self.assertFalse(result["ancestry_complete_to_requested_depth"])

    def test_source_failure_is_hold_not_an_actual_zero_relation(self):
        with patch("ecology_japan_wikidata_pedigree.source_get",
                   side_effect=TimeoutError("dummy")):
            output=source_report(max_targets=10,ancestor_generations=2)
        self.assertEqual(output["status"],"HOLD_WIKIDATA_SOURCE_REQUEST_FAILED")
        self.assertFalse(output["actual_horse_or_kin_counts_available"])

    def test_unsafe_breadth_blocked_without_network(self):
        with self.assertRaisesRegex(ValueError,"UNSAFE_PILOT_BOUNDS"):
            source_report(max_targets=20000)


if __name__=="__main__":
    unittest.main()
