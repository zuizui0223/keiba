# Horse common ability scale: opponent-network gain on first meetings among one-win horses

26 November 2026. [Frozen protocol](JAPAN_COMMON_ABILITY_PROTOCOL_20261126.md) · [software repair audit](JAPAN_COMMON_ABILITY_EXECUTION_AUDIT_20261126.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45779906967) · [aggregate log receipt](../evidence/japan-common-ability-20261126.json).

All source and optimization gates passed after a pandas column-access repair, with unchanged frozen scientific specifications. 550,062 classified JRA starts /62,199 horses across 2010–2021. Graph fits use strictly prior calendar years only. 2019 calibration chose slope 1.5 naive, 1.25 network. This is a relative statistical ability, not physical capacity, absolute speed or genetic merit.

| Target year | Group | Supported pairs | Races | Naive Brier | Network Brier | Gain | Conditional day 97.5% interval |
|---|---|---:|---:|---:|---:|---:|---|
| 2020 | all_connected | 151551 | 2552 | 0.235657156 | 0.233230035 | 0.002427121 | [0.002052091, 0.002761727] |
| 2020 | first_meeting | 123229 | 2551 | 0.235844455 | 0.233393709 | 0.002450746 | [0.002021711, 0.002838994] |
| 2020 | first_both_one_win | 23801 | 1166 | 0.241923089 | 0.238749259 | 0.003173831 | [0.001855037, 0.004423932] |
| 2020 | first_both_one_start_one_win | 24 | 16 | 0.250000000 | 0.249666180 | 0.000333820 | HOLD_SUPPORT |
| 2020 | first_naive_tie | 206 | 133 | 0.250000000 | 0.250177310 | -0.000177310 | [-0.001748338, 0.001292946] |
| 2021 | all_connected | 152916 | 2555 | 0.235217694 | 0.233466240 | 0.001751454 | [0.001451527, 0.002081789] |
| 2021 | first_meeting | 124751 | 2555 | 0.235338990 | 0.233535682 | 0.001803308 | [0.001489414, 0.002159640] |
| 2021 | first_both_one_win | 25677 | 1168 | 0.244888157 | 0.242273389 | 0.002614768 | [0.001270751, 0.003824441] |
| 2021 | first_both_one_start_one_win | 18 | 10 | 0.250000000 | 0.245562524 | 0.004437476 | HOLD_SUPPORT |
| 2021 | first_naive_tie | 142 | 110 | 0.250000000 | 0.250256821 | -0.000256821 | [-0.002845137, 0.002455670] |

Primary 2021 first meetings between horses each with one earlier observed JRA win: 25,677 connected pairs, 1,168 races, 2,341 horses, 106 days; Brier improvement 0.002614768 [0.001270751, 0.003824441]. Pair orientation accuracy (exact probability ties count 0.5) 0.571125 to 0.576714. The 2020 counterpart and both general first-meeting contrasts also have positive conditional intervals. This supports incremental value of historical opponent-network strength on the selected connected pairs, relative to the chosen shrunk-rank baseline. It does not show improvement over all stronger possible baselines, or physiological ability identification.

Coverage: connected first-meeting pairs 123,229/267,198 in 2020 and 124,751/264,062 in 2021. For one-win first meetings 23,801/41,928 and 25,677/44,618. For strict one-recorded-start one-win first meetings only 24/330 and 18/301; both fail frozen support thresholds. Naive-tie strata show adverse point Brier gains with intervals spanning zero, retained. Near-zero naive tie masks use tolerance while accuracy counts exact probability ties; report the metrics as originally calculated, not exact equality for every masked score. No claim about official debut, complete career wins, or disconnected comparisons. Year-start fits cannot include new same-year victories; PR107 separately tests day-batched global and surface-specific updates with strict prior-day information. The source has been examined previously and the date intervals omit graph-fit/repeated-horse dependence; no prospective or causal claim, no raw records redistributed.

Provenance: source head f5648beb82e06af01caff61e76b7da5cdbdc8355, artifact 15097518371, sha256:7b61fe8184abaacea0b06c49b4fc6eeeb07f8fd72f07022f80ec127aec276ab1; metadata and upload log agree, ZIP not independently extracted. No main merge.
