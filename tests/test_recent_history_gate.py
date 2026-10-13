import unittest
from datetime import datetime

from scripts.audit_recent_history import validate_horse_history, audit_race


class RecentHistoryGateTests(unittest.TestCase):
    def setUp(self):
        self.as_of = datetime.fromisoformat('2026-10-12T16:00:00+09:00')
        self.race_date = '2026-10-12'
        self.run = {
            'date': '2026-09-19',
            'class': '1勝クラス',
            'surface': 'dirt',
            'distance_m': 1200,
            'finish': 2,
            'beaten_margin_s': 0.0,
            'source_url': 'https://example.test/race/1',
        }

    def horse(self, **updates):
        h = {
            'number': 1,
            'name': 'テストホース',
            'career_starts': 3,
            'history_checked_at_jst': '2026-10-12T10:00:00+09:00',
            'history_source_url': 'https://example.test/horse/1',
            'source_latest_run_date': '2026-09-19',
            'recent_runs': [
                self.run,
                {**self.run, 'date': '2026-08-20', 'finish': 1, 'source_url': 'https://example.test/race/2'},
                {**self.run, 'date': '2026-07-01', 'finish': 4, 'beaten_margin_s': 0.4, 'source_url': 'https://example.test/race/3'},
            ],
        }
        h.update(updates)
        return h

    def test_missing_recent_runs_is_data_hold(self):
        horse = self.horse()
        del horse['recent_runs']
        out = validate_horse_history(horse, self.race_date, self.as_of)
        self.assertEqual(out['status'], 'DATA_HOLD')
        self.assertIn('missing_recent_runs', out['reasons'])

    def test_stale_history_check_is_data_hold(self):
        horse = self.horse(history_checked_at_jst='2026-10-10T10:00:00+09:00')
        out = validate_horse_history(horse, self.race_date, self.as_of)
        self.assertEqual(out['status'], 'DATA_HOLD')
        self.assertIn('history_check_too_old', out['reasons'])

    def test_three_complete_recent_runs_pass(self):
        out = validate_horse_history(self.horse(), self.race_date, self.as_of)
        self.assertEqual(out['status'], 'PASS')
        self.assertEqual(out['required_runs'], 3)

    def test_lightly_raced_horse_can_pass_with_all_career_starts(self):
        horse = self.horse(career_starts=2, recent_runs=self.horse()['recent_runs'][:2])
        out = validate_horse_history(horse, self.race_date, self.as_of)
        self.assertEqual(out['status'], 'PASS')
        self.assertEqual(out['required_runs'], 2)

    def test_future_or_out_of_order_run_is_data_hold(self):
        runs = self.horse()['recent_runs']
        runs[1] = {**runs[1], 'date': '2026-10-13'}
        out = validate_horse_history(self.horse(recent_runs=runs), self.race_date, self.as_of)
        self.assertEqual(out['status'], 'DATA_HOLD')
        self.assertIn('future_run_date', out['reasons'])

    def test_latest_run_must_match_source_latest_date(self):
        horse = self.horse(source_latest_run_date='2026-10-01')
        out = validate_horse_history(horse, self.race_date, self.as_of)
        self.assertEqual(out['status'], 'DATA_HOLD')
        self.assertIn('latest_run_mismatch', out['reasons'])

    def test_missing_history_source_url_is_data_hold(self):
        horse = self.horse()
        del horse['history_source_url']
        out = validate_horse_history(horse, self.race_date, self.as_of)
        self.assertEqual(out['status'], 'DATA_HOLD')
        self.assertIn('missing_history_source_url', out['reasons'])

    def test_official_text_margin_passes_without_seconds(self):
        run = dict(self.run)
        run.pop('beaten_margin_s')
        run['beaten_margin_text'] = 'アタマ'
        horse = self.horse(career_starts=1, recent_runs=[run])
        out = validate_horse_history(horse, self.race_date, self.as_of)
        self.assertEqual(out['status'], 'PASS')

    def test_missing_both_margin_forms_is_data_hold(self):
        run = dict(self.run)
        run.pop('beaten_margin_s')
        horse = self.horse(career_starts=1, recent_runs=[run])
        out = validate_horse_history(horse, self.race_date, self.as_of)
        self.assertEqual(out['status'], 'DATA_HOLD')
        self.assertIn('missing_run_margin', out['reasons'])

    def test_explicit_margin_source_omission_passes(self):
        run = dict(self.run)
        run.pop('beaten_margin_s')
        run['beaten_margin_missing_reason'] = 'source_does_not_publish_margin'
        horse = self.horse(career_starts=1, recent_runs=[run])
        out = validate_horse_history(horse, self.race_date, self.as_of)
        self.assertEqual(out['status'], 'PASS')

    def test_empty_margin_source_omission_still_holds(self):
        run = dict(self.run)
        run.pop('beaten_margin_s')
        run['beaten_margin_missing_reason'] = ''
        horse = self.horse(career_starts=1, recent_runs=[run])
        out = validate_horse_history(horse, self.race_date, self.as_of)
        self.assertEqual(out['status'], 'DATA_HOLD')
        self.assertIn('missing_run_margin', out['reasons'])

    def test_race_holds_if_any_runner_fails(self):
        good = self.horse()
        bad = self.horse(number=2, name='欠測馬')
        del bad['recent_runs']
        race = {'date': self.race_date, 'horses': [good, bad]}
        out = audit_race(race, self.as_of)
        self.assertEqual(out['status'], 'DATA_HOLD')
        self.assertEqual(out['failed_horses'], [2])


class RecentHistoryGateCliTests(unittest.TestCase):
    def test_cli_returns_nonzero_when_any_race_is_data_hold(self):
        import json
        from pathlib import Path
        import subprocess
        import sys
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            race = {
                'race': 12,
                'race_id': '2608040512',
                'date': '2026-10-12',
                'horses': [{'number': 1, 'name': '欠測馬'}],
            }
            (base / 'kyoto_12.json').write_text(json.dumps(race, ensure_ascii=False), encoding='utf-8')
            run = subprocess.run(
                [sys.executable, 'scripts/audit_recent_history.py', '--data-dir', str(base),
                 '--as-of', '2026-10-12T16:00:00+09:00'],
                cwd='/tmp/keiba_v3', capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 2)
            self.assertIn('DATA_HOLD', run.stdout)


if __name__ == '__main__':
    unittest.main()
