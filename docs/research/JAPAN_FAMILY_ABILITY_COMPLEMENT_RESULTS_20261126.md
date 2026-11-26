# Parent information complements daily ability: general gain, one-start primary HOLD

26 November 2026. [Frozen protocol](JAPAN_FAMILY_ABILITY_COMPLEMENT_PROTOCOL_20261126.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45824570098) · [aggregate receipt](../evidence/japan-family-ability-complement-20261126.json).

Original PR107 replay parity and 217,613 calibration pairs passed. All 62,199 source JRA horses eventually had both recorded parent labels, no observed label conflicts; 1,132 distinct sire and 19,734 dam labels. This is archive-specific identity consistency, not independently certified pedigree. Parent labels are learned after prior recorded days only.

| Year | Group | Pairs | Own O | Count N | Family F | F vs N gain (conditional 97.5% interval) | F directional accuracy |
|---|---|---:|---:|---:|---:|---|---:|
| 2020 | first_both_one_start_one_win | 291 | 0.250322086 | 0.248196775 | 0.235583442 | 0.012613333 [-0.005131510, 0.027860662] | 0.623206751 |
| 2020 | first_both_one_win | 41617 | 0.219937057 | 0.219900922 | 0.217852196 | 0.002048726 [0.001098033, 0.003078857] | 0.646133112 |
| 2020 | first_meeting | 224065 | 0.210783809 | 0.210783567 | 0.208915497 | 0.001868070 [0.001394303, 0.002307644] | 0.670715410 |
| 2020 | first_both_1_to_3_starts | 44417 | 0.210334671 | 0.210468558 | 0.207518228 | 0.002950330 [0.001315916, 0.004687801] | 0.672471080 |
| 2020 | first_both_4_plus_starts | 129466 | 0.211456863 | 0.211643337 | 0.210612907 | 0.001030430 [0.000449321, 0.001587498] | 0.665739430 |
| 2021 | first_both_one_start_one_win | 280 | 0.247410879 | 0.250998985 | 0.238647741 | 0.012351244 [-0.004162098, 0.029378412] | 0.551911977 |
| 2021 | first_both_one_win | 44446 | 0.218874476 | 0.218746767 | 0.217829584 | 0.000917183 [-0.000065411, 0.001961872] | 0.650591805 |
| 2021 | first_meeting | 223211 | 0.210004261 | 0.209978616 | 0.208436089 | 0.001542527 [0.001177129, 0.001925608] | 0.672017690 |
| 2021 | first_both_1_to_3_starts | 43339 | 0.207939932 | 0.208022345 | 0.205562210 | 0.002460135 [0.000986611, 0.003895520] | 0.679470453 |
| 2021 | first_both_4_plus_starts | 129728 | 0.210623170 | 0.210785708 | 0.209965521 | 0.000820187 [0.000299770, 0.001319416] | 0.668701140 |

Both 2021 frozen primary contrasts F vs N (strict one-start one-win and broader one-win) have intervals spanning zero. 2020 broader one-win is positive, strict remains uncertain. **Do not promote secondary results to primary confirmation.** General first-meeting increments are positive with conditional intervals excluding zero in both years; same for both 1–3 starts and both >=4 starts strata. All ten count-only gain intervals cross zero. The low-depth point gain is about three times the high-depth gain in 2021, but the model imposes 5/(n+5) attenuation. Thus this is not a test of a learned moderation mechanism, and cross-depth samples differ. The strict subgroup shows larger favorable point gains in both years but broad intervals. No inference from directional accuracy alone. F vs standalone daily surface improves general and broader one-win; this mixes model refitting and family features, not solely kin gain. Coefficients for sire and dam ability positive under this fitted model, not causal or a parent-channel comparison. Same source, conditional date intervals omit graph/horse/fit dependence. Earlier other-horse scores share competition/management/environment; focal self-exclusion does not make them independent. Next test remove imposed own-depth shrinkage, use a paired date-block low-minus-high contrast, and separately test parent identity against count-matched alternatives before claiming a mechanism. No raw export, no main merge.

Provenance: source head 6a1263f4a9eb096f7af41574ed91b0238a34b4ed; artifact 15120335662; sha256:ad1c71a001f285ef8c76ea8a953a4c451b6c923a62951aff3feda5accc4e65dd; metadata and upload-log parity, ZIP bytes not independently extracted.
