# Execution repair: within-focal decomposition

Run 45933660919 passed synthetic tests and source download, then failed at the second evaluation year because the nested PR113 interval-parity loop overwrote the outer year-panel variable `v` with an interval list. Rename the loop variable to `interval`. No scientific specifications, data, weights, matching, estimands, support thresholds, or inference rules changed. No completed aggregate result was returned or inspected from the failed run. Re-run all parity and synthetic gates.
