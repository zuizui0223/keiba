"""Reproducible artificial loss-to-observation stress tests; no real horses."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_demo_competitors import fabricate_competition
from ecology_h2_outcome_loss_stress import inject_nonfinishing,compare


class OutcomeLossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=fabricate_competition(n_days=65,n_horses=36,
                                      runners=12,seed=512)

    def test_selective_nonfinishing_preserves_actual_entry_rosters(self):
        censored=inject_nonfinishing(self.rows,"speed_dependent",seed=543)
        self.assertEqual(len(censored),len(self.rows))
        self.assertEqual({r["race_id"] for r in censored},
                         {r["race_id"] for r in self.rows})
        missing=[r for r in censored if r["finish_status"]=="did_not_finish"]
        self.assertGreater(len(missing),0)
        self.assertTrue(all(r["track_going"]!="良" for r in missing))
        self.assertTrue(all(r["finishing_position"]=="" and r["finish_time_s"]==""
                            for r in missing))
        # This field is a prior snapshot for competitors and does not
        # remove a starter when the result is unobserved.
        self.assertTrue(all(r["source_license"]=="synthetic" for r in censored))

    def test_random_and_selective_loss_are_reproducibly_different(self):
        a=inject_nonfinishing(self.rows,"random",seed=543)
        b=inject_nonfinishing(self.rows,"random",seed=543)
        self.assertEqual(a,b)
        c=inject_nonfinishing(self.rows,"speed_dependent",seed=543)
        self.assertNotEqual(
            [(r["race_id"],r["horse_id"]) for r in a
             if r["finish_status"]=="did_not_finish"],
            [(r["race_id"],r["horse_id"]) for r in c
             if r["finish_status"]=="did_not_finish"],
        )

    def test_one_panel_three_loss_mechanisms_and_missingness_gate(self):
        report=compare(seed=512)
        self.assertTrue(report["no_empirical_horse_claims"])
        self.assertEqual(report["status"],
                         "SYNTHETIC_MISSINGNESS_FALSIFICATION_ONLY")
        cases=report["scenarios"]
        self.assertEqual(set(cases),{"none","random","speed_dependent"})
        self.assertEqual(cases["none"]["nonfinisher_count"],0)
        self.assertGreater(cases["random"]["nonfinisher_count"],0)
        self.assertGreater(cases["speed_dependent"]["nonfinisher_count"],0)
        self.assertEqual(cases["none"]["empirical_missingness_decision"],
                         "NO_RECORDED_SPEED_LOSS_NOT_PROOF_OF_UNBIASED_COHORT")
        for name in ("random","speed_dependent"):
            self.assertEqual(
                cases[name]["empirical_missingness_decision"],
                "HOLD_POTENTIALLY_INFORMATIVE_SPEED_MISSINGNESS"
            )
            self.assertGreater(cases[name]["selection_audit"]["observed_speed_loss_fraction"],0)


if __name__=="__main__":
    unittest.main()
