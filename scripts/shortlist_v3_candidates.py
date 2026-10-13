#!/usr/bin/env python3
"""Build a bounded review shortlist from v3 broad candidate features.

This is not a horse ranking, probability model, or betting selector.
Market-supported candidates are retained, then at most a few non-market
"upside" candidates are added using pre-declared feature weights.
"""

SIGNAL_WEIGHTS = {
    'recent_similar_distance_win': 3,
    'lightly_raced_latest_win': 3,
    'lightly_raced_latest_close_form': 2,
    'recent_similar_distance_close_finish': 1,
}


def _upside_score(row):
    return sum(SIGNAL_WEIGHTS.get(signal, 0)
               for signal in row.get('positive_signals', []))


def shortlist_candidates(candidate_output, baseline_n=4, upside_slots=3):
    if candidate_output.get('status') != 'PASS':
        return {
            'status': 'DATA_HOLD',
            'shortlist': [],
            'baseline': [],
            'upside': [],
            'horse_ranking_produced': False,
            'ticket_selection_performed': False,
            'probabilities_assigned': False,
        }

    rows = [
        row for row in candidate_output.get('horse_features', [])
        if row.get('candidate')
    ]

    baseline_rows = [
        row for row in rows
        if 'market_top4' in row.get('positive_signals', [])
    ]
    baseline_rows.sort(
        key=lambda row: (
            row.get('market_rank') is None,
            row.get('market_rank') if row.get('market_rank') is not None else 10**9,
            row['number'],
        )
    )
    baseline_rows = baseline_rows[:baseline_n]
    baseline_numbers = {row['number'] for row in baseline_rows}

    upside_rows = []
    for row in rows:
        if row['number'] in baseline_numbers:
            continue
        score = _upside_score(row)
        if score <= 0:
            continue
        item = dict(row)
        item['upside_score'] = score
        upside_rows.append(item)

    upside_rows.sort(
        key=lambda row: (
            -row['upside_score'],
            row.get('market_rank') is None,
            row.get('market_rank') if row.get('market_rank') is not None else 10**9,
            row['number'],
        )
    )
    upside_rows = upside_rows[:upside_slots]

    baseline = [row['number'] for row in baseline_rows]
    upside = [row['number'] for row in upside_rows]
    shortlist = baseline + upside

    return {
        'status': 'PASS',
        'shortlist': shortlist,
        'baseline': baseline,
        'upside': upside,
        'upside_details': [
            {
                'number': row['number'],
                'name': row.get('name'),
                'market_rank': row.get('market_rank'),
                'upside_score': row['upside_score'],
                'positive_signals': row.get('positive_signals', []),
                'uncertainty_flags': row.get('uncertainty_flags', []),
            }
            for row in upside_rows
        ],
        'candidate_count_before_shortlist': len(rows),
        'shortlist_count': len(shortlist),
        'baseline_n': baseline_n,
        'upside_slots': upside_slots,
        'horse_ranking_produced': False,
        'ticket_selection_performed': False,
        'probabilities_assigned': False,
        'interpretation': (
            'Bounded review shortlist only. Baseline market support and '
            'upside signals are not calibrated win probabilities.'
        ),
    }
