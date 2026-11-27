# Mean evidence, evaluator dispersion and popularity feedback

27 November 2026 JST. [Frozen design](MARKET_INFORMATION_FEEDBACK_FACTORIAL_PROTOCOL_20261127.md) · [aggregate results](../evidence/market-information-feedback-factorial-20261127.json) · [Actions replay](https://github.com/zuizui0223/keiba/actions/runs/45952880053).

The fixed 96-cell grid (128 paired replicates/cell) separates the mean ability coefficient b from private Gaussian dispersion tau. The 256-replicate bridge reproduces all 12 PR119 endpoint means at 1e-10. Mass, no-feedback, no-intervention, deterministic and exact D decomposition gates passed. Initial D=.15, within-pair R=12/28, mechanical terminal D=.015. D=M*R+cross, where M is mean pair mass across worlds. D is a signed contrast in aggregate shares, not an individual vote probability.

| alpha | Prior posterior D contrast, low−high precision | Mean-evidence component | Dispersion component | Within-pair R contrast | Pair-mass M contrast |
|---:|---:|---:|---:|---:|---:|
| 0.5 | 0.001001 | 0.001683 | -0.000682 | -0.004519 | 0.014912 |
| 1 | 0.040081 | 0.043103 | -0.003022 | -0.021129 | 0.118655 |
| 1.5 | 0.292683 | 0.314908 | -0.022225 | 0.083426 | 0.352581 |

At alpha=1, aggregate D increases by 0.040081 under low-precision posterior mapping, while internal R decreases by 0.021129 and pair mass increases by 0.118655; do not infer within-pair amplification from aggregate D alone. At alpha=1.5, D increases 0.292683, arithmetic mean-evidence component +0.314908 and dispersion component −0.022225; R +0.083426 and M +0.352581. These are decomposition identities for chosen synthetic interventions, not empirically estimated mechanisms. Stronger private dispersion suppresses D and R at alpha=1.5 at every tested b; lowering b from 2 to 0 gives large positive D and R at tau=0/.5 but not uniformly across dispersion. The field is heterogeneous and focal-pair mass matters. Finite-horizon D grid: 13 amplify, 80 attenuate, 3 unresolved relative to initial D; classifications are conditional, not physical phases.

| Private dispersion | kappa | Uniform expected-drift local critical alpha | MC95 inverse interval |
|---:|---:|---:|---|
| 0 | 1.000000 | 1.000000 | [1.000000, 1.000000] |
| 0.5 | 0.968098 | 1.032953 | [1.032710, 1.033197] |
| 2 | 0.651776 | 1.534270 | [1.528751, 1.539830] |
| 6 | 0.264467 | 3.781189 | [3.742349, 3.820844] |

Uniform equal-strength mean-field drift has linear coefficient alpha*kappa−1 on zero-sum perturbations. This is a local expected-drift calculation, not an empirical critical value or global stability theorem; it does not directly describe the heterogeneous finite-grid field. No real participants, quotes, odds calibration, biological link from own history to private uncertainty, or causal market inference. PR118 remains separate empirical fixed-predictor score substitution, PR76 remains one synchronized real case. Net alpha cannot identify social imitation separately from price response. Future test: vary initial perturbation and field composition; match pair mass or use a two-stage aggregate/internal process, then test endogenous information arrival. Retain all signs and all conditional MC intervals, no real-world inference or betting advice. Existing frozen ledgers and main unchanged.

Replay status: REPLAY_VERIFIED. Full aggregate parity verified to absolute 0. Artifact metadata/upload digest agreement only.
