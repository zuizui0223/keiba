#!/usr/bin/env python3
"""Helpers for leakage-safe evaluation of a frozen prediction version."""
from datetime import date, datetime


def validate_test_date(race_date, frozen_at):
    day = date.fromisoformat(race_date)
    frozen = datetime.fromisoformat(frozen_at)
    if frozen.tzinfo is None or frozen.utcoffset() is None:
        raise ValueError('timezone_required')
    if day <= frozen.date():
        raise ValueError('not_out_of_sample')
    return day


def score_candidate_set(candidates, official_top3, field_size):
    if field_size <= 0:
        raise ValueError('invalid_field_size')
    if len(candidates) != len(set(candidates)):
        raise ValueError('duplicate_candidate')
    if len(official_top3) != 3 or len(set(official_top3)) != 3:
        raise ValueError('invalid_official_top3')
    if any((not isinstance(x, int) or x < 1 or x > field_size)
           for x in candidates + official_top3):
        raise ValueError('runner_out_of_range')
    selected = len(candidates)
    candidate_set = set(candidates)
    hits = sum(x in candidate_set for x in official_top3)
    return {
        'selected': selected,
        'coverage': selected / field_size,
        'top3_hits': hits,
        'top3_recall': hits / 3,
    }
