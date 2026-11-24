# Experience-dependent calibration of context allocation: completed retrospective results (2026-11-24)

**Conditional calibration improves the full correction and constant-weight comparator consistently, but the prespecified late-cohort useful-information primary remains uncertain.** [Frozen protocol](JAPAN_CONTEXT_INFORMATION_SUBSTITUTION_PROTOCOL.md) · [successful workflow](https://github.com/zuizui0223/keiba/actions/runs/45381454655) · [stdout evidence](../evidence/japan-context-information-substitution-20261124.json). Source commit `fe1f62635ebc43d159ac696d5e0901a2ea22863d`; synthetic tests, source/venue/strict cohort and PR81/86 parity passed. Artifact metadata verified, full ZIP not independently extracted.

A2020–21 calibration only, opposite horse-half, four count bins 0/1–3/4–7/8+, monotone [0,1] slopes. All six frozen calibration halves support each bin. Main seed weights: [1,0.614422,0.586786,0.344892] and [1,0.469202,0.349323,0.270748]. Across six halves, the 0 bin is 1, 1–3 spans 0.469–0.614, 4–7 spans 0.349–0.587, 8+ spans 0.265–0.366. Monotonicity was a modeling constraint; five of six unconstrained raw sequences are monotone (the other pools 1–3 and 4–7). Zero-count unconstrained slopes exceed 1; bounded estimates are not genetic effects. The A2021 check trained on A2020 only: N−G positive and pointwise interval positive all three seeds.

| Seed | Year | State | Horses | N | F | P | H | G | N−G MSE | Pointwise sire 95% interval |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 20261124 | 2022 | refreshed | 3011 | 0.372388 | 0.369745 | 0.365778 | 0.369430 | 0.360633 | 0.008616966 | [0.003683120, 0.013940911] |
| 20261124 | 2023 | stale | 1588 | 0.376618 | 0.374029 | 0.369962 | 0.371090 | 0.363439 | 0.009753471 | [0.003699048, 0.015853583] |
| 20261124 | 2023 | refreshed | 1588 | 0.326823 | 0.329368 | 0.324669 | 0.324339 | 0.316372 | 0.006721613 | [0.003447810, 0.010250894] |
| 20261124 | 2024 | stale | 743 | 0.405342 | 0.406595 | 0.402158 | 0.403518 | 0.396602 | 0.007009339 | [-0.002797669, 0.016947126] |
| 20261124 | 2024 | refreshed | 743 | 0.317934 | 0.332244 | 0.326275 | 0.318137 | 0.314325 | 0.002282005 | [-0.001714976, 0.006517540] |
| 20261125 | 2022 | refreshed | 3011 | 0.372388 | 0.371099 | 0.366472 | 0.369772 | 0.361113 | 0.008270008 | [0.003745497, 0.013886133] |
| 20261125 | 2023 | stale | 1588 | 0.376474 | 0.374365 | 0.369855 | 0.370564 | 0.362710 | 0.010173635 | [0.004953063, 0.016279686] |
| 20261125 | 2023 | refreshed | 1588 | 0.326681 | 0.330233 | 0.324958 | 0.324108 | 0.316078 | 0.006815555 | [0.003790450, 0.010189141] |
| 20261125 | 2024 | stale | 743 | 0.405139 | 0.405229 | 0.400638 | 0.402833 | 0.395181 | 0.007969628 | [-0.001312688, 0.017520925] |
| 20261125 | 2024 | refreshed | 743 | 0.317778 | 0.331363 | 0.324876 | 0.317453 | 0.313369 | 0.002782392 | [-0.001372432, 0.006636535] |
| 20261126 | 2022 | refreshed | 3011 | 0.372397 | 0.369465 | 0.365372 | 0.369526 | 0.360444 | 0.008759311 | [0.004106603, 0.014411950] |
| 20261126 | 2023 | stale | 1588 | 0.376533 | 0.373251 | 0.369170 | 0.371275 | 0.363122 | 0.009919445 | [0.004285781, 0.015876155] |
| 20261126 | 2023 | refreshed | 1588 | 0.326737 | 0.329632 | 0.324773 | 0.324630 | 0.316717 | 0.006447610 | [0.003293906, 0.009774228] |
| 20261126 | 2024 | stale | 743 | 0.405199 | 0.405094 | 0.400812 | 0.403147 | 0.395679 | 0.007624250 | [-0.002283368, 0.018048995] |
| 20261126 | 2024 | refreshed | 743 | 0.317828 | 0.331132 | 0.325027 | 0.317382 | 0.313227 | 0.002903874 | [-0.001584125, 0.007393833] |

2022 stale/refreshed predictions are identical, counted once above. N−G positive point estimates 15/15 and positive pointwise intervals 9/15. F−G and P−G positive with pointwise intervals above zero 15/15 and 15/15 respectively. These are dependent sensitivity contrasts, not independent replicates. H−G less certain in 2024.

**Primary** B2024 refreshed first seed, 743 horses/132 sires: N=0.3179340604, G=0.3143247707; MSE gain +0.0022820053 [-0.0017149759,+0.0065175400]. All three B2024 refreshed primary-like intervals cross zero. G beats F by +0.0115863014 [0.0072019370,0.0154284335], but improving a poor full correction alone is not sufficient to establish incremental gain over N. In 2022/23 (both applicable states), N−G positive with intervals above zero across all seeds. Primary 2024 refreshed bins have counts 18, 80, 161, 484; zero and 1–3 bins below the preregistered support gate, all other N−G intervals include zero. The 8+ full correction is negative [-0.0212716638,-0.0084515323], reduced to near-zero with G. Full receipt preserves all printed bin metrics; unprinted stale and A2021 bins remain uninspected.

## Scope

Conditional calibration is supported in the earlier historical years and relative to the full/constant alternatives throughout. The late-cohort primary N−G remains unestablished. A/B data and earlier B outcomes were already inspected in previous studies; weights fit using A only, but design is post-hoc relative to B, not independent prospective validation. The same population, seeds, profiles and years are dependent; no simultaneous inference. No causal learning, genetic inheritance, adaptation, animal choice, or prediction of new entrants. Observed turf fraction only, unbounded linear estimates. No individual data exported.

Next PR88 separates within-horse changes in fixed correction value from changes in cohort membership. No need to select a new gate using B outcomes.

[Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45381454655/artifacts/14913937279) · sha256:4118c1c7ff719905839581a0bb80a94ace2379cec0e652cfa3e557c7cfd6e32b.
