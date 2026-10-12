#!/usr/bin/env python3
"""Deterministic v3.1 candidate-channel classification.

v3.1 is a reduced broad-candidate generator. It uses only pre-race inputs,
does not read the target race result, and does not calculate expected value.
"""
from __future__ import annotations

import math


def within_band(distance: int | float | None,
                target: int | float,
                fraction: float = 0.20) -> bool:
    if distance is None or target <= 0:
        return False
    return abs(float(distance) - float(target)) / float(target) <= fraction + 1e-12


def market_channel(horses: list[dict]) -> set[int]:
    """Top quarter by frozen win odds, min 3/max 5, expanding cutoff ties."""
    if not horses:
        return set()
    ordered = sorted(horses, key=lambda h: (float(h['win_odds']), int(h['number'])))
    nominal = min(5, max(3, math.ceil(len(ordered) * 0.25)))
    nominal = min(nominal, len(ordered))
    cutoff = float(ordered[nominal - 1]['win_odds'])
    return {int(h['number']) for h in ordered if float(h['win_odds']) <= cutoff}


def _quality_class_rank(tier: str | None) -> int | None:
    return {'OP': 4, 'L': 4, 'GIII': 5, 'GII': 6, 'GI': 7}.get(tier)


def _history_key(start: dict) -> tuple:
    return (
        start.get('date'), start.get('venue'), start.get('surface'),
        start.get('distance_m'), start.get('finish'),
    )


def _enrich_last4(horse: dict, quality_tiers: dict[str, str]) -> dict:
    result = dict(horse)
    history = list(horse.get('full_history_before_target') or [])
    exact = {_history_key(row): row for row in history}
    loose = {
        (row.get('date'), row.get('venue'), row.get('surface'), row.get('distance_m')): row
        for row in history
    }
    enriched = []
    for raw in (horse.get('last4') or []):
        row = dict(raw)
        match = exact.get(_history_key(row)) or loose.get(
            (row.get('date'), row.get('venue'), row.get('surface'), row.get('distance_m'))
        )
        if match:
            for key in ('race_name', 'rt', 'jockey'):
                if row.get(key) is None and match.get(key) is not None:
                    row[key] = match[key]
            if row.get('class_rank') is None and match.get('class_rank') is not None:
                row['class_rank'] = match['class_rank']
        tier = quality_tiers.get(row.get('race_name')) if row.get('race_name') else None
        rank = _quality_class_rank(tier)
        if row.get('class_rank') is None and rank is not None:
            row['class_rank'] = rank
        enriched.append(row)
    result['last4'] = enriched
    return result


def classify_horse(horse: dict,
                   target_surface: str,
                   target_distance: int,
                   target_class_rank: int,
                   quality_tiers: dict[str, str]) -> dict:
    """Return deterministic C1/U/Q1/K1/rescue membership for one horse."""
    last4 = list(horse.get('last4') or [])
    latest = last4[0] if last4 else None

    c1 = False
    if (
        latest
        and latest.get('surface') == target_surface
        and latest.get('class_rank') is not None
        and int(latest['class_rank']) >= int(target_class_rank)
        and within_band(latest.get('distance_m'), target_distance)
    ):
        finish = latest.get('finish')
        margin = latest.get('margin_sec')
        finish_ok = (
            finish is not None and margin is not None
            and int(finish) <= 4 and float(margin) <= 1.0
        )
        close_ok = margin is not None and float(margin) <= 0.5
        c1 = finish_ok or close_ok

    u = bool(
        horse.get('age') == 3
        and horse.get('career_starts_before_target') is not None
        and int(horse['career_starts_before_target']) <= 5
        and latest
        and latest.get('is_win') is True
        and latest.get('surface') == target_surface
        and within_band(latest.get('distance_m'), target_distance)
    )

    q1 = False
    unknown_quality_tiers: list[str] = []
    for start in last4:
        if start.get('surface') != target_surface or not within_band(
            start.get('distance_m'), target_distance
        ):
            continue
        race_name = start.get('race_name')
        if not race_name:
            continue
        tier = quality_tiers.get(race_name)
        if tier is None:
            if start.get('rt') is not None or int(start.get('class_rank') or -1) >= 4:
                unknown_quality_tiers.append(race_name)
            continue
        finish = start.get('finish')
        if finish is None:
            continue
        finish = int(finish)
        if tier in {'L', 'GIII'} and finish == 1:
            q1 = True
        elif tier in {'GI', 'GII'} and finish <= 3:
            q1 = True

    kyoto_band = [
        start for start in (horse.get('full_history_before_target') or [])
        if start.get('venue') == '京都'
        and start.get('surface') == target_surface
        and within_band(start.get('distance_m'), target_distance)
        and start.get('finish') is not None
    ]
    k_wins = sum(int(start['finish']) == 1 for start in kyoto_band)
    k_top3 = sum(int(start['finish']) <= 3 for start in kyoto_band)
    k1 = k_wins >= 2 or (k_wins >= 1 and k_top3 >= 2)

    rescue = (q1 and k1) if int(target_class_rank) >= 6 else (q1 or k1)

    return {
        'C1': c1,
        'U': u,
        'Q1': q1,
        'K1': k1,
        'rescue': rescue,
        'K_wins': k_wins,
        'K_top3': k_top3,
        'unknown_quality_tiers': sorted(set(unknown_quality_tiers)),
    }


