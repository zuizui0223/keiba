#!/usr/bin/env python3
"""Build a derived v3 race JSON by merging structured history onto frozen inputs."""
from copy import deepcopy


def merge_history(base, history, base_sha):
    if base.get('race') != history.get('race'):
        raise ValueError('race_mismatch')

    base_numbers = {h['number'] for h in base['horses']}
    history_numbers = {int(k) for k in history.get('horses', {})}
    if base_numbers != history_numbers:
        raise ValueError('history_roster_mismatch')

    out = deepcopy(base)
    checked = history.get('history_checked_at_jst')
    for horse in out['horses']:
        patch = deepcopy(history['horses'][str(horse['number'])])
        if 'history_checked_at_jst' not in patch:
            patch['history_checked_at_jst'] = checked
        horse.update(patch)

    out['v3_history_migration'] = {
        'derived_from_blob_sha': base_sha,
        'history_checked_at_jst': checked,
    }
    return out
