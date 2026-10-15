#!/usr/bin/env python3
"""Create immutable v3.1 pre-result freezes and separate post-result scores."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

FORBIDDEN_RESULT_KEYS = {
    'result', 'results', 'top3', 'winner', 'payouts', 'finish_order',
    'actual_top3', 'actual_winner', 'target_result'
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def parse_aware_iso(value: str, label: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f'invalid_datetime:{label}') from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f'naive_datetime:{label}')
    return dt


def load_classifier(path: Path):
    spec = importlib.util.spec_from_file_location('v31_frozen_classifier', path)
    if spec is None or spec.loader is None:
        raise ValueError('classifier_import_failed')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, 'classify_race'):
        raise ValueError('classifier_missing_classify_race')
    return module


def check_quality_baseline(manifest: dict, quality_map: dict) -> None:
    baseline = manifest.get('metadata_inputs', {}).get('quality_tier_baseline', {})
    tiers = quality_map.get('tiers', quality_map)
    for race_name, expected in baseline.items():
        if tiers.get(race_name) != expected:
            raise ValueError(f'quality_baseline_changed:{race_name}')


def check_no_target_results(race_input: dict) -> None:
    for key in FORBIDDEN_RESULT_KEYS:
        if key in race_input:
            raise ValueError(f'forbidden_target_result_key:{key}')


def unique_numbers(rows: list[dict], label: str) -> list[int]:
    nums = [int(row['number']) for row in rows]
    if len(nums) != len(set(nums)):
        raise ValueError(f'duplicate_horse_number:{label}')
    return nums


def freeze(args) -> int:
    race_input = read_json(args.race_input)
    odds = read_json(args.odds)
    source_meta = read_json(args.source_meta)
    quality = read_json(args.quality_map)
    manifest = read_json(args.manifest)

    if manifest.get('status') != 'frozen_for_prospective_holdout':
        raise ValueError('manifest_not_frozen')
    expected_wrapper = manifest.get('frozen_blobs', {}).get('holdout_wrapper')
    actual_wrapper = git_blob_sha(Path(__file__))
    if not expected_wrapper or actual_wrapper != expected_wrapper:
        raise ValueError(f'holdout_wrapper_sha_mismatch:{actual_wrapper}')
    check_no_target_results(race_input)
    if race_input.get('venue') != '京都':
        raise ValueError('ineligible_venue')
    target_meta = race_input.get('target', {})
    if target_meta.get('surface') not in {'芝', 'ダ'}:
        raise ValueError('ineligible_nonflat_surface')
    if int(target_meta.get('class_rank', -1)) < 1:
        raise ValueError('ineligible_class_below_1win')
    if race_input.get('age_scope') == '2yo':
        raise ValueError('ineligible_2yo_only')

    expected_preparer = manifest.get('frozen_blobs', {}).get('snapshot_preparer')
    actual_preparer = source_meta.get('preparer_git_blob_sha')
    if not expected_preparer or actual_preparer != expected_preparer:
        raise ValueError(f'snapshot_preparer_sha_mismatch:{actual_preparer}')
    if source_meta.get('race_id') != race_input.get('race_id'):
        raise ValueError('source_meta_race_id_mismatch')
    if source_meta.get('observed_at_jst') != odds.get('observed_at_jst'):
        raise ValueError('source_meta_observed_at_mismatch')
    if source_meta.get('uses_target_race_results') is not False:
        raise ValueError('invalid_source_meta')

    expected_classifier = manifest.get('frozen_blobs', {}).get('classifier')
    actual_classifier = git_blob_sha(args.classifier)
    if not expected_classifier or actual_classifier != expected_classifier:
        raise ValueError(f'classifier_sha_mismatch:{actual_classifier}')

    check_quality_baseline(manifest, quality)

    observed = parse_aware_iso(args.observed_at_jst, 'freeze_observed_at_jst')
    scheduled = parse_aware_iso(race_input['scheduled_start_jst'], 'scheduled_start_jst')
    odds_observed = parse_aware_iso(odds['observed_at_jst'], 'odds_observed_at_jst')
    if observed >= scheduled or odds_observed >= scheduled:
        raise ValueError('freeze_not_prerace')
    freeze_minutes_before = (scheduled - observed).total_seconds() / 60.0
    odds_minutes_before = (scheduled - odds_observed).total_seconds() / 60.0
    if not (15.0 <= freeze_minutes_before <= 25.0 and 15.0 <= odds_minutes_before <= 25.0):
        raise ValueError('freeze_outside_odds_window')
    if odds_observed > observed:
        raise ValueError('odds_observed_after_freeze')
    manifest_created = manifest.get('created_at_jst')
    if manifest_created:
        created = parse_aware_iso(manifest_created, 'manifest_created_at_jst')
        if observed < created or scheduled <= created:
            raise ValueError('race_before_holdout_freeze')

    horses = race_input['horses']
    frozen_horses = odds['horses']
    race_nums = unique_numbers(horses, 'race_input')
    odds_nums = unique_numbers(frozen_horses, 'odds')
    if set(race_nums) != set(odds_nums):
        raise ValueError('horse_number_set_mismatch')
    meta_nums = [int(value) for value in source_meta.get('active_horse_numbers', [])]
    if sorted(meta_nums) != sorted(race_nums):
        raise ValueError('source_meta_horse_number_set_mismatch')

    target = race_input['target']
    classifier = load_classifier(args.classifier)
    classified = classifier.classify_race(
        horses,
        frozen_horses,
        target_surface=target['surface'],
        target_distance=int(target['distance_m']),
        target_class_rank=int(target['class_rank']),
        quality_tiers=quality.get('tiers', quality),
        target_date=race_input['date'],
        target_venue=race_input.get('venue', '京都'),
    )

    union = classified['sets']['union']
    record = {
        'schema_version': 1,
        'holdout_version': manifest.get('version', 'v3.1'),
        'race_id': race_input['race_id'],
        'date': race_input['date'],
        'venue': race_input['venue'],
        'race_number': race_input['race_number'],
        'scheduled_start_jst': race_input['scheduled_start_jst'],
        'freeze_observed_at_jst': args.observed_at_jst,
        'odds_observed_at_jst': odds['observed_at_jst'],
        'uses_target_race_results': False,
        'target': target,
        'field_size': len(horses),
        'candidate_count': len(union),
        'candidate_fraction': len(union) / len(horses) if horses else None,
        'sets': classified['sets'],
        'horses': classified['horses'],
        'unknown_quality_tiers': classified.get('unknown_quality_tiers', []),
        'integrity': {
            'classifier_git_blob_sha': actual_classifier,
            'manifest_sha256': sha256_file(args.manifest),
            'race_input_sha256': sha256_file(args.race_input),
            'odds_input_sha256': sha256_file(args.odds),
            'source_capture_meta_sha256': sha256_file(args.source_meta),
            'quality_map_sha256': sha256_file(args.quality_map),
        },
    }
    write_json(args.output, record)
    return 0


def score(args) -> int:
    frozen = read_json(args.freeze)
    result = read_json(args.result)
    if frozen.get('uses_target_race_results') is not False:
        raise ValueError('invalid_prerace_freeze')
    if result.get('race_id') != frozen.get('race_id'):
        raise ValueError('race_id_mismatch')
    top3 = [int(x) for x in result.get('top3', [])]
    if len(top3) != 3 or len(set(top3)) != 3:
        raise ValueError('invalid_top3')
    known = {int(row['number']) for row in frozen.get('horses', [])}
    if not set(top3).issubset(known):
        raise ValueError('top3_unknown_horse')

    sets = frozen['sets']
    union = {int(x) for x in sets['union']}
    market = {int(x) for x in sets['M']}
    union_hits = [x for x in top3 if x in union]
    market_hits = [x for x in top3 if x in market]
    by_number = {int(row['number']): row for row in frozen.get('horses', [])}
    rescues = []
    for n in top3:
        if n in market:
            continue
        row = by_number[n]
        channels = [k for k in ('C1', 'U', 'Q1', 'K1', 'rescue') if row.get(k)]
        rescues.append({'number': n, 'channels': channels, 'captured': n in union})

    scored = {
        'schema_version': 1,
        'holdout_version': frozen.get('holdout_version'),
        'race_id': frozen['race_id'],
        'top3': top3,
        'winner': top3[0],
        'candidate_count': frozen['candidate_count'],
        'field_size': frozen['field_size'],
        'candidate_fraction': frozen['candidate_fraction'],
        'union_top3_hits': len(union_hits),
        'union_top3_hit_numbers': union_hits,
        'top3_recall': len(union_hits) / 3,
        'winner_in_union': top3[0] in union,
        'M_top3_hits': len(market_hits),
        'M_top3_hit_numbers': market_hits,
        'M_top3_recall': len(market_hits) / 3,
        'non_M_top3_rescues': rescues,
        'misses': [n for n in top3 if n not in union],
        'integrity': {
            'prerace_freeze_sha256': sha256_file(args.freeze),
            'result_input_sha256': sha256_file(args.result),
        },
    }
    write_json(args.output, scored)
    return 0


def _ledger_summary(entries: list[dict]) -> dict:
    races = len(entries)
    starter_count = sum(int(e['field_size']) for e in entries)
    candidate_count = sum(int(e['candidate_count']) for e in entries)
    union_hits = sum(int(e['union_top3_hits']) for e in entries)
    market_hits = sum(int(e['M_top3_hits']) for e in entries)
    winners = sum(bool(e['winner_in_union']) for e in entries)
    extra_candidates = candidate_count - sum(int(e.get('M_candidate_count', 0)) for e in entries)
    extra_hits = union_hits - market_hits
    rescues = {'C1': 0, 'U': 0, 'rescue': 0}
    for entry in entries:
        for item in entry.get('non_M_top3_rescues', []):
            for channel in rescues:
                if channel in item.get('channels', []):
                    rescues[channel] += 1
    return {
        'races_scored': races,
        'starter_count': starter_count,
        'candidate_count': candidate_count,
        'candidate_fraction': candidate_count / starter_count if starter_count else None,
        'union_top3_hits': union_hits,
        'union_top3_recall': union_hits / (3 * races) if races else None,
        'M_top3_hits': market_hits,
        'M_top3_recall': market_hits / (3 * races) if races else None,
        'winner_hits': winners,
        'winner_recall': winners / races if races else None,
        'added_candidates_over_M': extra_candidates,
        'additional_top3_hits_over_M': extra_hits,
        'added_candidates_per_additional_top3_hit': (
            extra_candidates / extra_hits if extra_hits > 0 else None
        ),
        'unique_rescues_by_channel': rescues,
    }


def register(args) -> int:
    from v31_validate_postrace import validate as validate_postrace

    # Registration must never trust score.json merely because its race_id matches.
    # Independently reconcile the immutable freeze, source result, score and
    # the previously recorded FROZEN attempt before modifying the score ledger.
    validate_postrace(
        args.freeze, args.result, args.result_capture, args.score, args.attempt_ledger
    )
    ledger = read_json(args.ledger)
    frozen = read_json(args.freeze)
    scored = read_json(args.score)
    if scored.get('race_id') != frozen.get('race_id'):
        raise ValueError('race_id_mismatch')
    if ledger.get('version') != frozen.get('holdout_version'):
        raise ValueError('ledger_version_mismatch')
    entries = list(ledger.get('entries', []))
    if any(e.get('race_id') == frozen.get('race_id') for e in entries):
        raise ValueError('duplicate_holdout_race')
    target_races = int(ledger.get('target_races', 20))
    if len(entries) >= target_races:
        raise ValueError('holdout_target_already_complete')
    if entries:
        last_start = parse_aware_iso(entries[-1]['scheduled_start_jst'], 'ledger_last_start')
        current_start = parse_aware_iso(frozen['scheduled_start_jst'], 'current_start')
        if current_start <= last_start:
            raise ValueError('holdout_backfill_forbidden')

    m_count = len(frozen.get('sets', {}).get('M', []))
    entry = {
        'holdout_index': len(entries) + 1,
        'race_id': frozen['race_id'],
        'scheduled_start_jst': frozen['scheduled_start_jst'],
        'freeze_observed_at_jst': frozen['freeze_observed_at_jst'],
        'field_size': int(scored['field_size']),
        'candidate_count': int(scored['candidate_count']),
        'candidate_fraction': scored['candidate_fraction'],
        'M_candidate_count': m_count,
        'union_top3_hits': int(scored['union_top3_hits']),
        'M_top3_hits': int(scored['M_top3_hits']),
        'winner_in_union': bool(scored['winner_in_union']),
        'misses': list(scored.get('misses', [])),
        'non_M_top3_rescues': list(scored.get('non_M_top3_rescues', [])),
        'prerace_freeze_sha256': scored.get('integrity', {}).get('prerace_freeze_sha256'),
        'score_sha256': sha256_file(args.score),
    }
    entries.append(entry)
    updated = dict(ledger)
    updated['entries'] = entries
    updated['summary'] = _ledger_summary(entries)
    updated['status'] = 'complete' if len(entries) >= target_races else 'collecting'
    write_json(args.output, updated)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('freeze')
    p.add_argument('--race-input', type=Path, required=True)
    p.add_argument('--odds', type=Path, required=True)
    p.add_argument('--source-meta', type=Path, required=True)
    p.add_argument('--quality-map', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--classifier', type=Path, required=True)
    p.add_argument('--observed-at-jst', required=True)
    p.add_argument('--output', type=Path, required=True)

    p = sub.add_parser('score')
    p.add_argument('--freeze', type=Path, required=True)
    p.add_argument('--result', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)

    p = sub.add_parser('register')
    p.add_argument('--ledger', type=Path, required=True)
    p.add_argument('--freeze', type=Path, required=True)
    p.add_argument('--result', type=Path, required=True)
    p.add_argument('--result-capture', type=Path, required=True)
    p.add_argument('--score', type=Path, required=True)
    p.add_argument('--attempt-ledger', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)

    args = parser.parse_args()
    try:
        if args.command == 'freeze':
            return freeze(args)
        if args.command == 'score':
            return score(args)
        if args.command == 'register':
            return register(args)
        raise ValueError('unknown_command')
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
