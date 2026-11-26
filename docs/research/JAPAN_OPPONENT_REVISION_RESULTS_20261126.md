# One-hop opponent revision: useful incremental transfer not established

26 November 2026. [Frozen protocol](JAPAN_OPPONENT_REVISION_PROTOCOL_20261126.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45780514187) · [aggregate receipt](../evidence/japan-opponent-revision-20261126.json).

Original PR107 calibration, support and Brier parity passed. Both 2019 calibration strata passed support; fixed selected revision weights 2 (strict one-start one-win, upper grid boundary) and 0.75 (broader one-win). No target tuning.

| Year | Stratum | Connected pairs | Original daily Brier | Corrected Brier | Gain | Conditional date 97.5% interval |
|---|---|---:|---:|---:|---:|---|
| 2020 | first_both_one_start_one_win | 291 | 0.249497493 | 0.247139396 | 0.002358097 | [-0.009175331, 0.015700544] |
| 2020 | first_both_one_win | 41617 | 0.222901991 | 0.222932835 | -0.000030844 | [-0.000622496, 0.000520011] |
| 2021 | first_both_one_start_one_win | 280 | 0.250903927 | 0.253508632 | -0.002604705 | [-0.018765394, 0.011785744] |
| 2021 | first_both_one_win | 44446 | 0.223228242 | 0.222865093 | 0.000363149 | [-0.000164380, 0.000927922] |

## Alternate-race control, same matched targets

| Year | Stratum | Matched pairs | Actual vs control gain | Conditional date 97.5% interval | Actual vs base gain | Mean anchor rating mismatch |
|---|---|---:|---:|---|---:|---:|
| 2020 | first_both_one_start_one_win | 257 | -0.000664242 | [-0.016862780, 0.016071346] | 0.004668615 | 0.141675109 |
| 2020 | first_both_one_win | 34462 | 0.000539084 | [-0.000199163, 0.001249174] | -0.000037676 | 0.172115155 |
| 2021 | first_both_one_start_one_win | 235 | -0.004799611 | [-0.030436898, 0.016819701] | -0.004729687 | 0.164900592 |
| 2021 | first_both_one_win | 35866 | 0.000982826 | [0.000220350, 0.001828329] | 0.000359409 | 0.166095641 |

Primary strict 2021 gain is negative and uncertain; 2020 point gain is positive but uncertain. All four all-connected actual-vs-base intervals span zero. In broader 2021 only, actual beats alternate-race control on 35,866 matched pairs, but actual vs base remains uncertain. This is a descriptive specificity contrast against an imperfect control, not proof of useful incremental revision, independent replication or a causal network effect. The 2020 control contrast is uncertain and both strict control point contrasts are negative. Retain these adverse findings; do not extend grid or select a favorable subgroup. Anchor matching balances date/surface/distance/count imperfectly and does not balance future opportunities. Original online ratings do not retroactively revise an inactive horse. A periodic full joint graph refit, compared on matched pre-cutoff states with daily and snapshot controls, is a distinct next test. No physiological ability, genetic, prospective or wagering inference. Conditional intervals omit shared horse/graph/fit dependence. No raw export or main merge.

Provenance: head 82a2993c99889a53b00997315e5117d83c71983e; artifact 15097578347; sha256:17efd9ac8be92bf0c0cee326639cbb2503410201af9a81c8fd4062e655b1f5e4; metadata and upload-log parity, not independently extracted ZIP.