def _parse_date(value: str):
    from datetime import date
    return date.fromisoformat(value)


def _clean_jockey(value: str | None) -> str | None:
    if value is None:
        return None
    return str(value).strip().lstrip('★☆▲△◇').strip().replace(' ', '')


def uncertainty_flags(horse: dict,
                      target_surface: str,
                      target_distance: int,
                      target_class_rank: int,
                      target_date: str,
                      quality_tiers: dict[str, str],
                      target_venue: str = '京都') -> list[str]:
    """Report uncertainty; flags do not exclude a horse from the broad set."""
    history = list(horse.get('full_history_before_target') or [])
    flags: list[str] = []
    if history:
        latest = history[0]
        if latest.get('date'):
            days = (_parse_date(target_date) - _parse_date(latest['date'])).days
            if days > 120:
                flags.append('layoff_gt_120d')
        latest_rank = latest.get('class_rank')
        if latest_rank is None and latest.get('race_name'):
            latest_rank = _quality_class_rank(quality_tiers.get(latest['race_name']))
        if latest_rank is not None and int(latest_rank) < int(target_class_rank):
            flags.append('class_rise')
    if not any(row.get('venue') == target_venue for row in history):
        flags.append('first_run_at_venue')
    if not any(
        row.get('surface') == target_surface
        and row.get('distance_m') == target_distance
        for row in history
    ):
        flags.append('first_exact_distance')
    change = horse.get('body_weight_change_kg')
    if change is not None and abs(float(change)) >= 10:
        flags.append('body_weight_change_ge_10kg')
    current = _clean_jockey(horse.get('current_jockey'))
    past = {_clean_jockey(row.get('jockey')) for row in history if row.get('jockey')}
    if current and current not in past:
        flags.append('first_jockey_ride')
    return flags


def classify_race(normalized_horses: list[dict],
                  frozen_horses: list[dict],
                  target_surface: str,
                  target_distance: int,
                  target_class_rank: int,
                  quality_tiers: dict[str, str],
                  target_date: str,
                  target_venue: str = '京都') -> dict:
    """Classify one race using v3.1 and pre-race inputs only."""
    market = market_channel(frozen_horses)
    odds_by_number = {int(row['number']): float(row['win_odds']) for row in frozen_horses}
    rows = []
    unknown: set[str] = set()
    for source in normalized_horses:
        horse = _enrich_last4(source, quality_tiers)
        item = classify_horse(
            horse, target_surface, target_distance, target_class_rank, quality_tiers
        )
        item['M'] = int(horse['number']) in market
        item['union'] = item['M'] or item['C1'] or item['U'] or item['rescue']
        item['number'] = int(horse['number'])
        item['name'] = horse.get('name')
        item['frozen_win_odds'] = odds_by_number.get(item['number'])
        item['uncertainty_flags'] = uncertainty_flags(
            horse, target_surface, target_distance, target_class_rank,
            target_date, quality_tiers, target_venue,
        )
        unknown.update(item['unknown_quality_tiers'])
        rows.append(item)
    rows.sort(key=lambda row: row['number'])
    return {
        'method': 'v3.1_frozen_candidate_channels',
        'horses': rows,
        'sets': {
            key: [row['number'] for row in rows if row[key]]
            for key in ('M', 'C1', 'U', 'Q1', 'K1', 'rescue', 'union')
        },
        'unknown_quality_tiers': sorted(unknown),
    }


