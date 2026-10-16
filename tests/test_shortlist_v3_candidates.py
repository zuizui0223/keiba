import unittest

from scripts.shortlist_v3_candidates import shortlist_candidates


class ShortlistV3CandidatesTests(unittest.TestCase):
    def row(self, number, market_rank, signals, candidate=True):
        return {
            'number': number,
            'name': f'H{number}',
            'market_rank': market_rank,
            'candidate': candidate,
            'positive_signals': signals,
            'uncertainty_flags': [],
        }

    def test_market_top_four_are_retained(self):
        data = {'status':'PASS','horse_features':[
            self.row(1,1,['market_top4']),
            self.row(2,2,['market_top4']),
            self.row(3,3,['market_top4']),
            self.row(4,4,['market_top4']),
            self.row(5,5,['recent_similar_distance_win']),
        ]}
        out = shortlist_candidates(data)
        self.assertEqual(out['baseline'], [1,2,3,4])
        self.assertTrue({1,2,3,4}.issubset(out['shortlist']))

    def test_upside_is_capped_at_three_by_signal_score(self):
        data = {'status':'PASS','horse_features':[
            self.row(1,1,['market_top4']),
            self.row(2,2,['market_top4']),
            self.row(3,3,['market_top4']),
            self.row(4,4,['market_top4']),
            self.row(5,8,['recent_similar_distance_win','lightly_raced_latest_win']),
            self.row(6,6,['recent_similar_distance_close_finish']),
            self.row(7,7,['lightly_raced_latest_close_form']),
            self.row(8,5,['recent_similar_distance_win']),
        ]}
        out = shortlist_candidates(data, upside_slots=3)
        self.assertEqual(len(out['upside']), 3)
        self.assertEqual(out['upside'][0], 5)
        self.assertNotIn(6, out['upside'])

    def test_shortlist_size_is_bounded(self):
        rows = [self.row(i,i,['market_top4'] if i <= 4 else ['recent_similar_distance_win'])
                for i in range(1,13)]
        out = shortlist_candidates({'status':'PASS','horse_features':rows})
        self.assertLessEqual(len(out['shortlist']), 7)

    def test_data_hold_returns_empty_shortlist(self):
        out = shortlist_candidates({'status':'DATA_HOLD','horse_features':[]})
        self.assertEqual(out['status'], 'DATA_HOLD')
        self.assertEqual(out['shortlist'], [])

    def test_no_betting_or_probability_claim_is_added(self):
        data = {'status':'PASS','horse_features':[self.row(1,1,['market_top4'])]}
        out = shortlist_candidates(data)
        self.assertFalse(out['horse_ranking_produced'])
        self.assertFalse(out['ticket_selection_performed'])
        self.assertFalse(out['probabilities_assigned'])


if __name__ == '__main__':
    unittest.main()
