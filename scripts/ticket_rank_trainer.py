#!/usr/bin/env python3
"""Train a pre-race feature -> PL log-strength model with top-three censored labels.

Expected JSON: {"races": [{"race_id": ..., "start_jst": ...,
"result_known_at_jst": ..., "top3": [horse_number, ...],
"horses": [{"number": ..., "features_as_of_jst": ..., "features": {...}}, ...]}]}.
Only historical results available before --train-end may be included. This
program does not train on odds snapshots or construct fake pedigree features.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path

try:
    from scripts.ticket_type_models import _time
except ModuleNotFoundError:  # CLI: python scripts/ticket_rank_trainer.py
    from ticket_type_models import _time


def _vectorize(horses: list[dict], features: list[str], start: datetime) -> tuple[list[int], list[list[float]]]:
    nums, rows = [], []
    for horse in horses:
        n = horse.get('number')
        if type(n) is not int or n in nums or n < 1:
            raise ValueError('duplicate_or_invalid_horse_number')
        if _time(horse['features_as_of_jst']) >= start:
            raise ValueError('feature_not_known_before_start')
        data = horse['features']
        if not isinstance(data, dict):
            raise ValueError('invalid_features')
        vals = []
        for feature in features:
            v = data.get(feature)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f'missing_or_nonfinite_feature:{feature}')
            vals.append(float(v))
        nums.append(n)
        rows.append(vals)
    if not 3 <= len(nums) <= 18:
        raise ValueError('invalid_historical_field_size')
    return nums, rows


def fit_horse_log_strength(training_races: list[dict], features: list[str],
                           train_end_jst: str, *, steps: int = 150,
                           learning_rate: float = 0.2, l2: float = 0.02) -> dict:
    """Fit a ridge-regularized PL conditional top-three likelihood by gradient.

    Feature means/std are learned only from training rows. Each race has equal
    total weight; the 1st/2nd/3rd selections within a race share that weight.
    """
    cutoff = _time(train_end_jst)
    if not features or len(set(features)) != len(features) or not all(isinstance(x, str) and x for x in features):
        raise ValueError('feature_names_invalid')
    if type(steps) is not int or steps < 1 or not 0 < learning_rate <= 1 or l2 < 0:
        raise ValueError('optimizer_config_invalid')
    historical = []
    seen_ids = set()
    for race in training_races:
        start = _time(race['start_jst'])
        result_known = _time(race['result_known_at_jst'])
        if not start < result_known <= cutoff:
            raise ValueError('historical_result_not_known_at_train_end')
        nums, rows = _vectorize(race['horses'], features, start)
        top = race['top3']
        if len(top) != 3 or len(set(top)) != 3 or not set(top) <= set(nums):
            raise ValueError('invalid_historical_top3')
        if race['race_id'] in seen_ids:
            raise ValueError('duplicate_training_race_id')
        seen_ids.add(race['race_id'])
        historical.append((race['race_id'], nums, rows, top))
    if not historical:
        raise ValueError('no_training_races')
    flattened = [v for _, _, rows, _ in historical for v in rows]
    means = [math.fsum(row[k] for row in flattened) / len(flattened) for k in range(len(features))]
    sds = [math.sqrt(math.fsum((row[k] - means[k]) ** 2 for row in flattened) / len(flattened)) or 1.0
           for k in range(len(features))]
    data = [
        (nums, [[(row[k] - means[k]) / sds[k] for k in range(len(features))] for row in rows], top)
        for _, nums, rows, top in historical
    ]
    weights = [0.0] * len(features)
    for _ in range(steps):
        gradient = [0.0] * len(features)
        for nums, rows, top in data:
            position = {horse: i for i, horse in enumerate(nums)}
            available = list(range(len(nums)))
            for winner in top:
                logits = [math.fsum(weights[k] * rows[i][k] for k in range(len(features)))
                          for i in available]
                offset = max(logits)
                expv = [math.exp(v - offset) for v in logits]
                denom = math.fsum(expv)
                winner_pos = position[winner]
                for k in range(len(features)):
                    expected = math.fsum(expv[j] * rows[i][k] for j, i in enumerate(available)) / denom
                    gradient[k] += (rows[winner_pos][k] - expected) / 3
                available.remove(winner_pos)
        for k in range(len(features)):
            weights[k] += learning_rate * (gradient[k] / len(data) - l2 * weights[k])
    return {
        'model': 'ridge_pl_censored_top3', 'features': list(features),
        'means': means, 'sds': sds, 'coefficients': weights,
        'training_data_end_jst': train_end_jst,
        'training_race_count': len(historical),
        'calibrated': False,
    }


def score_future_race(model: dict, race: dict, as_of_jst: str) -> dict:
    as_of = _time(as_of_jst)
    start = _time(race['start_jst'])
    if not _time(model['training_data_end_jst']) < as_of < start:
        raise ValueError('model_not_pre_race')
    if 'top3' in race or 'result_known_at_jst' in race:
        raise ValueError('outcome_present_in_forecast_input')
    nums, rows = _vectorize(race['horses'], model['features'], start)
    if any(_time(h['features_as_of_jst']) > as_of for h in race['horses']):
        raise ValueError('feature_after_forecast_as_of')
    scores = {}
    for num, row in zip(nums, rows):
        scores[str(num)] = math.fsum(
            model['coefficients'][k] * ((value - model['means'][k]) / model['sds'][k])
            for k, value in enumerate(row)
        )
    return {
        'race_id': race['race_id'], 'training_data_end_jst': model['training_data_end_jst'],
        'scores_frozen_at_jst': as_of_jst, 'log_scores': scores,
        'model': model['model'], 'calibrated': False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training-races', type=Path, required=True)
    parser.add_argument('--features', required=True, help='Comma-separated strictly pre-race feature names')
    parser.add_argument('--train-end', required=True)
    parser.add_argument('--future-race', type=Path, required=True)
    parser.add_argument('--as-of', required=True)
    parser.add_argument('--output-model', type=Path, required=True)
    parser.add_argument('--output-scores', type=Path, required=True)
    args = parser.parse_args()
    try:
        historical = json.loads(args.training_races.read_text(encoding='utf-8'))['races']
        future = json.loads(args.future_race.read_text(encoding='utf-8'))
        model = fit_horse_log_strength(historical, args.features.split(','), args.train_end)
        scores = score_future_race(model, future, args.as_of)
    except (ValueError, KeyError, TypeError) as e:
        parser.error(str(e))
    for path, content in ((args.output_model, model), (args.output_scores, scores)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
