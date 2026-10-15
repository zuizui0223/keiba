"""Only anonymous frozen aggregate evidence and fictional counterexamples."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_manuscript_temporal_figure import (
    EVIDENCE, checked_evidence, svg_figure,
)


class ManuscriptAggregateEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=checked_evidence()

    def _check_mutated(self,mutator):
        q=copy.deepcopy(self.evidence)
        mutator(q)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"fictional_corrupt.json"
            path.write_text(json.dumps(q),encoding="utf-8")
            with self.assertRaises(ValueError):
                checked_evidence(path)

    def test_anonymous_paper_numbers_match_archived_primary_context(self):
        a=self.evidence["within_year_cannon"]
        b=self.evidence["year_forward_doomben"]
        self.assertEqual((a["scored_distinct_original_horses"],
                          a["scored_future_rows"]),(36,46))
        self.assertEqual((b["scored_distinct_original_horses"],
                          b["scored_future_rows"]),(26,27))
        self.assertAlmostEqual(
            a["rmse_seconds"]["own"],.25580872360868767,places=12)
        self.assertAlmostEqual(
            b["rmse_seconds"]["own"],.38613101186797555,places=12)
        self.assertGreater(a["other_minus_own_rmse_seconds"],0)
        self.assertLess(b["other_minus_own_rmse_seconds"],0)
        self.assertTrue(self.evidence["limitations"][
            "cannon_old_horse_roster_digest_missing"])

    def test_svg_is_well_formed_two_distinct_noncausal_cohort_panels(self):
        img=svg_figure(self.evidence)
        root=ET.fromstring(img)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("Cannon Park",img)
        self.assertIn("Doomben",img)
        self.assertIn("0.256",img)
        self.assertIn("0.386",img)
        self.assertIn("0.303",img)
        self.assertIn("0.369",img)
        self.assertIn("do NOT estimate temporal decay",img)
        self.assertIn("HOLD",img)
        self.assertEqual(img,svg_figure(self.evidence))
        for bad in ('HORSES/@Id','Jockey/@Id','Trainer/@Id',
                    'sk-proj','individual horse name'):
            self.assertNotIn(bad,img)

    def test_changed_own_error_without_changed_gain_must_fail(self):
        self._check_mutated(
            lambda x: x["within_year_cannon"]["rmse_seconds"].__setitem__(
                "own",.4
            )
        )

    def test_flipped_study_contrast_not_silently_claimed_as_supported(self):
        def change(x):
            b=x["year_forward_doomben"]
            b["rmse_seconds"]["own"]=.1
            b["other_minus_own_rmse_seconds"]=(
                b["rmse_seconds"]["other_horses_context"]-.1
            )
        self._check_mutated(change)

    def test_changed_doomben_horse_or_date_denominator_fails(self):
        self._check_mutated(
            lambda x:x["year_forward_doomben"].__setitem__(
                "scored_distinct_original_horses",27))
        self._check_mutated(
            lambda x:x["year_forward_doomben"].__setitem__(
                "original_dates_successful",42))

    def test_missing_HOLD_or_crossyear_influence_sign_warning_fails(self):
        self._check_mutated(
            lambda x:x["year_forward_doomben"]["strict_original_race_class_support"][
                "150m_same_distance_and_class"].__setitem__("status","SIGNIFICANT"))
        self._check_mutated(
            lambda x:x["year_forward_doomben"]["year_forward_leave_one_horse"].__setitem__(
                "own_better_count",0
            ))

    def test_causal_status_claim_fails_closed(self):
        self._check_mutated(
            lambda x:x["limitations"].__setitem__(
                "h1_ground_reaction_norm_fitted",True
            ))

    def test_full_paper_keeps_both_aggregate_signs_and_holds(self):
        manuscript=(EVIDENCE.parents[2]/"docs"/
                    "ecology-racehorse-individuality-manuscript-v1.md"
                   ).read_text(encoding="utf-8")
        self.assertIn("0.255809",manuscript)
        self.assertIn("0.303195",manuscript)
        self.assertIn("0.386131",manuscript)
        self.assertIn("0.368906",manuscript)
        self.assertIn("−0.017225",manuscript)
        self.assertIn("26 leave-one-horse",manuscript)
        self.assertIn("ten leave-one-2026-date",manuscript)
        self.assertIn("does not identify a temporal",manuscript)
        self.assertIn("38679488650",manuscript)
        self.assertIn("rq-racehorse-temporal-generalization-20261015.json",manuscript)

    def test_figure_generator_only_requires_aggregate_safe_source(self):
        source=EVIDENCE.read_text(encoding="utf-8")
        self.assertNotIn("horse_name",source)
        self.assertNotIn("jockey_license_id",source)
        self.assertNotIn("trainer_license_id",source)
        self.assertNotIn("first_section_sec",source)
        self.assertIn('"version": "2026-10-15.1"',source)
        self.assertTrue(
            self.evidence["limitations"][
                "comparisons_are_not_matched_treatment_effects"])


if __name__=="__main__":
    unittest.main()
