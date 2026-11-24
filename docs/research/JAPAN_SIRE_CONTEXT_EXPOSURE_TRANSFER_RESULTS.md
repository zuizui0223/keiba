# Family-associated observed environment occupancy: completed retrospective results (2026-11-24)

**Consistent positive conditional transfer of observed annual turf-start fraction; paired context-performance transfer remains uncertain (PR80).** [Frozen protocol](JAPAN_SIRE_CONTEXT_EXPOSURE_TRANSFER_PROTOCOL.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45332342678), source commit `e29c1c083be466398d1edac275d10d2c64741058` · [stdout evidence](../evidence/japan-sire-context-exposure-transfer-20261124.json). Artifact metadata verified separately; full ZIP not independently extracted.

Source parity: 57,208 candidate starts / 15,129 horses in JRA 1600–1999m in 2019–21. 2021: 7,276 observed horse-years, 349 sires, 18,905 starts; 2,862 turf-only, 3,429 dirt-only, 985 both; 3,737 had no earlier eligible start history, 3,538 had last-known trainer peers. The no-date-thinning paired counts exactly match PR80. The primary ordinary horse-disjoint 2021 split with own-history baseline: 6,589 supported and 6,358 matched. M0 RMSE 0.4232463747 → M1 0.4054954640, 4.193% relative improvement; paired MSE gain 0.0147109224 [0.0071443764,0.0232458254] conditional whole-sire pointwise interval. After historical trainer information, M0 0.4213921860 → M1 0.4057601290; gain 0.0129300922 [0.0056406951,0.0207950582].

| Split | Seed | Baseline | Year | N | M0 RMSE | M1 RMSE | M0−M1 MSE (95% interval) | P−M1 matched MSE (95% interval) |
|---|---|---|---|---:|---:|---:|---|---|
| horse_disjoint | 20261124 | own_history | 2020 | 7381 | 0.423365 | 0.400840 | 0.018565 [0.011536, 0.025709] | 0.037904 [0.025854, 0.049777] |
| horse_disjoint | 20261124 | own_history | 2021 | 7276 | 0.423246 | 0.405495 | 0.014711 [0.007144, 0.023246] | 0.044588 [0.032808, 0.058820] |
| horse_disjoint | 20261124 | own_and_last_trainer_history | 2020 | 7381 | 0.421569 | 0.400984 | 0.016932 [0.010537, 0.023592] | 0.036778 [0.024949, 0.048204] |
| horse_disjoint | 20261124 | own_and_last_trainer_history | 2021 | 7276 | 0.421392 | 0.405760 | 0.012930 [0.005641, 0.020795] | 0.042227 [0.030412, 0.055881] |
| horse_disjoint | 20261125 | own_history | 2020 | 7381 | 0.423311 | 0.401819 | 0.017733 [0.010968, 0.024246] | 0.037454 [0.024625, 0.051669] |
| horse_disjoint | 20261125 | own_history | 2021 | 7276 | 0.423160 | 0.405319 | 0.014781 [0.007112, 0.022139] | 0.032194 [0.021126, 0.045969] |
| horse_disjoint | 20261125 | own_and_last_trainer_history | 2020 | 7381 | 0.421572 | 0.402017 | 0.016105 [0.009672, 0.022386] | 0.036360 [0.023816, 0.050138] |
| horse_disjoint | 20261125 | own_and_last_trainer_history | 2021 | 7276 | 0.421324 | 0.405583 | 0.013017 [0.006041, 0.020279] | 0.030511 [0.020026, 0.043764] |
| horse_disjoint | 20261126 | own_history | 2020 | 7381 | 0.423187 | 0.401113 | 0.018196 [0.011169, 0.025603] | 0.041530 [0.025375, 0.061087] |
| horse_disjoint | 20261126 | own_history | 2021 | 7276 | 0.423145 | 0.404814 | 0.015177 [0.007534, 0.022880] | 0.036548 [0.024391, 0.049651] |
| horse_disjoint | 20261126 | own_and_last_trainer_history | 2020 | 7381 | 0.421437 | 0.401327 | 0.016546 [0.009874, 0.023599] | 0.040209 [0.024466, 0.059269] |
| horse_disjoint | 20261126 | own_and_last_trainer_history | 2021 | 7276 | 0.421311 | 0.405125 | 0.013377 [0.006400, 0.020758] | 0.035070 [0.023170, 0.047838] |
| horse_and_trainer_disjoint | 20261124 | own_history | 2020 | 3801 | 0.425331 | 0.406141 | 0.015956 [0.009038, 0.023332] | 0.031835 [0.016504, 0.046407] |
| horse_and_trainer_disjoint | 20261124 | own_history | 2021 | 3649 | 0.422919 | 0.406148 | 0.013904 [0.007028, 0.021769] | 0.021932 [0.014263, 0.030650] |
| horse_and_trainer_disjoint | 20261124 | own_and_last_trainer_history | 2020 | 3801 | 0.424310 | 0.406687 | 0.014645 [0.008092, 0.021833] | 0.030632 [0.015975, 0.045013] |
| horse_and_trainer_disjoint | 20261124 | own_and_last_trainer_history | 2021 | 3649 | 0.421231 | 0.406164 | 0.012466 [0.005749, 0.020173] | 0.021174 [0.013502, 0.029534] |
| horse_and_trainer_disjoint | 20261125 | own_history | 2020 | 3747 | 0.427279 | 0.407341 | 0.016641 [0.010271, 0.023888] | 0.040744 [0.026804, 0.055472] |
| horse_and_trainer_disjoint | 20261125 | own_history | 2021 | 3730 | 0.428746 | 0.412323 | 0.013813 [0.005387, 0.022169] | 0.036401 [0.022841, 0.049615] |
| horse_and_trainer_disjoint | 20261125 | own_and_last_trainer_history | 2020 | 3747 | 0.425822 | 0.407471 | 0.015292 [0.009345, 0.022072] | 0.039729 [0.025927, 0.054374] |
| horse_and_trainer_disjoint | 20261125 | own_and_last_trainer_history | 2021 | 3730 | 0.427390 | 0.413072 | 0.012033 [0.004097, 0.019933] | 0.034678 [0.022044, 0.047749] |
| horse_and_trainer_disjoint | 20261126 | own_history | 2020 | 3759 | 0.424160 | 0.406742 | 0.014473 [0.008587, 0.020187] | 0.024573 [0.015300, 0.034923] |
| horse_and_trainer_disjoint | 20261126 | own_history | 2021 | 3668 | 0.423717 | 0.406897 | 0.013971 [0.005705, 0.022893] | 0.028244 [0.016869, 0.040278] |
| horse_and_trainer_disjoint | 20261126 | own_and_last_trainer_history | 2020 | 3759 | 0.421843 | 0.406020 | 0.013100 [0.007402, 0.018856] | 0.023134 [0.014248, 0.033500] |
| horse_and_trainer_disjoint | 20261126 | own_and_last_trainer_history | 2021 | 3668 | 0.422754 | 0.407377 | 0.012765 [0.005030, 0.021792] | 0.027610 [0.016560, 0.039525] |

