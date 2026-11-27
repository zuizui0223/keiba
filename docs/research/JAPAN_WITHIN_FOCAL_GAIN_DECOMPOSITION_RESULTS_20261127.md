# Matched focal gain decomposition: predominantly alignment, not established recovery

27 November 2026 JST. [Frozen protocol](JAPAN_WITHIN_FOCAL_GAIN_DECOMPOSITION_PROTOCOL_20261127.md) · [successful repaired run](https://github.com/zuizui0223/keiba/actions/runs/45934968545) · [aggregate receipt](../evidence/japan-within-focal-gain-decomposition-20261127.json).

Initial run 45933660919 stopped on interval-loop variable shadowing. Execution-only repair preserves scientific settings. PR112/113 replay parity passed, including original gain means and conditional intervals. Same 774 focal horses per year and identical selected events. Exact focal Brier decomposition: gain = 2(y-p0)d − d², with p0 the focal-score-ablated prediction and d the full minus ablated probability.

| Year | Arm | Alignment | Penalty | Focal gain | Mean absolute focal logit score |
|---|---|---:|---:|---:|---:|
| 2020 | novel | 0.002117485 | 0.000931648 | 0.001185837 | 0.115285453 |
| 2020 | familiar | -0.000363769 | 0.001045320 | -0.001409089 | 0.116439272 |
| 2021 | novel | 0.002777348 | 0.000834135 | 0.001943214 | 0.109534463 |
| 2021 | familiar | 0.000694661 | 0.000904391 | -0.000209731 | 0.110397564 |

| Year | Component change | Point estimate | Conditional focal 97.5% interval |
|---|---|---:|---|
| 2020 | alignment_change | 0.002481255 | [-0.000342267, 0.005374572] |
| 2020 | penalty_change | -0.000113672 | [-0.000168669, -0.000057675] |
| 2020 | gain_change | 0.002594927 | [-0.000194317, 0.005473101] |
| 2020 | carry_gain_change | 0.002633234 | [-0.000145411, 0.005524261] |
| 2020 | new_signal_increment | -0.000038307 | [-0.000225854, 0.000160621] |
| 2021 | alignment_change | 0.002082688 | [-0.000154808, 0.004418699] |
| 2021 | penalty_change | -0.000070256 | [-0.000111031, -0.000027162] |
| 2021 | gain_change | 0.002152944 | [-0.000089242, 0.004490192] |
| 2021 | carry_gain_change | 0.001971508 | [-0.000139484, 0.004258683] |
| 2021 | new_signal_increment | 0.000181436 | [-0.000018253, 0.000392023] |

Alignment accounts for most of the positive observed gain difference in both years, but all alignment-change intervals span zero across the three separate axes. The penalty decreases in both years; all corresponding conditional intervals exclude zero. Penalty is a squared probability perturbation, not information quantity. The signed earlier focal logit score carried forward to the novel event retains 0.002633234 (2020) and 0.001971508 (2021) of the gain difference, with the latter about 91.6% of the observed 0.002152944. The 2020 point carry-forward difference exceeds the observed difference because newer score increment is negative. Neither carry-forward primary interval excludes zero. New-score increment is uncertain by focal and novel-day axes; familiar-day 2021 interval is positive but secondary and not robust across axes. Do not claim established recovery, independent corroboration, genetic effects, or equal probability perturbations. Arithmetic identities conditional on the existing selected events; previous PR113 primary HOLD unchanged. The same-horse three-event temporal control was frozen in PR115 before inspecting these components. It is a separate post-result test, not a rescue of the primary hypothesis. Same source, crossed race/horse/kin/fit uncertainty not jointly modeled. No raw export; no main merge.

Provenance: head 315e2aaa7994eb943451d974ebc2637d1240c4b8; artifact 15170148802; sha256:e10e83016f5f2b04e54a3803b3453d5ccb9d102b7427d91fbd49d62cddfc774c; metadata and upload-log parity, ZIP bytes not independently extracted.
