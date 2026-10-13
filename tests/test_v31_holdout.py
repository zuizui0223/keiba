import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'v31_holdout.py'


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


class FixtureMixin:
    def make_fixture(self, base: Path):
        classifier = base / 'classifier.py'
        classifier.write_text(
            "def classify_race(normalized_horses, frozen_horses, target_surface, target_distance, target_class_rank, quality_tiers, target_date, target_venue='京都'):\n"
            "    nums=[int(h['number']) for h in normalized_horses]\n"
            "    m=[int(h['number']) for h in frozen_horses[:1]]\n"
            "    return {'method':'stub','sets':{'M':m,'C1':[],'U':nums[1:2],'Q1':[],'K1':[],'rescue':[],'union':m+nums[1:2]},'horses':[{'number':n,'M':n in m,'C1':False,'U':n in nums[1:2],'Q1':False,'K1':False,'rescue':False,'union':n in (m+nums[1:2]),'uncertainty_flags':[]} for n in nums],'unknown_quality_tiers':[]}\n"
        )
        classifier_sha = git_blob_sha(classifier.read_bytes())
        manifest = {
            'schema_version': 1,
            'version': 'v3.1',
            'status': 'frozen_for_prospective_holdout',
            'created_at_jst': '2026-10-13T09:51:48+09:00',
            'holdout_target_races': 20,
            'frozen_blobs': {'classifier': classifier_sha, 'holdout_wrapper': git_blob_sha(SCRIPT.read_bytes()), 'snapshot_preparer': 'a'*40},
            'metadata_inputs': {
                'quality_tier_baseline': {'A賞': 'GIII'},
                'quality_tier_policy': 'append-only'
            }
        }
        (base/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False))
        (base/'quality.json').write_text(json.dumps({'tiers': {'A賞':'GIII','NEW賞':'L'}}, ensure_ascii=False))
        race = {
            'race_id':'2026-10-18-KYOTO-07',
            'date':'2026-10-18','venue':'京都','race_number':7,'age_scope':'3yo+',
            'scheduled_start_jst':'2026-10-18T13:25:00+09:00',
            'target':{'surface':'ダ','distance_m':1800,'class_rank':1},
            'horses':[
                {'number':1,'name':'A','age':4,'career_starts_before_target':8,'last4':[],'full_history_before_target':[]},
                {'number':2,'name':'B','age':3,'career_starts_before_target':3,'last4':[],'full_history_before_target':[]},
                {'number':3,'name':'C','age':5,'career_starts_before_target':10,'last4':[],'full_history_before_target':[]},
            ]
        }
        (base/'race.json').write_text(json.dumps(race, ensure_ascii=False))
        odds = {
            'observed_at_jst':'2026-10-18T13:00:00+09:00',
            'horses':[
                {'number':1,'win_odds':2.0},{'number':2,'win_odds':10.0},{'number':3,'win_odds':3.0}
            ]
        }
        (base/'odds.json').write_text(json.dumps(odds, ensure_ascii=False))
        source_meta = {
            'race_id':'2026-10-18-KYOTO-07',
            'observed_at_jst':'2026-10-18T13:00:00+09:00',
            'active_horse_numbers':[1,2,3],
            'uses_target_race_results':False,
            'preparer_git_blob_sha':'a'*40
        }
        (base/'source-meta.json').write_text(json.dumps(source_meta, ensure_ascii=False))
        return classifier

    def run_cmd(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str,args)], text=True, capture_output=True)


