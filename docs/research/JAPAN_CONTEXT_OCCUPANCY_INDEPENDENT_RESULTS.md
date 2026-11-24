# Frozen context occupancy transfer on source B: completed retrospective results (2026-11-24)

**Conditional family identity signal persists versus matched other-sire placebo, but the primary useful-information transfer is not established.** [Frozen protocol](JAPAN_CONTEXT_OCCUPANCY_INDEPENDENT_PROTOCOL.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45376549215) · [stdout evidence](../evidence/japan-context-occupancy-independent-20261124.json). Commit `991d20a9450e64cb1d2788d1d9e4393e7de86eb1`; metadata verified, ZIP not independently extracted. Synthetic checks, source and parity gates and upload passed.

Venue-code audit on pre-2022 records: 20,400 anchored horses, 85,856 distinct corroborated races; 10 JRA codes (25,878 races), 14 NAR codes (59,978 races), zero conflicting corroborated races. All target rows have a mapped circuit. This is source concordance, not independent official verification. Strict cohort remains 244,147 classified focal rows/12,887 horses; 11,337 non-strict focal rows excluded. The JRA 1600–1999m target is 9,379/4,824/1,863 strict starts in 2022/23/24 (3,011/1,588/743 horses, respectively; repeated horses across years possible).

Primary 2022 strict own-history baseline: M0 RMSE 0.372388028 → M1 0.369745242, paired MSE gain +0.0019612994, sire pointwise interval [-0.0047911303,+0.0092841012]. On matched 2,836 horses, P−M1 +0.0242911128 [0.0138282468,0.0354734597]. The latter does not establish a gain over M0.

