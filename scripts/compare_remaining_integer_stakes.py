#!/usr/bin/env python3
"""Compare integer 100-yen exacta allocations with equivalent quinellas.

Reads saved quotes only. Enumerates every positive split for total stakes from
200 through 1,000 yen. This measures the efficiency of the same target event at
the displayed quotes, not calibrated expected value or a live payout guarantee.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


CASES = ((8, (5, 11)), (11, (9, 14)), (12, (1, 14)))
UNIT_YEN = 100
MAX_UNITS = 10


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def analyze_case(snapshots, race, pair):
    pages, sources = {}, []
    for code in ('ur', 'ut'):
        path = snapshots / f'r{race}_{code}.json'
        raw = path.read_bytes()
        page = json.loads(raw)
        assert page['race'] == race and page['page_code'] == code
        assert datetime.fromisoformat(page['updated_at_jst']) <= datetime.fromisoformat(page['observed_at_jst'])
        pages[code] = page
        sources.append({
            'source_url': page['url'],
            'updated_at_jst': page['updated_at_jst'],
            'observed_at_jst': page['observed_at_jst'],
            'snapshot_path': str(path.relative_to(Path(__file__).resolve().parents[1]))
                if path.is_relative_to(Path(__file__).resolve().parents[1]) else str(path),
            'snapshot_sha256': sha256(raw),
            'html_sha256': page['html_sha256'],
        })

    quinellas = [quote for quote in pages['ur']['quotes']['quinella']
                 if tuple(quote['selection']) == pair]
    assert len(quinellas) == 1, ('missing_or_duplicate_quinella', race, pair)
    exactas = sorted(
        [quote for quote in pages['ut']['quotes']['exacta']
         if set(quote['selection']) == set(pair)],
        key=lambda quote: quote['odds_low'],
    )
    assert len(exactas) == 2, ('missing_or_duplicate_exacta', race, pair)
    assert exactas[0]['selection'] == list(reversed(exactas[1]['selection']))
    quinella_odds = Decimal(str(quinellas[0]['odds_low']))
    exacta_odds = [Decimal(str(quote['odds_low'])) for quote in exactas]
    assert all(value.is_finite() and value >= 1
               for value in [quinella_odds, *exacta_odds])

    budgets = []
    for total_units in range(2, MAX_UNITS + 1):
        direct_return = quinella_odds * UNIT_YEN * total_units
        allocations = []
        for first_units in range(1, total_units):
            units = (first_units, total_units - first_units)
            returns = [exacta_odds[index] * UNIT_YEN * units[index]
                       for index in range(2)]
            assert all(value == value.to_integral_value()
                       for value in [direct_return, *returns])
            allocations.append({
                'units': list(units),
                'stakes_yen': [UNIT_YEN * count for count in units],
                'payouts_yen': [int(value) for value in returns],
                'minimum_payout_yen': int(min(returns)),
                'strictly_beats_direct_in_both_orders': all(
                    value > direct_return for value in returns),
                'gains_yen': [int(value - direct_return) for value in returns],
            })
        best = max(allocations, key=lambda allocation: allocation['minimum_payout_yen'])
        budgets.append({
            'total_yen': UNIT_YEN * total_units,
            'direct_quinella_payout_yen': int(direct_return),
            'best_split': best,
            'all_splits_checked': total_units - 1,
            'any_strictly_better_split': any(
                allocation['strictly_beats_direct_in_both_orders']
                for allocation in allocations),
        })

    successes = [budget for budget in budgets if budget['any_strictly_better_split']]
    smallest = successes[0] if successes else None
    return {
        'race': race,
        'target_unordered_top_two': list(pair),
        'quinella_odds': float(quinella_odds),
        'exacta_selections': [quote['selection'] for quote in exactas],
        'exacta_odds': [float(value) for value in exacta_odds],
        'continuous_equal_return_synthetic_odds': float(
            1 / sum(1 / value for value in exacta_odds)),
        'same_update_time': pages['ur']['updated_at_jst'] == pages['ut']['updated_at_jst'],
        'smallest_strict_improvement': smallest,
        'lower_budgets_exhaustively_rejected': [] if smallest is None else [
            budget['total_yen'] for budget in budgets
            if budget['total_yen'] < smallest['total_yen']],
        'all_budgets_through_1000': budgets,
        'sources': sources,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshots', type=Path, default=root / 'data/2026-10-12/remaining-snapshots')
    parser.add_argument('--output', type=Path, default=root / 'reports/2026-10-12/remaining-integer-comparisons.json')
    args = parser.parse_args()
    result = {
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'script_sha256': sha256(Path(__file__).read_bytes()),
        'unit_yen': UNIT_YEN,
        'budget_limit_yen': MAX_UNITS * UNIT_YEN,
        'method': ('Exhaust every positive integer split a+b=N for N=2,...,10. '
                   'Compare both conditional exacta returns against an equal-budget '
                   'single quinella using exact decimal arithmetic.'),
        'scope': ('Efficiency for the specified identical target event at saved '
                  'quotes, not a calibrated expected-value estimate or globally best bet.'),
        'assumptions': [
            'No dead heats, withdrawals or refunds.',
            'Displayed odds frozen for calculation only; actual JRA final odds can change.',
            'Gross payouts include returned stake. No tax effects or self-impact modeled.',
            'Both constructions return zero outside the specified unordered top-two event.',
        ],
        'cases': [analyze_case(args.snapshots, race, pair) for race, pair in CASES],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for case in result['cases']:
        print(json.dumps({key: case[key] for key in (
            'race', 'exacta_selections', 'exacta_odds', 'quinella_odds',
            'smallest_strict_improvement', 'lower_budgets_exhaustively_rejected',
        )}, ensure_ascii=False))


if __name__ == '__main__':
    main()
