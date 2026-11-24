# Own-history-dependent calibration of family information in environment occupancy

2026-11-24. Follow-up to completed PR86. The 2021→2022 decline in the uncalibrated family correction was descriptively 79.8–89.1% associated with history-availability composition. Refreshed 2024 family additions worsened the refreshed no-family comparator in all three splits. Test whether a count-dependent weight on that same correction transfers better, rather than inventing a new endpoint or reinterpreting negative evidence.

## Frozen design before this run

Retain exact source A/B hashes and existing pre-2022 identity/venue gates, 244,147/12,887 strict focal cohort and annual JRA 1600–1999m eligible target counts 3,011/1,588/743. Reproduce PR81 and PR86 scores. Target annual observed turf fraction conditional on classified eligible starts; continuing anchored horses only. No new entrants.

Generate source A chronological calibration residuals for 2020 and 2021 using the original opposite-horse-half profiles, only earlier calendar years. Let B=own baseline + global residual; M=B+same-sire correction; d=M−B, r=observed−B. Per evaluation half, fit on calibration rows in opposite horse half, equal total weight per distinct calibration horse across years. For the A2021 check use 2020 only. For all B targets freeze weights from 2020–21 only. The B labels previously inspected for PR85/86 are not used to fit weights; this is still a post-hoc historical test, not an untouched holdout.

Count bins n=0, 1–3, 4–7, >=8 prior eligible classified starts. G=B+lambda(n)d. Solve weighted squared loss over four nonincreasing slopes in [0,1], using exact weighted PAVA on sums of d*r and d². Count only nonzero-d donor rows for support (>=100 distinct horses and >=30 sires each bin); insufficient support fails closed, no relaxation. A monotonicity constraint is a modeling assumption, not an empirical test of monotone biological dependence. Benchmarks N=B (no correction), F=M (full correction), P=pooled fitted slope in [0,1], H=full correction only if n=0. Both stale and chronologically refreshed own/profile states from PR86; count at each cutoff, not a future outcome. No clipping of predictions, preserve parity. All targets retained, including unsupported donor fallback. Report weights/support and all bin-specific losses.

Primary: seed 20261124, B2024 refreshed all-target N−G MSE. To support a useful gated correction, it must improve N, not merely F. F−G, P−G, H−G are separate diagnostics; 2022/23, stale states, other two seeds and A2021 check are sensitivity. Whole-sire 999-draw pointwise intervals with existing minimum 100 horses/30 sires. Shared histories and splits dependent; no joint/multiplicity or causal claims. Never select a favorable cutoff after B scores. Report null/negative results. If gating fails, no general transferability claim.

No genetic causal or physiological effect, animal voluntary niche choice, official debut, or betting inference. Temporary third-party data; anonymous aggregate only.

[Code](../../scripts/ecology_japan_context_information_substitution.py) · [Workflow](../../.github/workflows/ecology-japan-context-information-substitution.yml).
