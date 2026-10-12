#!/usr/bin/env python3
"""Gate race ranking on complete, recently checked structured recent-run history."""
import argparse
from datetime import date, datetime, timedelta
import json
from pathlib import Path

REQUIRED_RUN_FIELDS = {
    'date', 'class', 'surface', 'distance_m', 'finish', 'beaten_margin_s', 'source_url'
}


def _aware_datetime(value):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('timezone_required')
    return dt


def validate_horse_history(horse, race_date, as_of, min_recent_runs=3,
                           max_check_age_hours=24):
    reasons = []
    number = horse.get('number')
    checked = horse.get('history_checked_at_jst')
    if not checked:
        reasons.append('missing_history_checked_at')
    else:
        try:
            checked_dt = _aware_datetime(checked)
            if checked_dt > as_of:
                reasons.append('future_history_check')
            elif as_of - checked_dt > timedelta(hours=max_check_age_hours):
                reasons.append('history_check_too_old')
        except (TypeError, ValueError):
            reasons.append('invalid_history_checked_at')

    career_starts = horse.get('career_starts')
    if type(career_starts) is not int or career_starts < 0:
        reasons.append('invalid_or_missing_career_starts')
        required_runs = min_recent_runs
    else:
        required_runs = min(min_recent_runs, career_starts)

    runs = horse.get('recent_runs')
    if runs is None:
        reasons.append('missing_recent_runs')
        runs = []
    elif not isinstance(runs, list):
        reasons.append('invalid_recent_runs')
        runs = []

    if len(runs) < required_runs:
        reasons.append('insufficient_recent_runs')

    parsed_dates = []
    race_day = date.fromisoformat(race_date)
    for run in runs:
        if not isinstance(run, dict) or not REQUIRED_RUN_FIELDS.issubset(run):
            reasons.append('incomplete_recent_run_fields')
            continue
        try:
            run_day = date.fromisoformat(str(run['date']))
            parsed_dates.append(run_day)
            if run_day >= race_day:
                reasons.append('future_run_date')
        except ValueError:
            reasons.append('invalid_run_date')
        if run['surface'] not in ('turf', 'dirt'):
            reasons.append('invalid_run_surface')
        if type(run['distance_m']) is not int or run['distance_m'] <= 0:
            reasons.append('invalid_run_distance')
        if type(run['finish']) is not int or run['finish'] <= 0:
            reasons.append('invalid_run_finish')
        margin = run['beaten_margin_s']
        if not isinstance(margin, (int, float)) or margin < 0:
            reasons.append('invalid_run_margin')
        if not isinstance(run['source_url'], str) or not run['source_url'].startswith(('http://', 'https://')):
            reasons.append('invalid_run_source')

    if parsed_dates and parsed_dates != sorted(parsed_dates, reverse=True):
        reasons.append('recent_runs_not_newest_first')

    reasons = sorted(set(reasons))
    return {
        'number': number,
        'name': horse.get('name'),
        'status': 'PASS' if not reasons else 'DATA_HOLD',
        'required_runs': required_runs,
        'available_runs': len(runs),
        'reasons': reasons,
    }


def audit_race(race, as_of, min_recent_runs=3, max_check_age_hours=24):
    rows = [
        validate_horse_history(
            horse, race['date'], as_of, min_recent_runs, max_check_age_hours
        )
        for horse in race['horses']
    ]
    failed = [row['number'] for row in rows if row['status'] != 'PASS']
    return {
        'race': race.get('race'),
        'race_id': race.get('race_id'),
        'status': 'PASS' if not failed else 'DATA_HOLD',
        'failed_horses': failed,
        'horse_audit': rows,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir', type=Path, default=Path('data/2026-10-12'))
    p.add_argument('--as-of', required=True)
    p.add_argument('--output', type=Path)
    p.add_argument('--min-recent-runs', type=int, default=3)
    p.add_argument('--max-check-age-hours', type=int, default=24)
    args = p.parse_args()
    as_of = _aware_datetime(args.as_of)
    audits = []
    for path in sorted(args.data_dir.glob('kyoto_*.json')):
        race = json.loads(path.read_text(encoding='utf-8'))
        audits.append(audit_race(race, as_of, args.min_recent_runs,
                                 args.max_check_age_hours))
    out = {
        'as_of': as_of.isoformat(),
        'status': 'PASS' if audits and all(a['status'] == 'PASS' for a in audits) else 'DATA_HOLD',
        'races': audits,
    }
    text = json.dumps(out, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')


if __name__ == '__main__':
    main()
