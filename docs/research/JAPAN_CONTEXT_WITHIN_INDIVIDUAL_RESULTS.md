# Within-horse fixed-profile information substitution: completed results (2026-11-24)

**Fixed family correction loses predictive value within the same observed individuals, and changing membership offsets part of the decline.** [Frozen protocol](JAPAN_CONTEXT_WITHIN_INDIVIDUAL_PROTOCOL.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45382057980) · [stdout evidence](../evidence/japan-context-within-individual-20261124.json). Original commit `1f21f03905b0c989bfd48b272e192b8b296840a5`; source gates, synthetic tests and PR85/86 parity passed. Artifact metadata checked separately, ZIP not independently extracted.

Primary 2022–24 pair intersection: 599 horses/122 sires. Mean observed historical eligible starts 4.500835→12.383973. Fixed source-A baseline and correction invariant. Gain for the fixed sire term when own information is updated goes from +0.011711907 to −0.015865616, change −0.027577523. Exact within-individual decomposition: observed annual occupancy shift −0.011471708 (41.6% of decline), own-information update −0.016105815 (58.4%; conditional pointwise sire interval [-0.025056735,-0.007781647]). Full annual population difference −0.017080790, membership remainder +0.010496733, offsets 38.06% of within-intersection decline. This is arithmetic rather than a causal contribution estimate or a statistical test of membership.

| Seed | Years | Intersection | Horses | Own update | 95% pointwise interval | Occupancy shift | Within total | Membership remainder |
|---|---|---|---:|---:|---|---:|---:|---:|
| 20261124 | 2022-2023 | pair_intersection | 1287 | -0.009437072 | [-0.013790200, -0.004799198] | -0.003771300 | -0.013208373 | 0.005542425 |
| 20261124 | 2022-2023 | three_year_intersection | 527 | -0.011742397 | [-0.018537382, -0.005307669] | -0.005322377 | -0.017064774 | 0.009398826 |
| 20261124 | 2022-2024 | pair_intersection | 599 | -0.016105815 | [-0.025056735, -0.007781647] | -0.011471708 | -0.027577523 | 0.010496733 |
| 20261124 | 2022-2024 | three_year_intersection | 527 | -0.017228797 | [-0.027039367, -0.007962467] | -0.011881070 | -0.029109867 | 0.012029077 |
| 20261124 | 2023-2024 | pair_intersection | 616 | -0.006042055 | [-0.009953388, -0.002698753] | -0.006252140 | -0.012294195 | 0.002879353 |
| 20261124 | 2023-2024 | three_year_intersection | 527 | -0.005486400 | [-0.009230833, -0.002086754] | -0.006558693 | -0.012045093 | 0.002630252 |
| 20261125 | 2022-2023 | pair_intersection | 1287 | -0.009644506 | [-0.014303073, -0.005523099] | -0.003203986 | -0.012848492 | 0.005657259 |
| 20261125 | 2022-2023 | three_year_intersection | 527 | -0.011744886 | [-0.018175707, -0.006223153] | -0.005255440 | -0.017000326 | 0.009809093 |
| 20261125 | 2022-2024 | pair_intersection | 599 | -0.016200917 | [-0.026100814, -0.007687528] | -0.010316355 | -0.026517272 | 0.011272636 |
| 20261125 | 2022-2024 | three_year_intersection | 527 | -0.017293539 | [-0.027013359, -0.009018913] | -0.010757392 | -0.028050931 | 0.012806295 |
| 20261125 | 2023-2024 | pair_intersection | 616 | -0.006137020 | [-0.009583449, -0.002964308] | -0.005058387 | -0.011195407 | 0.003142004 |
| 20261125 | 2023-2024 | three_year_intersection | 527 | -0.005548653 | [-0.009443526, -0.002451369] | -0.005501952 | -0.011050605 | 0.002997202 |
| 20261126 | 2022-2023 | pair_intersection | 1287 | -0.009635248 | [-0.013920188, -0.005129925] | -0.003700571 | -0.013335819 | 0.005812947 |
| 20261126 | 2022-2023 | three_year_intersection | 527 | -0.011576049 | [-0.018833901, -0.005513335] | -0.004820482 | -0.016396530 | 0.008873658 |
| 20261126 | 2022-2024 | pair_intersection | 599 | -0.016153963 | [-0.025243598, -0.007416354] | -0.011391591 | -0.027545554 | 0.011143923 |
| 20261126 | 2022-2024 | three_year_intersection | 527 | -0.017264387 | [-0.027941421, -0.008544226] | -0.011576477 | -0.028840864 | 0.012439234 |
| 20261126 | 2023-2024 | pair_intersection | 616 | -0.006420452 | [-0.010155963, -0.003152381] | -0.006674081 | -0.013094533 | 0.004215774 |
| 20261126 | 2023-2024 | three_year_intersection | 527 | -0.005688339 | [-0.009514356, -0.002445317] | -0.006755995 | -0.012444334 | 0.003565575 |

All 18 repeated seed/year/intersection comparisons have negative own-update point estimates and negative conditional intervals; all within-total intervals negative and membership remainders positive. These are overlapping sensitivities, not independent replications. Annual 2023/24 own-update contrasts for both fixed and refreshed family profiles likewise have 12/12 negative pointwise intervals. Fixed three-year intersection 527 horses/115 sires: main-seed gains +0.011492672, −0.005572102, −0.017617195 in 2022, 2023, 2024; mean prior count 4.667932, 8.939279, 13.225806. Note the membership remainder differs from PR86's two-stratum cross-source decomposition, and can act in the opposite direction: different contrasts, not contradictory.

## Algebraic interpretation

For residual r and fixed family correction d, gain g=2E[rd]−E[d²]. Updating own predictor by u changes the gain by −2E[du]. On the common 527-horse cohort the correction energy is unchanged (main seed 0.029770627), while alignment E[rd] with refreshed own baseline falls 0.020631649→0.012099262→0.006076716. The descriptive oracle slope correspondingly falls 0.693→0.406→0.204; never use these held-out-label values as weights for prediction. PR87 separately fitted historical A weights and found 2022/23 useful gains but uncertain primary 2024 transfer.

The key evidence concerns predictive information, not an animal actually using genealogical information. Common-cohort membership is conditioned on later observed eligible starts; no survival, fitness, causal age, learning or adaptation inference. Environmental assignment by humans, source missingness and shared pedigree/management remain. No multiple-comparison or all-dependence uncertainty claim. All input data temporary, only anonymous aggregates retained. Next test generalization to predeclared adjacent distance bands rather than further optimizing the repeatedly inspected 1600–1999m endpoint.

[Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45382057980/artifacts/14914886825) · sha256:653159a084b4f47f8e7925eea91e0e2122b762759887bd181b2b8f995ed80695.
