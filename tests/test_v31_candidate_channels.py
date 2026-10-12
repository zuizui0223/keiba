import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from v31_candidate_channels import classify_horse, classify_race, market_channel, within_band


class V31ChannelTests(unittest.TestCase):
    def base_horse(self, *, age=4, career=10, last4=None, full=None):
        return {
            'number': 1,
            'name': 'fixture',
            'age': age,
            'career_starts_before_target': career,
            'body_weight_change_kg': 0,
            'current_jockey': 'A',
            'last4': last4 or [],
            'full_history_before_target': full or [],
        }

    def test_market_top_quarter_expands_cutoff_ties(self):
        horses = [
            {'number': 1, 'win_odds': 2.0}, {'number': 2, 'win_odds': 3.0},
            {'number': 3, 'win_odds': 4.0}, {'number': 4, 'win_odds': 4.0},
            {'number': 5, 'win_odds': 8.0}, {'number': 6, 'win_odds': 9.0},
            {'number': 7, 'win_odds': 10.0}, {'number': 8, 'win_odds': 11.0},
            {'number': 9, 'win_odds': 12.0}, {'number': 10, 'win_odds': 13.0},
            {'number': 11, 'win_odds': 14.0}, {'number': 12, 'win_odds': 15.0},
        ]
        self.assertEqual(market_channel(horses), {1, 2, 3, 4})

    def test_distance_band_is_inclusive_at_twenty_percent(self):
        self.assertTrue(within_band(1000, 1200))
        self.assertTrue(within_band(1440, 1200))
        self.assertFalse(within_band(1450, 1200))

    def test_c1_uses_latest_start_only(self):
        horse = self.base_horse(last4=[
            {'surface':'ダ','distance_m':1200,'class_rank':1,'finish':8,'margin_sec':1.2,'is_win':False,'date':'2026-09-01','venue':'中京'},
            {'surface':'ダ','distance_m':1200,'class_rank':1,'finish':2,'margin_sec':0.1,'is_win':False,'date':'2026-08-01','venue':'阪神'},
        ])
        result = classify_horse(horse, 'ダ', 1200, 1, {})
        self.assertFalse(result['C1'])

    def test_c1_requires_top4_within_one_second_or_margin_half_second(self):
        good_fourth = self.base_horse(last4=[
            {'surface':'ダ','distance_m':1000,'class_rank':1,'finish':4,'margin_sec':0.9,'is_win':False,'date':'2026-09-01','venue':'小倉'},
        ])
        bad_fourth = self.base_horse(last4=[
            {'surface':'ダ','distance_m':1000,'class_rank':1,'finish':4,'margin_sec':1.1,'is_win':False,'date':'2026-09-01','venue':'小倉'},
        ])
        close_fifth = self.base_horse(last4=[
            {'surface':'ダ','distance_m':1200,'class_rank':1,'finish':5,'margin_sec':0.4,'is_win':False,'date':'2026-09-01','venue':'阪神'},
        ])
        self.assertTrue(classify_horse(good_fourth, 'ダ', 1200, 1, {})['C1'])
        self.assertFalse(classify_horse(bad_fourth, 'ダ', 1200, 1, {})['C1'])
        self.assertTrue(classify_horse(close_fifth, 'ダ', 1200, 1, {})['C1'])

    def test_u_keeps_sparse_career_recent_winner(self):
        horse = self.base_horse(age=3, career=3, last4=[
            {'surface':'ダ','distance_m':1200,'class_rank':0,'finish':1,'margin_sec':0.0,'is_win':True,'date':'2026-08-02','venue':'中京'},
        ])
        self.assertTrue(classify_horse(horse, 'ダ', 1200, 1, {})['U'])

    def test_q1_is_stricter_for_listed_and_g3(self):
        tiers = {'Lrace':'L', 'G3race':'GIII', 'G2race':'GII', 'G1race':'GI'}
        def horse(name, finish):
            return self.base_horse(last4=[
                {'surface':'芝','distance_m':1600,'class_rank':None,'finish':finish,'margin_sec':0.1,
                 'is_win':finish == 1,'date':'2026-08-01','venue':'東京','race_name':name},
            ])
        self.assertFalse(classify_horse(horse('Lrace', 2), '芝', 1400, 6, tiers)['Q1'])
        self.assertTrue(classify_horse(horse('Lrace', 1), '芝', 1400, 6, tiers)['Q1'])
        self.assertFalse(classify_horse(horse('G3race', 2), '芝', 1400, 6, tiers)['Q1'])
        self.assertTrue(classify_horse(horse('G3race', 1), '芝', 1400, 6, tiers)['Q1'])
        self.assertTrue(classify_horse(horse('G2race', 3), '芝', 1400, 6, tiers)['Q1'])
        self.assertTrue(classify_horse(horse('G1race', 3), '芝', 1400, 6, tiers)['Q1'])

    def test_k1_requires_win_component(self):
        no_win = self.base_horse(full=[
            {'venue':'京都','surface':'芝','distance_m':1800,'finish':2},
            {'venue':'京都','surface':'芝','distance_m':2200,'finish':3},
        ])
        one_win_two_top3 = self.base_horse(full=[
            {'venue':'京都','surface':'芝','distance_m':1800,'finish':1},
            {'venue':'京都','surface':'芝','distance_m':2200,'finish':3},
        ])
        two_wins = self.base_horse(full=[
            {'venue':'京都','surface':'芝','distance_m':1800,'finish':1},
            {'venue':'京都','surface':'芝','distance_m':2200,'finish':1},
        ])
        self.assertFalse(classify_horse(no_win, '芝', 2000, 1, {})['K1'])
        self.assertTrue(classify_horse(one_win_two_top3, '芝', 2000, 1, {})['K1'])
        self.assertTrue(classify_horse(two_wins, '芝', 2000, 1, {})['K1'])

    def test_high_class_rescue_requires_q1_and_k1(self):
        tiers = {'G3race':'GIII'}
        q_only = self.base_horse(last4=[
            {'surface':'芝','distance_m':1600,'class_rank':None,'finish':1,'margin_sec':0.0,
             'is_win':True,'date':'2026-08-01','venue':'中山','race_name':'G3race'},
        ])
        both = self.base_horse(last4=q_only['last4'], full=[
            {'venue':'京都','surface':'芝','distance_m':1400,'finish':1},
            {'venue':'京都','surface':'芝','distance_m':1600,'finish':2},
        ])
        self.assertFalse(classify_horse(q_only, '芝', 1400, 6, tiers)['rescue'])
        self.assertTrue(classify_horse(both, '芝', 1400, 6, tiers)['rescue'])

    def test_lower_class_rescue_accepts_q1_or_k1(self):
        tiers = {'G3race':'GIII'}
        q_only = self.base_horse(last4=[
            {'surface':'芝','distance_m':1800,'class_rank':None,'finish':1,'margin_sec':0.0,
             'is_win':True,'date':'2026-08-01','venue':'中山','race_name':'G3race'},
        ])
        k_only = self.base_horse(full=[
            {'venue':'京都','surface':'芝','distance_m':1800,'finish':1},
            {'venue':'京都','surface':'芝','distance_m':1800,'finish':2},
        ])
        self.assertTrue(classify_horse(q_only, '芝', 1800, 2, tiers)['rescue'])
        self.assertTrue(classify_horse(k_only, '芝', 1800, 2, tiers)['rescue'])


