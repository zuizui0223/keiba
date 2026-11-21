# Sire signal concentration implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Measure how PR70's fixed conditional performance-block gain is distributed across recorded sire groups.

**Architecture:** Reuse the existing four-model source pipeline unchanged; add one aggregate-only analysis module and paired arithmetic tests. Reproduce the frozen PR70 score artifact before interpreting any new statistic.

**Tech Stack:** Python 3.12, numpy, pandas, unittest, GitHub Actions.

**Spec:** `docs/research/JAPAN_2022_24_SIRE_SIGNAL_CONCENTRATION_PROTOCOL.md`.

## Global constraints

- Same two source hashes, 244147 strict starts, 12887 horses, 35333 races.
- MC versus M2 only; same training years2018–21 and ridge alpha100.
- All four periods retained; no source records, identifiers or group rankings exported.
- Bootstrap999, seed20261121, minimum30 recorded sire groups for intervals.
- Worst-case deletion diagnoses fixed prediction losses, not retraining or causal family effects.

## Review focus

- Repeated starts must not give horses extra weight.
- Group size refers to evaluated horses; father-equal changes the target population.
- Missing sire labels remain outside known-sire estimands.
- Minimum simultaneous deletions must leave a nonempty cohort and count equality as nonpositive.
- Positive/negative concentration shares use separate gross masses, never a cancelling net denominator.

### Task 1: Concentration estimator and exact small examples

**Files:** `scripts/ecology_japan_2022_24_sire_signal_concentration.py`,
`tests/test_ecology_japan_2022_24_sire_signal_concentration.py`.

**Interfaces:** `sire_summary(panel, gain, draws=999, seed=20261121, min_clusters=30)`;
`analyze(archive, db)` with CLI `--archive --sqlite --output`.

- [x] Write failing tests for weighted versus group-equal means, covariance identity, LOSO,
      two-group failure despite positive LOSO, exact zero boundary, all-positive and all-zero
      cases, support-bin edges, repeated-start invariance, unknown parents and scalar bootstrap.
- [x] Run the new unittest module; confirm absent implementation fails.
- [x] Implement the aggregate estimator and source/PR70 parity gates; run tests to pass.
- [x] Retain original PR70 test suite unchanged; commit the protocol and implementation.

### Task 2: Actual-source execution and integration

**Files:** a dedicated Actions workflow, anonymous evidence/provenance JSON, result report,
research index, evidence matrix and concise root README entry.

- [x] Execute locally and in Actions on exact sources; compare numerical aggregates.
- [x] Independently review the estimator and claims, correcting material issues.
- [x] Run full ecology/non-ecology suites and repository navigation checks.
- [ ] Publish the result PR and integrate after its final-head checks under existing authorization.
