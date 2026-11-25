# Common-cohort transitional heterogeneity: results

2026-11-26 JST. **Annual intermediate-year peak not reproduced in same 527 horses. Frozen primary HOLD_LOW_STRATUM_SUPPORT, not a statistically established rejection.** [Frozen protocol](JAPAN_CONTEXT_TRANSITIONAL_HETEROGENEITY_PROTOCOL.md) · [Run](https://github.com/zuizui0223/keiba/actions/runs/45601408540) · [Receipt](../evidence/japan-context-transitional-heterogeneity-20261126.json).

Source commit 4591c479232643f74049230d4a3f15cb830aef61; source hashes, venue/strict denominators, original PR85/86/88 moments and synthetic checks passed. Output limited to anonymous aggregate statistics. Artifact 15016255784, sha256:50460e9fba3a7bacd535548b5a3e7fe837890c9cb53c8ec3bdbc440ec1170993; metadata verified but full ZIP not independently extracted. All annual and common cohorts are selected retrospective records.

## Fixed membership and support

All three seeds retain identical 527 horses / 115 recorded sires. Primary pre-2022 zero vs positive eligible history: 54 horses/37 sires versus 473/109; zero-history stratum is below 100 horses, so **HOLD** for intervals and peak inference under both profile conditions, all seeds. No change to frozen support. Predeclared alternate 0–3 vs 4+ counts: 288/83 vs 239/84; six conditions satisfy support and each uses 999 valid paired sire draws.

H = extra sample-optimal bounded two-stratum scalar gain over sample-optimal pooled scalar. This is not a deployable forecast. All twelve conditions show H2022 > H2023 > H2024, none show the proposed intermediate peak. Seed/profile comparisons share data and 2022 profiles are identical.

| Seed | Pre-2022 split | Profile | H2022 | H2023 | H2024 | Inference |
|---|---|---|---:|---:|---:|---|
| 20261124 | zero_vs_positive | fixed | 0.000579785 | 0.000278062 | 0.000011156 | HOLD |
| 20261124 | zero_vs_positive | refreshed | 0.000579785 | 0.000215032 | 0.000054161 | HOLD |
| 20261124 | 0_to_3_vs_4_plus | fixed | 0.001714535 | 0.000277719 | 0.000141338 | NOT_ESTABLISHED |
| 20261124 | 0_to_3_vs_4_plus | refreshed | 0.001714535 | 0.000379807 | 0.000194040 | NOT_ESTABLISHED |
| 20261125 | zero_vs_positive | fixed | 0.000489141 | 0.000190401 | 0.000009358 | HOLD |
| 20261125 | zero_vs_positive | refreshed | 0.000489141 | 0.000132269 | 0.000041955 | HOLD |
| 20261125 | 0_to_3_vs_4_plus | fixed | 0.001961406 | 0.000412406 | 0.000223455 | NOT_ESTABLISHED |
| 20261125 | 0_to_3_vs_4_plus | refreshed | 0.001961406 | 0.000569450 | 0.000259000 | NOT_ESTABLISHED |
| 20261126 | zero_vs_positive | fixed | 0.000641995 | 0.000226622 | 0.000004821 | HOLD |
| 20261126 | zero_vs_positive | refreshed | 0.000641995 | 0.000169010 | 0.000031344 | HOLD |
| 20261126 | 0_to_3_vs_4_plus | fixed | 0.001147497 | 0.000233050 | 0.000176226 | NOT_ESTABLISHED |
| 20261126 | 0_to_3_vs_4_plus | refreshed | 0.001147497 | 0.000307969 | 0.000163209 | NOT_ESTABLISHED |

## Supported sensitivity, not replacement primary

Primary seed, fixed profile, predeclared 0–3 vs 4+:
H2023−H2022 = −0.001436815 [two-contrast adjusted percentile interval −0.003536112, −0.000153384].
H2023−H2024 = +0.000136381 [−0.000557192, +0.000936206].
The first contrast is negative in two of six adjusted intervals; all six adjusted intervals for the second span zero. Neither the primary nor sensitivity establishes a 2023 peak. The second contrast is not a statistically established subsequent decline.

| Seed | Profile | H23−H22 | Adjusted 97.5% interval | H23−H24 | Adjusted 97.5% interval |
|---|---|---:|---|---:|---|
| 20261124 | fixed | -0.001436815 | [-0.003536112, -0.000153384] | 0.000136381 | [-0.000557192, 0.000936206] |
| 20261124 | refreshed | -0.001334728 | [-0.003449224, 0.000112398] | 0.000185767 | [-0.000570587, 0.001061160] |
| 20261125 | fixed | -0.001549000 | [-0.003972229, -0.000014292] | 0.000188951 | [-0.000601202, 0.001133067] |
| 20261125 | refreshed | -0.001391956 | [-0.003885370, 0.000218654] | 0.000310450 | [-0.000522413, 0.001390263] |
| 20261126 | fixed | -0.000914447 | [-0.002859790, 0.000137275] | 0.000056824 | [-0.000760477, 0.000785527] |
| 20261126 | refreshed | -0.000839528 | [-0.002806608, 0.000303161] | 0.000144760 | [-0.000643747, 0.000936756] |

## Descriptive transfer diagnostic

Previous-year scalar weights applied to later moments on the already selected common cohort. Zero-v-positive, fixed, primary seed: two-stratum minus pooled +0.000447254 (2022→23), −0.000166670 (2023→24), all three seeds same signs. With alternate 0–3 vs 4+, fixed, all three first transfers negative and all three later transfers positive. Refreshed profiles differ; full results in receipt. These are outcome-dependent earlier-year weights on future-common membership, not prospective forecasts. No transfer intervals or claim of improvement over previously frozen calibrated gate.

## Interpretation and stop

The population-level peak in earlier aggregate calculations is sensitive to restricting to same horses. Do not claim cohort composition is the unique causal explanation: restriction selects on future observation and changes the group residual/energy moments; a nonlinear optimum is not an additive mean contrast. No evidence for a universal hump-shaped temporal law, biological age effect, or individual learning. Retain robust earlier within-horse fixed-correction attenuation and recorded-sire direction control as main findings. Treat the transitional-peak hypothesis as unsupported in this selected panel, primary inferential HOLD. No new source, no genetic or market connection, no independent replication.
