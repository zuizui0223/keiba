"""Validation of ecological H2 within/between separation with ONLY fictional data."""
from __future__ import annotations
import csv
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_demo_competitors import fabricate_competition
from ecology_panel import REQUIRED, lagged_features, load_panel
from ecology_h2_pilot import competition_frame, split_dates
from ecology_h2_within_between import (
    add_total_field_fraction, check_rights, construct_context, run
)


def save(temp, rows):
    path=Path(temp)/"synthetic_h2.csv"
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(REQUIRED)+["first_call_position"])
        writer.writeheader()
        writer.writerows(rows)
    return path


class H2WithinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=fabricate_competition(
            n_days=65,n_horses=36,runners=12,seed=512,interaction=-0.9)

    def test_context_means_frozen_on_training_only(self):
        with tempfile.TemporaryDirectory() as temp:
            source=load_panel(save(temp,self.records))
            enriched=lagged_features(source)
        df=add_total_field_fraction(competition_frame(enriched))
        train, test, _=split_dates(df)
        tr, te, meta=construct_context(train,test)
        self.assertTrue(meta["training_horse_means_frozen_for_future"])
        self.assertLess(tr["date"].max(),te["date"].min())
        altered=test.copy()
        altered["other_front_runner_share"]=0.99
        _, changed, changed_meta=construct_context(train,altered)
        self.assertEqual(meta,changed_meta)
        # Moving heldout contexts does not change frozen per-horse baselines.
        self.assertTrue(np.allclose(
            (te["other_front_runner_share"]-te["context_within"]).to_numpy(),
            (changed["other_front_runner_share"]-changed["context_within"]).to_numpy(),
            atol=1e-12, rtol=0,
        ))

    def test_leave_one_out_and_complete_field_reconciliation(self):
        with tempfile.TemporaryDirectory() as temp:
            enriched=lagged_features(load_panel(save(temp,self.records)))
        frame=add_total_field_fraction(competition_frame(enriched))
        for race,group in frame.groupby("race_id"):
            full=group["total_front_runner_share"]
            self.assertLess(float(full.max()-full.min()),1e-12)
            self.assertGreaterEqual(float(full.min()),0.0)
            self.assertLessEqual(float(full.max()),1.0)

    def test_pipeline_runs_both_exposures_with_cluster_uncertainty(self):
        with tempfile.TemporaryDirectory() as temp:
            outcome=run(save(temp,self.records),permit_synthetic_demo=True)
        self.assertEqual(outcome["status"],"SYNTHETIC_H2_WITHIN_HORSE_DEMO_ONLY")
        self.assertLess(outcome["data_support"]["train_date_max"],
                        outcome["data_support"]["test_date_min"])
        self.assertGreaterEqual(outcome["data_support"]["training_horses_with_repeated_rival_contexts"],8)
        self.assertEqual(len(outcome["context_definitions"]),2)
        for variant in outcome["context_definitions"].values():
            interaction=variant["interaction"]
            self.assertFalse(interaction["ci_is_causal_or_confirmatory"])
            self.assertTrue(interaction["within_horse_context_use"])
            self.assertEqual(len(interaction["two_way_cluster_nominal_95pct_interval"]),2)
            self.assertEqual(len(variant["forward_test"]["race_block_bootstrap_95pct_interval"]),2)
        self.assertIsInstance(outcome["leave_one_out_vs_full_field_beta_sign_agreement"],bool)

    def test_no_effect_generator_is_never_marked_as_biological_inference(self):
        null=fabricate_competition(n_days=65,n_horses=36,runners=12,seed=911,interaction=0.0)
        with tempfile.TemporaryDirectory() as temp:
            outcome=run(save(temp,null),permit_synthetic_demo=True)
        self.assertEqual(outcome["status"],"SYNTHETIC_H2_WITHIN_HORSE_DEMO_ONLY")
        self.assertIn("Causal social plasticity or experimental competition effect",outcome["not_inferred"])

    def test_source_guard_denies_unverified_mixture(self):
        rows=[{"source_license":"synthetic"},{"source_license":"research-approved"}]
        with self.assertRaisesRegex(ValueError,"HOLD_MIXED_SYNTHETIC"):
            check_rights(rows,True)
        with self.assertRaisesRegex(ValueError,"synthetic"):
            check_rights([{"source_license":"synthetic"}],False)
        with self.assertRaisesRegex(ValueError,"HOLD_RIGHTS"):
            check_rights([{"source_license":"restricted"}],True)


if __name__ == "__main__":
    unittest.main()
