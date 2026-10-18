"""Repository cleanup must not silently change scientific or betting claims.

No real Racing Queensland horse records, JRA odds, live network requests
or betting probabilities are used by this suite.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from check_repository_navigation import (
    MANIFEST, NAVIGATION_DOCS,
    git_blob_sha, manifest_errors, markdown_errors,
    navigation_errors, repository_errors,
)


class ResearchFirstNavigationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index=json.loads((ROOT/MANIFEST).read_text(encoding="utf-8"))

    def test_all_real_repository_links_and_source_files_exist(self):
        self.assertEqual(repository_errors(ROOT),[])

    def test_separate_ecology_research_and_betting_track(self):
        self.assertEqual(self.index["primary_track"],"ecology")
        self.assertEqual(set(self.index["tracks"]),{"ecology","betting"})
        self.assertEqual(
            self.index["tracks"]["ecology"]["index"],"docs/research/README.md")
        self.assertEqual(
            self.index["tracks"]["betting"]["index"],"docs/betting/README.md")
        for path in NAVIGATION_DOCS:
            self.assertTrue((ROOT/path).is_file(),path)

    def test_archived_full_root_readme_not_lost_when_landing_shortened(self):
        archive=ROOT/self.index["legacy_full_readme"]
        self.assertGreater(len(archive.read_text(encoding="utf-8")),9000)
        self.assertLess(len((ROOT/"README.md").read_text(encoding="utf-8")),5000)
        self.assertIn("馬券",archive.read_text(encoding="utf-8"))
        self.assertIn("Research start here",(ROOT/"README.md").read_text(encoding="utf-8"))
        self.assertIn("ECOLOGY_RESEARCH.md",archive.read_text(encoding="utf-8"))

    def test_frozen_v31_classifier_hash_matches_unmodified_freeze(self):
        cfg=self.index["protected_frozen_v31"]
        git_sha=git_blob_sha((ROOT/cfg["classifier_path"]).read_bytes())
        freeze=json.loads(
            (ROOT/cfg["frozen_manifest_path"]).read_text(encoding="utf-8")
        )
        self.assertEqual(git_sha,cfg["expected_git_blob_sha_at_index_creation"])
        self.assertEqual(git_sha,freeze["frozen_blobs"]["classifier"])

    def test_individuality_not_promoted_to_causal_H1_H2(self):
        statuses={x["id"]:x["status"] for x in self.index["research_evidence"]}
        self.assertEqual(statuses["R2"],"OBSERVED_SOURCE_CONDITIONAL")
        self.assertEqual(statuses["R5"],"OBSERVED_NONTRANSFER")
        self.assertEqual(statuses["R6"],"HOLD_NONIDENTIFIABLE")
        self.assertEqual(statuses["R8"],"HOLD_NONIDENTIFIABLE")
        self.assertEqual(statuses["R9"],"SIMULATION_ONLY")
        matrix=(ROOT/"docs/research/EVIDENCE_MATRIX.md").read_text(encoding="utf-8")
        self.assertIn("0 shared",matrix)
        self.assertIn("H1",matrix)
        self.assertIn("H2",matrix)
        self.assertIn("SOURCE PROVENANCE",matrix)

    def test_missing_evidence_document_fails_navigation_gate(self):
        broken=copy.deepcopy(self.index)
        broken["research_evidence"][0]["primary_document"]="docs/missing-paper.pdf"
        errors=manifest_errors(broken,ROOT)
        self.assertTrue(any("missing indexed repository file" in x
                            for x in errors))

    def test_false_claim_promotion_is_rejected(self):
        for evidence_id in ("R6","R8"):
            fake=copy.deepcopy(self.index)
            row=next(x for x in fake["research_evidence"] if x["id"]==evidence_id)
            row["status"]="OBSERVED_SOURCE_CONDITIONAL"
            err=manifest_errors(fake,ROOT)
            self.assertTrue(any(evidence_id+" was silently promoted" in e
                                for e in err),err)

    def test_wrong_frozen_classifier_blob_is_rejected(self):
        fake=copy.deepcopy(self.index)
        fake["protected_frozen_v31"]["expected_git_blob_sha_at_index_creation"]="a"*40
        err=manifest_errors(fake,ROOT)
        self.assertTrue(any("FROZEN_V31_CLASSIFIER_SHA_CHANGED" in e for e in err))

    def test_dropping_betting_lane_cannot_hide_it_inside_ecology(self):
        fake=copy.deepcopy(self.index)
        fake["tracks"].pop("betting")
        errors=manifest_errors(fake,ROOT)
        self.assertIn(
            "research and betting must have exactly two separate tracks",
            errors,
        )

    def test_broken_and_escaping_markdown_links_are_detected(self):
        origin=ROOT/"docs/research/README.md"
        self.assertTrue(markdown_errors(
            "[bad](../missing_file_NOBODY.md)",origin,ROOT
        ))
        self.assertTrue(markdown_errors(
            "[bad](../../../outside-the-repo)",origin,ROOT
        ))
        self.assertFalse(markdown_errors(
            "[external](https://www.racingqueensland.com.au/)",origin,ROOT
        ))
        self.assertFalse(markdown_errors(
            "[local](EVIDENCE_MATRIX.md)",origin,ROOT
        ))

    def test_wrong_source_ecology_script_category_fails(self):
        fake=copy.deepcopy(self.index)
        fake["tracks"]["ecology"]["code_examples"][0]="scripts/v31_candidate_channels.py"
        err=manifest_errors(fake,ROOT)
        self.assertTrue(any("non-ecology model scripts" in x for x in err))

    def test_science_evidence_rows_have_distinct_IDS_and_statuses(self):
        identifiers=[v["id"] for v in self.index["research_evidence"]]
        self.assertEqual(len(identifiers),len(set(identifiers)))
        self.assertGreaterEqual(len(identifiers),11)
        duplicate=copy.deepcopy(self.index)
        duplicate["research_evidence"][0]["id"]="R6"
        self.assertTrue(any("duplicate or missing" in e
                            for e in manifest_errors(duplicate,ROOT)))

    def test_real_navigation_markdown_has_no_broken_repo_links(self):
        self.assertEqual(navigation_errors(ROOT),[])


if __name__=="__main__":
    unittest.main()
