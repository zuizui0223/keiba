# Historical surface-supply balance and predictive information substitution: completed results

2026-11-24. **The proposed negative within-band supply-balance association is not supported.** [Frozen protocol](JAPAN_CONTEXT_OPPORTUNITY_DIVERSITY_PROTOCOL.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45386135942) · [stdout receipt](../evidence/japan-context-opportunity-diversity-20261124.json). Original commit `01d79696e5c794a7595f118c2e16d807872601f4`. Source, venue, strict classified and PR89 parity checks passed. Aggregate artifact metadata separately checked; complete ZIP not independently extracted.

The three bands contain 5,617/7,014/2,242 distinct observed source-A races in 2017–21, including 2,443/2,941/1,956 turf and 3,174/4,073/286 dirt. The common-horse panel contains 1,397 rows, 1,199 horses, 158 sires. Eight rows fail historical portfolio coverage, leaving 1,389 rows/1,191 horses/158 sires.

| Seed | Model | Rows | Horses | Coefficient per 0.1 balance | Pointwise sire interval / HOLD |
|---|---|---:|---:|---:|---|
| 20261124 | adjusted | 1389 | 1191 | 0.000441084 | [-0.001228865, 0.002062472] |
| 20261124 | band_only | 1389 | 1191 | -0.000734169 | [-0.002166598, 0.000667072] |
| 20261124 | energy | 1389 | 1191 | 0.000847620 | [-0.000710816, 0.002522503] |
| 20261124 | within_horse | 396 | 198 | — | HOLD_BAND_SUPPORT |
| 20261124 | equal_cell_weights | 1389 | 1191 | 0.000726306 | [-0.000990932, 0.002342125] |
| 20261125 | adjusted | 1389 | 1191 | 0.000494691 | [-0.001512078, 0.002321047] |
| 20261125 | band_only | 1389 | 1191 | -0.000795965 | [-0.002380854, 0.000776733] |
| 20261125 | energy | 1389 | 1191 | 0.000954091 | [-0.000683182, 0.002603667] |
| 20261125 | within_horse | 396 | 198 | — | HOLD_BAND_SUPPORT |
| 20261125 | equal_cell_weights | 1389 | 1191 | 0.000626035 | [-0.001351341, 0.002478803] |
| 20261126 | adjusted | 1389 | 1191 | 0.000396490 | [-0.001392947, 0.002159519] |
| 20261126 | band_only | 1389 | 1191 | -0.000632537 | [-0.002218711, 0.000993496] |
| 20261126 | energy | 1389 | 1191 | 0.000802626 | [-0.000807582, 0.002351959] |
| 20261126 | within_horse | 396 | 198 | — | HOLD_BAND_SUPPORT |
| 20261126 | equal_cell_weights | 1389 | 1191 | 0.000703017 | [-0.001153224, 0.002420717] |

Primary adjusted coefficient +0.000441084 [−0.001228865,+0.002062472], opposite proposed direction but uncertain. All 12 estimated model/seed intervals include zero; band-only coefficients negative, adjusted/energy/equal-cell coefficients positive. Within-horse fit HOLD in all three seeds: 396 rows/198 horses/69 sires, short band only 86 rows versus frozen minimum 100. Do not relax support or equate HOLD with zero effect.

## Secondary descriptive arithmetic

For common-horse rows, mean update contrast = -2 RMS(d) RMS(du) cosine(d,du). Main seed short/middle/long d RMS = 0.139916/0.172378/0.087243; du RMS = 0.182964/0.171773/0.121474; cosine = 0.284024/0.271967/0.075946. These factors jointly contribute to the distance-band differences. A symmetric six-order arithmetic decomposition of the short→long and middle→long difference is preserved below. This is newly derived descriptive arithmetic, no statistical interval or causal attribution, not a fitted model.
| Seed | Contrast | Total change | Fixed correction RMS | Own update RMS | Alignment |
|---|---|---:|---:|---:|---:|
| 20261124 | short_to_long | 0.012932133 | 0.002998523 | 0.002626369 | 0.007307242 |
| 20261124 | middle_to_long | 0.014496101 | 0.004482824 | 0.002411533 | 0.007601744 |
| 20261125 | short_to_long | 0.010464579 | 0.003293692 | 0.003117117 | 0.004053770 |
| 20261125 | middle_to_long | 0.012693729 | 0.005315213 | 0.002934520 | 0.004443996 |
| 20261126 | short_to_long | 0.010455956 | 0.003480932 | 0.003001710 | 0.003973314 |
| 20261126 | middle_to_long | 0.012898784 | 0.005288821 | 0.002862823 | 0.004747140 |

The observed race supply and selected historical venue-quarter portfolio are imperfect proxies for individual feasible options; no causal environmental claim. Do not claim the long-band boundary is explained by Q. Next distinguish actual sire-identity alignment from arbitrary same-scale corrections while fixing historical-only donor mapping and own update. No target surface values needed for that algebraic contrast, but selection of later observed individuals persists. No genetics, animal learning, fitness or wagering inference. Shared cohorts and splits dependent.

[Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45386135942/artifacts/14917270285) · sha256:968b322ba9c94b7d47a4e99b2f015d777699cc732935f3a214ac11d68ac1a6df.
