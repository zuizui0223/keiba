"""No finite cross-section horse-ID identification without repeat IDs or quote ties."""
import math
import unittest
from scripts.ecology_ticket_market_odds_tie_identification import (
    analyze_tied_quotes, original_display_odds, run_analysis,
)


def setup(tied=True, unequal_wide=True):
    n=9
    odds={i:2.0+i for i in range(1,n+1)}
    if tied:
        odds[2]=odds[1]
    strength={i:1.0/o for i,o in odds.items()}
    frames={i:min(i,8) for i in odds}
    prices={}
    for i in odds:
        for j in odds:
            if i<j:
                val=10.0 + i*2.0 + j*.75
                if not unequal_wide and i in (1,2) and j>=3:
                    val=15.0+j*.75
                prices[(i,j)]=val
    wide=[{"selection":list(e),"odds_low":v,"odds_high":v+1}
          for e,v in prices.items()]
    return strength,frames,wide


class OddsTieIdentificationTests(unittest.TestCase):
    def test_tied_win_prices_distinguish_opponent_matched_wide_prices(self):
        s,frames,wide=setup(tied=True,unequal_wide=True)
        report=analyze_tied_quotes("syn-race","2026-10-12",s,frames,wide)
        self.assertEqual(report["tied_horse_pair_count"],1)
        self.assertEqual(report["same_win_quote_opponent_pair_comparisons"],7)
        self.assertGreater(report["same_win_quote_opponent_price_difference_count"],0)
        self.assertGreater(report["maximum_abs_matched_logprice_contrast"],0)
        self.assertFalse(report["distinct_win_odds_can_always_support_arbitrary_finite_function_interpolation"])
        self.assertFalse(report["stable_registry_horse_IDs_available_for_this_test"])

    def test_equal_win_and_equal_wide_opponent_prices_have_zero_contrast(self):
        s,frames,wide=setup(tied=True,unequal_wide=False)
        report=analyze_tied_quotes("syn-race","2026-10-12",s,frames,wide)
        self.assertEqual(report["same_win_quote_opponent_pair_comparisons"],7)
        self.assertTrue(report["same_win_quote_opponent_differences_are_all_exactly_zero"])
        self.assertEqual(report["same_win_quote_opponent_price_difference_count"],0)

    def test_unique_win_prices_do_not_identify_horse_specific_effects(self):
        s,frames,wide=setup(tied=False)
        report=analyze_tied_quotes("syn-race","2026-10-12",s,frames,wide)
        self.assertEqual(report["tied_win_quote_groups"],0)
        self.assertEqual(report["tied_horse_pair_count"],0)
        self.assertIsNone(report["maximum_abs_matched_logprice_contrast"])
        self.assertTrue(report["distinct_win_odds_can_always_support_arbitrary_finite_function_interpolation"])

    def test_hidden_non_tenth_quote_must_not_be_rounded_into_fake_tie(self):
        s,frames,wide=setup()
        s[1]=1./3.07
        with self.assertRaisesRegex(ValueError,"non_tenth_decimal_display"):
            original_display_odds(s)
        with self.assertRaisesRegex(ValueError,"non_tenth_decimal_display"):
            analyze_tied_quotes("syn-race","2026-10-12",s,frames,wide)

    def test_archived_nine_races_are_not_genetic_or_longitudinal_proofs(self):
        result=run_analysis()
        self.assertEqual(result["status"],
            "OBSERVED_DISPLAY_WIN_QUOTE_TIE_FALSIFICATION_NOT_BIOLOGICAL_IDENTIFICATION")
        self.assertEqual(len(result["races"]),9)
        self.assertEqual(result["by_date"]["2026-10-12"]["race_count"],5)
        self.assertEqual(result["by_date"]["2026-10-18"]["race_count"],4)
        self.assertTrue(result["no_registered_horse_identity_repeatability_tested"])
        self.assertTrue(result["no_independent_time_series_or_outcome_validation"])
        self.assertTrue(result["no_inference_about_heritability_or_actual_voter_behavior"])
        for race in result["races"]:
            self.assertLessEqual(race["tied_win_quote_groups"],race["tied_horse_pair_count"])
            self.assertEqual(race["runners"]-race["unique_display_win_quote_levels"]>=1,
                            race["tied_horse_pair_count"]>0)
            if race["tied_horse_pair_count"]:
                self.assertGreater(race["same_win_quote_opponent_pair_comparisons"],0)
                self.assertTrue(math.isfinite(race["maximum_abs_matched_logprice_contrast"]))
        self.assertGreaterEqual(len(result["input_file_sha256"]),30)


if __name__=="__main__":
    unittest.main()
