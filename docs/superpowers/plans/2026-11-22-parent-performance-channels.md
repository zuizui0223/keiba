# Parent Performance Channels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure conditional sire-side and dam-side historical performance value on the unchanged real 2022–24 cohort.

**Architecture:** Reuse PR70's historical feature builder and four original fits, add MS/MD to the same historical matrix, reproduce the complete frozen PR70 summary, then emit only anonymous parent-channel contrasts and support. Keep original scripts unchanged.

**Tech Stack:** Python 3.12, numpy, pandas, unittest, GitHub Actions.

**Spec:** `docs/research/JAPAN_2022_24_PARENT_PERFORMANCE_CHANNELS_PROTOCOL.md`.

## Global Constraints

- Exact source SHA and frozen PR70 JSON SHA; parity tolerance1e−12.
- Same244147 strict starts,12887 horses,35333 races; original2018–21 training and alpha100.
- MC,MS,MD,M2 always include both explicit count features. All PR70 models reproduced.
- Three primary paired contrasts × four periods =12 Bonferroni comparisons.
- Each parent bootstrap999, seed20261122, minimum30 recorded parent groups; unknown horses never create recorded-family support.
- No raw records, IDs, names, rankings or individual predictions published.

## Review Focus

- A feature omitted in MS/MD must not affect its fitted coefficients or predictions.
- The two conditional improvements are not an additive partition of the joint improvement.
- Multiple starts and period composition cannot silently change horse-equal weighting.
- Missing parents and zero-valued performance features must not be mistaken for positive/absent peer support.
- Parent resampling must use the selected parent's groups, with separate missing-horse singleton IDs and explicit low-known-group HOLD.

### Task 1: Fixed parent-channel estimator and source runner

**Files:** create `scripts/ecology_japan_2022_24_parent_performance_channels.py` and `tests/test_ecology_japan_2022_24_parent_performance_channels.py`.

**Interfaces:** `FEATURES` maps all six model names to original-order subsets; `fit_factorial(features,y,horses)` and `predict_factorial(models,features)` return all six; `paired_loss_terms(y,predictions)` returns combined_gain,sire_alone,dam_alone,sire_given_dam,dam_given_sire,sire_minus_dam; `paired_uncertainty(panel,gain,draws=999,seed=20261122,min_clusters=30)`; `parent_bootstrap(panel,gain,parent,draws=999,seed=20261122,min_clusters=30)`; `support_summary(panel,support)`; `summarize_period(panel,predictions,support,draws=999,min_clusters=30)`; `analyze(archive,db)` with CLI --archive --sqlite --output.

- [x] Write exact tests for original-fit parity, feature exclusion, signed loss paths, direct parent difference, repeated-start weights, parent-bootstrap scalar oracle and unknown-group handling, 12-way interval width, all joint/depth support cells and invalid records.
- [x] Run `python -m unittest discover -s tests -p 'test_ecology_japan_2022_24_parent_performance_channels.py' -v` and observe absent-module RED.
- [x] Implement the new module, reusing existing PR70 features/fits/variance and PR71 reference-parity helper. Keep original analysis modules unchanged.
- [x] Run new tests and unchanged PR70/71 tests to pass; obtain independent task review.

### Task 2: Actual sources, evidence and integration

**Files:** dedicated `.github/workflows/ecology-japan-2022-24-parent-performance-channels.yml`; aggregate/provenance JSON in docs/evidence; result report; research entrypoints.

- [x] Commit protocol/tests before inspecting new actual parent-channel results.
- [x] Run exact sources locally and in Actions; archive aggregate only and compare every numerical/status field.
- [x] Report all periods, both conditional gains, their paired difference, support and uncertain/negative outcomes; review numerical and scientific claims independently.
- [x] Run full ecology/non-ecology tests, navigation, relative-link checks and final branch review.
- [ ] Publish measured result PR for integration after final-head checks under existing authorization.
