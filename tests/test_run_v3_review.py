import unittest
from datetime import datetime

from scripts.run_v3_review import run_review


class RunV3ReviewTests(unittest.TestCase):
    def setUp(self):
        self.as_of = datetime.fromisoformat('2026-10-12T10:00:00+09:00')

    def run_row(self, date='2026-09-20', finish=2, margin=0.2):
        return {
            'date': date, 'class': '1勝クラス', 'surface': 'dirt',
            'distance_m': 1200, 'finish': finish, 'beaten_margin_s': margin,
            'source_url': 'https://example.test/race',
        }

    def horse(self, number, odds):
        runs = [
            self.run_row(),
            self.run_row('2026-08-20', 5, 0.8),
            self.run_row('2026-07-20', 6, 0.9),
        ]
        return {
            'number': number, 'name': f'H{number}', 'win_odds': odds,
            'career_starts': 6,
            'history_checked_at_jst': '2026-10-12T09:00:00+09:00',
            'history_source_url': f'https://example.test/h{number}',
            'source_latest_run_date': '2026-09-20',
            'recent_runs': runs,
        }

    def race(self):
        return {
            'race': 12, 'race_id': '2608040512', 'date': '2026-10-12',
            'surface': 'dirt', 'distance_m': 1200,
            'horses': [self.horse(i, float(i)) for i in range(1, 7)],
        }

    def test_pass_returns_pool_and_bounded_shortlist_without_prediction_claims(self):
        out = run_review(self.race(), self.as_of)
        self.assertEqual(out['status'], 'PASS')
        self.assertTrue(out['candidate_pool'])
        self.assertLessEqual(len(out['shortlist']), 7)
        self.assertFalse(out['horse_ranking_produced'])
        self.assertFalse(out['probabilities_assigned'])
        self.assertFalse(out['ticket_selection_performed'])

    def test_data_hold_stops_before_candidate_or_shortlist_output(self):
        race = self.race()
        del race['horses'][0]['recent_runs']
        out = run_review(race, self.as_of)
        self.assertEqual(out['status'], 'DATA_HOLD')
        self.assertEqual(out['candidate_pool'], [])
        self.assertEqual(out['shortlist'], [])


if __name__ == '__main__':
    unittest.main()
