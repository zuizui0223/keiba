# Observation membership can amplify or oppose within-individual information change

2026-11-25 · **New arithmetic crosswalk of existing real-data aggregates, not a new empirical fit or formal cross-endpoint interaction.** Main branch unchanged. Source files are pinned below. This comparison keeps the rank gate-vs-full loss contrast separate from the allocation no-family-vs-fixed-family loss contrast.

## Exact common-cohort bridge

For any specified loss advantage D, write D_all(t) and D_C(t) for the full observed set and common horses C. Then

    D_all(t1) − D_all(t0)
      = [D_C(t0) − D_all(t0)]
      + [D_C(t1) − D_C(t0)]
      + [D_all(t1) − D_C(t1)].

The sum of the first and third terms is the membership remainder. It can amplify, attenuate or reverse the within-C change. This is a decomposition of observed means, not an effect of survival, selection, learning, breeding or intervention.

| Endpoint/seed (2022–24) | Common horses | Within-C change | Early membership | Late membership | Combined membership | Full change | Direction |
|---|---:|---:|---:|---:|---:|---:|---|
| Rank: preselected history gate vs always-family | 5163 | -0.000105406 | -0.000077461 | -0.000000063 | -0.000077524 | -0.000182929 | amplifies |
| Allocation: fixed sire correction, 20261124 | 599 | -0.027577523 | 0.009750607 | 0.000746126 | 0.010496733 | -0.017080790 | opposes |
| Allocation: fixed sire correction, 20261125 | 599 | -0.026517272 | 0.010418904 | 0.000853732 | 0.011272636 | -0.015244636 | opposes |
| Allocation: fixed sire correction, 20261126 | 599 | -0.027545554 | 0.010020742 | 0.001123181 | 0.011143923 | -0.016401631 | opposes |

In the prior rank study, membership makes the observed gate-vs-always-family deterioration 1.735 times as large as the same-horse change. The paired interval includes zero, and later balanced three-year dependence sensitivity also does not support a robust year contrast. In the primary allocation study, membership offsets 38.1% of the same-horse decline; the paired pointwise interval is negative. The full observed decline is 61.9% of the paired decline. The direction difference is a descriptive **counterexample to a universal sign of membership distortion**, not a statistical comparison of the size of two biological effects. The cohorts overlap in archive, not verified independent replicates. The rank gate was selected using 2022 outcomes and own predictors are stale; allocation uses refreshed own histories with fixed correction. Positive loss advantage favors different alternatives in these two studies.

## Boundary conditions: adjacent distance bands

| Band | Seed | Common horses | Within | Membership | Full | Direction |
|---|---:|---:|---:|---:|---:|---|
| 1200-1599 | 20261124 | 531 | -0.020876280 | 0.015029868 | -0.005846413 | opposes |
| 1200-1599 | 20261125 | 531 | -0.021196076 | 0.014229573 | -0.006966504 | opposes |
| 1200-1599 | 20261126 | 531 | -0.017464138 | 0.011286613 | -0.006177525 | opposes |
| 1600-1999 | 20261124 | 599 | -0.027577523 | 0.010496733 | -0.017080790 | opposes |
| 1600-1999 | 20261125 | 599 | -0.026517272 | 0.011272636 | -0.015244636 | opposes |
| 1600-1999 | 20261126 | 599 | -0.027545554 | 0.011143923 | -0.016401631 | opposes |
| 2000-2399 | 20261124 | 267 | -0.002404819 | -0.002343065 | -0.004747884 | amplifies |
| 2000-2399 | 20261125 | 267 | -0.004931852 | 0.000828926 | -0.004102926 | opposes |
| 2000-2399 | 20261126 | 267 | -0.003503537 | 0.000821244 | -0.002682293 | opposes |

Longer-distance membership need not oppose the paired decline; support and surface mix differ, and the main long-band own-update interval includes zero. Shared horses and reused splits prevent independent replication or a formal moderator claim.

## Two further observation operators in earlier rank work

**Gate exposure vs utility:** the 2022 M1 selection-frequency difference between horses observed and not observed in 2024 is -16.5607 percentage points, but standardized by the fixed four-bin historical own-history input it is 0.03310 pp [-0.08756, 0.15317]. The gate itself uses own-history count. This is a measurement/decision-rule composition result, not an adaptive behavior. Conditional loss difference's sire interval includes zero; even the group contrast weakens in the 2023-observed subset.

**Family weighting and cancellation:** rank PR71's positive group contribution mass is 0.000447605, adverse contribution magnitude 0.000306695; 68.5% of the gross positive mass is arithmetically canceled. The remaining horse-equal mean 0.000140910 and sire-equal mean 0.000246870 are both uncertain (pointwise intervals cross zero). Every single-sire removal preserves positive sign but 11 outcome-selected groups removed can reverse it. Changing weights changes the estimand; size association interval spans zero.

These distinct results motivate a single *observation-conditional predictive information* framework: information source, update/weight, observation membership, group weights, and evaluation criterion must be specified separately. The stronger paired allocation finding is not a rescue of the weaker rank inference. No meta-analysis, no causal interpretation, no new genetic or market mechanism.

## Provenance

[Machine-readable arithmetic audit](../evidence/information-membership-nonalignment-20261125.json), source commit `b68bd5df41a433337d93cc6a270a73f15cda794b`. Original source reports: [rank membership](JAPAN_2022_24_GATE_FAILURE_DECOMPOSITION_RESULTS.md), [rank dependence](JAPAN_2022_24_DEPENDENCE_SENSITIVITY_RESULTS.md), [switch exposure](JAPAN_2022_INFORMATION_SWITCH_EXPOSURE_RESULTS.md), [family contribution](JAPAN_2022_24_SIRE_SIGNAL_CONCENTRATION_RESULTS.md), [allocation within-horse](JAPAN_CONTEXT_WITHIN_INDIVIDUAL_RESULTS.md), [distance bands](JAPAN_CONTEXT_DISTANCE_GENERALIZATION_RESULTS.md). All new values are arithmetic transformations of archived summaries; no independent raw-data replay or new intervals.