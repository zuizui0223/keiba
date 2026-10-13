#!/usr/bin/env python3
"""Freeze a pre-race v3 candidate manifest for out-of-sample evaluation."""
from datetime import timedelta

from scripts.audit_recent_history import _aware_datetime
from scripts.generate_v3_candidates import generate_candidates


def build_manifest(race, as_of, data_blob_sha, generator_blob_sha,
                   cutoff_minutes=2):
    start = _aware_datetime(race['start_jst'])
    if as_of >= start - timedelta(minutes=cutoff_minutes):
        raise ValueError('freeze_after_cutoff')

    generated = generate_candidates(race, as_of)
    if generated['status'] != 'PASS':
        raise ValueError('data_hold')

    market = [
        h for h in race['horses']
        if isinstance(h.get('win_odds'), (int, float)) and h['win_odds'] >= 1
    ]
    market.sort(key=lambda h: (h['win_odds'], h['number']))

    return {
        'race': race.get('race'),
        'race_id': race.get('race_id'),
        'date': race.get('date'),
        'start_jst': race.get('start_jst'),
        'frozen_at_jst': as_of.isoformat(),
        'cutoff_minutes': cutoff_minutes,
        'status': 'FROZEN',
        'data_blob_sha': data_blob_sha,
        'candidate_generator_blob_sha': generator_blob_sha,
        'candidates': generated['candidates'],
        'candidate_count': len(generated['candidates']),
        'horse_features': generated['horse_features'],
        'market_top4': [h['number'] for h in market[:4]],
        'result_attached': False,
        'ranking_produced': False,
        'ticket_selection_performed': False,
    }
