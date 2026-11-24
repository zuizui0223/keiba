"""Disjoint wide-edge block validation; never horse identity repeatability."""
import math
import unittest

from scripts.ecology_ticket_market_edge_block_holdout import (
    fit_weighted, predict, node_features, partition_edges, evaluate_partition,
    evaluate_race, run_analysis, TRAIN_FRACTION,
)
from scripts.ecology_ticket_market_smooth_null import feature_map


def make_synthetic(n=10):
    horses=list(range(1,n+1))
    weights={(i,j):1.0+((i*13+j*3)%7)/10.0 for i in horses for j in horses if i<j}
    nodes={i:.2*math.sin(i*2.31)+0.025*i for i in horses}
    val={e:nodes[e[0]]+nodes[e[1]] for e in weights}
    strengths={i:1.0/(1.0+i*.18+i*i*.011) for i in horses}
    return val,weights,strengths


class EdgeBlockHoldoutTests(unittest.TestCase):
    def test_masks_40pct_and_no_training_overlap(self):
        import random
        v,w,s=make_synthetic()
        train,test=partition_edges(v,random.Random(33))
        self.assertEqual(set(train)&set(test),set())
        self.assertEqual(set(train)|set(test),set(v))
        self.assertEqual(len(train),round(TRAIN_FRACTION*len(v)))
        self.assertGreater(len(test),0)

    def test_node_additive_signal_predicts_unseen_40pct(self):
        import random
        y,w,strengths=make_synthetic(10)
        train,test=partition_edges(y,random.Random(112))
        result=evaluate_partition(y,w,node_features(sorted(strengths)),
                                 feature_map(strengths,4),train,test)
        self.assertAlmostEqual(
            result["relative_heldout_R2_vs_train_mean"]["node"],1.0,places=10
        )
        self.assertGreater(result["weighted_test_squared_error"]["global_polynomial4"],1e-8)
        self.assertTrue(result["node_beats_global_smooth"])

    def test_same_horse_smooth_bias_is_global_comparator_and_correctly_fitted(self):
        import random
        y,w,strengths=make_synthetic()
        smooth=feature_map(strengths,4)
        y={e:.3+0.45*x[1]-0.2*x[2]+.12*x[3]+.09*x[4] for e,x in smooth.items()}
        train,test=partition_edges(y,random.Random(112))
        result=evaluate_partition(y,w,node_features(sorted(strengths)),smooth,train,test)
        self.assertAlmostEqual(
            result["relative_heldout_R2_vs_train_mean"]["global_polynomial4"],
            1.0, places=10,
        )

    def test_normalization_constant_does_not_create_out_of_block_skill(self):
        import random
        y,w,s=make_synthetic()
        train,test=partition_edges(y,random.Random(112))
        graph=node_features(sorted(s))
        smooth=feature_map(s,4)
        one=evaluate_partition(y,w,graph,smooth,train,test)
        another=evaluate_partition({e:v+20.7 for e,v in y.items()},w,graph,smooth,train,test)
        for label in ("node","node_ridge_0p1","global_polynomial4"):
            self.assertAlmostEqual(
                one["relative_heldout_R2_vs_train_mean"][label],
                another["relative_heldout_R2_vs_train_mean"][label],places=8
            )

    def test_missing_test_pairs_or_partial_support_fail_closed(self):
        import random
        y,w,s=make_synthetic()
        train,test=partition_edges(y,random.Random(112))
        with self.assertRaisesRegex(ValueError,"wrong_split_support"):
            evaluate_partition(y,w,node_features(sorted(s)),feature_map(s,4),
                               train,test[1:])
        with self.assertRaisesRegex(ValueError,"invalid_train_fraction"):
            partition_edges(y,random.Random(112),frac=.1)
        with self.assertRaisesRegex(ValueError,"invalid_repeated_split_count"):
            evaluate_race("dummy","2026-10-18",s,
                          {i:min(i,8) for i in s},[],n_splits=1)

    def test_nine_races_are_cross_sections_not_repeated_individuals(self):
        evidence=run_analysis(n_splits=9)
        self.assertEqual(evidence["status"],
            "OBSERVED_NINE_RACE_DISJOINT_EDGE_BLOCK_HOLDOUT_NOT_HORSE_REPEATS")
        self.assertEqual(len(evidence["races"]),9)
        self.assertEqual(evidence["by_date"]["2026-10-12"]["race_count"],5)
        self.assertEqual(evidence["by_date"]["2026-10-18"]["race_count"],4)
        self.assertFalse(evidence["biological_individuality_identified"])
        self.assertFalse(evidence["new_horse_prediction"])
        self.assertFalse(evidence["new_date_or_race_validation"])
        self.assertFalse(evidence["outcome_labels_used"])
        self.assertTrue(evidence["horse_number_not_stable_registry_id"])
        for result in evidence["races"]:
            self.assertEqual(result["repeated_splits"],9)
            self.assertEqual(
                result["train_pair_count_each_split"]+
                result["test_pair_count_each_split"],
                result["complete_wide_pair_count"]
            )
            self.assertEqual(set(result["pooled_heldout_R2_vs_train_mean"]),
                             {"node","node_ridge_0p1","global_polynomial4"})
            for v in result["pooled_heldout_R2_vs_train_mean"].values():
                self.assertTrue(math.isfinite(v))
        self.assertGreaterEqual(len(evidence["source_file_sha256"]),30)


if __name__=="__main__":
    unittest.main()
