#!/usr/bin/env python3
"""Audit saved Kyoto odds, compare identical events, and solve a snapshot maximin LP.

No fetching, outcome probabilities, bet execution, or claim of live arbitrage.
"""
import argparse
import hashlib
import itertools as it
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
from scipy import sparse
from scipy.optimize import linprog

KINDS = ('win', 'place', 'frame', 'quinella', 'wide', 'exacta', 'trio', 'trifecta')
CODES = ('tfw', 'ur', 'wide', 'ut', 'sf', 'st')
STARTS = {8: '14:00', 9: '14:35', 10: '15:10', 11: '15:45', 12: '16:30'}
COUNTS = {8: 11, 9: 12, 10: 10, 11: 18, 12: 16}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_race(folder, race):
    pages, provenance, markets = {}, [], {}
    start = datetime.fromisoformat('2026-10-12T' + STARTS[race] + ':00+09:00')
    for code in CODES:
        path = folder / f'r{race}_{code}.json'
        raw = path.read_bytes()
        page = json.loads(raw)
        assert page['race'] == race and page['page_code'] == code
        updated = datetime.fromisoformat(page['updated_at_jst'])
        observed = datetime.fromisoformat(page['observed_at_jst'])
        assert updated <= observed < start, ('non_pre_race_timestamp', race, code)
        assert not page['missing'], ('missing_parse_fields', race, code)
        source = {'path': str(path), 'snapshot_sha256': sha(raw),
                  'html_sha256': page['html_sha256'], 'source_url': page['url'],
                  'updated_at_jst': page['updated_at_jst'],
                  'observed_at_jst': page['observed_at_jst']}
        provenance.append(source)
        pages[code] = page
        for kind, quotes in page['quotes'].items():
            assert kind not in markets
            markets[kind] = {'quotes': quotes, **source}
    assert set(markets) == set(KINDS)
    horses = sorted(pages['tfw']['horses'], key=lambda h: h['number'])
    nums = [h['number'] for h in horses]
    n = len(nums)
    assert n == COUNTS[race] and len(set(nums)) == n
    assert nums == list(range(1, n + 1))
    horse_frame = {h['number']: h['frame'] for h in horses}
    assert set(horse_frame.values()) == set(range(1, 9))
    pairs = list(it.combinations(nums, 2))
    frame_pairs = {}
    for pair in pairs:
        frame = tuple(sorted(horse_frame[h] for h in pair))
        frame_pairs.setdefault(frame, []).append(pair)
    expected_sets = {'win': {(h,) for h in nums}, 'place': {(h,) for h in nums},
                     'frame': set(frame_pairs), 'quinella': set(pairs), 'wide': set(pairs),
                     'exacta': set(it.permutations(nums, 2)),
                     'trio': set(it.combinations(nums, 3)),
                     'trifecta': set(it.permutations(nums, 3))}
    by_kind, audit = {}, {}
    for kind, market in markets.items():
        quotes = market['quotes']
        keys = [tuple(q['selection']) for q in quotes]
        assert len(keys) == len(set(keys)), ('duplicate_selection', race, kind)
        assert set(keys) <= expected_sets[kind], ('invalid_selection', race, kind)
        assert all(math.isfinite(q['odds_low']) and q['odds_low'] >= 1 and
                   math.isfinite(q['odds_high']) and q['odds_high'] >= q['odds_low'] for q in quotes)
        expected = len(expected_sets[kind])
        assert len(keys) == (min(400, expected) if kind in ('trio', 'trifecta') else expected)
        by_kind[kind] = {tuple(q['selection']): q for q in quotes}
        audit[kind] = {'available': len(keys), 'expected_full': expected,
                       'missing_count': expected - len(keys), 'complete': len(keys) == expected,
                       'unique': True, 'all_selections_valid': True,
                       'updated_at_jst': market['updated_at_jst'], 'source_url': market['source_url']}
    return horses, horse_frame, frame_pairs, markets, by_kind, audit, provenance


