"""Synthetic QA of day-balanced γ ensemble; outcome on 2026-10-25 never read."""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "scripts"))
from betting_gamma_daybalanced_pure import (
    GAMMAS, DATES, predict, validate_source, validate_history, weights, sha
)
LOSS_FILE=ROOT/"docs/evidence/kikka-two-date-gamma-losses-20261025.json"


def fake():
    return {
       "schema":"KEIBA_KIKKA_LOCAL_PRICE_VECTOR_V1",
       "race_id":"2026-10-25-KYOTO-11",
       "runner_count":18,
       "provider_publication_clock_verified":False,
       "source_page_retrieved_at_jst":"2026-10-25T13:00:00+09:00",
       "odds_by_number":{str(i):2.5+0.3*i for i in range(1,19)}
    }


class DayBalancedGammaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history=json.loads(LOSS_FILE.read_text(encoding="utf-8"))
        cls.data=predict(fake(),cls.history)

    def test_history_sha_and_prior_status(self):
        self.assertEqual(len(GAMMAS),37)
        self.assertEqual(len(validate_history(self.history)),2)
        self.assertEqual(sha(self.history),"effed243bda3641ac8eabd44e0d72752cf0745112cb06ce7fefe6e1cd8ae286d")
        self.assertTrue(self.data["not_calibrated_and_not_a_valid_betting_roi"])
        self.assertFalse(self.data["result_used"])

    def test_date_tempering_posterior(self):
        h=validate_history(self.history)
        self.assertEqual(set(h),set(DATES))
        wt=weights(h,0.5)
        self.assertAlmostEqual(sum(wt),1,places=12)
        self.assertAlmostEqual(sum(g*p for g,p in zip(GAMMAS,wt)),
                               1.199495500289521,places=11)
        past=weights(h,0.5,dates=("2026-10-12",))
        self.assertAlmostEqual(sum(g*p for g,p in zip(GAMMAS,past)),
                               1.1703455511290415,places=11)

    def test_probability_mass_and_coverage(self):
        for name,m in self.data["models"].items():
            with self.subTest(name=name):
                self.assertEqual(len(m["horses"]),18)
                self.assertEqual(len(m["wide"]),153)
                self.assertEqual(len(m["trio"]),816)
                for name,target in (("win",1),("top2",2),("top3",3)):
                    self.assertAlmostEqual(
                        sum(r[name] for r in m["horses"].values()),target,places=11)
                self.assertAlmostEqual(sum(m["wide"].values()),3,places=11)
                self.assertAlmostEqual(sum(m["trio"].values()),1,places=11)

    def test_favorite_is_not_automatically_80_percent(self):
        q=fake()
        q["odds_by_number"]["8"]=1.7
        q["odds_by_number"]["10"]=4.4
        out=predict(q,self.history)
        m=out["models"]
        point=m["point_gamma185"]["horses"]["8"]["win"]
        mixture=m["sigma_0.50"]["horses"]["8"]["win"]
        self.assertLess(mixture,point)

    def test_reject_future_observed_price_and_outcome(self):
        q=fake();q["source_page_retrieved_at_jst"]="2026-10-25T15:35:00+09:00"
        with self.assertRaises(ValueError):validate_source(q)
        q=fake();q["winner"]=8
        with self.assertRaises(ValueError):validate_source(q)
        q=fake();q["odds_by_number"].pop("18")
        with self.assertRaises(ValueError):validate_source(q)
        q=fake();q["odds_by_number"]["3"]=0
        with self.assertRaises(ValueError):validate_source(q)

    def test_historical_pin_drift_or_wrong_date(self):
        h=copy.deepcopy(self.history)
        h["by_meeting_date"].pop("2026-10-18")
        with self.assertRaises(ValueError):validate_history(h)
        h=copy.deepcopy(self.history)
        h["source_git_blob_sha"].pop("oct12_r8")
        with self.assertRaises(ValueError):validate_history(h)

    def test_deterministic_rerun(self):
        self.assertEqual(sha(self.data),sha(predict(fake(),self.history)))
        altered=fake();altered["odds_by_number"]["8"]*=1.1
        self.assertNotEqual(sha(self.data),sha(predict(altered,self.history)))


if __name__=="__main__":unittest.main()
