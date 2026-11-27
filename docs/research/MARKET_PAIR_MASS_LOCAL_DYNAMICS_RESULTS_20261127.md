# Local growth laws separate pair attention from internal polarization

27 November 2026 JST. [Protocol](MARKET_PAIR_MASS_LOCAL_DYNAMICS_PROTOCOL_20261127.md) · [complete aggregate](../evidence/market-pair-mass-local-dynamics-20261127.json) · [compact summary](../evidence/market-pair-mass-local-dynamics-summary-20261127.json) · [successful replay](https://github.com/zuizui0223/keiba/actions/runs/45957684519).

For a single world, D=M r. For infinitesimal mirrored perturbations around an exchange-symmetric reference, pair mass has zero first antisymmetric variation. With expected new-pair choice P, K=1−E[(pA−pB)^2]/P, current total T, batch B, and feedback alpha, reference mass M'=(TM+BP)/(T+B); local gd=(T+B alpha K P/M)/(T+B), gr=(TM+B alpha K P)/(TM+BP), and gd=(M'/M)gr. Aggregate grows iff alpha K P/M>1; internal grows iff alpha K>1. Finite two-world decomposition retains the cross term in PR121. First moments and response derivatives use identical permutation symmetrization; corrected pre-run derivative projection inconsistency before completing factorial results. Max one-step identity discrepancy 4.440892098500626e-16, checked derivative discrepancy 5.874767339264508e-11.

| Direction classification | Agreement / conclusive ABM cells |
|---|---:|
| Aggregate | 87/89 |
| Internal | 86/86 |
| Both | 80/82 |
| Opposite aggregate/internal | 15/15 |

All 96 cells use same PR121 small finite perturbation, 128 paired replications; 3,456 previous numeric means, SDs and interval endpoints reproduced. Not independent test data. ABM conclusive when MC95 interval entirely above/below 1, neutral tangent is not scored as correct for either conclusive direction.

| Field | Initial flow ratio P/M | Final flow ratio | Local terminal D gain | Local terminal R gain | ABM D gain | ABM R gain |
|---|---:|---:|---:|---:|---:|---:|
| equal | 1.000000 | 1.000000 | 3.014101 | 3.014101 | 2.863672 | 2.501502 |
| pair_advantaged | 2.001388 | 1.165428 | 17.301727 | 5.104126 | 11.472656 | 3.373372 |
| pair_disadvantaged | 0.399501 | 0.130484 | 0.236596 | 1.328125 | 0.229492 | 1.249535 |
| heterogeneous | 1.098521 | 0.102601 | 0.437188 | 1.609226 | 0.497461 | 1.637690 |

Above: alpha=1.5, tau=0. Heterogeneous field: 5 successive grow/grow steps and 55 shrink/grow steps; disadvantaged: all 60 shrink/grow. Opposite directions reflect the reference pair's attention flow, not separate social feedback coefficients. All 15 conclusive opposite-direction cells recovered; two aggregate-direction misses occur at alpha=4. Strong-feedback tangent amplitudes may far exceed bounded finite shares, so directional agreement is not amplitude accuracy. Maximum absolute D-gain difference between 1024 and 2048 nested Gaussian quadrature banks: 8.999183653466147, a numerical sensitivity not an empirical interval. No global or empirical critical alpha, no claim of an actual odds threshold or separately identified social/price feedback. No real participant data, real horse linkage or causal market claim. Next test finite nonlinear symmetric/antisymmetric dynamics, alternative pool compositions and common external information arrival; compare to stochastic ABM without overstating local approximations. Existing frozen ledgers/main unchanged. No wagering advice.

Replay: 20112 numeric fields, maximum absolute difference 8.185452315956354e-12; scaled tolerance 1e-8 (large tangent values may magnify tiny floating point differences), prior 3456 comparisons absolute tolerance 1e-10. Source 978b7388a26f220b24b416b04c1b9a049681aa46, run 45957684519, artifact 15179631640, sha256:d6ec7f63831410437faaeff69177af4855d2e903adbb2b3d48fb9269fc4347bc. ZIP bytes not independently verified.
