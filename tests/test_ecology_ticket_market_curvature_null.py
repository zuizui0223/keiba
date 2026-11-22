"""Two-dimensional monotone favorite-longshot negative control (stdlib only)."""
import math
import unittest

from scripts.ecology_ticket_market_curvature_null import (
    GAMMA_GRID, curvature_curve, transformed_strengths,
    compare_curve_models, run_analysis
)
from scripts.ecology_ticket_market_temperature_null import (
    BETA_GRID, nonlinear_curve
)
from scripts.ticket_type_models import predict_tickets


def make_data():
    strengths={i:1/(1+i*i*.18) for i in range(1,10)}
    frames={i:min(i,8) for i in strengths}
    pl=predict_tickets(strengths,frames)
    weights={e:p/3 for e,p in pl["wide"].items()}
    one=nonlinear_curve(strengths,pl["wide"])
    two=curvature_curve(strengths,pl["wide"])
    return strengths,pl,weights,one,two


class MonotoneMarketCurvatureTests(unittest.TestCase):
    def test_curvature_preserves_horse_order_and_original_PL_at_baseline(self):
        strengths,pl,w,one,two=make_data()
        self.assertEqual(len(two),len(BETA_GRID)*len(GAMMA_GRID))
        original=transformed_strengths(strengths,1.0,0.0)
        norm=max(strengths.values())
        for i in strengths:
            self.assertAlmostEqual(original[i],strengths[i]/norm,places=12)
        for beta in BETA_GRID:
            for gamma in GAMMA_GRID:
                t=transformed_strengths(strengths,beta,gamma)
                ranked=sorted(strengths,key=strengths.get)
                self.assertEqual(ranked,sorted(t,key=t.get))
        self.assertLess(max(abs(v) for v in two[(1.0,0.0)].values()),1e-11)
        with self.assertRaises(ValueError):
            transformed_strengths(strengths,0.2,0.2)

    def test_true_quadratic_monotone_signal_has_perfect_edge_cv(self):
        _,pl,w,one,two=make_data()
        values={e:two[(1.2,0.15)][e]+0.4 for e in w}
        r=compare_curve_models(values,w,two,one)
        self.assertAlmostEqual(r["two_parameter_in_sample_R2"],1.0,places=8)
        self.assertAlmostEqual(r["two_parameter_heldout_R2"],1.0,places=7)
        self.assertAlmostEqual(r["two_parameter_plus_node_heldout_R2"],1.0,places=7)
        self.assertGreater(r["two_parameter_heldout_R2"],r["one_parameter_heldout_R2"])
        self.assertEqual(r["two_parameter_beta_gamma_in_sample"],[1.2,0.15])

    def test_global_price_normalizer_cannot_leak_heldout_price(self):
        _,pl,w,one,two=make_data()
        y={e:two[(.95,-.15)][e]+.025*((e[0]*7+e[1]*11)%9) for e in w}
        before=compare_curve_models(y,w,two,one)
        after=compare_curve_models({e:val+3.29 for e,val in y.items()},w,two,one)
        for key in (
            "two_parameter_heldout_R2",
            "horse_node_only_heldout_R2",
            "two_parameter_plus_node_heldout_R2",
            "node_minus_two_parameter_heldout_R2",
        ):
            self.assertAlmostEqual(before[key],after[key],places=7)

    def test_source_nine_races_no_outcomes_or_dna_inference(self):
        r=run_analysis()
        self.assertEqual(r["status"],
            "EXPLORATORY_CURVED_MONOTONE_FAVORITE_LONGSHOT_NULL_NO_CAUSAL_EFFECT")
        self.assertEqual(len(r["races"]),9)
        self.assertEqual(len(r["beta_grid"]),31)
        self.assertEqual(len(r["gamma_grid"]),3)
        self.assertTrue(r["strictly_monotone_transformation"])
        self.assertFalse(r["outcome_labels_used"])
        self.assertFalse(r["future_market_validation"])
        self.assertFalse(r["causal_biological_individuality_identified"])
        for d,v in r["by_date"].items():
            self.assertGreater(v["race_count"],0)
            for key,val in v.items():
                if key.startswith("mean_"):
                    self.assertTrue(math.isfinite(val))
        for row in r["races"]:
            self.assertEqual(row["complete_pair_count"],row["runner_count"]*(row["runner_count"]-1)//2)
            self.assertAlmostEqual(
                row["node_minus_two_parameter_heldout_R2"],
                row["horse_node_only_heldout_R2"]-row["two_parameter_heldout_R2"],
                places=11)
        self.assertGreaterEqual(len(r["input_file_sha256"]),30)


if __name__=="__main__":
    unittest.main()