def comparison(kind, selection, alternative, components, markets, by_kind):
    if any(s not in by_kind[alternative] for s in components):
        return None
    direct = by_kind[kind][selection]['odds_low']
    odds = [by_kind[alternative][s]['odds_low'] for s in components]
    synthetic = 1 / sum(1 / o for o in odds)
    return {'direct_market': kind, 'selection': list(selection), 'direct_odds': direct,
            'direct_popularity': by_kind[kind][selection].get('popularity'),
            'alternative_market': alternative, 'alternative_selections': [list(s) for s in components],
            'alternative_odds': odds, 'alternative_purchase_weights': [synthetic / o for o in odds],
            'equal_return_synthetic_odds': synthetic, 'identical_event': True,
            'singleton_exact_match': len(components) == 1,
            'preferred': 'direct' if direct >= synthetic else 'synthetic',
            'relative_payout_improvement': max(direct, synthetic) / min(direct, synthetic) - 1,
            'direct_to_synthetic_gain': direct / synthetic - 1,
            'same_update_time': markets[kind]['updated_at_jst'] == markets[alternative]['updated_at_jst'],
            'direct_updated_at_jst': markets[kind]['updated_at_jst'],
            'alternative_updated_at_jst': markets[alternative]['updated_at_jst'],
            'source_urls': [markets[kind]['source_url'], markets[alternative]['source_url']]}


def compare(markets, by_kind, frame_pairs):
    comparisons, skipped = [], []
    for selection in by_kind['quinella']:
        comparisons.append(comparison('quinella', selection, 'exacta',
                                      [selection, selection[::-1]], markets, by_kind))
    for selection in by_kind['trio']:
        item = comparison('trio', selection, 'trifecta', list(it.permutations(selection)), markets, by_kind)
        if item is None:
            skipped.append(list(selection))
        else:
            comparisons.append(item)
    for selection, pairs in frame_pairs.items():
        comparisons.append(comparison('frame', selection, 'quinella', pairs, markets, by_kind))
    assert all(x is not None for x in comparisons)
    dominance = []
    for frame, pairs in frame_pairs.items():
        f = by_kind['frame'][frame]['odds_low']
        for pair in pairs:
            q = by_kind['quinella'][pair]['odds_low']
            if f >= q and (f > q or len(pairs) > 1):
                dominance.append({'frame': list(frame), 'frame_odds': f, 'quinella': list(pair),
                                  'quinella_odds': q, 'frame_covered_horse_pairs': [list(p) for p in pairs],
                                  'strict_event_superset': len(pairs) > 1,
                                  'identical_event': len(pairs) == 1,
                                  'strictly_higher_quote': f > q, 'relative_payout_improvement': f / q - 1,
                                  'same_update_time': markets['frame']['updated_at_jst'] == markets['quinella']['updated_at_jst'],
                                  'source_urls': [markets['frame']['source_url'], markets['quinella']['source_url']]})
    dominance.sort(key=lambda d: (-d['relative_payout_improvement'], d['frame_odds']))
    # Readable opportunities: exact-match comparisons, supersets, and popular events.
    useful = []
    for d in dominance[:3]:
        useful.append({'comparison_type': 'frame_dominance', **d})
    popular = sorted((c for c in comparisons if c['direct_market'] != 'frame' and
                      c['direct_popularity'] is not None and c['direct_popularity'] <= 20),
                     key=lambda c: -c['relative_payout_improvement'])
    for c in popular:
        if len(useful) >= 5:
            break
        useful.append({'comparison_type': 'equivalent_event', **c})
    exclusive = {}
    for kind in ('win', 'frame', 'quinella', 'exacta'):
        inv = sum(1 / q['odds_low'] for q in by_kind[kind].values())
        exclusive[kind] = {'inverse_odds_sum': inv, 'full_book_equal_return_multiplier': 1 / inv}
    return {'equivalent_event_comparisons': comparisons,
            'comparison_counts': dict(Counter(c['direct_market'] for c in comparisons)),
            'trio_skipped_incomplete_six_trifectas': skipped,
            'frame_dominance_at_fixed_quotes': dominance,
            'top_useful_five': useful,
            'largest_relative_gains': sorted(comparisons, key=lambda c: -c['relative_payout_improvement'])[:10],
            'exhaustive_exclusive_markets': exclusive}


