"""Purely fictional tests for loss-matched unrelated-peer placebo estimands."""
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import ecology_japan_2022_24_family_feature_ablation as ablation
import ecology_japan_2022_24_parent_performance_channels as channels
import ecology_japan_2022_24_equal_peer_information as eq
import ecology_japan_2022_24_peer_identity_placebo as experiment


def fixture():
    p=pd.DataFrame({"horse":["a","a","b","c","d","e"],
                    "race":list("pqrstu"),"day":pd.date_range("2022-01-01",periods=6),
                    "sire_id":["1","1","2","3","4","5"],
                    "dam_id":["m1","m1","m2","m3","m4","m5"],
                    "y":[0.,1.,.2,.9,.1,.7]})
    support=pd.DataFrame({"sire_relative_count":[4,4,3,1,0,9],
                          "dam_relative_count":[2,2,3,1,0,4]})
    k=support.min(axis=1)
    full={name:np.full(len(p),.5 if name in ("MS","M1","MC") else .4)
          for name in channels.FEATURES}
    ms=np.stack([np.array([.02,.03,.04,.05,.06,.07])+i*.0001 for i in range(32)])
    md=np.stack([np.array([.08,.07,.06,.05,.04,.03])+i*.0001 for i in range(32)])
    control=np.stack([np.array([.10,.09,.08,.07,.06,.05])+i*.0003 for i in range(32)])
    both={"MS":ms,"MD":md}
    ref=eq.summarize_period(p,full,both,support,k,draws=30,min_clusters=2)
    return p,full,both,control,ref


class PlaceboEstimatorTests(unittest.TestCase):
    def test_exact_pairing_and_equal_horse_performance(self):
        p,full,losses,ctrl,ref=fixture()
        got=experiment.summarize_period(p,full,losses,ctrl,ref,draws=30,min_clusters=2)
        self.assertEqual(got["starts"],6)
        self.assertEqual(got["horses"],5)
        self.assertEqual(set(got["models"]),{"M0","MC","unrelated_N","true_equal_sire_MS","true_equal_dam_MD"})
        w=np.array([.1,.1,.2,.2,.2,.2])
        for key,side in [("sire_over_unrelated","MS"),("dam_over_unrelated","MD")]:
            per_seed=np.array([np.dot(ctrl[i]-losses[side][i],w) for i in range(32)])
            self.assertAlmostEqual(got["mean_MSE_contrasts"][key],per_seed.mean())
            self.assertAlmostEqual(got["monte_carlo"][key]["SD"],per_seed.std(ddof=1))
            self.assertAlmostEqual(got["monte_carlo"][key]["MCSE"],per_seed.std(ddof=1)/np.sqrt(32))
            self.assertAlmostEqual(got["primary_uncertainty"][key]["mean_MSE_gain"],per_seed.mean())
            np.testing.assert_allclose([row[key] for row in got["per_draw"]],per_seed,
                                       atol=1e-14,rtol=0)
            self.assertEqual([row["seed"] for row in got["per_draw"]],list(eq.SEEDS))
        s=got["mean_MSE_contrasts"]
        self.assertAlmostEqual(s["sire_over_unrelated"]-s["dam_over_unrelated"],
                               ref["mean_MSE_contrasts"]["balanced_sire_advantage"])
        self.assertAlmostEqual(s["unrelated_over_MC"],
                               got["models"]["MC"]["MSE"]-got["models"]["unrelated_N"]["MSE"])
        self.assertEqual(got["support"],ref["support"])

    def test_wrong_null_or_true_loss_shapes_prohibit_any_claim(self):
        p,full,losses,ctrl,ref=fixture()
        for wrong in (ctrl[:-1],ctrl[:,:-1],np.full_like(ctrl,np.nan),np.full_like(ctrl,-.01),
                      np.full_like(ctrl,1.01)):
            with self.subTest(shape=wrong.shape),self.assertRaises(ValueError):
                experiment.summarize_period(p,full,losses,wrong,ref,draws=30,min_clusters=2)
        with self.assertRaises(ValueError):
            experiment.summarize_period(p,full,{"MS":losses["MS"]},ctrl,ref)
        with self.assertRaises(ValueError):
            experiment.summarize_period(p,full,losses,ctrl,ref,draws=20)

    def test_tampered_pr73_draw_risk_or_support_gate_is_rejected(self):
        p,full,losses,ctrl,ref=fixture()
        import copy
        cases=[("draw",lambda r:r["per_draw"][5].update(balanced_sire_advantage=1.)),
               ("mse",lambda r:r["balanced_models"]["MS"].update(MSE=0.)),
               ("baseline",lambda r:r["full_models"]["MC"].update(MSE=0.))]
        for name,alter in cases:
            with self.subTest(name=name):
                bad=copy.deepcopy(ref)
                alter(bad)
                with self.assertRaisesRegex(ValueError,"HOLD_PR73"):
                    experiment.summarize_period(p,full,losses,ctrl,bad,draws=30,min_clusters=2)

    def test_reference_sha_fails_before_opening_actual_sources(self):
        with patch.object(experiment,"PR73_SHA256","invalid-digest"), \\
             patch.object(ablation,"load_sources") as sources:
            with self.assertRaisesRegex(ValueError,"PR73_REFERENCE"):
                experiment.analyze(Path("not-an-archive"),Path("not-a-db"))
            sources.assert_not_called()


if __name__=="__main__":
    unittest.main()
