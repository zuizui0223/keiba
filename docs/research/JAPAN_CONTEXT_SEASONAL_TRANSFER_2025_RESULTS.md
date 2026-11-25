# Season-matched 2025 allocation transfer: completed results

2026-11-25. [Frozen protocol](JAPAN_CONTEXT_SEASONAL_TRANSFER_2025_PROTOCOL.md) · [successful workflow](https://github.com/zuizui0223/keiba/actions/runs/45527759025) · [compact stdout receipt](../evidence/japan-context-seasonal-transfer-2025-20261125.json). Source commit `08f527ee365b237bae3de63fd178319dfaed8b26`. Synthetic, source, venue, strict and PR86 annual parity passed. Artifact metadata separately verified; full ZIP not independently extracted. The compact printed results include every all-target contrast and calibration weight; count-bin outputs remain in the aggregate artifact.

## Coverage

2025 Jan 1–Mar 27, JRA 1600–1999m: 310 candidate races; 280 strict complete, 9 tied/duplicated rank and 21 incomplete declared. 4,370 valid candidate starts/3,058 native horses; strict exact ID/rank 3,939 starts/2,839 native horses, no strict race entries missing matching valid history. Pre-2022 anchors with known recorded sire: 266 starts/194 horses (81 sires), 6.833% of strict horses and 6.753% of strict starts. Unanchored: 2,645 horses/3,673 starts. All 664 strict horses whose first valid B record occurs in 2025 are unanchored. Not official debut, not whole JRA coverage. Native horse columns id/hid/born/name/info/races, no explicit direct-parent ID columns; info payload not verified as pedigree and no new native parent mapping claimed.

## Main result: history-dependent correction better than full, useful increment uncertain in 2025

Same Jan1–Mar27 response in all years; full prior-calendar-year own histories and prior same-season donor outcomes. Source-A seasonal calibration support passed all seeds. Evaluation cohorts differ across years.

| Seed | Year | Horses | N RMSE | F RMSE | G RMSE | N−G MSE gain | Pointwise sire interval | F−G MSE gain |
|---|---|---:|---:|---:|---:|---:|---|---:|
| 20261124 | 2022 | 1861 | 0.370724545 | 0.359146404 | 0.356299960 | 0.010487027 | [0.005587819, 0.015061270] | 0.002036479 |
| 20261124 | 2023 | 1003 | 0.328364597 | 0.319844493 | 0.314003516 | 0.009225101 | [0.005563850, 0.013745013] | 0.003702292 |
| 20261124 | 2024 | 472 | 0.304765087 | 0.309790707 | 0.300603518 | 0.002519283 | [-0.002495275, 0.006529142] | 0.005607807 |
| 20261124 | 2025 | 194 | 0.320515260 | 0.335617402 | 0.319848566 | 0.000426927 | [-0.004383731, 0.005060798] | 0.010335935 |
| 20261125 | 2022 | 1861 | 0.370484939 | 0.360956089 | 0.357083363 | 0.009750562 | [0.004796284, 0.014617133] | 0.002780771 |
| 20261125 | 2023 | 1003 | 0.328175593 | 0.322917894 | 0.313906092 | 0.009162185 | [0.004831496, 0.013478364] | 0.005738932 |
| 20261125 | 2024 | 472 | 0.304619748 | 0.310953744 | 0.300900926 | 0.002251823 | [-0.001816944, 0.005879168] | 0.006150863 |
| 20261125 | 2025 | 194 | 0.320481653 | 0.326593604 | 0.314653740 | 0.003701514 | [-0.000324340, 0.007577187] | 0.007656406 |
| 20261126 | 2022 | 1861 | 0.370527809 | 0.359398968 | 0.356783849 | 0.009996142 | [0.004867643, 0.015688105] | 0.001872903 |
| 20261126 | 2023 | 1003 | 0.328260015 | 0.322267447 | 0.315595813 | 0.008153920 | [0.004160416, 0.012385356] | 0.004255590 |
| 20261126 | 2024 | 472 | 0.304585776 | 0.310753480 | 0.300957458 | 0.002197104 | [-0.002038872, 0.006155182] | 0.005992334 |
| 20261126 | 2025 | 194 | 0.320558137 | 0.333992466 | 0.318364531 | 0.001401544 | [-0.002982122, 0.005666407] | 0.010194993 |

Primary 2025 seed 20261124: N 0.320515260, F 0.335617402, P 0.334209194, H 0.319474697, G 0.319848566. N−G +0.000426927 [−0.004383731,+0.005060798]; F−G +0.010335935 [0.002580762,0.017462787]; P−G +0.009392680 [0.002044104,0.016389887]. H slightly better than G point estimate, no robust difference. All three 2025 season-calibrated N−G estimates positive, all three intervals include zero; all three F−G intervals positive. Full correction worsens all three point estimates, but none of its three 2025 N−F intervals wholly negative. Annual weights on season profile are sensitivity only; one seed's N−G interval narrowly positive, not rescue of frozen primary. All 12 season-calibrated refreshed N−G point estimates positive; 6/12 pointwise intervals positive. Earlier season supports useful information more clearly than late seasons. No independent replication across seed splits or years, no monotonicity test across changing cohorts. All effects conditional on selected old-identity horses. No new-entrant, causal genetic, learning, choice, fitness, or wagering claim.

[Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45527759025/artifacts/14983651717) · sha256:adcf17b1abcf915259bc93b67c509edf09d31b6836841b3c8769c5e1b7c70ce4.