class V31RaceTests(unittest.TestCase):
    def test_union_is_m_or_c1_or_u_or_rescue(self):
        normalized = [
            {'number':1,'name':'m','age':4,'career_starts_before_target':8,'body_weight_change_kg':0,
             'current_jockey':'A','last4':[],'full_history_before_target':[]},
            {'number':2,'name':'u','age':3,'career_starts_before_target':3,'body_weight_change_kg':0,
             'current_jockey':'B','last4':[{'surface':'ダ','distance_m':1200,'class_rank':0,'finish':1,
             'margin_sec':0.0,'is_win':True,'date':'2026-08-02','venue':'中京'}],
             'full_history_before_target':[]},
            {'number':3,'name':'other','age':5,'career_starts_before_target':10,'body_weight_change_kg':0,
             'current_jockey':'C','last4':[],'full_history_before_target':[]},
            {'number':4,'name':'other2','age':5,'career_starts_before_target':10,'body_weight_change_kg':0,
             'current_jockey':'D','last4':[],'full_history_before_target':[]},
        ]
        frozen = [
            {'number':1,'win_odds':2.0},{'number':2,'win_odds':20.0},
            {'number':3,'win_odds':3.0},{'number':4,'win_odds':4.0},
        ]
        result = classify_race(normalized, frozen, 'ダ', 1200, 1, {}, '2026-10-12')
        by_number = {x['number']:x for x in result['horses']}
        self.assertTrue(by_number[2]['U'])
        self.assertTrue(by_number[2]['union'])
        self.assertEqual(result['sets']['union'], [1, 2, 3, 4])
        self.assertEqual(result['method'], 'v3.1_frozen_candidate_channels')


class V31CliTests(unittest.TestCase):
    def test_cli_writes_result_free_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base/'frozen').mkdir()
            history = {'target_date':'2026-10-12','races':{'12':{'horses':[
                {'number':1,'name':'market','age':4,'career_starts_before_target':6,'body_weight_change_kg':0,
                 'current_jockey':'A','last4':[],'full_history_before_target':[]},
                {'number':2,'name':'young','age':3,'career_starts_before_target':3,'body_weight_change_kg':0,
                 'current_jockey':'B','last4':[{'date':'2026-08-02','venue':'中京','surface':'ダ','distance_m':1200,
                 'finish':1,'class_rank':0,'margin_sec':0.0,'is_win':True}],
                 'full_history_before_target':[]},
                {'number':3,'name':'market2','age':5,'career_starts_before_target':8,'body_weight_change_kg':0,
                 'current_jockey':'C','last4':[],'full_history_before_target':[]},
            ]}}}
            (base/'history.json').write_text(json.dumps(history, ensure_ascii=False))
            (base/'quality.json').write_text(json.dumps({'tiers':{}}, ensure_ascii=False))
            (base/'frozen'/'kyoto_12.json').write_text(json.dumps({'horses':[
                {'number':1,'win_odds':2.0},{'number':2,'win_odds':20.0},{'number':3,'win_odds':3.0}
            ]}, ensure_ascii=False))
            output=base/'out.json'
            run=subprocess.run([
                sys.executable,str(ROOT/'scripts'/'v31_candidate_channels.py'),
                '--history',str(base/'history.json'),'--frozen-dir',str(base/'frozen'),
                '--quality-map',str(base/'quality.json'),'--output',str(output),'--races','12'
            ],text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            data=json.loads(output.read_text())
            self.assertFalse(data['uses_target_race_results'])
            self.assertEqual(data['method'],'v3.1_frozen_candidate_channels')
            self.assertEqual(data['races']['12']['sets']['U'],[2])


if __name__ == '__main__':
    unittest.main()
