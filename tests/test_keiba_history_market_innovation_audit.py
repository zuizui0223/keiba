#!/usr/bin/env python3
"""No-lookahead and price-index counterfactual tests for history bridge."""
from __future__ import annotations
import copy
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ImportError:
    np=None

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/"scripts"))
if np is not None:
    import keiba_history_market_innovation_audit as m
    import keiba_coupled_history_falsification as history


def synthetic():
    row={
      "race_id":"SYNTHETIC","race_no":8,"meeting_day":"2026-10-12",
      "first_odds":{i:float(2*i+2) for i in range(1,7)},
      "last_odds":{i:float(2*i+2)*1.12 for i in range(1,7)},
      "initial_quote_at":"2026-10-12T12:00:00+09:00",
      "latest_quote_at":"2026-10-12T13:00:00+09:00",
      "post_at":"2026-10-12T15:00:00+09:00",
    }
    archive={
      "target_date":"2026-10-12","target_surface":"芝",
      "distance_m":1800,
      "rows":{i:{"full_history_before_target":[
          {"date":"2026-06-01","finish":i,
           "surface":"芝","distance_m":1800},
          {"date":"2026-08-02","finish":7-i,
           "surface":"ダ","distance_m":1600}
      ]} for i in range(1,7)},
    }
    return row,archive


@unittest.skipIf(np is None,"NumPy required by dedicated numerical CI")
class PriceMarketPureTest(unittest.TestCase):
    def test_geometric_bridge_endpoints_mass_and_finite(self):
        q=m.vector([2,3,4,5,6,7])
        h=m.vector([7,6,5,4,3,2])
        np.testing.assert_allclose(m.geometric_bridge(q,h,fraction=0),q,
                                   rtol=0,atol=1e-14)
        np.testing.assert_allclose(m.geometric_bridge(q,h,fraction=1),h,
                                   rtol=0,atol=1e-14)
        for f in [0.0,.2,.5,1.]:
            p=m.geometric_bridge(q,h,fraction=f)
            self.assertAlmostEqual(sum(p),1.,places=12)
            self.assertTrue(np.all(p>0))
        with self.assertRaisesRegex(ValueError,"BAD_INPUT"):
            m.geometric_bridge(q,h,fraction=1.1)

    def test_future_quote_and_future_outcome_have_zero_effect_on_prediction(self):
        row,archive=synthetic()
        p1=m.prepare_market_prediction(row,archive)
        changed=copy.deepcopy(row)
        changed["last_odds"]={i:float(2.2*i+11) for i in range(1,7)}
        changed["winner"]=3
        changed["target_payout"]=9000000
        changed["official_top3"]=[3,2,1]
        p2=m.prepare_market_prediction(changed,archive)
        for k in m.MODEL_NAMES:
            np.testing.assert_array_equal(
                p1["candidate_next_market_predictions"][k],
                p2["candidate_next_market_predictions"][k])
        self.assertEqual(p1["horse_numbers"],p2["horse_numbers"])
        self.assertTrue(p1["model_did_not_consume_later_win_quote_or_official_result"])
        # The *scorer* MUST respond to real later market changes.
        self.assertNotEqual(
            m.score_later_market(p1,row)["per_policy"]["early_market_only"],
            m.score_later_market(p1,changed)["per_policy"]["early_market_only"])

    def test_shuffled_horse_identity_is_a_placebo_with_same_weight_support(self):
        row,archive=synthetic()
        p=m.prepare_market_prediction(row,archive)
        q=p["q0_for_market"];h=p["history_prior_for_horse_ABM"]
        np.testing.assert_allclose(
            p["candidate_next_market_predictions"]["market_plus_shifted_history_020"],
            m.geometric_bridge(q,np.roll(h,1)),atol=1e-15)
        self.assertEqual(set(p["candidate_next_market_predictions"]),
                         set(m.MODEL_NAMES))
        self.assertEqual(p["history_record_count"],12)

    def test_market_clock_rejects_postevent_later_quote(self):
        row,archive=synthetic()
        pred=m.prepare_market_prediction(row,archive)
        future=copy.deepcopy(row)
        future["latest_quote_at"]=future["post_at"]
        with self.assertRaisesRegex(ValueError,"TOO_LATE"):
            m.score_later_market(pred,future)

    def test_market_divergence_is_zero_for_matched_price_indices(self):
        q=m.vector([.35,.2,.19,.12,.08,.06])
        self.assertAlmostEqual(m._kl(q,q),0,places=12)
        self.assertAlmostEqual(m._tv(q,q),0,places=12)
        self.assertGreater(m._kl(q,np.roll(q,1)),0)
        self.assertGreater(m._tv(q,np.roll(q,1)),0)

    def test_extra_history_result_fields_not_accepted_as_features(self):
        row,archive=synthetic()
        base=m.prepare_market_prediction(row,archive)
        weird=copy.deepcopy(archive)
        for horse in weird["rows"].values():
            horse["true_2026_winner"]=True
            for entry in horse["full_history_before_target"]:
                entry["popularity"]=1
                entry["horse_future_finish"]=1
                entry["race_payout"]=12345
        altered=m.prepare_market_prediction(row,weird)
        for k in m.MODEL_NAMES:
            np.testing.assert_array_equal(
                base["candidate_next_market_predictions"][k],
                altered["candidate_next_market_predictions"][k])


@unittest.skipIf(np is None or not (
    HERE/"data/2026-10-12/v3-normalized-prerace-history.json").exists(),
    "Requires full source-locked keiba checkout and NumPy")
class RealSourceBridgeTest(unittest.TestCase):
    def test_six_real_races_and_historical_source_gate(self):
        with patch("odds_six_race_predictive_increment.verify_official_oct12",
                   side_effect=AssertionError("NO_OFFICIAL_LABEL_ALLOWED")) as mock:
            result=m.audit()
            mock.assert_not_called()
        self.assertEqual(result["independent_race_outcomes"],6)
        self.assertEqual(result["independent_dates"],2)
        self.assertEqual(result["horse_race_rows"],84)
        self.assertTrue(result["no_independent_past_horse_source_receipt"])
        self.assertEqual(result["research_decision"],
            "HOLD_NO_EXTERNAL_ASOF_PAST_HISTORY_RECEIPTS_AND_ONLY_TWO_DATES")
        self.assertEqual(set(result["mean_race_equal_market_price_index_scores"]),
                         set(m.MODEL_NAMES))
        self.assertEqual(set(result["by_meeting_date"]),
                         {"2026-10-12","2026-10-18"})
        self.assertAlmostEqual(
            result["mean_race_equal_market_price_index_scores"][
                "early_market_only"]["price_index_TV_pp"],
            sum(r["per_policy"]["early_market_only"]["price_index_TV_pp"]
                for r in result["per_race"])/6,places=12)


if __name__=="__main__":
    unittest.main()
