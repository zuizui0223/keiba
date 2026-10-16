#!/usr/bin/env python3
"""Compare frozen pre-race rankings against an official finishing order."""

def _metrics(result, prediction):
    winner = result[0]
    try:
        winner_rank = prediction.index(winner) + 1
    except ValueError:
        winner_rank = None

    actual_top2 = set(result[:2])
    predicted_top2 = set(prediction[:2])
    top2_exact_unordered = len(result) >= 2 and actual_top2 == predicted_top2

    actual_top3 = result[:3]
    top3_recall = (
        sum(h in set(prediction[:3]) for h in actual_top3) / len(actual_top3)
        if actual_top3 else None
    )

    return {
        "winner_rank": winner_rank,
        "top2_exact_unordered": top2_exact_unordered,
        "top3_recall": top3_recall,
    }


def compare_rankings(result, old, v2):
    return {"old": _metrics(result, old), "v2": _metrics(result, v2)}