| Seed | Scope | Year | Baseline | N | M0 | M1 | M0−M1 MSE | Pointwise sire interval | P−M1 MSE | Pointwise sire interval |
|---|---|---|---|---:|---:|---:|---:|---|---:|---|
| 20261124 | all_source_B_valid | 2022 | own_history | 3070 | 0.371193 | 0.367953 | 0.002395 | [-0.003659, 0.009948] | 0.024314 | [0.013955, 0.035328] |
| 20261124 | all_source_B_valid | 2022 | own_last_trainer | 3070 | 0.368158 | 0.367961 | 0.000145 | [-0.006183, 0.007998] | 0.022943 | [0.012386, 0.034346] |
| 20261124 | all_source_B_valid | 2023 | own_history | 1627 | 0.377096 | 0.375826 | 0.000956 | [-0.007210, 0.009381] | 0.024829 | [0.010535, 0.038721] |
| 20261124 | all_source_B_valid | 2023 | own_last_trainer | 1627 | 0.374705 | 0.377568 | -0.002154 | [-0.009937, 0.006705] | 0.022736 | [0.008009, 0.036856] |
| 20261124 | all_source_B_valid | 2024 | own_history | 762 | 0.401662 | 0.401181 | 0.000386 | [-0.012379, 0.014997] | 0.020631 | [0.004468, 0.035809] |
| 20261124 | all_source_B_valid | 2024 | own_last_trainer | 762 | 0.398038 | 0.402029 | -0.003193 | [-0.015092, 0.010408] | 0.018156 | [0.001950, 0.034011] |
| 20261124 | strict_classified | 2022 | own_history | 3011 | 0.372388 | 0.369745 | 0.001961 | [-0.004791, 0.009284] | 0.024291 | [0.013828, 0.035473] |
| 20261124 | strict_classified | 2022 | own_last_trainer | 3011 | 0.369389 | 0.369772 | -0.000283 | [-0.007272, 0.006870] | 0.022968 | [0.012383, 0.034898] |
| 20261124 | strict_classified | 2023 | own_history | 1588 | 0.376618 | 0.374029 | 0.001944 | [-0.006040, 0.010414] | 0.026577 | [0.012408, 0.040347] |
| 20261124 | strict_classified | 2023 | own_last_trainer | 1588 | 0.374359 | 0.376001 | -0.001231 | [-0.008961, 0.007354] | 0.024393 | [0.009543, 0.038913] |
| 20261124 | strict_classified | 2024 | own_history | 743 | 0.405342 | 0.406595 | -0.001017 | [-0.013764, 0.012904] | 0.019301 | [0.002639, 0.035526] |
| 20261124 | strict_classified | 2024 | own_last_trainer | 743 | 0.401649 | 0.407411 | -0.004662 | [-0.016517, 0.008393] | 0.016711 | [0.000209, 0.033351] |
| 20261125 | all_source_B_valid | 2022 | own_history | 3070 | 0.371228 | 0.369357 | 0.001386 | [-0.005092, 0.008846] | 0.025522 | [0.014554, 0.037137] |
| 20261125 | all_source_B_valid | 2022 | own_last_trainer | 3070 | 0.368185 | 0.369280 | -0.000808 | [-0.007490, 0.006731] | 0.024329 | [0.013497, 0.035742] |
| 20261125 | all_source_B_valid | 2023 | own_history | 1627 | 0.376996 | 0.376461 | 0.000403 | [-0.006413, 0.008709] | 0.027438 | [0.014216, 0.043128] |
| 20261125 | all_source_B_valid | 2023 | own_last_trainer | 1627 | 0.374589 | 0.378142 | -0.002674 | [-0.009686, 0.005731] | 0.025579 | [0.012700, 0.040928] |
| 20261125 | all_source_B_valid | 2024 | own_history | 762 | 0.401450 | 0.399472 | 0.001584 | [-0.012116, 0.016291] | 0.028244 | [0.008953, 0.049550] |
| 20261125 | all_source_B_valid | 2024 | own_last_trainer | 762 | 0.397774 | 0.400096 | -0.001853 | [-0.014873, 0.011892] | 0.026273 | [0.006941, 0.047032] |
| 20261125 | strict_classified | 2022 | own_history | 3011 | 0.372388 | 0.371099 | 0.000958 | [-0.005620, 0.008135] | 0.026121 | [0.015115, 0.037926] |
| 20261125 | strict_classified | 2022 | own_last_trainer | 3011 | 0.369384 | 0.371031 | -0.001219 | [-0.007668, 0.006040] | 0.024902 | [0.013938, 0.036389] |
| 20261125 | strict_classified | 2023 | own_history | 1588 | 0.376474 | 0.374365 | 0.001583 | [-0.005158, 0.009993] | 0.029264 | [0.016135, 0.045529] |
| 20261125 | strict_classified | 2023 | own_last_trainer | 1588 | 0.374207 | 0.376306 | -0.001575 | [-0.008395, 0.006827] | 0.027318 | [0.014441, 0.043485] |
| 20261125 | strict_classified | 2024 | own_history | 743 | 0.405139 | 0.405229 | -0.000073 | [-0.013293, 0.011918] | 0.027669 | [0.007762, 0.049829] |
| 20261125 | strict_classified | 2024 | own_last_trainer | 743 | 0.401395 | 0.405856 | -0.003601 | [-0.016301, 0.008283] | 0.025581 | [0.006015, 0.047020] |
| 20261126 | all_source_B_valid | 2022 | own_history | 3070 | 0.371236 | 0.367759 | 0.002569 | [-0.004145, 0.010052] | 0.022960 | [0.013944, 0.034328] |
| 20261126 | all_source_B_valid | 2022 | own_last_trainer | 3070 | 0.368193 | 0.367746 | 0.000329 | [-0.006346, 0.008030] | 0.021903 | [0.012945, 0.033334] |
| 20261126 | all_source_B_valid | 2023 | own_history | 1627 | 0.377054 | 0.375160 | 0.001424 | [-0.005929, 0.010253] | 0.026337 | [0.014236, 0.040665] |
| 20261126 | all_source_B_valid | 2023 | own_last_trainer | 1627 | 0.374651 | 0.376861 | -0.001661 | [-0.008797, 0.007024] | 0.024949 | [0.012803, 0.039777] |
| 20261126 | all_source_B_valid | 2024 | own_history | 762 | 0.401513 | 0.399763 | 0.001402 | [-0.010686, 0.015014] | 0.021256 | [0.007135, 0.036629] |
| 20261126 | all_source_B_valid | 2024 | own_last_trainer | 762 | 0.397891 | 0.400418 | -0.002017 | [-0.013484, 0.011291] | 0.019693 | [0.005006, 0.035647] |
| 20261126 | strict_classified | 2022 | own_history | 3011 | 0.372397 | 0.369465 | 0.002175 | [-0.004630, 0.009658] | 0.023278 | [0.014095, 0.034550] |
| 20261126 | strict_classified | 2022 | own_last_trainer | 3011 | 0.369393 | 0.369480 | -0.000064 | [-0.006646, 0.007514] | 0.022197 | [0.012814, 0.033833] |
| 20261126 | strict_classified | 2023 | own_history | 1588 | 0.376533 | 0.373251 | 0.002461 | [-0.004647, 0.010982] | 0.027934 | [0.016302, 0.042434] |
| 20261126 | strict_classified | 2023 | own_last_trainer | 1588 | 0.374270 | 0.375184 | -0.000685 | [-0.007821, 0.007953] | 0.026528 | [0.014851, 0.041298] |
| 20261126 | strict_classified | 2024 | own_history | 743 | 0.405199 | 0.405094 | 0.000085 | [-0.012802, 0.014473] | 0.020225 | [0.005845, 0.036159] |
| 20261126 | strict_classified | 2024 | own_last_trainer | 743 | 0.401500 | 0.405721 | -0.003408 | [-0.015762, 0.009761] | 0.018520 | [0.003871, 0.035048] |

18/36 point estimates positive for useful-information comparison; all intervals include zero. 36/36 matched other-sire comparisons positive, 36/36 pointwise intervals positive. On strict last-trainer baseline all 9 gains negative; strict own baseline 7/9 positive. Same records reused across sensitivities. Do not call placebo contrast a useful predictive gain. Primary failed to establish external transfer beyond own history. In particular 2024 strict first-seed gain negative.

## Scope and next test

The strong PR81/82 source-A findings remain conditional on observed 2019–21 horses; source-B continuing anchored horses omit all new entrants, and the proportion without prior eligible A history is much smaller (334/3,011 in strict 2022 vs 3,737/7,276 in 2021 A). Information freshness, selection and cohort composition are confounded. A fixed end-2021 model does not identify a causal temporal decay. The new endpoint uses previously examined source B, not pristine prospective validation. No causal genetics, physiological preference, market or wagering claims. Next: hold the strict denominator fixed; compare supported and unsupported prior-history strata, and evaluate time-ordered updates of own versus same-sire residual information from earlier B years only. Record all negative results.

[Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45376549215/artifacts/14911996076) · sha256:c7615b3ea9adfbdbe44a3ec72d5140539234b94bdc40725a325104d4277a4167.
