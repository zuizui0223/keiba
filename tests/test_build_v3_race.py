import unittest

from scripts.build_v3_race import merge_history


class BuildV3RaceTests(unittest.TestCase):
    def base(self):
        return {
            'race': 11,
            'date': '2026-10-12',
            'horses': [
                {'number': 1, 'name': 'A', 'mark': '◎', 'notes': ['keep']},
                {'number': 2, 'name': 'B', 'mark': '○', 'notes': ['keep2']},
            ],
        }

    def history(self):
        run = {
            'date': '2026-10-01', 'class': '1勝クラス', 'surface': 'turf',
            'distance_m': 1400, 'finish': 2, 'beaten_margin_s': 0.1,
            'source_url': 'https://example.test/race'
        }
        return {
            'race': 11,
            'history_checked_at_jst': '2026-10-12T10:00:00+09:00',
            'horses': {
                '1': {'career_starts': 3, 'history_source_url': 'https://example.test/a',
                      'source_latest_run_date': '2026-10-01', 'recent_runs': [run, {**run, 'date':'2026-09-01'}, {**run, 'date':'2026-08-01'}]},
                '2': {'career_starts': 3, 'history_source_url': 'https://example.test/b',
                      'source_latest_run_date': '2026-10-01', 'recent_runs': [run, {**run, 'date':'2026-09-01'}, {**run, 'date':'2026-08-01'}]},
            }
        }

    def test_merge_preserves_frozen_prediction_fields(self):
        out = merge_history(self.base(), self.history(), 'base-sha')
        self.assertEqual(out['horses'][0]['mark'], '◎')
        self.assertEqual(out['horses'][0]['notes'], ['keep'])
        self.assertEqual(out['horses'][0]['history_checked_at_jst'], '2026-10-12T10:00:00+09:00')
        self.assertEqual(out['v3_history_migration']['derived_from_blob_sha'], 'base-sha')

    def test_missing_horse_history_is_rejected(self):
        hist = self.history()
        del hist['horses']['2']
        with self.assertRaisesRegex(ValueError, 'history_roster_mismatch'):
            merge_history(self.base(), hist, 'base-sha')

    def test_extra_horse_history_is_rejected(self):
        hist = self.history()
        hist['horses']['3'] = hist['horses']['1']
        with self.assertRaisesRegex(ValueError, 'history_roster_mismatch'):
            merge_history(self.base(), hist, 'base-sha')

    def test_race_mismatch_is_rejected(self):
        hist = self.history()
        hist['race'] = 12
        with self.assertRaisesRegex(ValueError, 'race_mismatch'):
            merge_history(self.base(), hist, 'base-sha')


if __name__ == '__main__':
    unittest.main()
