#!/usr/bin/env python3
"""2026 Tenno Sho no-result public quote M0 and hypothetical causal graph."""
from __future__ import annotations
import math
from pathlib import Path
import sys
import unittest

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
if np is not None:
    import keiba_tenno_20261101_public_market_shadow as m


@unittest.skipIf(np is None,"NumPy is required for existing linked model")
class DatedTennoPublicM0Tests(unittest.TestCase):
    def test_complete_stable_17_horse_JRA_card_odds_field(self):
        odds=m._field()
        self.assertEqual(set(odds),set(range(1,18)))
        self.assertEqual(len(odds),17)
        self.assertEqual(odds[7],2.4)
        self.assertEqual(odds[1],2.5)
        self.assertEqual(odds[17],11.4)
        self.assertEqual(odds[3],9.8)
        self.assertTrue(all(x>1 for x in odds.values()))
        self.assertEqual(m.RACE_LOCAL_POST,"2026-11-01T15:40:00+09:00")
        self.assertEqual(m.MARKET_SOURCE_REPORTED_CLOCK,
                         "2026-10-31T17:00:00+09:00")
        self.assertTrue(m.SOURCE_ODDS_URL.startswith("https://"))
        self.assertTrue(m.SOURCE_JRA_CARD_URL.startswith("https://"))

    def test_source_M0_is_not_true_JRA_vote_fraction_or_prospectively_verified(self):
        a=m.audit(include_physical=False)
        self.assertTrue(a["status"].startswith("EXPLORATORY_PRESTART"))
        self.assertEqual(a["full_horse_field"],17)
        self.assertTrue(a[
            "market_implied_proxy_not_calibrated_true_win_probabilities"])
        self.assertTrue(a[
            "coherent_PL_ticket_events_not_actual_pool_ticket_odds"])
        self.assertFalse(a["actual_JRA_outcome_read"])
        self.assertEqual(a["independent_asof_authenticated_source_receipts"],0)
        self.assertEqual(a["real_WIN_snapshot_count"],1)
        self.assertFalse(a["full_same_provider_real_WIDE_grid_received"])
        self.assertFalse(a[
            "prediction_eligible_for_PR22_or_PR30_capture_certificate"])
        self.assertEqual(a["synthetic_horse_social_sensitivity"],"NOT_RUN")
        self.assertAlmostEqual(sum(r["market_M0_win_index"]
                             for r in a["all_horses_source_market_M0_and_top3"]),
                         1.,places=12)

    def test_top3_and_pair_trio_PL_are_coherent_and_race_field_not_selected(self):
        a=m.audit(include_physical=False)
        bynum={r["horse_number"]:r for r in
               a["all_horses_source_market_M0_and_top3"]}
        self.assertEqual(set(bynum),set(range(1,18)))
        self.assertAlmostEqual(sum(r["Plackett_Luce_top3_index"]
                    for r in bynum.values()),3.,places=10)
        self.assertEqual(bynum[10][
            "JRA_2026_best_pre_rating_not_course_specific"],None)
        self.assertGreater(bynum[7]["market_M0_win_index"],
                           bynum[1]["market_M0_win_index"])
        self.assertGreater(bynum[1]["market_M0_win_index"],.30)
        self.assertGreater(bynum[7]["Plackett_Luce_top3_index"],.75)
        p=a["selected_coherent_event_indices"]
        self.assertGreater(p["unordered_umaren_probability_index"]["1-7"],.25)
        self.assertGreater(p["both_top3_wide_event_probability_index"]["1-7"],.50)
        self.assertGreater(p["unordered_top3_trio_event_probability_index"]["1-3-7"],.10)
        self.assertTrue(all(0<=v<=1 for d in p.values() for v in d.values()))

    def test_fixed_JRA_rating_only_covariate_missing_value_never_claimed_measured(self):
        rated=m._rating_prior()
        self.assertEqual(len(rated),17)
        self.assertAlmostEqual(sum(rated),1,places=12)
        self.assertGreater(rated[0],rated[2])
        self.assertEqual(m.FIELD[9][3],None)

    def test_future_market_or_winner_mutation_not_input_to_source_shadow(self):
        a=m.audit(include_physical=False)
        b=m.audit(include_physical=False)
        self.assertEqual(a,b)
        self.assertFalse(a["actual_JRA_outcome_read"])
        self.assertFalse(a["predictive_skill_proven_on_new_target"])

    def test_linked_horse_abm_pde_and_staged_bettor_synthetic_only(self):
        a=m.audit(include_physical=True,horse_draws=45,seed_count=1,
                  seed=20261031)
        physical=a["synthetic_horse_social_sensitivity"]
        pde=physical["paired_PDE_and_particle_numeric_check"]
        self.assertTrue(pde["nonnegative_density"])
        self.assertAlmostEqual(pde["min_horse_probability_mass"],1,places=9)
        self.assertAlmostEqual(pde["max_horse_probability_mass"],1,places=9)
        self.assertTrue(pde["finite_horse_factorized_PDE_NOT_true_GPS_validated"])
        self.assertEqual(set(physical["averaged_over_synthetic_seeds_not_new_real_races"]),
                         {"market_price_q0",
                          "JRA_rating_only_NEUTRAL_missing_imputation_TOY"})
        for alternative in physical[
                "averaged_over_synthetic_seeds_not_new_real_races"].values():
            for k in ("hypothetical_horse_win",
                      "synthetic_bettors_round1",
                      "synthetic_bettors_no_signal_round5"):
                self.assertAlmostEqual(sum(alternative[k].values()),1,places=10)
        self.assertTrue(physical["settings_fixed_hypothetical_not_fitted"][
            "no_two_real_synchronized_quote_snapshots"])
        self.assertFalse(a["actual_JRA_outcome_read"])


if __name__=="__main__":
    unittest.main()
