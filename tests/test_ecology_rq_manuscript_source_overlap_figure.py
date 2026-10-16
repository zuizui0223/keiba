"""Source-frozen aggregate only Figure 2 falsification; NO individual horse rows."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from ecology_rq_manuscript_source_overlap_figure import (
    EVIDENCE, validate_evidence, overlap_figure,
)


class SourceOverlapManuscriptFigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=validate_evidence()

    def altered_should_fail(self,mutate):
        val=copy.deepcopy(self.original)
        mutate(val)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"altered_fake_metadata.json"
            p.write_text(json.dumps(val),encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_evidence(p)

    def test_real_source_incidence_and_artifact_hashes_are_frozen(self):
        a=self.original
        q=a["two_original_horizon_population_comparisons"][
            "same_150m_first_marker_and_official_race_distance"]
        self.assertEqual(q["individuals_with_2plus_distinct_source_dates_in_2025"],23)
        self.assertEqual(q["individuals_with_1plus_date_in_both_2025_and_2026"],26)
        self.assertEqual(q["individuals_with_2plus_dates_2025_and_1plus_date_2026"],0)
        self.assertEqual(q["individuals_with_2plus_dates_each_year"],0)
        self.assertEqual(a["locked_cohort"]["fetched_source_dates_successfully"],38)
        two=a["independent_original_source_replays"]
        self.assertEqual({x["actions_run_id"] for x in two},{38703717378,38703784178})
        self.assertEqual(len({x["anonymous_aggregate_json_sha256"] for x in two}),1)
        self.assertTrue(a["comparison"]["source_manifest_entries_all_equal_across_runs"])
        self.assertTrue(a["comparison"]["CANNOT_identify_within_horse_temporal_decay_or_age_effect"])

    def test_well_formed_figure_disjoint_eligible_population_not_ageing(self):
        a=overlap_figure(self.original)
        root=ET.fromstring(a)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("A common-horse test across time horizons is not estimable",a)
        self.assertIn("≥2 separate dates in 2025",a)
        self.assertIn("≥1 date in EACH year",a)
        self.assertIn("shared horses",a)
        self.assertIn("Scientific decision: HOLD",a)
        self.assertIn("NOT aging or loss of personality",a)
        self.assertIn("38 / 42",a)
        self.assertEqual(a,overlap_figure(self.original))
        for forbidden in ('"horse_id"', '"horse_name"', "Jockey/@Id", "REAL-HORSE-NAME",
                          '"trainer_license_id"', '"first_section_sec"'):
            self.assertNotIn(forbidden,a)

    def test_timing_outcomes_never_in_citable_evidence(self):
        t=EVIDENCE.read_text(encoding="utf-8")
        for forbidden in ('"horse_name"', '"horse_id":', '"jockey_license_id"',
                          '"trainer_license_id"', '"first_section_sec"'):
            self.assertNotIn(forbidden,t)
        self.assertIn("ANONYMOUS_ORIGINAL_SOURCE_IDENTIFIABILITY_AUDIT",t)

    def test_fictional_nonzero_shared_horses_invalidates_result(self):
        self.altered_should_fail(
            lambda q:q["two_original_horizon_population_comparisons"][
                "same_150m_first_marker_and_official_race_distance"
            ].__setitem__("individuals_with_2plus_dates_2025_and_1plus_date_2026",1)
        )

    def test_fictional_source_coverage_change_fails(self):
        self.altered_should_fail(
            lambda q:q["locked_cohort"].__setitem__("fetched_source_dates_successfully",42)
        )

    def test_fictional_discordant_source_artifact_hash_fails(self):
        self.altered_should_fail(
            lambda q:q["independent_original_source_replays"][1].__setitem__(
                "anonymous_aggregate_json_sha256","0"*64
            )
        )

    def test_missing_HOLD_or_Class_exclusion_fails(self):
        self.altered_should_fail(
            lambda q:q["two_original_horizon_population_comparisons"][
                "add_exact_original_race_Class"
            ].__setitem__("scientific_status","SUPPORTED_CROSS_YEAR_AGE_EFFECT")
        )

    def test_draft_manuscript_annotates_zero_common_actual_horses(self):
        f=ROOT/"docs"/"ecology-racehorse-individuality-manuscript-v1.md"
        m=" ".join(f.read_text(encoding="utf-8").split())
        self.assertIn("### 3.5.",m)
        self.assertIn("### 2.7.",m)
        self.assertIn("zero original HORSES IDs",m)
        self.assertIn("within-animal change",m)
        self.assertEqual(m.count("### 3.5."),1)
        self.assertIn("ecology-rq-doomben-matched-timescale-overlap-real-results.md",m)


if __name__=="__main__":
    unittest.main()
