# Three-event temporal control: contextual recovery remains HOLD

27 November 2026 JST. [Frozen protocol](JAPAN_CONTEXT_TEMPORAL_CONTROL_PROTOCOL_20261127.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45935048104) · [aggregate receipt](../evidence/japan-context-temporal-control-20261127.json).

PR112/113 replay parity passed. Restrict original 774 matched focal horses per year to those with an additional earlier familiar event in exactly the middle event's context, same depth bins, comparable elapsed intervals. No loss-based selection.

| Year | Triplets / original | Mean early→middle days | Mean middle→novel days | Mean absolute gap difference | Days early/middle/novel |
|---|---:|---:|---:|---:|---|
| 2020 | 156/774 | 44.60 | 44.80 | 14.63 | 75/75/77 |
| 2021 | 178/774 | 40.90 | 43.13 | 12.05 | 76/74/73 |

| Year | Arm | Observed focal gain | Fixed earliest score gain |
|---|---|---:|---:|
| 2020 | early | 0.003456801 | 0.003456801 |
| 2020 | middle | 0.002471943 | 0.002658763 |
| 2020 | novel | 0.000211231 | -0.000021071 |
| 2021 | early | 0.002077729 | 0.002077729 |
| 2021 | middle | -0.001210647 | -0.001173695 |
| 2021 | novel | 0.001494506 | 0.001154555 |

| Year | Contrast | Estimate | Conditional focal 97.5% interval |
|---|---|---:|---|
| 2020 | observed_gain_before | -0.000984859 | [-0.005644466, 0.003838792] |
| 2020 | observed_gain_after | -0.002260712 | [-0.007727895, 0.002937125] |
| 2020 | observed_gain_difference | -0.001275853 | [-0.009970338, 0.007399409] |
| 2020 | fixed_signal_gain_before | -0.000798039 | [-0.005589171, 0.004050636] |
| 2020 | fixed_signal_gain_after | -0.002679834 | [-0.008428119, 0.002844024] |
| 2020 | fixed_signal_gain_difference | -0.001881795 | [-0.010838509, 0.006878922] |
| 2021 | observed_gain_before | -0.003288376 | [-0.007941263, 0.001098980] |
| 2021 | observed_gain_after | 0.002705153 | [-0.001841023, 0.007029989] |
| 2021 | observed_gain_difference | 0.005993529 | [-0.000997484, 0.013307399] |
| 2021 | fixed_signal_gain_before | -0.003251425 | [-0.007910340, 0.000949254] |
| 2021 | fixed_signal_gain_after | 0.002328251 | [-0.002344077, 0.006784861] |
| 2021 | fixed_signal_gain_difference | 0.005579676 | [-0.001544381, 0.013137953] |

The 2021 frozen primary difference of observed changes is positive (+0.005993529), but every conditional interval spans zero. The 2020 counterpart has opposite sign (-0.001275853). Fixed earliest signed score gives the same year-dependent directional pattern with all intervals spanning zero. Neither interval duration balance nor same-focal matching identifies a causal environmental change. The shared middle event may generate regression-to-mean structure; selection of only 20.2%/23.0% of original matched focal horses is material. No pooling rescue, no threshold relaxation, no claim of equivalence or established reversibility. PR111's broad between-pair depth contrast remains the supported primary result under its assumptions. Prioritize testing whether actual direct-parent identity contributes beyond count-, experience- and recency-matched other horses on that same daily common ability scale. No raw export, no main merge. Conditional intervals omit crossed horse/race/parent/graph/fit dependence.

Provenance: head 00b97481bd2d41c118fbc161d1b9c757f3be58b4; artifact 15170273465; sha256:78b42257ed2e7dc03f862ca970dda967ae18046ffaae6f68e9dfdcca9e6056d6; metadata and upload-log parity, ZIP bytes not independently extracted.
