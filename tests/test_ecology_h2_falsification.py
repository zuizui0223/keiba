"""Negative-control design tests with fabricated rival fields only."""
import unittest

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from ecology_demo_competitors import fabricate_competition
from ecology_h2_falsification import SCENARIOS, run_stress


class H2FalsificationTests(unittest.TestCase):
    def test_generator_is_reproducible_under_null_and_confounding(self):
        kwargs=dict(n_days=30,n_horses=24,runners=12,seed=422,
                    interaction=0,assortment=0.65,going_style_effect=0.7)
        a=fabricate_competition(**kwargs)
        b=fabricate_competition(**kwargs)
        self.assertEqual(a,b)
        self.assertEqual({r["source_license"] for r in a},{"synthetic"})
        c=fabricate_competition(n_days=30,n_horses=24,runners=12,
                               seed=422,interaction=0)
        # Changing only the confounding mechanisms changes the artificial data.
        self.assertNotEqual(
            [(r["race_id"],r["horse_id"]) for r in a],
            [(r["race_id"],r["horse_id"]) for r in c],
        )

    def test_three_mechanisms_include_zero_opponent_effect_control(self):
        self.assertEqual(SCENARIOS["null_random_entry"]["interaction"],0)
        self.assertEqual(SCENARIOS["confounded_null"]["interaction"],0)
        self.assertGreater(SCENARIOS["confounded_null"]["assortment"],0)
        self.assertNotEqual(SCENARIOS["planted_opponent_interaction"]["interaction"],0)

    def test_stress_reports_holds_separately_and_never_claims_ecology(self):
        out=run_stress(seeds=(512,),n_days=65,n_horses=36,runners=12)
        self.assertEqual(out["status"],"SYNTHETIC_DESIGN_STRESS_ONLY")
        self.assertEqual(len(out["runs"]),3)
        for scenario,summary in out["summary"].items():
            self.assertEqual(summary["runs"],1)
            self.assertEqual(summary["model_completed"]+summary["hold_count"],1)
        for run in out["runs"]:
            self.assertIn(run["status"],
                          ("SYNTHETIC_SOFTWARE_STRESS_ONLY","HOLD_MODEL_OR_DESIGN"))
        self.assertTrue(any("social plasticity" in text for text in out["never_conclude"]))

    def test_duplicate_stress_seeds_rejected(self):
        with self.assertRaisesRegex(ValueError,"distinct"):
            run_stress(seeds=(512,512))


if __name__=="__main__":
    unittest.main()
