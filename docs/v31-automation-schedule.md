# v3.1 holdout automation schedule — Kyoto 2026-10-17

This schedule is operational metadata only. It does not change the frozen v3.1 scientific/candidate rules.

## Timeline

| JST | Stage | Target | Repository effect |
|---|---|---|---|
| 2026-10-15 17:00 | pre-processing | all currently eligible Kyoto races | cache current JRA cards and pre-race horse histories; no target result |
| 2026-10-17 12:55 | pre-result freeze | R7, scheduled 13:15 | freeze inside the fixed 15–25 minute window; register FROZEN or PRE_RESULT_DATA_FAILURE attempt |
| 2026-10-17 13:25 | pre-result freeze | R8, scheduled 13:45 | same |
| 2026-10-17 14:30 | pre-result freeze | R10, scheduled 14:50 | same |
| 2026-10-17 15:10 | pre-result freeze | R11, scheduled 15:30 | same |
| 2026-10-17 15:55 | pre-result freeze | R12, scheduled 16:15 | same |
| 2026-10-17 16:50 | post-result scoring | every FROZEN attempt from the day | write result/score separately and register score ledger entries |
| 2026-10-17 17:20 | fail-safe audit | all eligible attempts from the day | detect missing attempt records or unscored FROZEN races; no result-driven backfill |

R9 Momiji S is excluded under the frozen rule because it is restricted to 2-year-olds.

## Pre-processing stage

The Thursday stage may fetch the current race cards and full horse histories for all eligible Kyoto races.

It must not:

- create scored holdout entries;
- lock Thursday odds for Saturday;
- infer or inspect target-race outcomes;
- modify v3.1 thresholds, classifier, protocol, decision contract or manifest.

Race-day tasks must revalidate the active horse set and current odds. Thursday data are preparation caches only.

## Pre-result attempt stage

Eligibility:

- Kyoto only;
- flat turf or dirt;
- 1-win class or higher;
- not restricted to 2-year-olds.

Every chronologically eligible race must produce exactly one attempt-ledger event:

- `FROZEN` when a valid pre-result freeze is created;
- `PRE_RESULT_DATA_FAILURE` with an explicit reason when the race is eligible but cannot be validly frozen.

A race that becomes ineligible under the current official conditions is documented operationally but does not enter the eligible-attempt denominator.

A failed eligible freeze is **not discarded**: it remains in `docs/v31-holdout-attempt-ledger.json` and lowers the technical evaluability rate.

Prediction performance is never a reason to skip a race or change an attempt status.

## Post-result stage

After the programme has finished:

1. verify the frozen contract;
2. re-check the official list of that day's eligible races against the attempt ledger;
3. fail closed if an eligible race has no chronological attempt record;
4. for each `FROZEN` attempt only, obtain the official JRA top three for that exact `race_id`;
5. write `result.json` separately;
6. calculate `score.json` without editing the freeze;
7. register score-ledger entries chronologically;
8. leave `PRE_RESULT_DATA_FAILURE` attempts unscored but in the attempt denominator;
9. create descriptive residual audits only for union misses.

No post-result process may backfill a missing pre-result attempt merely because the result is known.

## Formal evaluation

The formal evaluator is run only after 20 scored FROZEN races.

It uses both:

- `docs/v31-holdout-ledger.json` — scored FROZEN races;
- `docs/v31-holdout-attempt-ledger.json` — every eligible attempt through the 20th scored freeze.

PROMOTE requires all three frozen gates:

- exact one-sided stratified random-addition p <= 0.05;
- overall union candidate fraction <= 0.65;
- freeze success rate >= 0.80.

Interim values are descriptive only.

## Current first candidate

The scheduled programme currently makes Kyoto 7R on 2026-10-17 (3yo+ 1-win, dirt 1800m, scheduled 13:15) the first candidate. This remains provisional until the current JRA race card is revalidated.

See:

- `docs/v31-holdout-freeze.json`
- `docs/v31-holdout-ledger.json`
- `docs/v31-holdout-attempt-ledger.json`
- `docs/v31-holdout-decision-contract.json`
- `docs/v31-next-holdout-plan.md`
- `docs/v31-holdout-operations.md`
- `scripts/v31_prepare_snapshot.py`
- `scripts/v31_holdout.py`
- `scripts/v31_attempt_ledger.py`
- `scripts/v31_evaluate_holdout.py`
