# Fixed-target own-score rollback: conditional parent information restoration

27 November 2026 JST. [Frozen protocol](JAPAN_FIXED_TARGET_OWN_SCORE_ROLLBACK_PROTOCOL_20261127.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45946819618) · [aggregate receipt](../evidence/japan-fixed-target-own-score-rollback-20261127.json).

PR111/116/117 replay and individual own-score parity gates passed. Same matched late event, opponent, observed outcome, actual and three alternate early parent contributions, late count and other covariates. Restore earlier own performance terms with passive decay. Positive specificity change means actual parent score gains over matched alternate scores increase under rollback.

| Year | Same horses | Current specificity | Rollback specificity | Difference (conditional focal 97.5%) |
|---|---:|---:|---:|---|
| 2020 | 1819 | 0.000303165 | 0.000835034 | 0.000531868 [0.000269021, 0.000801284] |
| 2021 | 1939 | 0.000050605 | 0.000663440 | 0.000612835 [0.000374543, 0.000870808] |

Both primary-direction contrasts are positive on all three separate conditional resampling axes. Current-parent sensitivity likewise positive. Rollback worsens ablated and full-model Brier loss; this is loss accounting, not improved final predictive performance from discarding information. Under this fitted score intervention, earlier own performance information restores some incremental parent specificity on identical late outcomes. Does not identify pure information versus biological state, a causal experience or inheritance effect, or actual retraining under censored history. Late count fields retained, hybrid features may extrapolate. Same previously examined source, intervals omit crossed dependence and fit uncertainty. Market social influence is a separate unvalidated hypothesis: no common registered horse ID join or sufficient synchronized real trajectories. Synthetic market counterfactuals may test model implications without claiming real social behavior. No raw exports or main merge.

Provenance: head e52a49d50445ce086ff0d7338b8e141ad3320a63; artifact 15175470257; sha256:62050b1882f89fcbe0e5fb98837ffb3a4b6816c257b86b2821c10774c516a9b7; upload-log/metadata parity, ZIP bytes not independently verified.