class V31HoldoutTests(FixtureMixin, unittest.TestCase):
    def test_freeze_writes_result_free_record(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); out=b/'freeze.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',out)
            self.assertEqual(r.returncode,0,r.stderr)
            data=json.loads(out.read_text())
            self.assertEqual(data['race_id'],'2026-10-18-KYOTO-07')
            self.assertFalse(data['uses_target_race_results'])
            self.assertEqual(data['sets']['union'],[1,2])
            self.assertNotIn('result',data)
            self.assertNotIn('top3',data)

    def test_freeze_rejects_classifier_sha_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); classifier.write_text(classifier.read_text()+'# changed\n'); out=b/'freeze.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('classifier_sha_mismatch',r.stderr)

    def test_freeze_rejects_wrapper_sha_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); manifest=json.loads((b/'manifest.json').read_text()); manifest['frozen_blobs']['holdout_wrapper']='0'*40; (b/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False)); out=b/'freeze.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('holdout_wrapper_sha_mismatch',r.stderr)

    def test_freeze_rejects_snapshot_preparer_sha_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); meta=json.loads((b/'source-meta.json').read_text()); meta['preparer_git_blob_sha']='b'*40; (b/'source-meta.json').write_text(json.dumps(meta,ensure_ascii=False)); out=b/'freeze.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('snapshot_preparer_sha_mismatch',r.stderr)

    def test_freeze_rejects_changed_baseline_quality_tier(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); (b/'quality.json').write_text(json.dumps({'tiers':{'A賞':'GII'}},ensure_ascii=False)); out=b/'freeze.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('quality_baseline_changed:A賞',r.stderr)

    def test_freeze_rejects_observation_at_or_after_post(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); out=b/'freeze.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:25:00+09:00','--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('freeze_not_prerace',r.stderr)

    def test_freeze_rejects_non_kyoto_venue(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); race=json.loads((b/'race.json').read_text()); race['venue']='東京'; (b/'race.json').write_text(json.dumps(race,ensure_ascii=False)); out=b/'freeze.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('ineligible_venue',r.stderr)

    def test_freeze_rejects_two_year_old_only_race(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); race=json.loads((b/'race.json').read_text()); race['age_scope']='2yo'; (b/'race.json').write_text(json.dumps(race,ensure_ascii=False)); out=b/'freeze.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('ineligible_2yo_only',r.stderr)

    def test_freeze_rejects_class_below_one_win(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); race=json.loads((b/'race.json').read_text()); race['target']['class_rank']=0; (b/'race.json').write_text(json.dumps(race,ensure_ascii=False)); out=b/'freeze.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('ineligible_class_below_1win',r.stderr)

    def test_freeze_rejects_odds_snapshot_too_early(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); odds=json.loads((b/'odds.json').read_text()); odds['observed_at_jst']='2026-10-18T12:25:00+09:00'; (b/'odds.json').write_text(json.dumps(odds,ensure_ascii=False)); out=b/'freeze.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T12:25:00+09:00','--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('freeze_outside_odds_window',r.stderr)

    def test_freeze_rejects_odds_snapshot_too_late(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); odds=json.loads((b/'odds.json').read_text()); odds['observed_at_jst']='2026-10-18T13:20:00+09:00'; (b/'odds.json').write_text(json.dumps(odds,ensure_ascii=False)); out=b/'freeze.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:20:00+09:00','--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('freeze_outside_odds_window',r.stderr)

    def test_freeze_rejects_target_result_keys(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); race=json.loads((b/'race.json').read_text()); race['top3']=[1,2,3]; (b/'race.json').write_text(json.dumps(race,ensure_ascii=False)); out=b/'freeze.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('forbidden_target_result_key:top3',r.stderr)

    def test_score_is_separate_and_computes_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); freeze=b/'freeze.json'; score=b/'score.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',freeze)
            self.assertEqual(r.returncode,0,r.stderr)
            (b/'result.json').write_text(json.dumps({'race_id':'2026-10-18-KYOTO-07','top3':[2,3,1]},ensure_ascii=False))
            r=self.run_cmd('score','--freeze',freeze,'--result',b/'result.json','--output',score)
            self.assertEqual(r.returncode,0,r.stderr)
            data=json.loads(score.read_text())
            self.assertEqual(data['union_top3_hits'],2)
            self.assertEqual(data['M_top3_hits'],1)
            self.assertTrue(data['winner_in_union'])
            self.assertEqual(data['top3_recall'],2/3)
            self.assertTrue(freeze.exists())
            frozen=json.loads(freeze.read_text())
            self.assertNotIn('top3',frozen)

    def test_score_rejects_race_id_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); freeze=b/'freeze.json'; score=b/'score.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',freeze)
            self.assertEqual(r.returncode,0,r.stderr)
            (b/'result.json').write_text(json.dumps({'race_id':'wrong','top3':[2,3,1]},ensure_ascii=False))
            r=self.run_cmd('score','--freeze',freeze,'--result',b/'result.json','--output',score)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('race_id_mismatch',r.stderr)


