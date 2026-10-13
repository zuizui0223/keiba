#!/usr/bin/env python3
"""Generate broad v3 horse candidates from audited recent-run history.

This module does not rank horses, use odds, or select betting tickets.
"""
from datetime import date

from scripts.audit_recent_history import audit_race


def _margin_is_close(run, threshold=0.5):
    margin = run.get('beaten_margin_s')
    if isinstance(margin, (int, float)):
        return margin <= threshold
    text = run.get('beaten_margin_text')
    return text in {'ハナ', 'アタマ', 'クビ', '同着'}


def _horse_features(race, horse):
    surface = race['surface']
    distance = race['distance_m']
    runs = horse['recent_runs']
    positive = []
    uncertainty = []

    similar = [
        run for run in runs
        if run['surface'] == surface and abs(run['distance_m'] - distance) <= 200
    ]
    if any(run['finish'] == 1 for run in similar):
        positive.append('recent_similar_distance_win')
    if any(run['finish'] <= 3 and _margin_is_close(run) for run in similar):
        positive.append('recent_similar_distance_close_finish')

    if horse['career_starts'] <= 6 and runs:
        latest = runs[0]
        if (latest['surface'] == surface and latest['finish'] == 1
                and abs(latest['distance_m'] - distance) <= 400):
            positive.append('lightly_raced_latest_win')

    if runs:
        latest = runs[0]
        latest_day = date.fromisoformat(latest['date'])
        race_day = date.fromisoformat(race['date'])
        if (race_day - latest_day).days > 90:
            uncertainty.append('layoff_gt_90d')
        if latest['surface'] != surface:
            uncertainty.append('latest_surface_switch')
        if abs(latest['distance_m'] - distance) > 300:
            uncertainty.append('latest_distance_shift_gt_300m')

    return {
        'number': horse['number'],
        'name': horse.get('name'),
        'candidate': bool(positive),
        'positive_signals': sorted(set(positive)),
        'uncertainty_flags': sorted(set(uncertainty)),
    }


def generate_candidates(race, as_of):
    audit = audit_race(race, as_of)
    if audit['status'] != 'PASS':
        return {
            'race': race.get('race'),
            'race_id': race.get('race_id'),
            'status': 'DATA_HOLD',
            'candidates': [],
            'horse_features': [],
            'data_audit': audit,
        }

    rows = [_horse_features(race, horse) for horse in race['horses']]
    return {
        'race': race.get('race'),
        'race_id': race.get('race_id'),
        'status': 'PASS',
        'candidates': [row['number'] for row in rows if row['candidate']],
        'horse_features': rows,
        'ranking_produced': False,
        'odds_used': False,
        'ticket_selection_performed': False,
    }
