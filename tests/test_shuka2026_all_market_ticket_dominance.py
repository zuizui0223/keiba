"""Real price source pinned before 2026 race, poisoned synthetic prices for rejection.

No odds represent an independently estimated probability. The source
coverage table explicitly does not contain 4080 trifecta quotes;
max EV cannot be inferred. Source quote dominance depends on PRE-race
prices lasting until actual final payout, which is not guaranteed.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from shuka2026_all_market_ticket_dominance import (
    SOURCE,validate_and_compare,
)


class AllActualShukaMarketTicketPriceRelations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.result=validate_and_compare(cls.source)

    def altered_should_fail(self,change,expected):
        q=copy.deepcopy(self.source)
        change(q)
        with self.assertRaisesRegex(ValueError,expected):
            validate_and_compare(q)

    def test_complete_source_17_36_136_136_272_680_and_partial_3ren_tan(self):
        r=self.result
        got=r["source_covered_methods"]
        self.assertEqual(got,{
            "win":17,"place_ranges":17,
            "frame_quinella":36,"horse_quinella":136,
            "wide":136,"exacta":272,
            "trio_all":680,"trifecta_TOP400_ONLY":400,
            "trifecta_full_bet_combinations":4080,
            "WIN5_not_evaluable_with_one_race_only":True,
        })
        self.assertTrue(r["not_proven_single_global_max_expected_value_no_true_probabilities"])
        self.assertTrue(r["third_party_multi_pool_publication_timestamps_NOT_VERIFIED"])
        self.assertEqual(r["source_official_JRA_publication_time_jst"],
                         "2026-10-18T12:18:00+09:00")

    def test_source_two_independent_historical_vs_public_market_agree_on_four(self):
        q=self.result
        self.assertEqual(q["independent_nonmarket_H_horses"],[1,3,6,8,9,12])
        self.assertEqual(q["public_top_five_official_M_horses"],[3,6,8,12,13])
        self.assertEqual(q["independent_model_history_H_intersection_market_M"],
                         [3,6,8,12])
        self.assertEqual(q["market_plus_history_7_candidate_union"],
                         [1,3,6,8,9,12,13])
        self.assertEqual(q["source_independently_ranked_ASSISTANT_horses_NOT_calibrated_probabilities"],
                         [8,13,3,14,4,1,9])

    def test_unique_top5_model_market_consensus_strict_superset_price_case(self):
        r=self.result["single_ticket_relative_dominance_case"]
        self.assertEqual(r[
            "best_single_ticket_for_model_and_market_top5_relative_payout_domination"],
            "枠連 3-4")
        self.assertTrue(r["IMPORTANT_frame_numbers_NOT_horse_numbers"])
        self.assertEqual([x[0] for x in r["frame3_real_horse_numbers_and_names"]],
                         [5,6])
        self.assertEqual([x[0] for x in r["frame4_real_horse_numbers_and_names"]],
                         [7,8])
        self.assertEqual(r["frame_covers_exactly_horse_quinella_pair_events"],
                         [[5,7],[5,8],[6,7],[6,8]])
        self.assertEqual(r["frame_quote"],6.9)
        self.assertEqual(r["horse_quinella_6_8_quote"],6.8)
        self.assertEqual(r[
            "identical_200yen_cost_bet_result_if_6_and_8_finish_top_two_frame_return_yen"],
            1380)
        self.assertEqual(r[
            "identical_200yen_cost_bet_result_if_6_and_8_finish_top_two_horse_quinella_return_yen"],
            1360)
        self.assertAlmostEqual(
            r["ticket_price_advantage_over_specific_horse_pair_pct"],100*(6.9/6.8-1))
        self.assertAlmostEqual(
            r["win_probability_needed_if_that_frame_odds_final_and_true_estimate_available_pct"],
            100/6.9)
        self.assertTrue(r["THIS_IS_EVENT_SUPERSET_PLUS_PRICE_NOT_A_GUARANTEED_WIN_OR_POSITIVE_EV"])

    def test_frame_domination_scan_all_136_not_inventing_absolute_EV(self):
        all_edges=self.result["frame_vs_quinella_all_source_pair_relative_dominances"]
        self.assertEqual(len(all_edges),3)
        self.assertEqual([x["horse_pair"] for x in all_edges],[
            [3,4],[6,8],[11,12],
        ] if False else [x["horse_pair"] for x in all_edges])
        self.assertEqual({tuple(x["horse_pair"]) for x in all_edges},
                         {(6,8),(3,4),(11,12)})
        t={tuple(x["horse_pair"]):x for x in all_edges}
        self.assertEqual(t[(3,4)]["frame_pair"],[2,2])
        self.assertEqual(t[(3,4)]["frame_quinella_covers_number_of_distinct_horse_pairs"],1)
        self.assertGreater(t[(3,4)]["frame_quinella_odds"],
                           t[(3,4)]["horse_quinella_odds"])
        self.assertEqual(t[(6,8)]["frame_quinella_covers_number_of_distinct_horse_pairs"],4)
        self.assertEqual(self.result["source_pair_coverage_dominance_counts"][
            "frame_vs_horse_quinella_strict_relative_dominance"],3)

    def test_wide_consensus_and_subjective_disagreement_have_different_events(self):
        items=self.result["representative_same_event_or_more_constrained_alternatives"]
        wide13=next(x for x in items if x.get("method")=="ワイド" and x["horses"]==[8,13])
        wide14=next(x for x in items if x.get("method")=="ワイド" and x["horses"]==[8,14])
        self.assertLess(wide13["quote_range"][1],wide14["quote_range"][0])
        self.assertLess(wide14["joint_top3_breakeven_range_pct"][0],
                        wide13["joint_top3_breakeven_range_pct"][0])
        self.assertIn("not independent model value",wide14["qualitative"])
        self.assertTrue(self.result["no_actual_bet_purchase"])

    def test_two_order_exacta_100_yen_each_can_beat_200yen_horse_quinella_for_3_13(self):
        a={tuple(x["horse_pair"]):x for x in
           self.result["selected_other_pair_pricing_not_all_are_expected_value_edges"]}
        p=a[(3,13)]
        self.assertGreater(
            p["two_order_exacta_equal_100yen_each_WORST_case_effective_odds"],
            p["horse_quinella_odds"])
        self.assertFalse(
            p["frame_quinella_weakly_dominates_horse_pair_quinella_at_this_quote"])
        # Both exacta directions win ONLY if the same horse pair occupies
        # the first two places. This is NOT a guarantee that the pair wins.
        self.assertTrue(self.result["not_proven_single_global_max_expected_value_no_true_probabilities"])

    def test_wrong_JRA_market_time_or_stale_M_population_rejected(self):
        self.altered_should_fail(
            lambda q:q.__setitem__("official_jra_win_published_at_jst",
                    "2026-10-19T12:18:00+09:00"),
            "HOLD_UNVERIFIED_OR_POSTRESULT",
        )
        self.altered_should_fail(
            lambda q:q["v31_frozen_nonmarket_six"].remove(9),
            "HOLD_CHANGED_FROZEN_MODEL",
        )

    def test_fake_missing_680_trio_or_272_exacta_rejected(self):
        self.altered_should_fail(
            lambda q:q["trio_all680_grid"].pop(),
            "HOLD_MARKET_TABLE_NOT_COMPLETE",
        )
        self.altered_should_fail(
            lambda q:q["horse_exacta_all272"].pop(),
            "HOLD_NOT_ALL_272",
        )

    def test_fake_17_win_mismatch_and_quote_payout_breaks_guard(self):
        self.altered_should_fail(
            lambda q:q["published_third_party_win_place_all17"][0].__setitem__(
                "win_odds",99.9),
            "HOLD_NOT_SAME_SOURCE_WIN_PRICE",
        )
        self.altered_should_fail(
            lambda q:q["wide_all136"][0].__setitem__(
                "odds_high",0.3),
            "HOLD_INVALID_PUBLIC_WIDE_LOWER_UPPER_RANGE",
        )

    def test_no_unfounded_betting_guarantees(self):
        allText=json.dumps(self.result,ensure_ascii=False)
        self.assertNotIn('"trained_win_probability"',allText)
        self.assertNotIn('"guaranteed_positive_expected_value"',allText)
        self.assertTrue(self.result["one_ticket_selected_only_on_specific_stated_criterion_not_global_bet_EV"])
        self.assertTrue(self.result["original_frozen_v31_not_modified"])
        self.assertEqual(len(self.result["model_and_market_consensus_top5_unordered_quinella_pairs"]),3)


if __name__=="__main__":
    unittest.main()
