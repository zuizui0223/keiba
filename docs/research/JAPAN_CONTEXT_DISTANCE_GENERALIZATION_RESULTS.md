# Distance-band generalization: completed retrospective results (2026-11-24)

**The fixed family correction loses incremental value after own-history updating in the adjacent short band. Long-band evidence is weaker; the main long-band interval includes zero.** [Frozen protocol](JAPAN_CONTEXT_DISTANCE_GENERALIZATION_PROTOCOL.md) · [successful workflow](https://github.com/zuizui0223/keiba/actions/runs/45383198727) · [stdout evidence](../evidence/japan-context-distance-generalization-20261124.json). Source commit `eb51fda64809617794f552d016040969589c78a6`. Synthetic, source, venue, strict classified and reference-band parity gates passed. Artifact metadata verified separately; ZIP not independently extracted.

| Distance (m) | Source A horses 2021 | Source B horses 2022/23/24 | B2024 turf/dirt starts | Common 2022/24 horses |
|---|---:|---|---|---:|
| 1200-1599 | 5870 | 2538/1352/688 | 922/1017 | 531 |
| 1600-1999 | 7276 | 3011/1588/743 | 684/1179 | 599 |
| 2000-2399 | 2875 | 1410/750/356 | 557/122 | 267 |

All three bands meet frozen annual surface/horse coverage gates. In A2021 all nine band×seed conditional own+family contrasts have positive point estimates and pointwise intervals. Fixed same-sire information value then changes after updating individual history, conditional on observed horses in both years.

| Distance | Seed | Common horses | Own update MSE | Pointwise sire interval | Occupancy shift | Within total | Membership remainder |
|---|---|---:|---:|---|---:|---:|---:|
| 1200-1599 | 20261124 | 531 | -0.015037529 | [-0.022124893, -0.008753320] | -0.005838752 | -0.020876280 | 0.015029868 |
| 1200-1599 | 20261125 | 531 | -0.014490624 | [-0.022441218, -0.008318164] | -0.006705453 | -0.021196076 | 0.014229573 |
| 1200-1599 | 20261126 | 531 | -0.014124133 | [-0.021409144, -0.007328497] | -0.003340005 | -0.017464138 | 0.011286613 |
| 1600-1999 | 20261124 | 599 | -0.016105815 | [-0.025056735, -0.007781647] | -0.011471708 | -0.027577523 | 0.010496733 |
| 1600-1999 | 20261125 | 599 | -0.016200917 | [-0.026100814, -0.007687528] | -0.010316355 | -0.026517272 | 0.011272636 |
| 1600-1999 | 20261126 | 599 | -0.016153963 | [-0.025243598, -0.007416354] | -0.011391591 | -0.027545554 | 0.011143923 |
| 2000-2399 | 20261124 | 267 | -0.001588491 | [-0.004958299, 0.000926452] | -0.000816328 | -0.002404819 | -0.002343065 |
| 2000-2399 | 20261125 | 267 | -0.003458165 | [-0.008296166, -0.000359915] | -0.001473687 | -0.004931852 | 0.000828926 |
| 2000-2399 | 20261126 | 267 | -0.003211930 | [-0.007240231, -0.000181328] | -0.000291607 | -0.003503537 | 0.000821244 |

Primary short band, first seed: 531 horses, 120 sires; own-update term −0.015037529 [-0.022124893,-0.008753320]; within total −0.020876280; membership remainder +0.015029868. Own-update term negative with pointwise interval below zero in all 12 overlapping short-band comparisons; all 12 reference-band comparisons likewise. Long band: 267 horses/63 sires in 2022–24 main split, own-update term −0.001588491 [-0.004958299,+0.000926452]. Other seeds have negative pointwise intervals, but the main long-band estimate is uncertain; the membership remainder can be negative, unlike the short/reference bands. Do not claim universal decline or identical mechanisms. The long band has strongly unequal surface coverage and smaller intersections; no formal between-band difference test. All data reused from previously inspected A/B archives and horses can overlap bands. No independent prospective test, animal learning, genetic adaptation, choice, or causal distance effect. No individual records or betting outputs.

[Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45383198727/artifacts/14913743564) · sha256:3ef804fa03cb5ddb3ade39030a3f7666773ba53286c4422f806d715a2abf27c5.