class V31LedgerTests(FixtureMixin, unittest.TestCase):
    def test_register_appends_and_updates_cumulative_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); freeze=b/'freeze.json'; score=b/'score.json'; ledger=b/'ledger.json'; out=b/'ledger2.json'
            ledger.write_text(json.dumps({'schema_version':1,'version':'v3.1','target_races':20,'entries':[]},ensure_ascii=False))
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',freeze)
            self.assertEqual(r.returncode,0,r.stderr)
            (b/'result.json').write_text(json.dumps({'race_id':'2026-10-18-KYOTO-07','top3':[2,3,1]},ensure_ascii=False))
            r=self.run_cmd('score','--freeze',freeze,'--result',b/'result.json','--output',score)
            self.assertEqual(r.returncode,0,r.stderr)
            r=self.run_cmd('register','--ledger',ledger,'--freeze',freeze,'--score',score,'--output',out)
            self.assertEqual(r.returncode,0,r.stderr)
            data=json.loads(out.read_text())
            self.assertEqual(data['entries'][0]['holdout_index'],1)
            self.assertEqual(data['summary']['races_scored'],1)
            self.assertEqual(data['summary']['union_top3_recall'],2/3)
            self.assertEqual(data['summary']['M_top3_recall'],1/3)
            self.assertEqual(data['summary']['winner_recall'],1.0)
            self.assertEqual(data['summary']['candidate_fraction'],2/3)

    def test_register_rejects_duplicate_race(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); freeze=b/'freeze.json'; score=b/'score.json'; ledger=b/'ledger.json'; out=b/'ledger2.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',freeze)
            self.assertEqual(r.returncode,0,r.stderr)
            (b/'result.json').write_text(json.dumps({'race_id':'2026-10-18-KYOTO-07','top3':[2,3,1]},ensure_ascii=False))
            r=self.run_cmd('score','--freeze',freeze,'--result',b/'result.json','--output',score)
            self.assertEqual(r.returncode,0,r.stderr)
            ledger.write_text(json.dumps({'schema_version':1,'version':'v3.1','target_races':20,'entries':[{'holdout_index':1,'race_id':'2026-10-18-KYOTO-07','scheduled_start_jst':'2026-10-18T13:25:00+09:00','field_size':3,'candidate_count':2,'union_top3_hits':2,'M_top3_hits':1,'winner_in_union':True,'non_M_top3_rescues':[]}]},ensure_ascii=False))
            r=self.run_cmd('register','--ledger',ledger,'--freeze',freeze,'--score',score,'--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('duplicate_holdout_race',r.stderr)

    def test_register_rejects_backfill_before_last_race(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td); classifier=self.make_fixture(b); freeze=b/'freeze.json'; score=b/'score.json'; ledger=b/'ledger.json'; out=b/'ledger2.json'
            r=self.run_cmd('freeze','--race-input',b/'race.json','--odds',b/'odds.json','--source-meta',b/'source-meta.json','--quality-map',b/'quality.json','--manifest',b/'manifest.json','--classifier',classifier,'--observed-at-jst','2026-10-18T13:05:00+09:00','--output',freeze)
            self.assertEqual(r.returncode,0,r.stderr)
            (b/'result.json').write_text(json.dumps({'race_id':'2026-10-18-KYOTO-07','top3':[2,3,1]},ensure_ascii=False))
            r=self.run_cmd('score','--freeze',freeze,'--result',b/'result.json','--output',score)
            self.assertEqual(r.returncode,0,r.stderr)
            ledger.write_text(json.dumps({'schema_version':1,'version':'v3.1','target_races':20,'entries':[{'holdout_index':1,'race_id':'later','scheduled_start_jst':'2026-10-18T14:00:00+09:00','field_size':3,'candidate_count':2,'union_top3_hits':2,'M_top3_hits':1,'winner_in_union':True,'non_M_top3_rescues':[]}]},ensure_ascii=False))
            r=self.run_cmd('register','--ledger',ledger,'--freeze',freeze,'--score',score,'--output',out)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('holdout_backfill_forbidden',r.stderr)


if __name__ == '__main__':
    unittest.main()
