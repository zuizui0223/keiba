# Initial popularity perturbation depends on competitive field and scale

27 November 2026 JST. [Frozen protocol](MARKET_PERTURBATION_FIELD_STABILITY_PROTOCOL_20261127.md) · [complete synthetic aggregate](../evidence/market-perturbation-field-stability-20261127.json) · [successful Actions replay](https://github.com/zuizui0223/keiba/actions/runs/45953277700).

288 fixed cells, 128 common-shock paired replications/cell (36,864 pairs). Four fields × three initial differences × three dispersion levels × eight feedback levels. Conservation, identical worlds, no feedback exact dilution, exact D decomposition, deterministic reproduction and four PR120 endpoint D/R/M means passed. The initial local numerical QA failed for epsilon 1e-4 under strong feedback before any factorial cell results. Refined finite difference epsilon 1e-6 and scaled tolerance 1e-6; max scaled discrepancy 8.881784197001252e-9. All scientific simulation settings unchanged. Initial pair mass .25 and equal focal abilities across fields. D/D0 and R/R0 measure relative amplification of aggregate and within-pair contrasts, respectively.

| Field | Aggregate D gain | Within-pair R gain | Final pair mass | Aggregate MC95 | Within-pair MC95 |
|---|---:|---:|---:|---|---|
| Equal | 2.863672 | 2.501502 | 0.258887 | [2.540629,3.186715] | [2.291827,2.711176] |
| Pair advantaged | 11.472656 | 3.373372 | 0.848965 | [10.408868,12.536444] | [3.054526,3.692218] |
| Pair disadvantaged | 0.229492 | 1.249535 | 0.045630 | [0.213338,0.245647] | [1.172619,1.326451] |
| Heterogeneous | 0.497461 | 1.637690 | 0.074097 | [0.459983,0.534939] | [1.531840,1.743540] |

Above: alpha 1.5, tau 0, initial D=.025. Disadvantaged and heterogeneous pairs show opposite classifications: aggregate attenuation and within-pair amplification. Pair mass falls from .25 to .04563/.07410, respectively. Advantaged pair mass grows to .84896. Competitive field affects both levels of response, not proof of real observer mechanisms.

| Field | Initial D .025 gain | Initial D .10 gain | Initial D .20 gain | Large minus small normalized D gain (MC95) |
|---|---:|---:|---:|---|
| Equal | 2.863672 | 2.611133 | 2.340234 | -0.523438 [-0.812379,-0.234496] |
| Pair advantaged | 11.472656 | 7.332666 | 4.297559 | -7.175098 [-8.238396,-6.111800] |
| Pair disadvantaged | 0.229492 | 0.243262 | 0.234863 | +0.005371 [-0.008568,0.019311] |
| Heterogeneous | 0.497461 | 0.484229 | 0.494824 | -0.002637 [-0.037999,0.032726] |

Same alpha/tau. Normalized growth does not scale proportionally with the perturbation. Equal and advantaged fields have lower relative amplification at large perturbation, but absolute final difference is larger, and finite share bounds matter. No universal threshold.

| Uniform field dispersion | PR120 local critical alpha | Simulated gain at alpha=1.5, D0=.025 | Uniform local linear gain |
|---:|---:|---:|---:|
| 0 | 1.000000 | 2.863672 | 3.014101 |
| 2 | 1.534270 | 0.982813 | 0.951233 |
| 6 | 3.781189 | 0.265820 | 0.253367 |

At alpha 1.5, tau 2 stochastic interval overlaps 1, so do not declare attenuation from the theoretical coefficient alone. At tau 6, alpha 3.5 mean D gain .872656, attenuation; alpha 4 mean 1.218555, amplification in this equal-field/small-shock case. Terminal aggregate finite-horizon classifications: 86 amplify, 189 attenuate, 13 unresolved. This is a parameter grid, not real prevalence. Uniform local expected-drift stability is not global and cannot be transferred directly to unequal fields; deterministic expected recursion is not stochastic expectation. Next: symmetric pair reference trajectory and time-varying pair-specific growth equation, separate pair mass and within-pair response. No real quotes, participant data, empirical threshold, causal or genetic claims, actual horse-history mapping or betting advice. Prior empirical PR118 remains separate. No main merge or frozen ledger modification.

Replay: 25733 numerical entries checked, maximum absolute discrepancy 8.43769498715119e-15. Complete original aggregate in repository; independent connector retrieval exceeded size limit. Actions compared the full stored JSON recursively, not just summary. ZIP bytes not independently verified.
