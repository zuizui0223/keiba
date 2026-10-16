#!/usr/bin/env python3
"""Build an interpretable v3 candidate union from frozen pre-race inputs."""
import math


def _class_token(value):
    value = str(value)
    if '1勝' in value:
        return '1勝'
    if '2勝' in value:
        return '2勝'
    if '3勝' in value:
        return '3勝'
    if '未勝利' in value:
        return '未勝利'
    return value


def _is_close(run, threshold):
    if 'beaten_margin_s' in run:
        value = run['beaten_margin_s']
        return isinstance(value, (int, float)) and value <= threshold
    text = run.get('beaten_margin_text')
    return isinstance(text, str) and bool(text.strip())


def build_candidate_union(race, market_top_n=5, similar_distance_tolerance=200,
                          close_margin_s=0.6, lightly_raced_max_starts=5):
    target_surface = race['surface']
    target_distance = race['distance_m']
    target_class = _class_token(race['class'])
    valid_market = [h for h in race['horses']
                    if isinstance(h.get('win_odds'), (int, float))
                    and math.isfinite(h['win_odds'])]
    market_order = sorted(valid_market, key=lambda h: (h['win_odds'], h['number']))
    market_top = {h['number'] for h in market_order[:market_top_n]}

    rows = []
    for horse in race['horses']:
        reasons = []
        if horse['number'] in market_top:
            reasons.append('market_top_n')
        runs = horse.get('recent_runs') or []
        if any(run.get('surface') == target_surface
               and abs(run.get('distance_m', -99999) - target_distance) <= similar_distance_tolerance
               and run.get('finish') == 1 for run in runs):
            reasons.append('recent_similar_distance_win')
        if any(_class_token(run.get('class')) == target_class
               and run.get('surface') == target_surface
               and run.get('finish', 999) <= 4
               and _is_close(run, close_margin_s) for run in runs):
            reasons.append('recent_same_class_close')
        if (isinstance(horse.get('career_starts'), int)
                and horse['career_starts'] <= lightly_raced_max_starts
                and runs
                and runs[0].get('surface') == target_surface
                and abs(runs[0].get('distance_m', -99999) - target_distance) <= similar_distance_tolerance
                and runs[0].get('finish') == 1):
            reasons.append('lightly_raced_recent_win')
        rows.append({'number': horse['number'], 'name': horse.get('name'),
                     'reasons': reasons, 'reason_count': len(reasons)})

    return {
        'candidate_numbers': [r['number'] for r in rows if r['reasons']],
        'horses': rows,
        'parameters': {
            'market_top_n': market_top_n,
            'similar_distance_tolerance': similar_distance_tolerance,
            'close_margin_s': close_margin_s,
            'lightly_raced_max_starts': lightly_raced_max_starts,
        },
        'validated_prediction_model': False,
    }
