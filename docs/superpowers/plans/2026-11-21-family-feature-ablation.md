# Family feature ablation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Execute the real 2022–24 four-model feature-block comparison and preserve all results.

**Architecture:** Reuse the locked source loader, historical features and strict denominator. Add a separate analysis module for the factorial fit and paired inference; avoid changes to original models. Save only anonymous aggregates and a result report.

**Tech Stack:** Python 3.12, numpy, pandas, unittest, GitHub Actions.

**Spec:** `docs/research/JAPAN_2022_24_FAMILY_FEATURE_ABLATION_PROTOCOL.md`.

## Global constraints

- Exact pre-2022 source hashes and same strict 244147 starts / 12887 horses.
- Training 2018–2021, alpha=100, unchanged original feature definitions.
- P contains count-dependent shrinkage; MC/MP are new retrospective refits.
- Positive MSE difference means improvement; no individual records exported.

## Review focus

- Endpoint parity must use the prior full and strict scores, not a refit-selected target.
- Equal-horse weights must be recomputed in each period, not per-row averages.
- Missing sire labels cannot combine unrelated horses into one family.
- Paired group inference must preserve repeated-horse and within-day dependence.
- All signs, M0 failures and feature-shrinkage limitations must survive publication.

### Task 1: Factorial predictions and paired aggregate statistics

**Files:** new `scripts/ecology_japan_2022_24_family_feature_ablation.py` and
`tests/test_ecology_japan_2022_24_family_feature_ablation.py`.

**Interfaces:** `fit_factorial(features, y, horses)` and `predict_factorial(models, features)`;
`paired_loss_terms(y, predictions)`; `paired_uncertainty(panel, gain, draws=999, seed=20261121, min_clusters=30)`;
`summarize_period(panel, predictions, draws=999, min_clusters=30)`; `analyze(archive, db)`.

- [x] Write tests for endpoint agreement, excluded-feature invariance, hand-computed signed loss decomposition, unequal-start horse weighting, missing-sire singleton handling, invalid row/rank rejection and absent-cluster HOLD.
- [x] Run `python -m unittest discover -s tests -p 'test_ecology_japan_2022_24_family_feature_ablation.py' -v`; confirm missing implementation fails.
- [x] Implement the interfaces and locked-source CLI; run the same tests to PASS.
- [x] Run original strong-history and strict-denominator tests; commit implementation and protocol.

### Task 2: Execute, review and integrate the actual result

**Files:** `.github/workflows/ecology-japan-2022-24-family-feature-ablation.yml`,
`docs/evidence/japan-2022-24-family-feature-ablation-20261121.json`, result report,
root/research README and evidence matrix.

- [x] Execute on both original SHA-verified files; fail closed on any parity drift.
- [x] Preserve all four model scores and two signed conditional contrasts per period; record source and run provenance.
- [x] Add independent code/scientific review and resolve material findings.
- [x] Run repository navigation, ecology regression and existing non-ecology gates.
- [x] Prepare PR #70 for integration after successful final-head checks under existing session authorization.

## Execution record

- Real locked-source cohort and all endpoint scores reproduced; two Actions executions succeeded.
- Code review identified one misleading inherited parity-field name; replaced by explicit M0/M1/M2 RMSE names and verified by a new regression test. No strict score changed.
- Claim review checked numerical tables and corrected the displayed MSE-unit caption; no P-versus-C superiority interval is claimed.
- Ruling: excluded-feature invariance uses absolute tolerance 1e-14 instead of bitwise equality because pandas/BLAS layout changed rounding by 2.2e-16. This ignores machine-rounding differences, while the original empirical 1e-8 score-parity gate stays unchanged.
- Final validation: 14 new tests, 876 ecology tests, 176 non-ecology tests passed. Required statsmodels was installed only in an ignored local QA environment after the first full local run reported seven missing-module import errors.
- Final result and run provenance: `docs/evidence/japan-2022-24-family-feature-ablation-provenance-20261121.json`.
- Integration is tracked by PR #70; the plan records readiness before the final merge event.
