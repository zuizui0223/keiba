import unittest
from datetime import datetime

from scripts.generate_v3_candidates import generate_candidates


class V3CandidateGenerationTests(unittest.TestCase):
    def setUp(self):
        self.as_of = datetime.fromisoformat('2026-10-12T10:00:00+09:00')
        self.race = {
            'race': 12,
            'race_id': '2608040512',
            'date': '2026-10-12',
            'surface': 'dirt',
            'distance_m': 1200,
            'horses': [],
        }

    def horse(self, number=1, career_starts=8, runs=None):
        if runs is None:
            runs = [
                {'date':'2026-09-20','class':'1勝クラス','surface':'dirt','distance_m':1200,
                 'finish':2,'beaten_margin_s':0.2,'source_url':'https://example.test/r1'},
                {'date':'2026-08-20','class':'1勝クラス','surface':'dirt','distance_m':1400,
                 'finish':6,'beaten_margin_s':0.8,'source_url':'https://example.test/r2'},
                {'date':'2026-07-20','class':'1勝クラス','surface':'dirt','distance_m':1200,
                 'finish':5,'beaten_margin_s':0.7,'source_url':'https://example.test/r3'},
            ]
        return {
            'number':number, 'name':f'H{number}', 'career_starts':career_starts,
            'history_checked_at_jst':'2026-10-12T09:00:00+09:00',
            'history_source_url':f'https://example.test/h{number}',
            'source_latest_run_date':runs[0]['date'] if runs else None,
            'recent_runs':runs,
        }

    def test_recent_similar_distance_win_is_candidate(self):
        h = self.horse(runs=[
            {'date':'2026-09-20','class':'1勝クラス','surface':'dirt','distance_m':1200,
             'finish':1,'beaten_margin_s':0.0,'source_url':'https://example.test/r1'},
            {'date':'2026-08-20','class':'1勝クラス','surface':'dirt','distance_m':1400,
             'finish':5,'beaten_margin_s':0.7,'source_url':'https://example.test/r2'},
            {'date':'2026-07-20','class':'1勝クラス','surface':'dirt','distance_m':1200,
             'finish':6,'beaten_margin_s':0.8,'source_url':'https://example.test/r3'},
        ])
        self.race['horses'] = [h]
        out = generate_candidates(self.race, self.as_of)
        row = out['horse_features'][0]
        self.assertTrue(row['candidate'])
        self.assertIn('recent_similar_distance_win', row['positive_signals'])

    def test_close_similar_distance_finish_is_candidate(self):
        self.race['horses'] = [self.horse()]
        out = generate_candidates(self.race, self.as_of)
        row = out['horse_features'][0]
        self.assertTrue(row['candidate'])
        self.assertIn('recent_similar_distance_close_finish', row['positive_signals'])

    def test_lightly_raced_latest_win_expands_distance_window(self):
        h = self.horse(career_starts=4, runs=[
            {'date':'2026-09-20','class':'未勝利','surface':'dirt','distance_m':1500,
             'finish':1,'beaten_margin_s':0.0,'source_url':'https://example.test/r1'},
            {'date':'2026-08-20','class':'未勝利','surface':'dirt','distance_m':1400,
             'finish':4,'beaten_margin_s':0.6,'source_url':'https://example.test/r2'},
            {'date':'2026-07-20','class':'未勝利','surface':'dirt','distance_m':1400,
             'finish':5,'beaten_margin_s':0.8,'source_url':'https://example.test/r3'},
        ])
        self.race['horses'] = [h]
        out = generate_candidates(self.race, self.as_of)
        row = out['horse_features'][0]
        self.assertTrue(row['candidate'])
        self.assertIn('lightly_raced_latest_win', row['positive_signals'])
        self.assertNotIn('recent_similar_distance_win', row['positive_signals'])

    def test_layoff_is_uncertainty_not_exclusion(self):
        h = self.horse(runs=[
            {'date':'2026-06-01','class':'1勝クラス','surface':'dirt','distance_m':1200,
             'finish':2,'beaten_margin_s':0.2,'source_url':'https://example.test/r1'},
            {'date':'2026-05-01','class':'1勝クラス','surface':'dirt','distance_m':1200,
             'finish':5,'beaten_margin_s':0.6,'source_url':'https://example.test/r2'},
            {'date':'2026-04-01','class':'1勝クラス','surface':'dirt','distance_m':1200,
             'finish':6,'beaten_margin_s':0.9,'source_url':'https://example.test/r3'},
        ])
        self.race['horses'] = [h]
        out = generate_candidates(self.race, self.as_of)
        row = out['horse_features'][0]
        self.assertTrue(row['candidate'])
        self.assertIn('layoff_gt_90d', row['uncertainty_flags'])

    def test_no_positive_signal_is_not_candidate(self):
        h = self.horse(runs=[
            {'date':'2026-09-20','class':'1勝クラス','surface':'turf','distance_m':1800,
             'finish':8,'beaten_margin_s':1.2,'source_url':'https://example.test/r1'},
            {'date':'2026-08-20','class':'1勝クラス','surface':'dirt','distance_m':1800,
             'finish':7,'beaten_margin_s':1.0,'source_url':'https://example.test/r2'},
            {'date':'2026-07-20','class':'1勝クラス','surface':'dirt','distance_m':1800,
             'finish':6,'beaten_margin_s':0.9,'source_url':'https://example.test/r3'},
        ])
        self.race['horses'] = [h]
        out = generate_candidates(self.race, self.as_of)
        self.assertEqual(out['candidates'], [])
        self.assertFalse(out['horse_features'][0]['candidate'])

    def test_data_hold_returns_no_candidates(self):
        h = self.horse()
        del h['recent_runs']
        self.race['horses'] = [h]
        out = generate_candidates(self.race, self.as_of)
        self.assertEqual(out['status'], 'DATA_HOLD')
        self.assertEqual(out['candidates'], [])
        self.assertEqual(out['horse_features'], [])


if __name__ == '__main__':
    unittest.main()
