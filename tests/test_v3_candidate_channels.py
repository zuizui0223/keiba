import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from v3_candidate_channels import classify_horse, market_channel, within_band


class V3ChannelTests(unittest.TestCase):
    def test_market_top_quarter_expands_cutoff_ties(self):
        horses = [
            {'number': 1, 'win_odds': 2.0},
            {'number': 2, 'win_odds': 3.0},
            {'number': 3, 'win_odds': 4.0},
            {'number': 4, 'win_odds': 4.0},
            {'number': 5, 'win_odds': 8.0},
            {'number': 6, 'win_odds': 9.0},
            {'number': 7, 'win_odds': 10.0},
            {'number': 8, 'win_odds': 11.0},
            {'number': 9, 'win_odds': 12.0},
            {'number': 10, 'win_odds': 13.0},
            {'number': 11, 'win_odds': 14.0},
            {'number': 12, 'win_odds': 15.0},
        ]
        self.assertEqual(market_channel(horses), {1, 2, 3, 4})

    def test_distance_band_is_inclusive_at_twenty_percent(self):
        self.assertTrue(within_band(1000, 1200))
        self.assertTrue(within_band(1440, 1200))
        self.assertFalse(within_band(1450, 1200))

    def test_c_recent_same_class_adjacent_distance(self):
        horse = self.base_horse()
        horse['last4'] = [
            {'surface':'ダ','distance_m':1000,'class_rank':1,'finish':4,'margin_sec':0.6,'is_win':False,'date':'2026-07-04','venue':'小倉'},
            {'surface':'ダ','distance_m':1200,'class_rank':1,'finish':7,'margin_sec':0.8,'is_win':False,'date':'2026-05-09','venue':'京都'},
        ]
        result = classify_horse(horse, target_surface='ダ', target_distance=1200,
                                target_class_rank=1, quality_tiers={})
        self.assertTrue(result['C'])

    def test_u_lightly_raced_class_riser(self):
        horse = self.base_horse(age=3, career=3)
        horse['last4'] = [
            {'surface':'ダ','distance_m':1200,'class_rank':0,'finish':1,'margin_sec':0.0,'is_win':True,'date':'2026-08-02','venue':'中京'},
        ]
        result = classify_horse(horse, target_surface='ダ', target_distance=1200,
                                target_class_rank=1, quality_tiers={})
        self.assertTrue(result['U'])

    def test_q_listed_requires_win_but_graded_accepts_top_three(self):
        listed = self.base_horse()
        listed['last4'] = [
            {'surface':'芝','distance_m':1400,'class_rank':4,'finish':2,'margin_sec':0.1,'is_win':False,'date':'2026-06-14','venue':'東京','race_name':'パラダイスS'},
        ]
        graded = self.base_horse()
        graded['last4'] = [
            {'surface':'芝','distance_m':1600,'class_rank':4,'finish':2,'margin_sec':0.1,'is_win':False,'date':'2026-08-16','venue':'中京','race_name':'中京記念'},
        ]
        tiers = {'パラダイスS':'L', '中京記念':'GIII'}
        self.assertFalse(classify_horse(listed, '芝', 1400, 6, tiers)['Q'])
        self.assertTrue(classify_horse(graded, '芝', 1400, 6, tiers)['Q'])
        listed['last4'][0]['finish'] = 1
        listed['last4'][0]['is_win'] = True
        self.assertTrue(classify_horse(listed, '芝', 1400, 6, tiers)['Q'])

    def test_k_uses_full_kyoto_history_inside_distance_band(self):
        horse = self.base_horse()
        horse['full_history_before_target'] = [
            {'venue':'京都','surface':'芝','distance_m':2200,'finish':1},
            {'venue':'京都','surface':'芝','distance_m':2200,'finish':2},
            {'venue':'京都','surface':'芝','distance_m':1400,'finish':1},
        ]
        result = classify_horse(horse, '芝', 2000, 1, {})
        self.assertTrue(result['K'])
        self.assertEqual(result['K_top3'], 2)

    def test_op_is_not_q(self):
        horse = self.base_horse()
        horse['last4'] = [
            {'surface':'芝','distance_m':1600,'class_rank':4,'finish':1,'margin_sec':0.0,'is_win':True,'date':'2026-01-24','venue':'京都','race_name':'睦月S'},
        ]
        self.assertFalse(classify_horse(horse, '芝', 1400, 6, {'睦月S':'OP'})['Q'])

    @staticmethod
    def base_horse(age=4, career=10):
        return {
            'number': 1,
            'name': 'fixture',
            'age': age,
            'career_starts_before_target': career,
            'last4': [],
            'full_history_before_target': [],
        }


