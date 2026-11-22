import unittest
from scripts.ticket_rank_trainer import fit_horse_log_strength, score_future_race


class TicketRankTrainerTests(unittest.TestCase):
    def setUp(self):
        self.races = []
        for i in range(8):
            self.races.append({
                'race_id': str(i), 'start_jst': f'2026-10-{i+1:02d}T14:00:00+09:00',
                'result_known_at_jst': f'2026-10-{i+1:02d}T15:00:00+09:00',
                'top3': [4, 3, 2],
                'horses': [
                    {'number': n, 'features_as_of_jst': f'2026-10-{i+1:02d}T10:00:00+09:00',
                     'features': {'pace': n, 'track': n * 0.5 if i % 2 else 0.5*n + 0.1*i}}
                    for n in range(1,5)
                ],
            })
        self.future = {
            'race_id': 'future', 'start_jst': '2026-10-10T14:00:00+09:00',
            'horses': [
                {'number': n, 'features_as_of_jst': '2026-10-10T10:00:00+09:00',
                 'features': {'pace': n, 'track': n * 0.5}} for n in range(1, 5)
            ],
        }

    def test_fit_and_forecast_monotonic_example(self):
        model = fit_horse_log_strength(self.races, ['pace', 'track'], '2026-10-09T00:00:00+09:00',
                                       steps=70)
        scores = score_future_race(model, self.future, '2026-10-10T11:00:00+09:00')
        self.assertEqual(len(scores['log_scores']), 4)
        self.assertGreater(scores['log_scores']['4'], scores['log_scores']['1'])
        self.assertEqual(model['training_race_count'], 8)
        self.assertFalse(model['calibrated'])

    def test_historical_future_result_leak_is_rejected(self):
        with self.assertRaises(ValueError):
            fit_horse_log_strength(self.races, ['pace'], '2026-10-03T00:00:00+09:00')
        model = fit_horse_log_strength(self.races, ['pace'], '2026-10-09T00:00:00+09:00', steps=2)
        self.future['top3'] = [4, 3, 2]
        with self.assertRaises(ValueError):
            score_future_race(model, self.future, '2026-10-10T11:00:00+09:00')

    def test_feature_after_as_of_rejected(self):
        model = fit_horse_log_strength(self.races, ['pace'], '2026-10-09T00:00:00+09:00', steps=2)
        self.future['horses'][0]['features_as_of_jst'] = '2026-10-10T12:00:00+09:00'
        with self.assertRaises(ValueError):
            score_future_race(model, self.future, '2026-10-10T11:00:00+09:00')


if __name__ == '__main__':
    unittest.main()
