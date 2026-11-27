# Recorded-parent specificity after donor count, depth and recency matching

27 November 2026 JST. [Frozen protocol](JAPAN_PARENT_SPECIFICITY_MATCHED_DONORS_PROTOCOL_20261127.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45939089087) · [aggregate receipt](../evidence/japan-parent-specificity-matched-donors-20261127.json).

Original PR111 fits, denominator, support and Brier/gain parity passed. All 217,613 calibration first meetings and all test strata had 100% matched coverage, in both recorded-parent channels for both horses. Controls share neither recorded direct parent with focal, matching exact donor counts in the prespecified coarse prior-start × recency cells; three fixed independently drawn controls, separately fitted with the same 2019 records and model structure. Positive contrast means lower Brier loss for actual recorded-parent ratings.

| Year | Group | Pairs | Count N | Actual U | Mean alternate loss | Actual vs count gain | Alternate minus actual gain (conditional 97.5% interval) |
|---|---|---:|---:|---:|---:|---:|---|
| 2020 | first_both_one_start_one_win | 291 | 0.248196775 | 0.241002780 | 0.246387893 | 0.007193994 | 0.005385113 [-0.004196435, 0.014677613] |
| 2020 | first_both_one_win | 41617 | 0.219900922 | 0.218658241 | 0.219813975 | 0.001242681 | 0.001155734 [0.000309127, 0.002022824] |
| 2020 | first_meeting | 224065 | 0.210783567 | 0.209476595 | 0.210536302 | 0.001306972 | 0.001059707 [0.000753266, 0.001375411] |
| 2020 | first_both_1_to_3_starts | 44417 | 0.210468558 | 0.207821340 | 0.209946906 | 0.002647218 | 0.002125566 [0.001290708, 0.003010303] |
| 2020 | first_both_4_plus_starts | 129466 | 0.211643337 | 0.210935010 | 0.211494001 | 0.000708327 | 0.000558990 [0.000106877, 0.001017010] |
| 2021 | first_both_one_start_one_win | 280 | 0.250998985 | 0.242673448 | 0.251990297 | 0.008325537 | 0.009316849 [0.000572381, 0.018222926] |
| 2021 | first_both_one_win | 44446 | 0.218746767 | 0.218310088 | 0.218758350 | 0.000436679 | 0.000448262 [-0.000506207, 0.001390783] |
| 2021 | first_meeting | 223211 | 0.209978616 | 0.208758811 | 0.209762154 | 0.001219805 | 0.001003343 [0.000713414, 0.001253005] |
| 2021 | first_both_1_to_3_starts | 43339 | 0.208022345 | 0.205719851 | 0.207603304 | 0.002302494 | 0.001883453 [0.001062478, 0.002640986] |
| 2021 | first_both_4_plus_starts | 129728 | 0.210785708 | 0.210111098 | 0.210708515 | 0.000674610 | 0.000597416 [0.000196043, 0.001037861] |

| Year | Low-minus-high specificity | Conditional date 97.5% interval |
|---|---:|---|
| 2020 | 0.001566576 | [0.000645920, 0.002569122] |
| 2021 | 0.001286036 | [0.000298891, 0.002142553] |

Both 2021 primary contrasts supported under the conditional date analysis; both 2020 counterparts likewise positive. All 30 individual-seed alternate-minus-actual point contrasts positive. Strict one-start winner specificity positive with conditional interval excluding zero in 2021 only, but actual vs count remains uncertain in both years; broader one-win 2021 also uncertain. Do not promote strict-winner subgroup to an established outcome. Matched counts and binned depth/recency do not match natural grouping, training environment, historical competition or deeper genetic relatedness. Randomly assembled donors are not necessarily independent or unrelated; they may lack coherent latent group structure. This is evidence of incremental recorded-parent-specific predictive information beyond these matched alternate donors, not genetic causation, a within-horse moderation effect or a prospective forecast. Same previously inspected source; date intervals conditional on three fixed draws and fitted models omit graph/horse/parent dependence. Next discriminate between cross-sectional group composition and same-focal changing value using the same fitted U model, swapping only one focal's signed parent contribution for its matched alternate contribution and holding rival/baseline fixed. Match within focal across history levels and preserve null/support outcomes. No raw exports, no main merge.

Provenance: head 4005cc75ebebef09c18c73010a26dd516f00c6e7; artifact 15171833579; sha256:f5e362edf2c4fd08f478412c3c05e7519147b6b3552d010f714c59ac26cbd3b8; metadata and upload-log parity, ZIP bytes not independently extracted.