def solve_lp(horses, horse_frame, frame_pairs, markets):
    nums = [h['number'] for h in horses]
    n = len(nums)
    outcomes = np.array(list(it.permutations(nums, 3)), dtype=np.int16)
    sorted2 = np.sort(outcomes[:, :2], axis=1)
    sorted3 = np.sort(outcomes, axis=1)
    frame_lookup = np.array([0] + [horse_frame[h] for h in nums])
    frame2 = np.sort(frame_lookup[outcomes[:, :2]], axis=1)
    rows, cols, values, tickets = [], [], [], []
    counts_checked = Counter()
    for kind in KINDS:
        market = markets[kind]
        for q in market['quotes']:
            s = np.array(q['selection'])
            odds = float(q['odds_low'])
            if kind == 'win': hit = outcomes[:, 0] == s[0]; expected = (n-1)*(n-2)
            elif kind == 'place': hit = np.any(outcomes == s[0], axis=1); expected = 3*(n-1)*(n-2)
            elif kind == 'frame': hit = np.all(frame2 == s, axis=1); expected = len(frame_pairs[tuple(s)])*2*(n-2)
            elif kind == 'quinella': hit = np.all(sorted2 == s, axis=1); expected = 2*(n-2)
            elif kind == 'wide': hit = np.any(outcomes == s[0], axis=1) & np.any(outcomes == s[1], axis=1); expected = 6*(n-2)
            elif kind == 'exacta': hit = np.all(outcomes[:, :2] == s, axis=1); expected = n-2
            elif kind == 'trio': hit = np.all(sorted3 == s, axis=1); expected = 6
            elif kind == 'trifecta': hit = np.all(outcomes == s, axis=1); expected = 1
            idx = np.flatnonzero(hit)
            assert len(idx) == expected, ('payout_coverage_count', kind, q)
            counts_checked[kind] += 1
            rows.extend(idx.tolist()); cols.extend([len(tickets)] * len(idx)); values.extend([odds]*len(idx))
            tickets.append({'type': kind, 'selection': q['selection'], 'odds_low': odds,
                            'updated_at_jst': market['updated_at_jst'], 'source_url': market['source_url']})
    A = sparse.csc_matrix((values, (rows, cols)), shape=(len(outcomes), len(tickets)))
    m = len(tickets)
    aub = sparse.hstack([-A, sparse.csc_matrix(np.ones((len(outcomes), 1)))], format='csc')
    aeq = sparse.csc_matrix(np.array([[1.0]*m+[0.0]]))
    objective = np.zeros(m+1); objective[-1] = -1
    result = linprog(objective, A_ub=aub, b_ub=np.zeros(len(outcomes)), A_eq=aeq,
                     b_eq=[1.0], bounds=(0, None), method='highs')
    if not result.success:
        raise RuntimeError(result.message)
    weights, value = result.x[:-1], float(result.x[-1])
    returns = np.asarray(A @ weights).ravel()
    dual = -np.asarray(result.ineqlin.marginals)
    bound = -float(result.eqlin.marginals[0])
    dual_returns = np.asarray(A.T @ dual).ravel()
    checks = {'weight_sum_error': float(abs(weights.sum()-1)), 'min_weight': float(weights.min()),
              'max_primal_violation': float(max(0, value-returns.min())),
              'recomputed_min_return': float(returns.min()), 'recomputed_max_return': float(returns.max()),
              'dual_weight_sum_error': float(abs(dual.sum()-1)), 'min_dual_weight': float(dual.min()),
              'dual_upper_bound': bound, 'max_dual_violation': float(max(0, dual_returns.max()-bound)),
              'primal_dual_gap': float(bound-value), 'all_column_coverage_counts_checked': dict(counts_checked)}
    assert max(checks[k] for k in ('weight_sum_error', 'dual_weight_sum_error', 'max_primal_violation', 'max_dual_violation')) < 1e-7
    assert abs(checks['primal_dual_gap']) < 1e-7 and weights.min() > -1e-7 and dual.min() > -1e-7
    # Independent scalar hit definitions, all tickets on six representative outcomes.
    probe_rows = sorted(set([0, 1, len(outcomes)//4, len(outcomes)//2, len(outcomes)-2, len(outcomes)-1]))
    for row in probe_rows:
        o = tuple(map(int, outcomes[row])); f = sorted(horse_frame[h] for h in o[:2])
        for col, ticket in enumerate(tickets):
            s, k = ticket['selection'], ticket['type']
            hit = {'win': lambda: s[0] == o[0], 'place': lambda: s[0] in o,
                   'frame': lambda: sorted(s) == f, 'quinella': lambda: set(s) == set(o[:2]),
                   'wide': lambda: set(s).issubset(o), 'exacta': lambda: tuple(s) == o[:2],
                   'trio': lambda: set(s) == set(o), 'trifecta': lambda: tuple(s) == o}[k]()
            assert A[row, col] == (ticket['odds_low'] if hit else 0)
    checks['independent_scalar_payout_checks'] = len(probe_rows)*m
    active = sorted(({**t, 'weight': float(w)} for t, w in zip(tickets, weights) if w > 1e-9), key=lambda t: -t['weight'])
    return {'outcome_count': len(outcomes), 'ticket_count': m, 'nonzero_ticket_count': len(active),
            'maximin_gross_return_multiplier': value, 'maximin_net_return_fraction': value-1,
            'selected_tickets': active, 'verification': checks,
            'interpretation': 'Saved-quote continuous-weight minimum gross return, not calibrated EV or a live guarantee.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshots', type=Path, default=Path('data/2026-10-12/remaining-snapshots'))
    parser.add_argument('--output', type=Path, default=Path('reports/2026-10-12/remaining-market-analysis.json'))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'script_sha256': sha(Path(__file__).read_bytes()),
              'versions': {'numpy': np.__version__, 'scipy': scipy.__version__},
              'assumptions': ['No dead heats, withdrawals, refunds, or other exceptional settlements.',
                  'Actual frame assignments are read from each tfw.horses array.',
                  'Place and wide use displayed lower odds on every covered outcome.',
                  'Continuous nonnegative stakes total one; no budget, 100-yen rounding, or self-impact.',
                  'Intermediate quotes are not fixed at purchase and timestamps can differ between markets.',
                  'LP uses only observed tickets. Trifectas are partial in every race; trio is partial in R11/R12.',
                  'No probabilities, calibrated expected value, forecast of winners, or live arbitrage guarantee.'],
              'races': {}}
    for race in range(8, 13):
        horses, frames, frame_pairs, markets, by_kind, audit, sources = load_race(args.snapshots, race)
        item = {'race': race, 'race_id': f'26080405{race:02}', 'start_at_jst': '2026-10-12T'+STARTS[race]+':00+09:00',
                'horses': horses, 'market_audit': audit, 'sources': sources,
                'snapshot_bundle_sha256': sha(''.join(s['snapshot_sha256'] for s in sources).encode()),
                'comparisons': compare(markets, by_kind, frame_pairs)}
        item['lp'] = solve_lp(horses, frames, frame_pairs, markets)
        output['races'][str(race)] = item
        args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps({'race': race, 'lp': {k: item['lp'][k] for k in ('outcome_count','ticket_count','nonzero_ticket_count','maximin_gross_return_multiplier')},
                          'comparison_counts': item['comparisons']['comparison_counts'],
                          'frame_dominance_count': len(item['comparisons']['frame_dominance_at_fixed_quotes'])}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
