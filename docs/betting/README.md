# Betting/odds methods — separate from the ecological research

This is the **historical price-analysis and prediction-methods track**
of `keiba`, not the biological evidence base.
Return to [ecological research](../research/README.md) or
[repository home](../../README.md).

## New: eight ticket-type probability prototype (2026-11-22)

[Ticket-type joint model and validation plan](TICKET_TYPE_MODELS.md) adds a
separate, **uncalibrated** Plackett–Luce probability baseline for win/place,
frame/quinella/wide/exacta/trio/trifecta, with optional pre-race feature
training, strict snapshot cutoff checks and exact box/flow basket hit
probabilities. It does **not** replace or unfreeze v3.1, establish profit,
or enter its formal holdout ledger.

**New measured archive:** [2026-10-12 Kyoto 8R–12R odds-by-ticket audit](KYOTO_20261012_TICKET_TYPE_AUDIT.md) compared coherent win-odds-to-tickets probabilities with each ticket market’s simple normalized inverse-odds baseline. Five same-day retrospective races only; **not** a forward skill or profitable betting claim. The historical audit CI produces an inspectable source-hashed artifact.

**Latest cross-market test:** [Wide pair information transfer: 2026-10-12 vs 2026-10-18, nine races](WIDE_PAIR_INFORMATION_TRANSFER_RESULTS.md). A coherent 8-ticket distribution can use wide-pair residuals, but the two calendar dates show different signs for ordered-pair outcomes; place/wide Brier worsened on both dates across all nine price/strength sensitivity settings. **All retrospective**, not a prospectively validated forecasting edge or real odds arbitrage.

## New future validation track (2026-11-22, no real forecasts yet)

[Ticket-forward-v1 protocol, source-pinned manifest, 30 attempted races, server-sealed prediction and post-race scoring](TICKET_FORWARD_V1_PROTOCOL.md) adds a **separate prospective evaluation** of win-only PL versus coherent win+wide pair-residual forecasts across eight ticket types. The 2026-10-12 and 10-18 archived outcomes are explicitly excluded from its future denominator. The frozen v3.1 candidate-score and attempt ledgers are unchanged. The code uses synthetic-only tests; first future real forecast is **0** until new pre-race source snapshots are available.

**Next race-day preflight:** [JRA 2026-11-23 Tokyo/Fukushima preliminary first ten](JRA_2026-11-23_PROGRAM_PREFLIGHT.md) is a **provisional program**, not a prospectively sealed sample. The new [GitHub day-universe proof](../../scripts/ticket_forward_day_proof.py) and full 24/36-entry venue-roster guard demand the actual official whole-day source, a before-first-race server receipt and frozen day selection; no real day has passed that gate yet.

**Official-card read-only evidence (Nov 22 night):** [all 24 Nov23 JRA source URL / SHA256 / numbered-horse-row observations](../evidence/ticket-forward-20261123-jra-card-numbered-rows-20261122.json) and [strict reconciliation](../../scripts/ticket_forward_jra_reconcile.py) document 24/24 extracted numeric card tables and three discrepancies against an explicitly third-party provisional roster (Tokyo 1R, 4R, 6R). This is **not** source-complete live active runners, post-scratch confirmation, synchronized win/wide odds or a pre-first-race server-sealed cohort. The signed forward denominator remains 0.

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
