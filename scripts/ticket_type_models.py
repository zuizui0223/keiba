#!/usr/bin/env python3
"""Coherent, deterministic top-three probabilities for eight JRA ticket types.

This is a *methodological baseline*, not a fitted/calibrated betting edge.
The same Plackett--Luce ordered finish distribution generates every ticket
probability. Historical odds are used as a market-only strength proxy unless
separately timestamped, independently trained log-scores are supplied.
No result files or v3.1 holdout ledger are read or modified.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations, permutations
import json
import math
from pathlib import Path

KINDS = ('win', 'place', 'frame', 'quinella', 'wide', 'exacta', 'trio', 'trifecta')
SINGLE_WINNER_KINDS = {'win', 'frame', 'quinella', 'exacta', 'trio', 'trifecta'}


def _time(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError('missing_timestamp')
    when = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError('naive_timestamp')
    return when


def _positive(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f'{label}_invalid')
    try:
        result = float(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f'{label}_invalid') from e
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f'{label}_invalid')
    return result


def _available(n: int, frames: dict[int, int], sale_n: int) -> dict[str, bool]:
    has_shared_frame = max(Counter(frames.values()).values(), default=0) >= 2
    return {
        'win': sale_n >= 2,
        'place': sale_n >= 5,
        'frame': sale_n >= 9 or has_shared_frame,
        'quinella': sale_n >= 3,
        'wide': sale_n >= 4 and n >= 3,
        'exacta': sale_n >= 3,
        'trio': sale_n >= 4 and n >= 3,
        'trifecta': sale_n >= 4 and n >= 3,
    }


def event_selection(kind: str, order: tuple[int, ...], frames: dict[int, int],
                    place_slots: int = 3) -> list[tuple[int, ...]]:
    """Return *all* winning selections for an ordered top-three outcome."""
    if kind == 'win':
        return [(order[0],)]
    if kind == 'place':
        return [(horse,) for horse in order[:place_slots]]
    if kind == 'frame':
        return [tuple(sorted((frames[order[0]], frames[order[1]])))]
    if kind == 'quinella':
        return [tuple(sorted(order[:2]))]
    if kind == 'wide':
        return [tuple(sorted(pair)) for pair in combinations(order[:3], 2)]
    if kind == 'exacta':
        return [order[:2]]
    if kind == 'trio':
        return [tuple(sorted(order[:3]))]
    if kind == 'trifecta':
        return [order[:3]]
    raise ValueError(f'unknown_ticket_kind:{kind}')


def predict_tickets(strengths: dict[int, float], frames: dict[int, int],
                    on_sale_field_size: int | None = None) -> dict[str, dict[tuple[int, ...], float]]:
    """Exactly enumerate top-three PL permutations (at most 18P3 = 4,896).

    Unordered pairs/triples are aggregated *after* sampling without replacement.
    Frame 1-1 style selections are kept when two separate horses share a frame.
    """
    if not 2 <= len(strengths) <= 18:
        raise ValueError('field_size_out_of_range')
    numbers = sorted(strengths)
    if any(type(n) is not int or n < 1 or n > 18 for n in numbers):
        raise ValueError('horse_numbers_invalid')
    if set(frames) != set(numbers) or any(type(v) is not int or not 1 <= v <= 8 for v in frames.values()):
        raise ValueError('missing_or_invalid_frames')
    if on_sale_field_size is None:
        on_sale_field_size = len(numbers)
    if type(on_sale_field_size) is not int or not len(numbers) <= on_sale_field_size <= 18:
        raise ValueError('invalid_on_sale_field_size')
    max_s = max(_positive(strengths[n], f'strength_{n}') for n in numbers)
    weights = {n: _positive(strengths[n], f'strength_{n}') / max_s for n in numbers}
    if min(weights.values()) <= 0:
        raise ValueError('strength_numerical_underflow')
    available = _available(len(numbers), frames, on_sale_field_size)
    output: dict[str, dict[tuple[int, ...], float]] = {
        kind: defaultdict(float) for kind in KINDS if available[kind]
    }
    k = min(len(numbers), 3)
    slots = 2 if 5 <= on_sale_field_size <= 7 else 3
    for ordered in permutations(numbers, k):
        remaining = set(numbers)
        mass = 1.0
        for n in ordered:
            denom = math.fsum(weights[i] for i in remaining)
            mass *= weights[n] / denom
            remaining.remove(n)
        for kind in output:
            for selection in event_selection(kind, ordered, frames, slots):
                output[kind][selection] += mass
    return {kind: dict(probs) for kind, probs in output.items()}



def forecast_basket(strengths: dict[int, float], frames: dict[int, int],
                    tickets: list[dict], on_sale_field_size: int | None = None) -> dict:
    """Exactly compute a box/flow/formation basket's chance of *any* ticket hit.

    Multiple overlapping place/wide tickets cannot be summed as independent
    events. Price-dependent expected return is omitted unless every ticket has
    its own stated hypothetical decimal odds (not final dividends).
    """
    events = predict_tickets(strengths, frames, on_sale_field_size)
    normalized = []
    for ticket in tickets:
        kind = ticket['kind']
        if kind not in events:
            raise ValueError('ticket_not_on_sale')
        key = _normalized_key(kind, ticket['selection'])
        if key not in events[kind]:
            raise ValueError('ticket_not_in_field')
        stake = ticket.get('stake_yen', 100)
        if type(stake) is not int or stake <= 0 or stake % 100:
            raise ValueError('stake_must_be_positive_100_yen_multiple')
        odds = ticket.get('odds_low')
        if odds is not None:
            odds = _positive(odds, 'odds_low')
            if odds < 1:
                raise ValueError('invalid_ticket_price')
        normalized.append((kind, key, stake, odds))
    if len({(kind, key) for kind, key, _, _ in normalized}) != len(normalized):
        raise ValueError('duplicate_ticket_selection')
    if not normalized:
        raise ValueError('empty_basket')
    numbers = sorted(strengths)
    weights = {n: _positive(strengths[n], 'strength') for n in numbers}
    slots = 2 if 5 <= (on_sale_field_size or len(numbers)) <= 7 else 3
    probability_any = 0.0
    probability_profit_at_low = 0.0
    total_stake = sum(stake for _, _, stake, _ in normalized)
    all_priced = all(price is not None for _, _, _, price in normalized)
    expected_hits = math.fsum(events[kind][key] for kind, key, _, _ in normalized)
    for ordered in permutations(numbers, min(3, len(numbers))):
        remaining = set(numbers)
        mass = 1.0
        for n in ordered:
            mass *= weights[n] / math.fsum(weights[i] for i in remaining)
            remaining.remove(n)
        winning = {kind: set(event_selection(kind, ordered, frames, slots))
                   for kind in {kind for kind, _, _, _ in normalized}}
        hits = [(stake, price) for kind, key, stake, price in normalized
                if key in winning[kind]]
        if hits:
            probability_any += mass
        if all_priced and sum(stake * price for stake, price in hits) > total_stake:
            probability_profit_at_low += mass
    expected_return_low = (math.fsum(stake * price * events[kind][key]
                           for kind, key, stake, price in normalized)
                           if all_priced else None)
    return {
        'ticket_count': len(normalized), 'total_stake_yen': total_stake,
        'probability_at_least_one_hit': probability_any,
        'probability_all_miss': max(0.0, 1.0 - probability_any),
        'expected_winning_ticket_count': expected_hits,
        'hypothetical_expected_return_low_yen': expected_return_low,
        'hypothetical_expected_net_low_yen':
            expected_return_low - total_stake if all_priced else None,
        'hypothetical_probability_net_profit_low': probability_profit_at_low if all_priced else None,
        'status': 'UNCALIBRATED_PL_AND_NONFINAL_ODDS',
    }

def _market_odds(snapshot: dict, as_of: datetime) -> tuple[dict[int, float], dict, datetime]:
    markets = snapshot['markets']
    start = _time(snapshot['start_jst'])
    checked = _time(snapshot['checked_at_utc'])
    if as_of >= start or checked > as_of or checked >= start:
        raise ValueError('snapshot_not_pre_race_as_of')
    win = markets['win']
    quotes = win['quotes']
    if not quotes or len(quotes) != len(snapshot['horse_frames']):
        raise ValueError('incomplete_win_market')
    odds = {}
    for quote in quotes:
        selection = quote['selection']
        if len(selection) != 1 or type(selection[0]) is not int or selection[0] in odds:
            raise ValueError('duplicate_or_invalid_win_selection')
        low = _positive(quote['odds_low'], 'win_odds')
        high = _positive(quote['odds_high'], 'win_odds')
        if high < low or low < 1:
            raise ValueError('invalid_win_odds_range')
        odds[selection[0]] = low
    frame_ids = {int(k) for k in snapshot['horse_frames']}
    if set(odds) != frame_ids:
        raise ValueError('market_field_mismatch')
    for kind, market in markets.items():
        if kind not in KINDS:
            continue
        observed = _time(market['observed_at_utc'])
        updated = _time(market['updated_at_jst'])
        if observed < updated or observed > as_of or updated > as_of or observed >= start:
            raise ValueError(f'{kind}_quote_after_as_of_or_race')
    return odds, markets, start


def _read_external_scores(scores: dict, race_id: str, numbers: set[int], as_of: datetime,
                          start: datetime) -> dict[int, float]:
    if scores.get('race_id') != race_id:
        raise ValueError('score_race_id_mismatch')
    trained = _time(scores['training_data_end_jst'])
    frozen = _time(scores['scores_frozen_at_jst'])
    if not trained < frozen <= as_of < start:
        raise ValueError('future_or_unfrozen_independent_scores')
    raw = {int(n): v for n, v in scores['log_scores'].items()}
    if set(raw) != numbers:
        raise ValueError('score_field_mismatch')
    vals = {}
    for n, v in raw.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ValueError('nonfinite_log_score')
        vals[n] = float(v)
    maximum = max(vals.values())
    return {n: max(math.exp(v - maximum), 1e-300) for n, v in vals.items()}


def _normalized_key(kind: str, selection: list[int]) -> tuple[int, ...]:
    lengths = {'win': 1, 'place': 1, 'frame': 2, 'quinella': 2,
               'wide': 2, 'exacta': 2, 'trio': 3, 'trifecta': 3}
    if len(selection) != lengths[kind] or any(type(v) is not int for v in selection):
        raise ValueError('invalid_ticket_selection')
    key = tuple(selection)
    if kind in ('frame', 'quinella', 'wide', 'trio'):
        key = tuple(sorted(key))
    if kind != 'frame' and len(set(key)) != len(key):
        raise ValueError('duplicate_horse_in_ticket')
    return key


def forecast_snapshot(snapshot: dict, as_of_jst: str, *, source: str = 'market',
                      external_scores: dict | None = None, top: int = 5) -> dict:
    """Output pre-race ticket forecasts; low/high odds EV is only hypothetical."""
    as_of = _time(as_of_jst)
    win_odds, markets, _ = _market_odds(snapshot, as_of)
    frame_ids = {int(n): int(frame) for n, frame in snapshot['horse_frames'].items()}
    if source == 'market':
        strengths = {n: 1.0 / odds for n, odds in win_odds.items()}
        source_label = 'MARKET_ONLY_BASELINE_NOT_INDEPENDENT'
    elif source == 'external' and external_scores is not None:
        strengths = _read_external_scores(external_scores, snapshot['race_id'],
                                         set(win_odds), as_of, _time(snapshot['start_jst']))
        source_label = 'EXTERNAL_FROZEN_SCORES_NOT_YET_VALIDATED'
    else:
        raise ValueError('invalid_strength_source')
    probs = predict_tickets(strengths, frame_ids, snapshot.get('on_sale_field_size'))
    if type(top) is not int or top < 1:
        raise ValueError('invalid_top')
    reports = {}
    for kind, dist in probs.items():
        quotes = {}
        market = markets.get(kind)
        if market:
            for quote in market['quotes']:
                key = _normalized_key(kind, quote['selection'])
                if key in quotes or key not in dist:
                    raise ValueError(f'{kind}_invalid_or_duplicate_quote')
                low = _positive(quote['odds_low'], 'odds_low')
                high = _positive(quote['odds_high'], 'odds_high')
                if low < 1 or high < low:
                    raise ValueError(f'{kind}_invalid_odds_range')
                quotes[key] = (low, high)
        ordered = sorted(dist.items(), key=lambda row: (-row[1], row[0]))
        top_rows = []
        for sel, p in ordered[:top]:
            entry = {'selection': list(sel), 'probability': p}
            if sel in quotes:
                low, high = quotes[sel]
                entry.update(odds_low=low, odds_high=high,
                             hypothetical_ev_low_per_100_yen=100 * (p * low - 1),
                             hypothetical_ev_high_per_100_yen=100 * (p * high - 1))
            top_rows.append(entry)
        reports[kind] = {
            'selection_count': len(dist),
            'quoted_count': len(quotes),
            'quoted_market_complete': len(quotes) == len(dist),
            'expected_winning_selections': math.fsum(dist.values()),
            'top_by_probability': top_rows,
        }
    return {
        'race_id': snapshot['race_id'], 'as_of_jst': as_of_jst,
        'model': 'joint_plackett_luce_exact_top_three',
        'source': source_label,
        'probability_status': 'UNCALIBRATED_RESEARCH_BASELINE',
        'historical_data_note': 'Observed snapshot; not a live price or prospectively proven edge',
        'horse_count': len(win_odds),
        'market_quote_limits': 'Only quoted selections have hypothetical price EV; final payouts unknown',
        'ticket_types': reports,
    }


def evaluate_outcome(strengths: dict[int, float], frames: dict[int, int],
                     actual_top3: list[int], on_sale_field_size: int | None = None) -> dict:
    """Pure holdout scorer; call only *after* an immutable forecast exists."""
    if len(actual_top3) != min(3, len(strengths)) or len(set(actual_top3)) != len(actual_top3):
        raise ValueError('finish_top3_invalid_or_dead_heat')
    if not set(actual_top3) <= set(strengths):
        raise ValueError('unknown_finisher')
    probs = predict_tickets(strengths, frames, on_sale_field_size)
    slots = 2 if 5 <= (on_sale_field_size or len(strengths)) <= 7 else 3
    results = {}
    for kind, dist in probs.items():
        winners = set(event_selection(kind, tuple(actual_top3), frames, slots))
        if not winners <= dist.keys():
            raise ValueError('winner_not_in_support')
        brier = math.fsum((p - int(key in winners)) ** 2 for key, p in dist.items()) / len(dist)
        clipped = lambda x: min(1-1e-15, max(1e-15, x))
        logloss = -math.fsum(
            math.log(clipped(p)) if key in winners else math.log1p(-clipped(p))
            for key, p in dist.items()
        ) / len(dist)
        results[kind] = {
            'ticket_count': len(dist), 'winning_ticket_count': len(winners),
            'brier_mean_per_ticket': brier, 'binary_log_loss_mean_per_ticket': logloss,
            'winning_selection_probability': math.fsum(dist[k] for k in winners),
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--market-snapshot', type=Path, required=True)
    parser.add_argument('--as-of', required=True, help='e.g. 2026-10-12T13:45:00+09:00')
    parser.add_argument('--strength-source', choices=['market', 'external'], default='market')
    parser.add_argument('--external-scores', type=Path)
    parser.add_argument('--top', type=int, default=5)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        snapshot = json.loads(args.market_snapshot.read_text(encoding='utf-8'))
        external = json.loads(args.external_scores.read_text(encoding='utf-8')) if args.external_scores else None
        report = forecast_snapshot(snapshot, args.as_of, source=args.strength_source,
                                   external_scores=external, top=args.top)
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    output = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding='utf-8')
    else:
        print(output, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
