# Betting/odds methods — separate from the ecological research

This is the **historical price-analysis and prediction-methods track**
of `keiba`, not the biological evidence base.
Return to [ecological research](../research/README.md) or
[repository home](../../README.md).

## What belongs here

- JRA racecards, dated actual win/place/quinella/wide/etc.
  source quotes, ticket inclusion/price comparisons,
  optional subjective selections and postrace audits.
- Frozen `v3.1` candidate-selection rules, fixed holdout
  contract, attempt/score ledgers, and separate model
  versus same-size market-popularity baselines.
- Archived race-day reports with their own dated source snapshots.
  **A saved quote is not the current payout.**

This program has **not** established calibrated win, Top-3
or multi-ticket probabilities, positive expected value or
profitable future wagering.

## Frozen v3.1 — read these first

| Purpose | Grounded source file |
| --- | --- |
| Candidate-generation rule `M/C1/U/Q1/K1/rescue` | [`scripts/v31_candidate_channels.py`](../../scripts/v31_candidate_channels.py) |
| Immutable classifier/input source version | [`docs/v31-holdout-freeze.json`](../v31-holdout-freeze.json) |
| Formal 20-race PROMOTE decision | [`docs/v31-holdout-decision-contract.json`](../v31-holdout-decision-contract.json) |
| Scored ledger | [`docs/v31-holdout-ledger.json`](../v31-holdout-ledger.json) |
| Chronologically eligible race attempt ledger | [`docs/v31-holdout-attempt-ledger.json`](../v31-holdout-attempt-ledger.json) |
| Runbook | [`docs/v31-holdout-operations.md`](../v31-holdout-operations.md) |
| Same-size market comparator | [`docs/v31-equal-market-shadow-protocol.md`](../v31-equal-market-shadow-protocol.md) |
| Betting regression test runner | [`scripts/run_non_ecology_tests.py`](../../scripts/run_non_ecology_tests.py) |

**Current `main` ledger at this reorganization commit:
scored 0/20 races, attempt 0.** The archived 2026-10-12
R7–R12 candidate recall is **in-sample development**, not
a 20-race prospective estimate of forecasting skill.
Changing this ledger requires the existing frozen date,
source and verification gates: do not add favorable past
analyses retrospectively.

## Dated analysis archives

| Cohort | Where to look | Provenance boundary |
| --- | --- | --- |
| 2026-10-12 Kyoto R6–R12 | [reports](../../reports/2026-10-12/), [historical data](../../data/2026-10-12/), [full old README preserved](../archive/README-main-before-reorganization-20261018.md) | Mixed original snapshot times and partially observed markets; postrace diagnostics cannot become pre-result predictions |
| 2026-10-17 Kyoto preflight | [official-card audit](../v31-prep-2026-10-17-thursday-correction.json), [historical preflight notes](../../reports/2026-10-15/v31-pre-card-readiness.md) | Not a successful eligible 20-race freeze |
| 2026-10-18 three-venue ticket evidence | [source input](../../data/2026-10-18/ticket-odds-snapshot.json), [saved audit](../../reports/2026-10-18/ticket-audit.md) | Snapshot-specific relative prices, not demonstrated expected value |
| 2026-10-18 秋華賞 (Shuka Sho) | **[Draft PR #5](https://github.com/zuizui0223/keiba/pull/5)** on `analysis/shuka-20261018-official-form` | The separate branch contains JRA 17-horse histories, real odds, relative ticket dominance, testing; **not merged into `main`** as of this reorganization |

Read-only archives are preserved. No historical price
or ticket suggestion is automatically live after its
specified quote timestamp.

## Critical distinction from ecology

An observation that the same horse's early GPS
interval is repeatable across dates does **not**
estimate its chance of winning or being one of the
Top 3. Likewise, a positive historical classifier
Top-3 recall on its development races does not
demonstrate an innate behavioral trait,
environmental reaction norm, or causal rival effect.

For ecological science use the
[original HORSES-ID sectionals evidence matrix](../research/EVIDENCE_MATRIX.md),
not race-day betting ranks or odds.
