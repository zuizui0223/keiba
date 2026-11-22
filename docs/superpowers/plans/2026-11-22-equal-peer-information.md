# Equal Peer Information Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure parent prediction differences after equalizing the number of distinct historical peers on the fixed real cohort.

**Architecture:** Add an isolated peer-selection module and a source runner that reuse unchanged PR70/72 features, fits, strict cohort and uncertainty helpers. Prepare historical peer pools once per cutoff, refit the two single-channel models for 32 fixed draws, average per-start losses, and publish aggregate-only results.

**Tech Stack:** Python3.12, numpy, pandas, unittest, GitHub Actions.

**Spec:** `docs/research/JAPAN_2022_24_EQUAL_PEER_INFORMATION_PROTOCOL.md`.

## Global Constraints

- Source A/B exact hashes and frozen PR70/72 evidence; new PR72 reference SHA18caad41d66257cc064de13051fbf65241493f869960cff2d05d7fde2968657f, parity1e−12.
- Same244147 starts/12887 horses/35333 races; training2018–21, alpha100, original column order/standardization/horse weights/clipping.
- Retain all rows, both original raw/log support counts and all own/context features. Replace only sire_kin_history/dam_kin_history with equal-k histories; k=min(s,d) excluding focal.
- Exactly32 seeds2026112200..2026112231. SHA256 over compact UTF-8 JSON array["keiba-equal-peer-v1",seed,cutoff_year,stratum,horse], digest order then horse ID. Evaluation cutoff_year=2022 for all years.
- Two primary contrasts balanced_sire_advantage and change_in_sire_advantage ×4periods=8Bonferroni; parent bootstrap999, seed20261122, min30 recordedgroups.
- Average squared losses, never averaged predictions; MCSE from32 whole-draw period contrasts, ddof1, SD/sqrt32.
- No raw rows/IDs/selected lists/predictions exported. Original analysis modules unchanged.

## Review Focus

- Focal exclusion at every rank, zero-score membership, all-strata own start counts; scalar oracle pins these.
- Common deterministic priorities, stable under permutation/subsetting, same2022 evaluation cutoff; golden digest and identical-pool tests.
- Unknown/conflicting parent mappings, invalid/future history and target outcome columns must fail before construction.
- Same-k replacement must leave all other features exactly unchanged and cannot silently misalign rows.
- Monte Carlo draws cannot become observations or a prediction ensemble; independent loss/weight/SD and paired-change identities required.

### Task 1: Equal-count feature engine and fixed source estimator

**Files:** create `scripts/ecology_japan_balanced_parent_history.py`, `scripts/ecology_japan_2022_24_equal_peer_information.py`, matching two test modules.

**Interfaces:**
- `peer_priority(seed,cutoff_year,stratum,horse)->bytes` implements the frozen encoding.
- `prepare_peer_block(history,target_context,*,cutoff_year)` returns a prepared block with `.counts` (RangeIndex DataFrame, sire_relative_count/dam_relative_count), `.k` integer array, `.own_counts` all-strata start counts, internal cached memberships. Target context has exactly ablation.CONTEXT columns, no outcomes. Nonempty, valid timestamps/IDs/scores, no conflicting parent mapping across history/targets. Reset target row order positionally to a RangeIndex.
- `balanced_performance(block,*,seed)->DataFrame` returns exactly the two legacy performance columns with same RangeIndex. One prefix-sum-ranked pool per parent/stratum, common priorities; exclude focal before top-k. Feature5/(own_counts+5)*selected_sum/(8+k).
- `replace_performance(base_features,performance)->DataFrame` requires matching unique RangeIndex, equal row count, finite values; returns a copy with only these two columns replaced.
- Runner constants SEEDS, PRIMARY, COMPARISONS=8, PARENT_REFERENCE/PARENT_REFERENCE_SHA; `summarize_period(panel,full_predictions,draw_losses,support,selected_counts,*,draws=999,min_clusters=30)` accepts all6 full predictions, draw_losses keysMS/MD each shape(32,n), support unchanged originalcounts, selected_counts aligned Series ofk. Returns full_models(all7 inclM0), balanced_models(MS/MD meanMSE andsqrtRMSE), mean_MSE_contrasts, primary_uncertainty, monte_carlo (mean,SD,MCSE,min,max), per_draw anonymous32 entries and support(original+balanced k bins/mean).
- `analyze(archive:Path,db:Path)->dict`, CLI --archive --sqlite --output. Hash both references before loading, verify full PR70/72 parity before balancedfits, build base train/eval features once, cache five cutoffs, then32×2fits. Work one draw at a time; keep only losses/statistics needed. It may restrict balanced evaluation construction to strict rows after original all-row parity.

Golden priority for seed2026112200,cutoff2022,stratum`turf:4`,horse`peer-a`: `6114d9dd86abf438839553522f6e974631e97a4822732a80351ebc8416c76c14`.

- [ ] Write failing sampling tests: independent scalar filtering/sorting oracle; unequal pools; neutral peers; focal rank0,k−1,k,last/absent; missing side; same pools; full smaller-side parity; permutations/subsets/repeated contexts; cutoff2022 for2024 targets; parent/date/ID/target-y errors; unchanged feature columns and misalignment.
- [ ] Write failing estimator tests: for y=[0,1], varying draw predictions prove mean loss differs from loss of mean prediction; correct fixed32 shape, bounds/finite, loss pairing C=E_S−E_D, equalhorse period weights, SD/MCSE and same B/C SD; k partitions and zero-support agreement;8-way correction replaces12; minimum recorded-parent groups; source/reference/target-label gate wiring.
- [ ] Observe absent-module RED, implement the two modules, run new tests and unchanged PR70/72 tests GREEN.
- [ ] Obtain independent task review, address correctness findings with scoped regression/re-review; freeze implementation.

### Task 2: Real data, evidence and integration

**Files:** `.github/workflows/ecology-japan-2022-24-equal-peer-information.yml`; aggregate/provenance JSON under docs/evidence; result report and research entrypoints.

- [ ] Commit protocol/plan before new actual-source runs; pin Python3.12,numpy2.2.6,pandas2.2.3 and single BLAS thread in aggregate-only workflow.
- [ ] Run exact private sources locally and Actions; verify archive member/digest and all aggregate fields across executions within1e−12 with exact integer/type/status equality.
- [ ] Report all4 periods, both primary intervals, per-side point changes,32-draw MC precision, support and M0; independently verify science/numbers.
- [ ] Run full ecology and other tests, navigation/links, whole-branch review and final-head CI.
- [ ] Publish and integrate measured results under prior main-merge authorization; verify merged tree/hashes and clean local state.
