# Environmental diversity of kin information and competitive similarity (2026-11-24)

## Scientific hypothesis

A large number of related phenotypic observations need not yield high precision if they share the same environments and common errors. In a simple model of distinct peers, observation = latent target + family-common error + context-common error + individual error. Under independent context errors and one context per peer, mean error variance = sigma_I^2/n + sigma_E^2 sum(p_e^2) + sigma_F^2. Define D_E=1/sum(p_e^2). With illustrative variances (1,1,0.25), 100 peers in 1 context give error variance 1.26; 12 peers evenly across 4 contexts give 0.583333. These are theoretical values, not fit to horses. The model assumes common context errors across individuals, not established from records. The empirical exposure metric extends the mass definition to repeated contexts per peer and is not asserted to equal the effective sample size.

## Primary historical test (frozen before examining new effects)

Retain the original source A/B exact SHA and strict 244,147 focal starts, 12,887 horses, 35,333 complete-classified source races. Recreate M2 (original STRONG_KIN) score both on full and strict cohort to 1e-8. Train fixed ridge alpha=100 in 2018-21, each target year uses only records of earlier years; 2022-24 all use source A through 2021. No future source outcomes or later history enter features. This is a new exploratory analysis of a previously inspected calendar interval, not independent confirmation. The focal panel is not all entrants.

Within each target horse x surface/400m band, exclude the focal and ALL records in the target band+surface from each recorded direct-parent peer pool. Distinct peers contribute one unit of exposure mass allocated among their observed off-target contexts proportional to their own start counts. Compute inverse Simpson D_E, peer count, total starts, mean per-peer latest-year age, share of same surface, mean absolute distance-band gap, and equal-peer rank signal shrunk by n/(n+8). Zero peers have explicit zero features. Paternal and maternal pools separate; double counting across sides and deep relatedness remain limitations.

M2: unchanged strong own and target-context kin model.
M3: M2 + off-target counts, depth, recency, proximity and performance, plus interactions of off-target performance with these controls and own count/context count.
M4: M3 + log D_E main effects.
M5: M4 + off-target performance x log D_E terms.

Primary estimand: horse-equal paired MSE(M4)-MSE(M5) among focal starts with no own target-context history in frozen source A and at least one off-target peer. Positive means the interaction improves retrospective out-of-time rank estimates, not that horses use kin information. Report M0/M2/M3/M4/M5 and the primary horse x day two-way sensitivity and whole-sire bootstrap using the existing implementation. The preexisting eight-comparison interval may be retained as conservative sensitivity; the one primary contrast is pre-specified. Report raw unscaled interaction coefficient signs separately: positive rank-signal x diversity slopes are consistent with higher influence in a larger D_E, not causal. If primary interval includes zero, insufficient support, M5 fails M2 or midpoint, or slopes are inconsistent, do not promote the hypothesis. Null/negative results and all year-specific scores retained. Count, depth, age and proximity control by feature adjustment, not exact matching. Diversity by fixed peer count bins (1, 2-4, 5-19, 20+) is descriptive. Cross-validation by horse and family and exact matched nonkin in a new untouched cohort remain necessary.

## Separate competition paradox: preregistration candidate, HOLD empirical causal claim

H1: close kin or similar historical pacing predicts similar reaction norms in individually observed settings.
H2: competitors with similar independently estimated pacing/space use interfere more strongly when they actually share a race, conditional on field composition; drafting can reverse the sign, so allow both.
Use an independently verified absolute sectional speed or absolute completion time, not same-race relative rank (a fixed-sum outcome), plus complete confirmed starters, nonfinish status, actual rider, and stable identities. Within-horse repeated comparisons across opponent composition, context-matched nonkin and horse/race-date dependence. Similarity from histories strictly before target. Kin-specific competition and similarity-mediated competition are different contrasts. Same stable/trainer, age, ability, race selection and common environment are competing explanations. Current Cannon/Doomben and Japanese datasets are not joined at the horse GPS-parent level; do not treat simulation as a real causal finding. No market price or wagering outcome is used for either biological test.

## Execution

See [analysis code](../../scripts/ecology_japan_kin_context_diversity.py) and [workflow](../../.github/workflows/ecology-japan-kin-context-diversity.yml). The workflow downloads original third-party inputs to the runner only, checks existing source hashes, runs synthetic leakage/mass tests and emits only aggregate JSON. No old ledgers or models changed. Rights and official registration/publication times remain unverified; original inputs are removed. Empirical status stays HOLD until a successful artifact is inspected.
