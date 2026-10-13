# v3 implementation status — 2026-10-13

## What is implemented

- Structured recent-history sidecars for Kyoto 7R-12R.
- Derived v3 race JSONs that preserve frozen marks/notes.
- Fail-closed recent-history data gate.
- Broad candidate-pool generator.
- Bounded review shortlist (market Top4 + at most 3 upside runners).
- One-race v3 review runner.
- Frozen prospective evaluation specification.
- GitHub Actions unittest workflow.

## Structural data verification

Kyoto 7R-12R:
- races: 6
- runners: 83
- PASS: 83
- DATA_HOLD: 0
- frozen mark/notes mismatches: 0
- sidecar mismatches: 0

This is structural eligibility only. It is not predictive validation.

## Development diagnostics — not validation

The 2026-10-12 races were used to design v3 and are therefore excluded from prospective validation.

Broad candidate pool after the current signals:
- candidate slots: 49 / 83 runners
- official Top3 hits: 16 / 18

Bounded shortlist:
- maximum size: 7
- official Top3 hits: 15 / 18

These numbers describe training/development behavior only and must not be presented as out-of-sample performance.

## Frozen next-race rules

See `docs/v3-frozen-evaluation-spec.md`.

Key rules:
- data gate must PASS before any review output;
- broad candidate signals are frozen;
- shortlist = saved market Top4 + at most 3 upside candidates;
- no calibrated probabilities;
- no horse ranking claim;
- no ticket/betting selector;
- do not tune from individual future misses;
- at least 30 frozen races across at least 3 race days before any improvement claim.

## CI verification

Commit tested: `4056aaf8dca1543022022c0e76cab9fd08299794`.

GitHub Actions:
- `tests` run 38346689093: **success**
- `v3.1 holdout tests` run 38346689179: **success**

The previous CI failure was traced to one obsolete unit test whose "no signal" fixture became market Top4 after the intentional market-support feature was added. The test was corrected to place the no-signal runner outside the market Top4; production code was not changed for that failure.

## Current scientific status

**Ready for prospective evaluation, not validated as a predictive improvement.**

The next meaningful evidence must come from future races frozen before outcomes are observed.
