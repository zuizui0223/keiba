import unittest
from datetime import datetime

from scripts.freeze_v3_forward_test import build_manifest


class FreezeV3ForwardTestTests(unittest.TestCase):
    def race(self):
        return {
            'race': 12,
            'race_id': '2608040512',
            'date': '2026-10-12',
            'start_jst': '2026-10-12T16:30:00+09:00',
            'surface': 'dirt',
            'distance_m': 1200,
            'class': '1勝クラス',
            'horses': [
                {
                    'number': 1, 'name': 'A', 'win_odds': 2.0, 'career_starts': 3,
                    'history_checked_at_jst': '2026-10-12T10:00:00+09:00',
                    'history_source_url': 'https://example.test/a',
                    'source_latest_run_date': '2026-09-20',
                    'recent_runs': [
                        {'date':'2026-09-20','class':'1勝クラス','surface':'dirt','distance_m':1200,'finish':2,'beaten_margin_s':0.2,'source_url':'https://example.test/a1'},
                        {'date':'2026-08-20','class':'1勝クラス','surface':'dirt','distance_m':1200,'finish':5,'beaten_margin_s':0.7,'source_url':'https://example.test/a2'},
                        {'date':'2026-07-20','class':'1勝クラス','surface':'dirt','distance_m':1400,'finish':6,'beaten_margin_s':0.8,'source_url':'https://example.test/a3'},
                    ],
                },
                {
                    'number': 2, 'name': 'B', 'win_odds': 10.0, 'career_starts': 3,
                    'history_checked_at_jst': '2026-10-12T10:00:00+09:00',
                    'history_source_url': 'https://example.test/b',
                    'source_latest_run_date': '2026-09-15',
                    'recent_runs': [
                        {'date':'2026-09-15','class':'未勝利','surface':'dirt','distance_m':1200,'finish':1,'beaten_margin_s':0.0,'source_url':'https://example.test/b1'},
                        {'date':'2026-08-15','class':'未勝利','surface':'dirt','distance_m':1400,'finish':4,'beaten_margin_s':0.6,'source_url':'https://example.test/b2'},
                        {'date':'2026-07-15','class':'未勝利','surface':'dirt','distance_m':1400,'finish':5,'beaten_margin_s':0.8,'source_url':'https://example.test/b3'},
                    ],
                },
            ],
        }

    def test_freeze_records_hashes_candidates_and_market_baseline(self):
        out = build_manifest(
            self.race(),
            datetime.fromisoformat('2026-10-12T16:00:00+09:00'),
            data_blob_sha='data-sha',
            generator_blob_sha='generator-sha',
        )
        self.assertEqual(out['status'], 'FROZEN')
        self.assertEqual(out['data_blob_sha'], 'data-sha')
        self.assertEqual(out['candidate_generator_blob_sha'], 'generator-sha')
        self.assertEqual(out['market_top4'], [1, 2])
        self.assertEqual(set(out['candidates']), {1, 2})
        self.assertFalse(out['result_attached'])

    def test_after_cutoff_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'freeze_after_cutoff'):
            build_manifest(
                self.race(),
                datetime.fromisoformat('2026-10-12T16:28:00+09:00'),
                data_blob_sha='data-sha',
                generator_blob_sha='generator-sha',
            )

    def test_data_hold_is_rejected(self):
        race = self.race()
        del race['horses'][0]['recent_runs']
        with self.assertRaisesRegex(ValueError, 'data_hold'):
            build_manifest(
                race,
                datetime.fromisoformat('2026-10-12T16:00:00+09:00'),
                data_blob_sha='data-sha',
                generator_blob_sha='generator-sha',
            )


if __name__ == '__main__':
    unittest.main()
