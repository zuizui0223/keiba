"""Flexible global price-bias test: 1–4 degree smooth horse popularity controls."""
import math
import unittest

from scripts.ecology_ticket_market_smooth_null import (
    DEGREES, feature_map, weighted_linear_edge_cv, run_analysis,
)
from scripts.ticket_type_models import predict_tickets


def synthetic():
    strength={i:1/(1+i*i*.14) for i in range(1,12)}
    frames={i:min(i,8) for i in strength}
    p=predict_tickets(strength,frames)["wide"]
    weights={e:v/3 for e,v in p.items()}
    return strength,weights


class SmoothBiasNegativeControlTests(unittest.TestCase):
    def test_polynomial_signal_exactly_recovers_missing_pairs(self):
        strength,weights=synthetic()
        features=feature_map(strength,3)
        y={e:0.4+0.2*x[1]-0.3*x[2]+0.15*x[3] for e,x in features.items()}
        result=weighted_linear_edge_cv(y,weights,features)
        self.assertAlmostEqual(result["pair_holdout_R2"],1.,places=9)
        self.assertAlmostEqual(result["in_sample_R2"],1.,places=9)
        self.assertEqual(result["parameter_count"],4)
        self.assertGreater(result["max_edge_leverage"],0)
        self.assertLess(result["max_edge_leverage"],1)

    def test_full_node_pattern_not_universally_smooth(self):
        strength,weights=synthetic()
        x={i:math.sin(i*6.3)*0.6 for i in strength}
        y={(i,j):x[i]+x[j] for (i,j) in weights}
        d1=weighted_linear_edge_cv(y,weights,feature_map(strength,1))
        d4=weighted_linear_edge_cv(y,weights,feature_map(strength,4))
        self.assertTrue(math.isfinite(d1["pair_holdout_R2"]))
        self.assertTrue(math.isfinite(d4["pair_holdout_R2"]))
        self.assertLess(d4["pair_holdout_R2"],.95)

    def test_shared_quote_normalization_constant_is_invariant(self):
        strength,weights=synthetic()
        features=feature_map(strength,4)
        y={edge:0.3+0.16*features[edge][2]+0.03*(edge[0]%3)
           for edge in weights}
        p=weighted_linear_edge_cv(y,weights,features)
        s=weighted_linear_edge_cv({e:v+11 for e,v in y.items()},
                                  weights,features)
        self.assertAlmostEqual(p["pair_holdout_R2"],s["pair_holdout_R2"],places=8)
        self.assertAlmostEqual(p["in_sample_R2"],s["in_sample_R2"],places=8)

    def test_missing_edge_or_unidentified_strength_rejected(self):
        strength,weights=synthetic()
        f=feature_map(strength,2)
        y={e:f[e][1] for e in f}
        with self.assertRaises(ValueError):
            weighted_linear_edge_cv(y,weights,{e:v for e,v in f.items() if e!=(1,2)})
        with self.assertRaises(ValueError):
            feature_map({i:1 for i in strength},3)
        with self.assertRaises(ValueError):
            feature_map(strength,5)

    def test_all_archived_races_and_four_global_controls(self):
        result=run_analysis()
        self.assertEqual(result["status"],
           "EMPIRICAL_SMOOTH_GLOBAL_PRICE_BIAS_CONTROL_NINE_RACES_RETROSPECTIVE")
        self.assertEqual(result["degrees_tested"],[1,2,3,4])
        self.assertEqual(len(result["races"]),9)
        self.assertEqual(result["by_date"]["2026-10-12"]["race_count"],5)
        self.assertEqual(result["by_date"]["2026-10-18"]["race_count"],4)
        self.assertFalse(result["outcome_labels_used"])
        self.assertFalse(result["genomic_A_G_or_biological_individual_trait_identified"])
        self.assertFalse(result["market_time_series_measured"])
        for r in result["races"]:
            self.assertEqual(r["pair_count"],r["runner_count"]*(r["runner_count"]-1)//2)
            self.assertTrue(math.isfinite(r["node_pair_holdout_R2"]))
            for d in DEGREES:
                v=r["global_smooth_models"][f"degree_{d}"]
                self.assertTrue(math.isfinite(v["pair_holdout_R2"]))
                self.assertEqual(v["parameter_count"],d+1)
                self.assertTrue(0<v["max_edge_leverage"]<1)
        self.assertGreaterEqual(len(result["input_file_sha256"]),30)


if __name__=="__main__":
    unittest.main()
