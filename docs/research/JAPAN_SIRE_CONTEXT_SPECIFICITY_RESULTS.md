# Sire-specific context resemblance: retrospective results (2026-11-24)

**Positive predeclared split-half contrast, with conditional sensitivity and heterogeneous annual effects.** Original [protocol](JAPAN_SIRE_CONTEXT_SPECIFICITY_PROTOCOL.md), source commit `a1f44af67d52dd77a38df1d2c015f83de7139142`, [successful workflow](https://github.com/zuizui0223/keiba/actions/runs/45329113256). All numerical values are from completed job stdout; [anonymous receipt](../evidence/japan-sire-context-specificity-20261124.json). Artifact metadata/digest verified, ZIP contents not independently opened.

The original source-A 2,092,836 starts / 90,962 horses passed parity. JRA turf/dirt 1600–1999m 2019–21 diagnostic candidate cohort: 57,208 starts / 15,129 horses. Residuals from historical own/trainer model. Primary horse+day-disjoint seed retains 28,521 starts/11,640 horses before four-cell sire/year support gate; 83 sires, 174 sire-years pass. The strict trainer-disjoint primary-seed version retains 14,394 starts/5,986 horses before that gate, 57 sires and 105 sire-years pass.

| Split | Seed | Sires | Sire-years | Equal-sire mean product | Pointwise 95% whole-sire interval |
|---|---:|---:|---:|---:|---|
| horse_day_disjoint | 20261124 | 83 | 174 | 0.0065307 | [0.0036261, 0.0098842] |
| horse_day_disjoint | 20261125 | 87 | 181 | 0.0062088 | [0.0014506, 0.0102417] |
| horse_day_disjoint | 20261126 | 86 | 187 | 0.0026770 | [-0.0007839, 0.0064934] |
| horse_day_trainer_disjoint | 20261124 | 57 | 105 | 0.0053035 | [0.0012791, 0.0097806] |
| horse_day_trainer_disjoint | 20261125 | 58 | 102 | 0.0031224 | [-0.0020107, 0.0089965] |
| horse_day_trainer_disjoint | 20261126 | 58 | 107 | 0.0066002 | [0.0018372, 0.0125399] |

All six split estimates positive; four pointwise intervals exclude zero. These reuse the same observed records, not six independent replicates. Main estimate 0.0065307244 [0.0036261295, 0.0098841872]. Main split's 2020 estimate is negative (-0.0006841573); strict primary-seed 2020 also negative (-0.0004436973). Other split/year results, including null and negative results, retained in receipt. The baseline outperformed midpoint each calendar year on JRA evaluations. No multiple-comparison claim; uncertainty conditional on this fitted model and sample.

## Interpretation and falsification

The same recorded sire's turf-minus-dirt residual differences are associated across disjoint horses and days, and the direction persists in trainer-disjoint splits. This is evidence of recurring **family-indexed context-specific resemblance**, not genetic variance, causal reaction norms, or universal time transfer. Different horses select into surfaces; shared farms, related sires, nonrandom entry, common baseline calibration and family-specific environment can generate agreement. Whole-sire bootstrap alone does not resolve all dependence. Individual ranks are relative, not absolute performance or competitive interference.

PR77's primary diversity interaction was unsupported, while the off-context block descriptively helped novel-context starts. The new result suggests environment-relevance as a competing explanation, not a proof of its role in PR77. Next falsify selection by requiring the same horse to appear on both surfaces within each split/year; test sire correspondence against matched other-sire group contrasts, keeping the fixed primary cohort and report support loss. Do not interpret matched nonkin as genomic unrelatedness. Keep the two experiments distinct.

[Full anonymous artifact](https://github.com/zuizui0223/keiba/actions/runs/45329113256/artifacts/14890558776) · sha256:0edb3498e1c565888a4793f7c9ede1d2fd4d3629d25e77f054eb4af8473da350.
