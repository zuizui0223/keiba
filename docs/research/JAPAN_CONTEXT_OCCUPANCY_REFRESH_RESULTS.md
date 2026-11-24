# Context occupancy composition and information refresh: completed results (2026-11-24)

**The fixed family-profile signal is conditional on own-history availability. In the late anchored cohort, refreshing own history dominates updating the family/global profile; adding the refreshed fixed sire correction beyond the refreshed baseline worsens prediction.** [Frozen protocol](JAPAN_CONTEXT_OCCUPANCY_REFRESH_PROTOCOL.md) · [successful workflow](https://github.com/zuizui0223/keiba/actions/runs/45378664497) · [stdout evidence](../evidence/japan-context-occupancy-refresh-20261124.json). Source commit `f8eae4e0da898db731a5a2e1e07ca3ce6f695ac5`; source, venue, strict denominator and PR81/85 parity passed. Artifact metadata checked; complete ZIP not independently extracted.

## Composition

| Seed | A 2021 minus B 2022 MSE gain | Composition term | Within-stratum term | Composition share |
|---|---:|---:|---:|---:|
| 20261124 | 0.012749623 | 0.011360264 | 0.001389359 | 89.103% |
| 20261125 | 0.013822821 | 0.011031871 | 0.002790949 | 79.809% |
| 20261126 | 0.013002054 | 0.011193943 | 0.001808111 | 86.094% |

The primary stratum shares are 3,737/7,276 vs 334/3,011 without previous eligible history. In source A 2021 the no-prior and prior-history gain means are +0.0324064684 and -0.0039746542; in B 2022 +0.0197802797 and -0.0002619129. B 2022's no-prior subgroup is positive with pointwise sire intervals above zero in all three splits; primary interval [0.0040655089,0.0343878769]. B 2023 initially-no-A-history subgroup also has a positive refreshed gain in all three splits; this definition does NOT imply zero updated own history. No 2024 cold subgroup interval excludes zero. Composition is exact arithmetic, not causal explanation: archive/anchor selection, years and covariates differ, and no composition uncertainty interval is estimated.

## Frozen and refreshed models

| Seed | Year | Horses | M00 | M10 | M01 | M11 | B11 | B11−M11 MSE | Pointwise sire interval | M10−M11 MSE |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 20261124 | 2022 | 3011 | 0.369745 | 0.369745 | 0.369745 | 0.369745 | 0.372388 | 0.001961299 | [-0.004791130, 0.009284101] | 0.000000000 |
| 20261124 | 2023 | 1588 | 0.374029 | 0.336559 | 0.367209 | 0.329368 | 0.326823 | -0.001670276 | [-0.006783982, 0.003874027] | 0.004788444 |
| 20261124 | 2024 | 743 | 0.406595 | 0.342630 | 0.397810 | 0.332244 | 0.317934 | -0.009304296 | [-0.016082264, -0.001845081] | 0.007008986 |
| 20261125 | 2022 | 3011 | 0.371099 | 0.371099 | 0.371099 | 0.371099 | 0.372388 | 0.000958078 | [-0.005619722, 0.008134749] | 0.000000000 |
| 20261125 | 2023 | 1588 | 0.374365 | 0.337197 | 0.367921 | 0.330233 | 0.326681 | -0.002332970 | [-0.006791538, 0.003214948] | 0.004648145 |
| 20261125 | 2024 | 743 | 0.405229 | 0.341251 | 0.396716 | 0.331363 | 0.317778 | -0.008818703 | [-0.016367475, -0.001858921] | 0.006650728 |
| 20261126 | 2022 | 3011 | 0.369465 | 0.369465 | 0.369465 | 0.369465 | 0.372397 | 0.002174804 | [-0.004630017, 0.009657785] | 0.000000000 |
| 20261126 | 2023 | 1588 | 0.373251 | 0.335940 | 0.367325 | 0.329632 | 0.326737 | -0.001900058 | [-0.006738067, 0.003521912] | 0.004198160 |
| 20261126 | 2024 | 743 | 0.405094 | 0.341204 | 0.396713 | 0.331132 | 0.317828 | -0.008633554 | [-0.016323178, -0.000799152] | 0.006771678 |

In primary 2024, M00 to M11 gain = 0.054933245. Two-order arithmetic allocation: own 0.047895241 (87.19%), donor-profile including global recalibration 0.007038003. B00→B11 RMSE reduction 21.56%. All three 2024 B11−M11 pointwise intervals are negative. The three 2023 contrasts are negative, intervals cross zero. Positive M10−M11 only means refreshing an already-added profile helps; it does not mean a refreshed family correction is useful relative to B11. Unbounded linear scores and incomplete classified-history observation retained for parity.

## Scope and next step

No claim that kin information biologically harms individuals, that elapsed time causes decay, or that genetic effects are identified. Fixed additive family correction can be miscalibrated after own information becomes informative. The next test is a source-A-only count-dependent calibration of the same correction, frozen before scoring source B, with explicit zero-history and no-correction benchmarks, shared denominators and chronology checks. This follow-up is post-hoc relative to already inspected B outcomes. No new entrants or prospective claims. Reused splits are dependent; intervals are pointwise conditional sensitivities. No betting or individual records exported.

[Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45378664497/artifacts/14912887286) · sha256:85016358e1fbc7ff408c353d6c6ecac444822fa1d0f0b6561ac54f9032aabcbd.
