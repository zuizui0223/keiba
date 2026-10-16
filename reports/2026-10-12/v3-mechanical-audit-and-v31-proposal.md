# v3.0 mechanical audit and v3.1 reduction proposal

This report is **development-only**. All Kyoto R7-R12 outcomes were already known while v3.0/v3.1 rules were being designed. None of the recall values below are prospective predictive evidence.

## Fully mechanical v3.0 result

Inputs:

- frozen pre-race win odds from `kyoto_07.json` ... `kyoto_12.json`
- all 83 starters' JRA histories truncated strictly before 2026-10-12
- verified quality-tier map for Q
- no target-race result inside the classifier

The deterministic classifier returns:

| Method | Candidates / starters | Candidate fraction | Top3 hits / slots | Development recall |
|---|---:|---:|---:|---:|
| M only | 22 / 83 | 26.5% | 11 / 18 | 61.1% |
| Old qualitative marks | 38 / 83 | 45.8% | 15 / 18 | 83.3% |
| **v3.0 M∪C∪U∪Q∪K** | **64 / 83** | **77.1%** | **18 / 18** | **100%** |

v3.0 therefore solves the three known omission examples, but at an excessive coverage cost. It adds 42 candidates over M to rescue 7 additional top-three slots: **6.0 extra candidates per additional top-three hit**.

This is not a satisfactory endpoint.

## Channel diagnostics

Channel memberships overlap.

| Channel | Candidate memberships | Top3 memberships |
|---|---:|---:|
| M | 22 | 11 |
| C | 38 | 10 |
| U | 6 | 4 |
| Q | 11 | 2 |
| K | 27 | 7 |

U is compact in this sample. C and K are broad. Q is concentrated almost entirely in the GII R11 field, where many runners necessarily have prior stakes/graded credentials.

The seven actual top-three horses missed by M and rescued by v3.0 are:

- R7 #9: C, K
- R8 #1: C
- R8 #7: K
- R9 #3: C
- R11 #4: Q, K
- R12 #10: U
- R12 #12: C

## Why v3.0 gets too large

### C

v3.0 allows any of the last three starts to qualify and uses:

> finish <= 4 OR beaten <= 0.5 seconds

In class races this can retain several horses that had one acceptable run among three.

### K

v3.0 accepts:

> >=2 Kyoto near-distance wins OR >=2 Kyoto near-distance top-three finishes

Repeated placings without a win are common enough to make K broad.

### Q

In a GII field, previous graded/listed form is not rare. Treating Q as a standalone rescue channel causes almost the entire strong-field race to become a candidate.

## Proposed v3.1 reduction

This is a **proposal**, not yet the prospective production rule.

### C1 — most recent start only

Require the **latest start** to satisfy:

- same surface
- same or higher class
- target distance ±20%
- and either:
  - finish 1-4 with beaten margin <=1.0 second, or
  - beaten margin <=0.5 second

This makes “recent form” literal instead of searching three starts for any qualifying run.

### K1 — require a win component

Require either:

- >=2 Kyoto near-distance wins, or
- >=1 Kyoto near-distance win AND >=2 top-three finishes.

Two placings without a win no longer independently rescue a horse.

### Q1 — stronger quality transfer

- Listed: win only
- GIII: win only
- GII / GI: top three

### Class-aware rescue gate

For targets below GII:

> rescue = Q1 OR K1

For GII/GI targets:

> rescue = Q1 AND K1

The rationale is that prior graded form and course records are common in a graded field and should not independently expand the candidate set.

Final proposed union:

> **M OR C1 OR U OR rescue**

## v3.1 development-only comparison

Applying those rules retrospectively:

| R | Field | v3.1 candidates | Fraction | Top3 captured |
|---|---:|---:|---:|---:|
| 7 | 16 | 8 | 50.0% | 3/3 |
| 8 | 11 | 7 | 63.6% | 3/3 |
| 9 | 12 | 7 | 58.3% | 3/3 |
| 10 | 10 | 7 | 70.0% | 3/3 |
| 11 | 18 | 9 | 50.0% | 3/3 |
| 12 | 16 | 11 | 68.8% | 3/3 |
| **Total** | **83** | **49** | **59.0%** | **18/18** |

Compared with v3.0:

- 64 -> 49 candidates
- 77.1% -> 59.0% candidate fraction
- development recall remains 18/18
- extra candidates per additional hit over M: 6.0 -> **3.86**

This is a large efficiency improvement, but 59.0% is still broad.

## Interpretation

Do **not** choose v3.1 because it preserved 18/18 on the same six races used to design it.

The legitimate reason to prefer its structure is narrower:

- C now means the most recent form rather than “one of three happened to look good”.
- K now requires evidence of winning at the venue/near distance.
- Q is prevented from flooding graded fields.
- U remains an explicit sparse-career growth channel.

If adopted, v3.1 must be frozen before the first holdout race and left unchanged for the full prospective window.

## Reproducibility

- normalized histories: `data/2026-10-12/v3-normalized-prerace-history.json`
- quality tiers: `data/2026-10-12/v3-quality-tier-map.json`
- v3.0 classifier: `scripts/v3_candidate_channels.py`
- v3.0 machine output: `reports/2026-10-12/v3-mechanical-channel-audit.json`
- outcome evaluation: `reports/2026-10-12/v3-mechanical-development-evaluation.json`
- unit tests: `tests/test_v3_candidate_channels.py`

The v3.1 numbers in this report are an exploratory reduction analysis; no v3.1 production script has been substituted for v3.0.
