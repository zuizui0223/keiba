# Unattenuated parent ability: depth contrast persists without imposed own-history attenuation

27 November 2026 JST. [Frozen protocol](JAPAN_FAMILY_DEPTH_UNCONSTRAINED_PROTOCOL_20261127.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45869192227) · [aggregate receipt](../evidence/japan-family-depth-unconstrained-20261127.json).

Exact PR107/110 replay parity passed. U removes 5/(n+5) from parent rating signal, retaining distinct-peer shrinkage k/(k+8). O/N/F unchanged; U separately fitted on the same 2019 first meetings. Positive gain means less Brier loss.

| Year | Group | Pairs | Count N | Attenuated F | Unattenuated U | U vs N gain (conditional 97.5% interval) | U vs F gain |
|---|---|---:|---:|---:|---:|---|---:|
| 2020 | first_both_one_start_one_win | 291 | 0.248196775 | 0.235583442 | 0.241002780 | 0.007193994 [-0.002098229, 0.015429407] | -0.005419339 |
| 2020 | first_both_one_win | 41617 | 0.219900922 | 0.217852196 | 0.218658241 | 0.001242681 [0.000277261, 0.002253054] | -0.000806044 |
| 2020 | first_meeting | 224065 | 0.210783567 | 0.208915497 | 0.209476595 | 0.001306972 [0.000925669, 0.001697426] | -0.000561098 |
| 2020 | first_both_1_to_3_starts | 44417 | 0.210468558 | 0.207518228 | 0.207821340 | 0.002647218 [0.001689298, 0.003651261] | -0.000303112 |
| 2020 | first_both_4_plus_starts | 129466 | 0.211643337 | 0.210612907 | 0.210935010 | 0.000708327 [0.000147001, 0.001228240] | -0.000322103 |
| 2021 | first_both_one_start_one_win | 280 | 0.250998985 | 0.238647741 | 0.242673448 | 0.008325537 [-0.000659690, 0.018247691] | -0.004025707 |
| 2021 | first_both_one_win | 44446 | 0.218746767 | 0.217829584 | 0.218310088 | 0.000436679 [-0.000574417, 0.001592904] | -0.000480504 |
| 2021 | first_meeting | 223211 | 0.209978616 | 0.208436089 | 0.208758811 | 0.001219805 [0.000918384, 0.001524983] | -0.000322722 |
| 2021 | first_both_1_to_3_starts | 43339 | 0.208022345 | 0.205562210 | 0.205719851 | 0.002302494 [0.001391721, 0.003186493] | -0.000157641 |
| 2021 | first_both_4_plus_starts | 129728 | 0.210785708 | 0.209965521 | 0.210111098 | 0.000674610 [0.000181407, 0.001155701] | -0.000145577 |

## Common-date depth contrast

| Year | Low/high pairs | Low U gain | High U gain | Low-minus-high U gain (conditional 97.5%) | Low-minus-high F gain | Difference-of-differences (conditional 97.5%) |
|---|---|---:|---:|---|---:|---|
| 2020 | 44417/129466 | 0.002647218 | 0.000708327 | 0.001938891 [0.000855498, 0.003083594] | 0.001919901 | 0.000018990 [-0.000729406, 0.000738888] |
| 2021 | 43339/129728 | 0.002302494 | 0.000674610 | 0.001627885 [0.000547567, 0.002749590] | 0.001639948 | -0.000012064 [-0.000638257, 0.000604509] |

Both frozen 2021 primary contrasts are positive with conditional intervals excluding zero. Their 2020 counterparts are also positive. The 2021 U gain is 0.001219805 for general first meetings and the low-minus-high U gain is 0.001627885. Removing imposed depth attenuation does not remove the observed between-group difference. This is not proof of equivalence of F and U depth contrasts, biological information substitution within an individual, or genetics. The full F model still has better all-first Brier loss than U in both years, with negative U-vs-F intervals. Strict both-one-start winners remain uncertain in 2020 and 2021, as does broader one-win in 2021; preserve these boundaries. All results use the same previously inspected archive, with common-date bootstrap conditional on fitted predictions and omitting crossed horse/race/parent/fit dependence. Low/high groups differ in many ways, including count and baseline error; no causal moderation. Next test context novelty among experienced horses, using stronger context-history baseline and common depth/context strata, with unchanged U comparator and no imposed novelty multiplier. No raw export or main merge.

Provenance: head cc9c988dc5c1059e9fb6d773304128ac48a7d146; artifact 15141357565; sha256:567d6c04d02b477aff03f304f44a1bb6bf39847e55058cc0a692e3ae318c6656; metadata and upload-log parity, ZIP bytes not independently extracted.
