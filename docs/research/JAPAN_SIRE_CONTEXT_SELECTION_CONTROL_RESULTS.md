# Within-horse and matched-sire falsification: completed retrospective results (2026-11-24)

[Protocol](JAPAN_SIRE_CONTEXT_SELECTION_CONTROL_PROTOCOL.md); [successful run](https://github.com/zuizui0223/keiba/actions/runs/45330108918), original commit `10abe66ab7f59fc8ad6e3d81e9eed5998375bd77`. Numerical results are from completed stdout; the artifact metadata was checked separately, not its ZIP contents. [Anonymous evidence receipt](../evidence/japan-sire-context-selection-control-20261124.json).

The primary PR78 contrast was reproduced to numerical precision: 83 sires, 174 sire-years, +0.006530724376455442. Candidate sample 57,208 starts / 15,129 horses. Within-horse and other-sire controls use the same previously examined source, not independent replication.

| Split | Seed | Paired horses before sire-year gate | Supported sires | Sire-years | Within-horse product | Matched sire pairs | Same−swapped product | Conditional pointwise 95% matched-pair interval |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| horse_day_disjoint | 20261124 | 1206 | 24 | 42 | 0.00745434 | 20 | 0.00662154 | [0.00148031, 0.01357794] |
| horse_day_disjoint | 20261125 | 1212 | 24 | 48 | 0.00941675 | 24 | -0.00384866 | [-0.01237448, 0.00297760] |
| horse_day_disjoint | 20261126 | 1161 | 25 | 44 | -0.00380363 | 20 | 0.00036920 | [-0.00812909, 0.00938335] |
| horse_day_trainer_disjoint | 20261124 | 603 | 10 | 12 | 0.02223154 | 15 | 0.01587770 | HOLD (<20 pairs) |
| horse_day_trainer_disjoint | 20261125 | 608 | 11 | 15 | 0.00391184 | 18 | 0.00115517 | HOLD (<20 pairs) |
| horse_day_trainer_disjoint | 20261126 | 617 | 9 | 12 | -0.00245918 | 14 | 0.01823910 | HOLD (<20 pairs) |

**Within-horse:** every split has fewer than the predeclared minimum 30 sires, so no interval or positive inference; main split +0.00745434, 24 sires / 42 sire-years, and negative point estimates in two sensitivity splits. The 1,206 paired horses in the main split are counted before the supported sire-year restriction. Trainer-disjoint versions yield just 9–11 sires. Do not relax the gate after inspection.

**Count-matched correspondence:** primary 20 disjoint matched pairs (40/83 sires), same-sire product 0.0063894262 vs swapped other-sire product −0.0002321147, difference +0.0066215409, pointwise interval [+0.0014803072,+0.0135779364]. However, a second split reverses sign and a third is near zero; their intervals include zero. Strict trainer-disjoint matched analyses have <20 pairs and are HOLD. Matching balances observed support years and counts, not all environmental or pedigree covariance. No claim of stable sire-specific advantage.

## Consequence

The observed PR78 family-indexed context resemblance remains descriptive; neither a stable within-horse reaction norm nor robust sire-specific correspondence is established. Target-context relevance is a plausible hypothesis, not a demonstrated explanation for PR77. Preserve both negative results and coverage loss. A next diagnostic should exploit whole-year temporal separation (rather than discarding half the dates) and disjoint horses: estimate family-indexed paired context contrasts from earlier years and predict held-year paired differences, with common-mean comparator and fixed shrinkage; inspect support and selection. No new independent prospective or causal evidence, no betting outcomes.

[Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45330108918/artifacts/14891910568); sha256:2c6d06f2f8bd533a58a9dfbd2d77d6f16f27bafc557b9e303872f66be3927885.
