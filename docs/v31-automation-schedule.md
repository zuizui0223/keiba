# v3.1 holdout automation schedule — Kyoto 2026-10-17

This schedule is operational metadata only. It does not change the frozen v3.1 scientific/candidate rules.

## Timeline

| JST | Stage | Allowed information | Repository effect |
|---|---|---|---|
| 2026-10-15 17:00 | pre-processing | current JRA race card and horse profiles; no target result | prepare source capture / normalized pre-race history only |
| 2026-10-17 12:55 | pre-result freeze | revalidated current card, active runners, current timestamped win odds, pre-race history | create the first valid v3.1 holdout freeze |
| 2026-10-17 16:40 | post-result scoring | official JRA result for the already frozen race only | write separate result/score and register ledger entry |

## Pre-processing stage

The Thursday stage may fetch the current race card and full horse histories for the earliest eligible Kyoto race.

It must not:

- create a holdout ledger entry;
- lock Thursday odds for Saturday;
- infer or inspect a target-race outcome;
- modify v3.1 thresholds, classifier, protocol or manifest.

Saturday's pre-result task must revalidate the active horse set and current odds. Thursday data are only a preparation cache.

## Pre-result freeze stage

The first chronologically eligible Kyoto race that passes all frozen checks becomes holdout #1.

Eligibility:

- Kyoto only;
- flat turf or dirt;
- 1-win class or higher;
- not restricted to 2-year-olds.

The freeze must exist before post time. It must validate the final active horse-number set, odds observation time, classifier/wrapper/preparer integrity and baseline quality tiers. A failed or impossible freeze does not enter the denominator; the next eligible Kyoto race may be attempted.

Prediction performance is never a reason to skip a successfully frozen race.

## Post-result stage

After the day's eligible programme has finished, locate the single valid holdout #1 freeze created earlier that day.

Then:

1. obtain the official JRA top three for that exact `race_id`;
2. write `result.json` separately;
3. calculate `score.json` without editing the freeze;
4. register the race in `docs/v31-holdout-ledger.json`;
5. re-check duplicate/backfill/integrity guards.

If no valid freeze exists, keep the ledger at 0/20.

## Current first candidate

The scheduled programme currently makes Kyoto 7R on 2026-10-17 (3yo+ 1-win, dirt 1800m, scheduled 13:15) the first candidate. This remains provisional until the current race card is revalidated.

See:

- `docs/v31-holdout-freeze.json`
- `docs/v31-holdout-ledger.json`
- `docs/v31-next-holdout-plan.md`
- `docs/v31-holdout-operations.md`
- `scripts/v31_prepare_snapshot.py`
- `scripts/v31_holdout.py`
