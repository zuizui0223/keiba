# First context assignment versus later use: completed retrospective results (2026-11-24)

**Positive family-associated surface assignment after a learned own/history/trainer and donor-count comparator.** [Frozen protocol](JAPAN_SIRE_FIRST_CONTEXT_ASSIGNMENT_PROTOCOL.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45360712301) · [stdout evidence](../evidence/japan-sire-first-context-assignment-20261124.json). Original commit `e44599070be0c7ab7e0e29dc8cc6812deea579a7`; artifact metadata checked separately, complete ZIP not independently extracted. Source parity and synthetic checks passed. Known-sire annual eligible counts 7,265/7,381/7,276 (2019–21) match PR81.

| Seed | Endpoint | Year | Horses | C RMSE | F RMSE | C−F MSE | Conditional pointwise 95% interval | Matched P−F MSE |
|---|---|---|---:|---:|---:|---:|---|---:|
| 20261124 | first | 2020 | 7381 | 0.407146 | 0.387822 | 0.015362 | [0.010548, 0.021039] | 0.034725 |
| 20261124 | first | 2021 | 7276 | 0.403959 | 0.386565 | 0.013751 | [0.008975, 0.019714] | 0.029269 |
| 20261124 | later | 2020 | 4529 | 0.319187 | 0.315227 | 0.002512 | [0.000952, 0.004093] | 0.005738 |
| 20261124 | later | 2021 | 4477 | 0.318305 | 0.315012 | 0.002085 | [0.000910, 0.003375] | 0.005705 |
| 20261125 | first | 2020 | 7381 | 0.407466 | 0.388974 | 0.014728 | [0.010093, 0.019702] | 0.027409 |
| 20261125 | first | 2021 | 7276 | 0.403413 | 0.386830 | 0.013105 | [0.007904, 0.018556] | 0.032570 |
| 20261125 | later | 2020 | 4529 | 0.319201 | 0.315694 | 0.002227 | [0.000743, 0.003744] | 0.005931 |
| 20261125 | later | 2021 | 4477 | 0.318083 | 0.314588 | 0.002211 | [0.000875, 0.003573] | 0.005248 |
| 20261126 | first | 2020 | 7381 | 0.406974 | 0.387316 | 0.015614 | [0.010286, 0.021021] | 0.034893 |
| 20261126 | first | 2021 | 7276 | 0.403935 | 0.386460 | 0.013812 | [0.008686, 0.019381] | 0.031237 |
| 20261126 | later | 2020 | 4529 | 0.319254 | 0.315595 | 0.002323 | [0.000817, 0.003827] | 0.006076 |
| 20261126 | later | 2021 | 4477 | 0.318690 | 0.315293 | 0.002154 | [0.000991, 0.003393] | 0.003962 |

Primary 2021 first eligible source record, 7,276 horses/349 sires: C=0.403958936 → F=0.386564506, MSE gain +0.0137507043 [0.0089747344,0.0197138022]. Matched 6,639 horses, P−F +0.0292686370 [0.0223864710,0.0368183637]. All 12 primary/sensitivity endpoint-year-seed comparisons and all 12 matched swap comparisons have positive point estimates and positive pointwise intervals; they reuse historical records, not independent confirmations.

## Prespecified 2021 primary-seed strata

| Stratum | Horses | C RMSE | F RMSE | Relative RMSE decrease (%) | C−F MSE and pointwise interval |
|---|---:|---:|---:|---:|---|
| all | 7276 | 0.403959 | 0.386565 | 4.306 | 0.013751 [0.008975, 0.019714] |
| no_eligible_before_year | 3737 | 0.453273 | 0.425089 | 6.218 | 0.024755 [0.016067, 0.034976] |
| has_eligible_before_year | 3539 | 0.344303 | 0.341195 | 0.903 | 0.002131 [0.000615, 0.003455] |
| raw_first_record_at_entry | 2150 | 0.446373 | 0.406045 | 9.035 | 0.034376 [0.023345, 0.047211] |
| raw_prior_at_entry | 5126 | 0.384780 | 0.378095 | 1.737 | 0.005100 [0.001921, 0.008774] |

The point estimate is larger for horses without prior eligible records and for the raw-first-record-at-entry subset. Those are observational strata, not a formal test of differences between subgroup effects; groups of different definitions overlap, and raw first source record is not verified debut. First and later endpoints have different denominators and outcomes. Do not equate their raw MSE effects or infer that the first assignment causes later use. Entry-recorded age/sex/trainer are conditional covariates, not verified decision-time information. Parent labels and historical exposure are not genetic causal evidence. All intervals are conditional pointwise sensitivity, not simultaneous inference.

## Biological interpretation

The family-associated information is not just donor count, and persists after a more flexible own-history/trainer model. This complements PR81 occupancy transfer and PR80's uncertain paired response transfer. The strongest current claim is structured observed environmental allocation, not inherited physiological response, voluntary niche preference, or a causal effect of human decisions. The raw-first-record subgroup supports an information-availability hypothesis, but early-age, management and archive selection confounding remain. Next isolate paternal and maternal donor channels, equalize peer counts with fixed outcome-blind subsampling, preserve count-zero fallback and explicitly report maternal support. No betting models or ledgers changed.

[Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45360712301/artifacts/14904961224) · sha256:1372361e53011a366995d91bf5077e9292fa119ce801ba61ddbe4e07ff130a15.
