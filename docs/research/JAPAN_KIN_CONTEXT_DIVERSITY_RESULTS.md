# Kin context diversity: completed retrospective test (2026-11-24)

**Primary diversity–performance interaction not supported.** [Protocol](JAPAN_KIN_CONTEXT_DIVERSITY_PROTOCOL.md), original fixed commit `97dcaad33de8e05f33f5792587a47df5a4d771cc`, [successful Actions run](https://github.com/zuizui0223/keiba/actions/runs/45328700713), [job stdout and anonymous aggregate receipt](../evidence/japan-kin-context-diversity-20261124.json). This is not an untouched prospective test; the 2022–24 cohort was previously inspected. Source checks, synthetic tests, full/strict M2 parity and aggregate upload passed by run status. The job stdout is the source for the numerical results below. ZIP artifact metadata was checked, but its complete contents (yearwise/interaction slopes/diversity-count strata) were not independently read in this receipt.

| Group | Starts | Horses | M0 RMSE | M2 | M3 | M4 | M5 | M4-M5 MSE ×10^-6 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 244,147 | 12,887 | 0.321744142 | 0.312167869 | 0.312252586 | 0.312246524 | 0.312242315 | 2.628 |
| novel_supported | 40,130 | 5,729 | 0.327105515 | 0.318950325 | 0.317988563 | 0.317974447 | 0.317974812 | -0.232 |
| seen_supported | 203,972 | 12,520 | 0.319829772 | 0.309996154 | 0.310074863 | 0.310067772 | 0.310064275 | 2.169 |
| no_off_context_peers | 45 | 2 | 0.337660625 | 0.364741029 | 0.368317357 | 0.368482491 | 0.368560458 | -57.465 |

Primary novel_supported: 40,130 starts, 5,729 horses, 20,122 races, 1,067 days. M4-M5 paired equal-horse MSE gain −0.231981 ×10^-6. Horse×day pointwise 95% sensitivity interval [−18.693001, +18.229038] ×10^-6; conservative 8-comparison interval [−25.987166, +25.523204]. Whole-sire 999-draw interval [−30.161537, +32.953463] ×10^-6, 279 clusters. Neither supports the predeclared positive interaction. The all-row M5 error is larger than original M2. Do not select a new primary or claim a monotonic diversity benefit.

Secondary descriptive finding: on novel_supported, M2→M3 RMSE decreases by 0.000961762 (~0.302%); the MSE gain is 612.584 ×10^-6. M3 includes off-context peer counts, depth, recency, proximity, score and their interactions, so this is not isolated kin-performance or diversity evidence. No interval for this secondary comparison appears in stdout; it is a hypothesis-generating descriptive contrast. M3 worsens the all-row M2, and the seen_supported group also worsens. The supported and seen groups overlap in horses; no claim that the between-group effect differs statistically. The remaining 45 starts without off-context peers represent two horses and are not a generalization sample.

## Research implication

Off-context information may complement missing focal context history; the additional diversity moderation is not confirmed. Distinguish the relevance of off-context signal from contextual covariance/redundancy and family-specific exposure selection. PR #78, frozen separately before reading this primary result, tests whether a sire's residual context profile is reproducible across disjoint horses and days (trainer-disjoint sensitivity), rather than declaring it to be genetic variance or a noise term. No evidence here for causal kin competition, adaptive genes, markets or artificial selection.

[Complete aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45328700713/artifacts/14890822686); SHA256 recorded by Actions: sha256:bee6e212c6dd93b19214b881ada2807aa37299374a6fda3d43a3a1a84bf0d66f. Full-year and coefficient claims remain HOLD until inspected. No raw rows, horse/parent IDs or individual predictions published.
