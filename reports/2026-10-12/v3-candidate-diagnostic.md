# v3 broad-candidate retrospective diagnostic

**Status: retrospective diagnostic, not validation.**  
The v3 rules were designed after observing the 2026-10-12 failures. These races are training/diagnostic evidence and cannot validate predictive improvement.

Canonical generator: `scripts/generate_v3_candidates.py`.

## Aggregate

| Metric | v3 union | Old marked candidates | Market Top4 |
|---|---:|---:|---:|
| Candidate slots | 49 | 38 | 24 |
| Mean candidates / race | 8.17 | 6.33 | 4.00 |
| Winners captured | **6/6** | 5/6 | 5/6 |
| Top3 captured | **16/18** | 15/18 | 12/18 |
| Top3 recall | **88.9%** | 83.3% | 66.7% |
| Top3 hits / candidate slot | 32.7% | 39.5% | **50.0%** |

The v3 union has the highest coverage, including the 12R upset winner, but it uses 49 runner-slots. Market Top4 is much more selective.

**Conclusion: coverage improved retrospectively; selection efficiency did not.**

## Race-level result

| R | Field | v3 candidates | Top3 recall | Missed |
|---|---:|---:|---:|---|
| 7R | 16 | 9 | 2/3 | 9 |
| 8R | 11 | 5 | 2/3 | 7 |
| 9R | 12 | 7 | 3/3 | — |
| 10R | 10 | 6 | 3/3 | — |
| 11R | 18 | 12 | 3/3 | — |
| 12R | 16 | 10 | 3/3 | — |

Total: **49 candidates, 16/18 Top3, 6/6 winners**.

## What the union actually does

A horse can enter through any of these pre-result signals:

- market Top4;
- win within ±200m of today's distance on the same surface;
- close Top3 within ±200m on the same surface;
- lightly raced horse with a latest win or close form within a wider distance window.

Layoff/surface/distance changes are stored as uncertainty flags rather than automatic exclusions.

No probabilities are produced. No ticket is selected.

## Missed cases

### 7R 9 エイユーファイヤー

The canonical union missed the eventual third-place horse. This is a reminder that even a broad 9/16 screen is incomplete.

### 8R 7 レーヌマロン

Latest structured runs were 1-win turf1800 9th (+1.0), 1-win turf2000 7th (+1.1), and 1-win dirt1800 11th (+2.9). No current v3 positive rule fires.

Adding a custom condition after the result would be overfitting.

## Why not widen it further now

The current screen already covers **59% of runner-slots (49/83)**. Adding rules to chase the remaining two Top3 misses would make the screen even less selective.

Therefore the next problem is not “catch every horse.” It is:

> given a broad candidate set, can a frozen ranking/pruning layer beat the market baseline on future races?

## Decision

1. Freeze the current `generate_v3_candidates.py` rules.
2. Do not tune thresholds further on the October 12 races.
3. Treat 7R–12R only as diagnostic/training evidence.
4. Build ranking features separately from candidate generation and separately from ticket pricing.
5. Evaluate the ranking/pruning layer on a future race set, tracking both recall and candidate count/efficiency.

The matching machine-readable record is `v3-candidate-diagnostic.json`.
