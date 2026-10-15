# v3 broad-candidate retrospective diagnostic

**Status: retrospective diagnostic, not validation.**  
The v3 candidate rules were designed after observing the 2026-10-12 outcomes, so these races cannot validate predictive improvement.

## Aggregate

| Metric | v3 union | Market Top5 |
|---|---:|---:|
| Candidate slots | 57 | 30 |
| Mean candidates / race | 9.5 | 5 |
| Winners captured | 6/6 | 5/6 |
| Top3 captured | 16/18 | 13/18 |
| Top3 recall | 88.9% | 72.2% |
| Top3 hits / candidate slot | 28.1% | 43.3% |

The union screen catches three additional Top3 finishers and the 12R winner that market Top5 missed, but it nearly doubles the candidate count. **Coverage improved; efficiency did not.**

## Race-level result

- 7R: 11 candidates, Top3 3/3.
- 8R: 9 candidates, Top3 2/3; missed 7 レーヌマロン.
- 9R: 10 candidates, Top3 3/3.
- 10R: 7 candidates, Top3 3/3.
- 11R: 9 candidates, Top3 2/3; missed 4 スズハローム.
- 12R: 11 candidates, Top3 3/3.

## Missed cases

### 8R 7 レーヌマロン

Latest three structured runs before the race were 1-win turf 1800m 9th (+1.0), 1-win turf 2000m 7th (+1.1), and 1-win dirt 1800m 11th (+2.9). No current v3 union criterion fires.

**Do not add a bespoke rule just to capture this result.** The evidence available before the race did not make this an obvious systematic omission.

### 11R 4 スズハローム

Latest three were G1 turf1600 17th (+1.8), G3 turf1600 1st, and Listed turf1600 1st. The present union has no “recent high-class win at adjacent distance” criterion.

That may be a useful hypothesis for a future feature, but adding it now because the horse finished second would be retrospective overfitting.

## Decision

The broad union is useful as a **screening layer only**. It should feed a separate ranking/pruning model.

Next step:
1. freeze the broad-candidate feature extractor;
2. build ranking features without using 10/12 results as validation;
3. evaluate on future races against market baselines;
4. score both recall and candidate-set size/efficiency.