TARGETS = {
    7: {'surface': 'ダ', 'distance_m': 1900, 'class_rank': 1},
    8: {'surface': '芝', 'distance_m': 2000, 'class_rank': 1},
    9: {'surface': 'ダ', 'distance_m': 1800, 'class_rank': 2},
    10: {'surface': '芝', 'distance_m': 1800, 'class_rank': 2},
    11: {'surface': '芝', 'distance_m': 1400, 'class_rank': 6},
    12: {'surface': 'ダ', 'distance_m': 1200, 'class_rank': 1},
}


def run_audit(history_path, frozen_dir, quality_map_path, races):
    import json
    from pathlib import Path

    history = json.loads(Path(history_path).read_text(encoding='utf-8'))
    quality = json.loads(Path(quality_map_path).read_text(encoding='utf-8'))
    tiers = quality.get('tiers', quality)
    output_races = {}
    starter_count = candidate_count = 0
    channel_counts = {key: 0 for key in ('M', 'C1', 'U', 'Q1', 'K1', 'rescue')}
    unknown = set()

    for race in races:
        if race not in TARGETS:
            raise ValueError(f'unsupported_race:{race}')
        race_key = str(race)
        normalized = history['races'][race_key]['horses']
        frozen = json.loads(
            (Path(frozen_dir) / f'kyoto_{race:02d}.json').read_text(encoding='utf-8')
        )['horses']
        target = TARGETS[race]
        classified = classify_race(
            normalized, frozen,
            target_surface=target['surface'],
            target_distance=target['distance_m'],
            target_class_rank=target['class_rank'],
            quality_tiers=tiers,
            target_date=history.get('target_date', '2026-10-12'),
        )
        classified['target'] = target
        classified['field_size'] = len(normalized)
        classified['candidate_count'] = len(classified['sets']['union'])
        classified['candidate_fraction'] = (
            classified['candidate_count'] / classified['field_size']
            if classified['field_size'] else None
        )
        output_races[race_key] = classified
        starter_count += classified['field_size']
        candidate_count += classified['candidate_count']
        for key in channel_counts:
            channel_counts[key] += len(classified['sets'][key])
        unknown.update(classified['unknown_quality_tiers'])

    return {
        'schema_version': 1,
        'method': 'v3.1_frozen_candidate_channels',
        'uses_target_race_results': False,
        'target_date': history.get('target_date', '2026-10-12'),
        'races': output_races,
        'summary': {
            'starter_count': starter_count,
            'candidate_count': candidate_count,
            'candidate_fraction': candidate_count / starter_count if starter_count else None,
            'channel_memberships_nonexclusive': channel_counts,
            'unknown_quality_tiers': sorted(unknown),
        },
    }


def main() -> int:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', type=Path, required=True)
    parser.add_argument('--frozen-dir', type=Path, required=True)
    parser.add_argument('--quality-map', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--races', default='7,8,9,10,11,12')
    args = parser.parse_args()
    try:
        races = [int(value) for value in args.races.split(',') if value.strip()]
        result = run_audit(args.history, args.frozen_dir, args.quality_map, races)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
        )
        print(json.dumps(result['summary'], ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        print(str(error), file=__import__('sys').stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
