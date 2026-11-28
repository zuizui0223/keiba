# Attention, internal imbalance and outside composition can separately govern information response

28 November 2026 JST. [Protocol](MARKET_STATE_COMPONENTS_COUNTERFACTUAL_PROTOCOL_20261128.md) · [committed compact results](../evidence/market-state-components-counterfactual-summary-20261128.json) · [Actions run](https://github.com/zuizui0223/keiba/actions/runs/46109856955).

96 result rows (48 base cells × two information types), 128 history replications, same PR124 histories and post-intervention random stream. Recombine early/late M (pair mass), r (signed within-pair balance), C (conditional shares of six alternatives) in each mirrored world, all eight masks at fixed stock 200 and 560. Each treated state compared to its untreated counterpart. Shapley average over six orders at each stock; average allocations across stocks. Positive simplex, component preservation, exact decomposition and 5,760 previous PR124 means/MC95 endpoints passed in original calculation.

## Differential signal: early-state correction advantage

Selected continuity panel alpha=1.5, tau=0, initial d=4. Outcome is news-induced change in reversed world's signed within-pair balance. Values are early-minus-late contributions to response, averaged over fixed stocks, not the population's average support or an empirical effect.

| Field | Total state | Pair mass M | Internal r | Outside C |
|---|---:|---:|---:|---:|
| Equal | .023882 | -.002438 | .024750 | .001570 |
| Pair advantaged | .039993 | .008014 | .032145 | -.000166 |
| Pair disadvantaged | .006210 | .004459 | .000491 | .001260 |
| Heterogeneous | .011987 | .006033 | .000383 | .005572 |

| Field | M conditional MC95 | r conditional MC95 | C conditional MC95 |
|---|---|---|---|
| Equal | [-.005036,.000161] | [.020016,.029484] | [-.000587,.003726] |
| Pair advantaged | [.006149,.009879] | [.026490,.037800] | [-.000561,.000229] |
| Pair disadvantaged | [.000884,.008034] | [-.000809,.001791] | [-.000845,.003366] |
| Heterogeneous | [.003738,.008328] | [-.000897,.001662] | [.003253,.007890] |

In heterogeneous field, M and C account for approximately 97% of the arithmetic point contrast (.011605/.011987); r interval spans zero. Both fixed-stock subanalyses preserve this direction: small stock M .008619 [.005055,.012184], C .007350 [.003337,.011362], r .000196 [-.002026,.002419]; large stock M .003447 [.001883,.005010], C .003794 [.002486,.005102], r .000569 [-.000342,.001480]. In equal and advantaged field r contribution is positive and larger than M or C in point magnitude, not a test of pairwise contribution dominance. Advantaged field has positive M×r baseline-anchored interaction .007601 [.004774,.010428].

Across all 48 differential conditions, total state positive/negative/unresolved 27/1/20; M 23/2/23; r 15/0/33; C 14/0/34. For new-arrival signed full-cohort response, M 26/7/15, r 8/0/40, C 13/0/35. For symmetric signal and aggregate D, total 22/1/25, M 24/0/24, r 9/10/29, C 12/2/34. These are chosen-cell classifications, not independent tests or real prevalence. All adverse and uncertain cases retained. In heterogeneous symmetric attention, M .003086 [.002653,.003519], C .001774 [.001417,.002132] and r -.000306 [-.000467,-.000146] contribute to aggregate D, illustrating contrasting component signs. Do not conflate relative correction and two-world sensitivity.

The model is Markov in count state; three coordinates exhaust normalized share state. Shapley allocations are symmetric accounting across artificial hybrid states, not unique independent causal mechanisms, and hybrid fractional states may be historically unreachable. Fixed fields and shared histories do not provide empirical replication; conditional MC intervals not multiplicity-adjusted. No actual odds, participants, or real-world calibration. Next stop expanding the same simulation grid and audit empirical availability of timestamped race-level market trajectories and identity linkage; need a measurement model separating support proxies from true pool shares, and a preregistered empirical state-response test with externally timed information. Existing frozen ledgers/main unchanged.

Replay status COMPACT_REPLAY_VERIFIED. CI verified 6938 compact numerical fields, maximum absolute discrepancy 0. Full aggregate generated as Actions artifact, not full original JSON comparison; ZIP bytes not independently verified. No main merge.
