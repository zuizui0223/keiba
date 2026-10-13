#!/usr/bin/env python3
"""Run the fail-closed v3 review pipeline for one race.

Pipeline:
1. recent-history data gate;
2. broad candidate pool;
3. bounded review shortlist.

No calibrated probabilities, horse ranking, or betting-ticket selection is produced.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path

from scripts.generate_v3_candidates import generate_candidates
from scripts.shortlist_v3_candidates import shortlist_candidates


def run_review(race, as_of, baseline_n=4, upside_slots=3):
    candidates = generate_candidates(race, as_of)
    if candidates.get('status') != 'PASS':
        return {
            'race': race.get('race'),
            'race_id': race.get('race_id'),
            'status': 'DATA_HOLD',
            'candidate_pool': [],
            'shortlist': [],
            'data_audit': candidates.get('data_audit'),
            'horse_ranking_produced': False,
            'probabilities_assigned': False,
            'ticket_selection_performed': False,
        }

    short = shortlist_candidates(
        candidates, baseline_n=baseline_n, upside_slots=upside_slots
    )
    return {
        'race': race.get('race'),
        'race_id': race.get('race_id'),
        'status': short['status'],
        'candidate_pool': candidates['candidates'],
        'candidate_features': candidates['horse_features'],
        'shortlist': short['shortlist'],
        'shortlist_baseline': short['baseline'],
        'shortlist_upside': short['upside'],
        'shortlist_upside_details': short.get('upside_details', []),
        'candidate_count': len(candidates['candidates']),
        'shortlist_count': len(short['shortlist']),
        'horse_ranking_produced': False,
        'probabilities_assigned': False,
        'ticket_selection_performed': False,
        'interpretation': (
            'Review-only output. Candidate inclusion and shortlist membership '
            'are not calibrated win probabilities or betting recommendations.'
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--as-of', required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--baseline-n', type=int, default=4)
    parser.add_argument('--upside-slots', type=int, default=3)
    args = parser.parse_args()

    as_of = datetime.fromisoformat(args.as_of)
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise SystemExit('timezone_required')

    race = json.loads(args.input.read_text(encoding='utf-8'))
    out = run_review(
        race, as_of, baseline_n=args.baseline_n,
        upside_slots=args.upside_slots,
    )
    text = json.dumps(out, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')
    return 0 if out['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
