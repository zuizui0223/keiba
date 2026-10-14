#!/usr/bin/env python3
"""Deterministic v3 feature extraction and broad candidate union.

No probabilities, outcome lookup, or ticket recommendation.
"""
from datetime import date


def normalize_class(value):
    text = str(value).strip()
    aliases = {
        'GI': 'G1', 'G1': 'G1',
        'GII': 'G2', 'G2': 'G2',
        'GIII': 'G3', 'G3': 'G3',
        'Listed': 'L', 'L': 'L',
    }
    if text in aliases:
        return aliases[text]
    for prefix in ('3歳', '4歳以上', '3歳以上'):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text


def _margin_seconds(run):
    value = run.get('beaten_margin_s')
    return value if isinstance(value, (int, float)) else None


def horse_features(race, horse):
    race_day = date.fromisoformat(race['date'])
    runs = horse.get('recent_runs', [])
    latest = runs[0] if runs else None
    race_surface = race['surface']
    race_distance = race['distance_m']
    race_class = normalize_class(race['class'])

    days_since_last_run = None
    if latest:
        days_since_last_run = (race_day - date.fromisoformat(latest['date'])).days

    same_surface = [r for r in runs if r.get('surface') == race_surface]
    near_distance = [r for r in same_surface
                     if abs(r.get('distance_m', 10**9) - race_distance) <= 200]
    same_class_good = []
    for r in same_surface:
        if normalize_class(r.get('class')) != race_class:
            continue
        margin = _margin_seconds(r)
        if r.get('finish', 999) <= 4 or (margin is not None and margin <= 0.5):
            same_class_good.append(r)

    kyoto_dist = horse.get('kyoto_distance_record')
    kyoto_dist_top3 = None
    if isinstance(kyoto_dist, list) and len(kyoto_dist) == 4:
        kyoto_dist_top3 = sum(kyoto_dist[:3])

    career_starts = horse.get('career_starts')
    latest_same_surface = bool(latest and latest.get('surface') == race_surface)
    latest_distance_diff = (
        abs(latest.get('distance_m') - race_distance)
        if latest and isinstance(latest.get('distance_m'), int) else None
    )

    return {
        'number': horse['number'],
        'name': horse.get('name'),
        'career_starts': career_starts,
        'days_since_last_run': days_since_last_run,
        'long_layoff': days_since_last_run is not None and days_since_last_run >= 120,
        'low_experience': isinstance(career_starts, int) and career_starts <= 8,
        'recent_win_count_3': sum(r.get('finish') == 1 for r in runs[:3]),
        'same_surface_count_3': len(same_surface[:3]),
        'near_distance_count_3': len(near_distance[:3]),
        'same_class_good_count_3': len(same_class_good[:3]),
        'latest_finish': latest.get('finish') if latest else None,
        'latest_same_surface': latest_same_surface,
        'latest_distance_diff_m': latest_distance_diff,
        'recent_near_distance_win': any(r.get('finish') == 1 for r in near_distance),
        'recent_same_class_good': bool(same_class_good),
        'lightly_raced_latest_good': bool(
            latest and isinstance(career_starts, int) and career_starts <= 8
            and latest_same_surface
            and latest.get('finish', 999) <= 2
            and latest_distance_diff is not None and latest_distance_diff <= 400
        ),
        'kyoto_distance_top3': kyoto_dist_top3,
    }


def candidate_union(race, market_top_n=5):
    horses = list(race['horses'])
    market = sorted(
        horses,
        key=lambda h: (h.get('win_odds', float('inf')), h['number'])
    )
    market_numbers = {
        h['number'] for h in market[:min(market_top_n, len(market))]
    }

    rows = []
    for horse in horses:
        f = horse_features(race, horse)
        reasons = []
        if horse['number'] in market_numbers:
            reasons.append('market_top_n')
        if f['recent_near_distance_win']:
            reasons.append('recent_near_distance_win')
        if f['recent_same_class_good']:
            reasons.append('recent_same_class_good')
        if f['lightly_raced_latest_good']:
            reasons.append('lightly_raced_latest_good')
        if f['kyoto_distance_top3']:
            reasons.append('kyoto_distance_top3')
        if reasons:
            rows.append({
                'number': horse['number'],
                'name': horse.get('name'),
                'win_odds': horse.get('win_odds'),
                'reasons': reasons,
                'features': f,
            })

    rows.sort(
        key=lambda r: (
            r['win_odds'] if isinstance(r['win_odds'], (int, float))
            else float('inf'),
            r['number']
        )
    )
    return {
        'race': race.get('race'),
        'candidate_order': 'market_odds_baseline_only',
        'probabilities_assigned': False,
        'candidate_count': len(rows),
        'candidates': rows,
        'note': (
            'Broad deterministic candidate union for diagnostic use; '
            'not a calibrated ranking or expected-value model.'
        ),
    }
