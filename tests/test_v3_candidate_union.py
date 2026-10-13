import unittest

from scripts.build_v3_candidate_union import build_candidate_union


def run(date, cls='1勝クラス', surface='dirt', distance=1200, finish=5, margin=1.2):
    return {'date': date, 'class': cls, 'surface': surface, 'distance_m': distance,
            'finish': finish, 'beaten_margin_s': margin, 'source_url': 'https://x'}


def horse(n, odds, starts, runs):
    return {'number': n, 'name': f'h{n}', 'win_odds': odds,
            'career_starts': starts, 'recent_runs': runs}


class CandidateUnionTests(unittest.TestCase):
    def test_lightly_raced_same_distance_winner_is_included(self):
        race = {'surface': 'dirt', 'distance_m': 1200, 'class': '1勝クラス',
                'horses': [
                    horse(1, 20.0, 3, [run('2026-08-02', cls='3歳未勝利',
                                           finish=1, margin=0.0),
                                      run('2026-05-01'), run('2026-03-01')]),
                    horse(2, 2.0, 10, [run('2026-09-01')])]}
        out = build_candidate_union(race, market_top_n=1)
        row = next(x for x in out['horses'] if x['number'] == 1)
        self.assertIn('recent_similar_distance_win', row['reasons'])
        self.assertIn('lightly_raced_recent_win', row['reasons'])
        self.assertIn(1, out['candidate_numbers'])

    def test_same_class_close_fourth_is_included(self):
        race = {'surface': 'dirt', 'distance_m': 1200, 'class': '1勝クラス',
                'horses': [
                    horse(1, 20.0, 7, [run('2026-07-04', distance=1000,
                                           finish=4, margin=0.6)]),
                    horse(2, 2.0, 10, [run('2026-09-01')])]}
        out = build_candidate_union(race, market_top_n=1)
        row = next(x for x in out['horses'] if x['number'] == 1)
        self.assertIn('recent_same_class_close', row['reasons'])
        self.assertIn(1, out['candidate_numbers'])

    def test_market_top_n_is_a_separate_reason(self):
        race = {'surface': 'dirt', 'distance_m': 1200, 'class': '1勝クラス',
                'horses': [horse(1, 2.0, 10, [run('2026-09-01')]),
                           horse(2, 4.0, 10, [run('2026-09-01')]),
                           horse(3, 9.0, 10, [run('2026-09-01')])]}
        out = build_candidate_union(race, market_top_n=2)
        reasons = {x['number']: x['reasons'] for x in out['horses']}
        self.assertIn('market_top_n', reasons[1])
        self.assertIn('market_top_n', reasons[2])
        self.assertNotIn('market_top_n', reasons[3])

    def test_no_reason_means_not_candidate(self):
        race = {'surface': 'dirt', 'distance_m': 1200, 'class': '1勝クラス',
                'horses': [
                    horse(1, 50.0, 20, [run('2026-09-01', surface='turf',
                                            distance=1800, finish=10, margin=2.0)]),
                    horse(2, 2.0, 10, [run('2026-09-01')])]}
        out = build_candidate_union(race, market_top_n=1)
        self.assertNotIn(1, out['candidate_numbers'])


if __name__ == '__main__':
    unittest.main()