class V3RaceClassificationTests(unittest.TestCase):
    def test_classify_race_enriches_quality_and_keeps_union(self):
        from v3_candidate_channels import classify_race
        normalized = [
            {
                'number': 1, 'name': 'market', 'age': 4,
                'career_starts_before_target': 8,
                'body_weight_change_kg': 0, 'current_jockey': 'A',
                'last4': [], 'full_history_before_target': [],
            },
            {
                'number': 2, 'name': 'quality', 'age': 6,
                'career_starts_before_target': 20,
                'body_weight_change_kg': 0, 'current_jockey': 'B',
                'last4': [
                    {'date':'2026-04-04','venue':'中山','surface':'芝','distance_m':1600,
                     'finish':1,'class_rank':None,'margin_sec':0.0,'is_win':True},
                ],
                'full_history_before_target': [
                    {'date':'2026-04-04','venue':'中山','surface':'芝','distance_m':1600,
                     'finish':1,'race_name':'ダービーCT','class_rank':None,'rt':109,'jockey':'B'},
                ],
            },
            {
                'number': 3, 'name': 'other', 'age': 5,
                'career_starts_before_target': 12,
                'body_weight_change_kg': 0, 'current_jockey': 'C',
                'last4': [], 'full_history_before_target': [],
            },
        ]
        frozen = [
            {'number':1,'win_odds':2.0},
            {'number':2,'win_odds':20.0},
            {'number':3,'win_odds':3.0},
        ]
        result = classify_race(
            normalized, frozen, target_surface='芝', target_distance=1400,
            target_class_rank=6, quality_tiers={'ダービーCT':'GIII'},
            target_date='2026-10-12',
        )
        by_number = {row['number']: row for row in result['horses']}
        self.assertTrue(by_number[2]['Q'])
        self.assertTrue(by_number[2]['union'])
        self.assertEqual(result['sets']['M'], [1, 2, 3])

    def test_uncertainty_flags_are_reported_not_exclusion_rules(self):
        from v3_candidate_channels import uncertainty_flags
        horse = {
            'body_weight_change_kg': 12,
            'current_jockey': 'New Rider',
            'full_history_before_target': [
                {'date':'2026-05-01','venue':'阪神','surface':'ダ','distance_m':1400,
                 'finish':1,'class_rank':0,'jockey':'Old Rider'},
            ],
        }
        flags = uncertainty_flags(
            horse, target_surface='ダ', target_distance=1200,
            target_class_rank=1, target_date='2026-10-12'
        )
        self.assertIn('layoff_gt_120d', flags)
        self.assertIn('first_run_at_venue', flags)
        self.assertIn('first_exact_distance', flags)
        self.assertIn('body_weight_change_ge_10kg', flags)
        self.assertIn('class_rise', flags)
        self.assertIn('first_jockey_ride', flags)


class V3CliTests(unittest.TestCase):
    def test_cli_writes_blind_channel_audit(self):
        import json
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'frozen').mkdir()
            history = {
                'schema_version': 1,
                'races': {'12': {'horses': [
                    {'number':1,'name':'market','age':4,'career_starts_before_target':6,
                     'body_weight_change_kg':0,'current_jockey':'A','last4':[],
                     'full_history_before_target':[]},
                    {'number':2,'name':'young','age':3,'career_starts_before_target':3,
                     'body_weight_change_kg':0,'current_jockey':'B',
                     'last4':[{'date':'2026-08-02','venue':'中京','surface':'ダ','distance_m':1200,
                               'finish':1,'class_rank':0,'margin_sec':0.0,'is_win':True}],
                     'full_history_before_target':[{'date':'2026-08-02','venue':'中京','surface':'ダ','distance_m':1200,
                               'finish':1,'class_rank':0,'race_name':'3歳未勝利','jockey':'B'}]},
                    {'number':3,'name':'market2','age':5,'career_starts_before_target':10,
                     'body_weight_change_kg':0,'current_jockey':'C','last4':[],
                     'full_history_before_target':[]},
                ]}}
            }
            (base/'history.json').write_text(json.dumps(history, ensure_ascii=False))
            frozen = {'horses':[{'number':1,'win_odds':2.0},{'number':2,'win_odds':20.0},{'number':3,'win_odds':3.0}]}
            (base/'frozen'/'kyoto_12.json').write_text(json.dumps(frozen, ensure_ascii=False))
            (base/'quality.json').write_text(json.dumps({'tiers':{}}, ensure_ascii=False))
            output = base/'out.json'
            run = subprocess.run([
                sys.executable, str(ROOT/'scripts'/'v3_candidate_channels.py'),
                '--history', str(base/'history.json'), '--frozen-dir', str(base/'frozen'),
                '--quality-map', str(base/'quality.json'), '--output', str(output), '--races', '12'
            ], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            data = json.loads(output.read_text())
            self.assertEqual(data['races']['12']['sets']['U'], [2])
            self.assertEqual(data['summary']['starter_count'], 3)
            self.assertEqual(data['summary']['candidate_count'], 3)
            self.assertFalse(data['uses_target_race_results'])


if __name__ == '__main__':
    unittest.main()