All 24 contrasts positive, all conditional pointwise intervals positive for both M0 and matched other-sire comparisons. The sensitivities reuse the same records, not independent replications; no simultaneous confidence or all-dependence claim. The trainer-disjoint filter changes the denominator. The own-history predictor is a fixed shrinkage baseline, not an optimized nonlinear model; the last-trainer prior is only a historical label. No inference about biological niche preference, genetic causality, realized fitness or human intent. Occupancy is an observed fraction conditional on eligible starts, not a forecast of entry or a calibrated probability.

## Relation to PR80

PR80 paired rank-residual response: 4/12 positive M0−M1 gains, all intervals cross zero. PR81 occupancy: 24/24 positive. The endpoints, scales and support differ; this is an evidence-pattern contrast, not a formal between-endpoint effect or mediation analysis. Stable family-associated environment assignment and uncertain transfer of performance across environments are consistent with a sorting–response decoupling hypothesis. Shared breeding/training, age, sex, class and unobserved opportunity can generate the pattern. Do not infer that occupancy predicts performance or explains PR78 causally.

## Next test

Use a learned, history-rich baseline and same chronological horse-disjoint support, then isolate the first eligible context observation per horse-year from later occupancy. Explicitly distinguish no prior eligible context from no prior race anywhere in the archive; do not equate either with official debut. Test family signal conditional on own-history availability and prior trainer. Preserve denominators and compare actual same-parent information with matched other-family controls. The results below do not establish a portable biological reaction norm.

[Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45332342678/artifacts/14892328333) · sha256:a9ceeb8dc8f6daed8da4f8cf1c3c8e55b06e1ebd0f50fde423214344fea19393.
