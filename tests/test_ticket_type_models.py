"""Exact ticket-event oracle and strict pre-race timestamp regression tests."""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ticket_type_models import (  # noqa: E402
    evaluate_outcome, event_selection, forecast_basket, forecast_snapshot, predict_tickets,
)


class TicketTypeProbabilityTests(unittest.TestCase):
    def test_uniform_four_horses_exact_event_oracle(self):
        dist = predict_tickets({i: 1.0 for i in range(1, 5)}, {i: i for i in range(1, 5)})
        self.assertNotIn('place', dist)
        self.assertNotIn('frame', dist)
        for kind, key, expected in (
            ('win', (1,), 1/4), ('quinella', (1, 2), 1/6),
            ('exacta', (1, 2), 1/12), ('wide', (1, 2), 1/2),
            ('trio', (1, 2, 3), 1/4), ('trifecta', (1, 2, 3), 1/24),
        ):
            self.assertAlmostEqual(dist[kind][key], expected, msg=kind)
        self.assertEqual([len(dist[k]) for k in ('win', 'quinella', 'wide', 'exacta', 'trio', 'trifecta')],
                         [4, 6, 6, 12, 4, 24])
        for kind, expected in [('win', 1), ('quinella', 1), ('wide', 3),
                               ('exacta', 1), ('trio', 1), ('trifecta', 1)]:
            self.assertAlmostEqual(math.fsum(dist[kind].values()), expected)

    def test_place_payout_slots_switch_at_eight(self):
        five = predict_tickets({i: 1.0 for i in range(1, 6)}, {i: i for i in range(1, 6)})
        self.assertAlmostEqual(five['place'][(1,)], 2 / 5)
        self.assertAlmostEqual(sum(five['place'].values()), 2)
        eight = predict_tickets({i: 1.0 for i in range(1, 9)}, {i: i for i in range(1, 9)})
        self.assertAlmostEqual(eight['place'][(1,)], 3 / 8)
        self.assertAlmostEqual(sum(eight['place'].values()), 3)
        self.assertNotIn('frame', eight)  # No shared frames; not on sale under 9.

    def test_frame_same_frame_zorome_without_same_horse(self):
        frames = {i: i if i <= 8 else 8 for i in range(1, 10)}
        dist = predict_tickets({i: 1.0 for i in frames}, frames)
        self.assertEqual(len(dist['frame']), 29)  # 8C2 + frame 8-8
        self.assertAlmostEqual(dist['frame'][(8, 8)], 2/(9*8))
        self.assertAlmostEqual(sum(dist['frame'].values()), 1)
        self.assertEqual(event_selection('frame', (8, 9, 1), frames), [(8, 8)])
        self.assertTrue(all(len(set(k)) == 2 for k in dist['exacta']))

    def test_frame_exception_and_post_sale_place_slots(self):
        frames = {i: i for i in range(1, 9)}
        frames[8] = 7
        dist = predict_tickets({i: 1.0 for i in frames}, frames, on_sale_field_size=9)
        self.assertIn('frame', dist)
        self.assertIn((7, 7), dist['frame'])
        self.assertAlmostEqual(sum(dist['place'].values()), 3)

    def test_weighted_model_win_marginal_exact(self):
        strengths = {1: 7.0, 2: 2.0, 3: 1.0, 4: 1.0}
        out = predict_tickets(strengths, {i: i for i in strengths})
        self.assertAlmostEqual(out['win'][(1,)], 7 / 11)
        self.assertGreater(out['exacta'][(1, 2)], out['exacta'][(2, 1)])

    def test_score_against_result_is_a_separate_function(self):
        strengths = {i: 1.0 for i in range(1, 6)}
        frame = {i: i for i in strengths}
        scores = evaluate_outcome(strengths, frame, [2, 1, 4])
        self.assertEqual(scores['place']['winning_ticket_count'], 2)
        self.assertEqual(scores['wide']['winning_ticket_count'], 3)
        self.assertEqual(scores['trio']['winning_ticket_count'], 1)
        self.assertTrue(0 < scores['trifecta']['brier_mean_per_ticket'] < 1)
        with self.assertRaises(ValueError):
            evaluate_outcome(strengths, frame, [2, 2, 4])

    def test_box_events_overlap_and_are_not_summed(self):
        strengths = {i: 1.0 for i in range(1, 5)}
        frames = {i: i for i in strengths}
        basket = forecast_basket(strengths, frames, [
            {'kind': 'wide', 'selection': [1, 2], 'odds_low': '3.0', 'stake_yen': 100},
            {'kind': 'wide', 'selection': [1, 3], 'odds_low': 3.0, 'stake_yen': 100},
        ])
        self.assertAlmostEqual(basket['expected_winning_ticket_count'], 1)
        self.assertAlmostEqual(basket['probability_at_least_one_hit'], 3/4)
        self.assertAlmostEqual(basket['hypothetical_expected_return_low_yen'], 300)
        self.assertAlmostEqual(basket['hypothetical_probability_net_profit_low'], 3/4)
        with self.assertRaises(ValueError):
            forecast_basket(strengths, frames, [
                {'kind': 'win', 'selection': [1]}, {'kind': 'win', 'selection': [1]}])

    def test_fail_closed_inputs(self):
        for bad in ({1: 1, 2: 0, 3: 1}, {1: 1, 2: float('nan'), 3: 1}):
            with self.assertRaises(ValueError):
                predict_tickets(bad, {1: 1, 2: 1, 3: 2})
        with self.assertRaises(ValueError):
            predict_tickets({1: 1., 2: 1.}, {1: 1})
        with self.assertRaises(ValueError):
            predict_tickets({1: 1., 2: 1.}, {1: 1, 2: 2}, on_sale_field_size=1)


class MarketSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.as_of = '2026-10-12T13:45:00+09:00'
        self.snapshot = {
            'race_id': 'testrace', 'start_jst': '2026-10-12T14:00:00+09:00',
            'checked_at_utc': '2026-10-12T04:44:55+00:00',
            'horse_frames': {'1': 1, '2': 1, '3': 2, '4': 3, '5': 4},
            'markets': {
                'win': {
                    'updated_at_jst': '2026-10-12T13:44:00+09:00',
                    'observed_at_utc': '2026-10-12T04:44:55+00:00',
                    'quotes': [{'selection': [i], 'odds_low': 2.0 + i, 'odds_high': 2.0 + i}
                               for i in range(1, 6)],
                },
                'trifecta': {
                    'updated_at_jst': '2026-10-12T13:44:00+09:00',
                    'observed_at_utc': '2026-10-12T04:44:55+00:00',
                    'quotes': [{'selection': [1, 2, 3], 'odds_low': 20, 'odds_high': 20}],
                },
                'place': {
                    'updated_at_jst': '2026-10-12T13:44:00+09:00',
                    'observed_at_utc': '2026-10-12T04:44:55+00:00',
                    'quotes': [{'selection': [1], 'odds_low': 1.3, 'odds_high': 1.9}],
                },
            },
        }

    def test_report_all_eight_types_and_partial_odds(self):
        report = forecast_snapshot(self.snapshot, self.as_of, top=120)
        self.assertEqual(report['source'], 'MARKET_ONLY_BASELINE_NOT_INDEPENDENT')
        self.assertEqual(set(report['ticket_types']), {'win','place','frame','quinella','wide','exacta','trio','trifecta'})
        self.assertEqual(report['ticket_types']['trifecta']['quoted_count'], 1)
        self.assertEqual(report['ticket_types']['trifecta']['selection_count'], 60)
        self.assertFalse(report['ticket_types']['trifecta']['quoted_market_complete'])
        self.assertEqual(report['ticket_types']['place']['quoted_count'], 1)
        self.assertAlmostEqual(report['ticket_types']['place']['expected_winning_selections'], 2)
        self.assertTrue(all('hypothetical_ev_low_per_100_yen' not in row
                            for row in report['ticket_types']['trifecta']['top_by_probability']
                            if row['selection'] != [1,2,3]))

    def test_saved_kyoto8_real_market_snapshot_integration(self):
        snapshot = json.loads((ROOT / 'data/2026-10-12/r8_markets_latest.json').read_text(encoding='utf-8'))
        forecast = forecast_snapshot(snapshot, '2026-10-12T13:45:00+09:00', top=3)
        self.assertEqual(forecast['horse_count'], 11)
        self.assertEqual({kind: row['selection_count'] for kind, row in forecast['ticket_types'].items()},
                         {'win': 11, 'place': 11, 'frame': 31, 'quinella': 55,
                          'wide': 55, 'exacta': 110, 'trio': 165, 'trifecta': 990})
        self.assertEqual(forecast['ticket_types']['trifecta']['quoted_count'], 400)
        self.assertFalse(forecast['ticket_types']['trifecta']['quoted_market_complete'])
        self.assertAlmostEqual(forecast['ticket_types']['win']['top_by_probability'][0]['probability'],
                               0.20287, places=4)

    def test_time_leakage_refused(self):
        for time in ('2026-10-12T13:40:00+09:00', '2026-10-12T14:00:00+09:00'):
            with self.assertRaises(ValueError):
                forecast_snapshot(self.snapshot, time)
        bad = copy.deepcopy(self.snapshot)
        bad['markets']['trifecta']['updated_at_jst'] = '2026-10-12T13:46:00+09:00'
        with self.assertRaises(ValueError):
            forecast_snapshot(bad, self.as_of)

    def test_external_requires_frozen_and_matching_scores(self):
        extra = {
            'race_id': 'testrace', 'training_data_end_jst': '2026-10-10T00:00:00+09:00',
            'scores_frozen_at_jst': '2026-10-12T13:43:00+09:00',
            'log_scores': {str(i): i/10 for i in range(1, 6)},
        }
        report = forecast_snapshot(self.snapshot, self.as_of, source='external', external_scores=extra)
        self.assertEqual(report['source'], 'EXTERNAL_FROZEN_SCORES_NOT_YET_VALIDATED')
        bad = dict(extra, training_data_end_jst='2026-10-12T13:46:00+09:00')
        with self.assertRaises(ValueError):
            forecast_snapshot(self.snapshot, self.as_of, source='external', external_scores=bad)
        missing = dict(extra, log_scores={'1': 0.2})
        with self.assertRaises(ValueError):
            forecast_snapshot(self.snapshot, self.as_of, source='external', external_scores=missing)

    def test_no_missing_winners_or_fake_ev(self):
        malformed = copy.deepcopy(self.snapshot)
        malformed['markets']['win']['quotes'] = malformed['markets']['win']['quotes'][:-1]
        with self.assertRaises(ValueError):
            forecast_snapshot(malformed, self.as_of)


if __name__ == '__main__':
    unittest.main()
