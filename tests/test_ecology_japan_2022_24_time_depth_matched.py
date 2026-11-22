"""Fictional fail-closed support audit and paired frozen-model uncertainty checks."""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ecology_japan_balanced_parent_history as balanced
import ecology_japan_time_depth_nonkin_match as sam
import ecology_japan_2022_24_time_depth_matched as experiment
from test_ecology_japan_unrelated_peer_control import example
from test_ecology_japan_2022_24_peer_identity_placebo import fixture


class FullPopulationGuardTests(unittest.TestCase):
    def test_32_draw_overlapping_source_stays_eligible(self):
        history,targets=example()
        block=balanced.prepare_peer_block(history,targets,cutoff_year=2022)
        matched=sam.prepare_temporal_match(history,targets,block,cutoff_year=2022)
        # Five separate study stages are represented by five synthetic copies.
        summary,storage=experiment._audit([matched]*5,seeds=range(2026112200,2026112232))
        self.assertEqual(summary["status"],"EXACT_MATCH_SUPPORT_COMPLETE")
        self.assertEqual(summary["total_draw_block_side_checks"],320)
        self.assertEqual(summary["fully_matched_draw_block_side_checks"],320)
        self.assertIsNotNone(storage)
        self.assertEqual(len(storage),320)
        self.assertTrue(summary["no_individual_horse_parent_race_or_peer_ID_exported"])

    def test_exact_match_shortage_holds_whole_cohort_not_only_stratum(self):
        history,targets=example()
        history.loc[history.horse.str.startswith("unrelated"),"day"]="2020-05-01"
        history.loc[history.horse.eq("neutral"),"day"]="2020-05-01"
        block=balanced.prepare_peer_block(history,targets,cutoff_year=2022)
        matched=sam.prepare_temporal_match(history,targets,block,cutoff_year=2022)
        summary,storage=experiment._audit([matched]*5,seeds=[2026112200,2026112201])
        self.assertEqual(summary["status"],experiment.HOLD)
        self.assertIsNone(storage)
        self.assertGreater(summary["unsupported_draw_block_side_checks"],0)
        self.assertGreater(summary["year_side"]["2022_sire"]["minimum_missing_peer_slots"],0)
        self.assertTrue(summary["one_unmatched_target_invalidates_full_population_model_comparison"])

    def test_matched_model_losses_maintain_exact_original_true_parent_identity(self):
        panel,full,true,ctrl,ref=fixture()
        negatives={"NS":true["MS"]+.003,"ND":true["MD"]+.005}
        x=experiment.summarize_period(panel,full,true,negatives,ref,
                                      draws=30,min_clusters=2)
        self.assertEqual(x["starts"],len(panel))
        self.assertEqual(x["horses"],5)
        self.assertAlmostEqual(x["main_MSE_contrasts"]["sire_over_matched_nonkin"],.003)
        self.assertAlmostEqual(x["main_MSE_contrasts"]["dam_over_matched_nonkin"],.005)
        self.assertAlmostEqual(x["models"]["MS"]["MSE"],
                               ref["balanced_models"]["MS"]["MSE"])
        self.assertTrue(x["exact_paired_parent_and_negative_control_identity"])
        self.assertEqual(len(x["per_draw"]),32)

    def test_changed_pr73_true_loss_is_rejected_before_comparing_nonkin(self):
        panel,full,true,ctrl,ref=fixture()
        bad=copy.deepcopy(true)
        bad["MS"]=bad["MS"]+.01
        with self.assertRaisesRegex(ValueError,"HOLD_PR73"):
            experiment.summarize_period(panel,full,bad,
                                         {"NS":ctrl,"ND":ctrl},ref,
                                         draws=30,min_clusters=2)

    def test_invalid_model_loss_shape_or_nan_rejected(self):
        panel,full,true,ctrl,ref=fixture()
        for negative in [ctrl[:31],ctrl[:,1:],np.full_like(ctrl,np.nan)]:
            with self.assertRaises(ValueError):
                experiment.summarize_period(panel,full,true,
                    {"NS":negative,"ND":ctrl},ref,
                    draws=30,min_clusters=2)

    def test_reference_sha_must_be_exact_before_source_access(self):
        with (patch.object(experiment,"PR74_SHA256","definitely_not_sha"),
              patch.object(experiment.ablation,"load_sources") as source):
            with self.assertRaisesRegex(ValueError,"PR74_REFERENCE"):
                experiment.analyze(Path("private-never-opened"),Path("never-opened"))
            source.assert_not_called()


if __name__=="__main__":
    unittest.main()
