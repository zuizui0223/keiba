# Temporal transfer of paired context differences: completed retrospective results (2026-11-24)

**Primary transfer not established.** [Frozen protocol](JAPAN_SIRE_CONTEXT_TIME_TRANSFER_PROTOCOL.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45330597654), source commit `b10c99b9940c40ee56efceb34c5e8a3dc780617f` · [anonymous complete stdout receipt](../evidence/japan-sire-context-time-transfer-20261124.json). Artifact metadata separately checked, ZIP not independently extracted.

The original 57,208 candidate starts / 15,129 horses were reproduced. With no date thinning, 3,031 horse-years from 2,887 distinct paired-surface horses were available, 260 recorded sires. Primary 2021 target: 985 horses, 164 sires, 806 with >=3 earlier opposite-half paired horses in their sire, 793 also count-matched. M0=0.3191526260 and M1=0.3178873991 RMSE; MSE gain +0.0008060002, conditional whole-sire 95% interval [-0.0013482201,+0.0027638887]. Zero comparator RMSE 0.3230214204. About 0.3964% RMSE reduction in this split, not established as a repeatable gain.

| Split | Seed | Year | All target horses | Supported | Matched | M0−M1 MSE ×10^-3 | Pointwise 95% interval ×10^-3 | P−M1 MSE ×10^-3 (matched) | Pointwise interval ×10^-3 |
|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| horse_disjoint | 20261124 | 2020 | 1051 | 750 | 718 | -0.143531 | [-2.151528, 2.037310] | 3.477457 | [-0.187317, 7.660812] |
| horse_disjoint | 20261124 | 2021 | 985 | 806 | 793 | 0.806000 | [-1.348220, 2.763889] | 7.215613 | [1.978117, 13.161013] |
| horse_disjoint | 20261125 | 2020 | 1051 | 730 | 698 | -0.646666 | [-3.432428, 2.392741] | 0.123701 | [-4.305517, 4.608114] |
| horse_disjoint | 20261125 | 2021 | 985 | 801 | 767 | -0.620225 | [-2.942682, 1.745054] | 0.959298 | [-2.754703, 4.701536] |
| horse_disjoint | 20261126 | 2020 | 1051 | 711 | 678 | -0.658000 | [-2.549620, 1.681213] | 2.909621 | [-1.600163, 7.695488] |
| horse_disjoint | 20261126 | 2021 | 985 | 770 | 724 | 0.202841 | [-2.407254, 2.847667] | 5.898851 | [1.456077, 10.960117] |
| horse_and_trainer_disjoint | 20261124 | 2020 | 529 | 259 | 239 | 0.344177 | [-1.602562, 2.116486] | 3.411463 | [-1.188793, 8.852603] |
| horse_and_trainer_disjoint | 20261124 | 2021 | 508 | 329 | 318 | -1.660206 | [-4.986033, 1.127356] | -1.390044 | [-6.331200, 3.247600] |
| horse_and_trainer_disjoint | 20261125 | 2020 | 517 | 271 | 266 | -1.402035 | [-5.028499, 2.143394] | 0.750236 | [-10.049063, 9.511251] |
| horse_and_trainer_disjoint | 20261125 | 2021 | 468 | 307 | 291 | 0.068416 | [-2.533222, 2.696372] | 7.841508 | [2.519590, 13.274547] |
| horse_and_trainer_disjoint | 20261126 | 2020 | 554 | 288 | 281 | -0.546281 | [-1.653354, 0.721887] | 0.544425 | [-1.887881, 3.211823] |
| horse_and_trainer_disjoint | 20261126 | 2021 | 489 | 319 | 304 | -0.343508 | [-2.403144, 1.654842] | 3.333726 | [-2.023329, 8.580648] |

All-target gain positive in 4/12 conditions; no interval excludes zero. All three ordinary 2020 splits are negative. Same-sire predictor beats count-matched other-sire predictor in 11/12 conditions; 3/12 pointwise intervals positive, with no multiple-comparison or independent replication claim. In particular, placebo comparison is NOT a test of useful improvement versus population mean; a worse placebo can coexist with no gain versus M0. Full supported/matched scores are preserved. Negative strict 2021 primary-seed gain (-0.0016602062) is important.

## Interpretation

Family-indexed context resemblance (PR78) does not establish temporal portability on paired individual responses. PR79's insufficient paired support is partly resolved by year separation, but primary transfer intervals are still uncertain. The previously examined years are not an independent prospective confirmation. The target is conditioned on horses observed on both surfaces; normalized rank residuals are not absolute speed, heritability, or causal reaction norms. Same-sire vs other-sire matching balances counts only; common histories, management and environmental exposure remain. No betting models or ledgers changed.

Next contrast: observed family-specific context occupancy (which surface horses actually run on), using an own-history baseline, versus paired context performance. Stable exposure patterns can coexist with weak transferable performance. This does not establish voluntary habitat preference or genetic causality; environment assignment is mediated by human management.

[Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45330597654/artifacts/14891162854) · sha256:820bc5cbedb28678d7b3c3e67b2007d0e2763ec1e0b0dde40b7d1cb9ccce5def.
