# Common evidence arrival changes evaluation differently from initial-popularity dependence

27 November 2026 JST. [Protocol](MARKET_PUBLIC_EVIDENCE_NONLINEAR_PROTOCOL_20261127.md) · [compact numerical summary](../evidence/market-public-evidence-nonlinear-summary-20261127.json) · [Actions run](https://github.com/zuizui0223/keiba/actions/runs/45970257501).

336 fixed cells, 128 paired common-shock replications each (43,008 pairs). Exact finite M/r update and two-world D decomposition checked per step. A is initially disfavored in the swapped world. Differential signal gives A +.3, B -.3 utility; symmetric attention gives both +.3. Neither is fitted to real information. Initial theta is a *public mean evidence* profile, held fixed; differential disclosure represents a hypothesized latent A advantage, not actual race results. Equal field refers to equal initial public evidence. All paths before intervention identical; same exposure prefix for pulse and persistent.

## Same ten exposed batches

At alpha=1.5, tau=0, initial D=.10: early minus late effect on initially disfavored A's signed within-pair balance, each measured against same-time untreated trajectory.

| Initial evidence field | Difference | Paired MC95 |
|---|---:|---|
| Equal | .064802 | [.055952,.073652] |
| Pair advantaged | .063336 | [.054132,.072541] |
| Pair disadvantaged | .020802 | [.015749,.025855] |
| Heterogeneous | .028833 | [.023658,.034008] |

Incoming composition contrast is also positive in those four cases (signed full-cohort A-minus-B arrivals: .023307, .087435, .007682, .020052). Equal exposure avoids comparing unequal pulse lengths but does not equalize the accumulated stock or state. Persistent early and late schedules have unequal exposure at the terminal horizon; not a pure timing contrast.

## Correction of the initially disfavored individual is not the same as erasing path dependence

Illustration: heterogeneous initial evidence, alpha=1.5, tau=0, d=4.

| Scenario | Terminal within-pair signed balance in reversed world | Change vs no news (MC95) | Change in aggregate two-world D |
|---|---:|---|---:|
| None | -.572239 | — | — |
| Early differential pulse | -.538691 | .033548 [.028687,.038409] | +.000742 |
| Late differential pulse | -.567253 | .004986 [.003462,.006511] | +.000107 |
| Early persistent differential | -.503867 | .068372 [.060658,.076086] | +.001792 |
| Late persistent differential | -.563634 | .008605 [.006160,.011050] | +.000186 |
| Early symmetric attention | -.582483 | -.010244 [-.014907,-.005580] | +.005259 |
| Late symmetric attention | -.573033 | -.000794 [-.002253,.000664] | +.000713 |

The favorable differential news moves A toward relative parity but none of 128 reversed worlds rank A above B in this example (ties half). Aggregate D can increase even while A's disadvantage decreases; do not infer initial-condition sensitivity from one world's A rank. For alpha=.8 in this same synthetic field, terminal A>B indicator (ties half) is .03125 without news, .11328 early pulse, .046875 late pulse, .51953 early persistent, .08203 late persistent. Persistent durations differ. No statement about an actual horse winning.

Across 48 base cells, terminal relative A balance has positive conditional MC95 news effects in 43 early differential pulse and 38 late differential pulse cells, no negative conclusive cells. Early symmetric attention increases aggregate D in 29/48 (none conclusively decreases), late symmetric attention in 25/48 (none conclusively decreases); direction counts for internal R are mixed. These are counts of chosen synthetic scenarios, not real frequency or independent statistical tests. Results distinguish evaluation correction, path dependence, and pair attention. At tau=0 deterministic finite mean recursion is not expectation of stochastic paths. No observed market, calibrated participants, price response or actual odds threshold. Net alpha cannot separately identify imitation and price response. Next use equal accumulated stock at intervention and no-news reference with randomized prior histories to separate clock/pool dilution from state-dependent responsiveness, then empirical source feasibility. No causal/genetic interpretation, betting advice, main merge, or edits to frozen ledgers.

Execution: original full-result transfer failed with HTTP/2 error before commit; unchanged settings rerun with compact committed summary and full Actions artifact. Replay status COMPACT_REPLAY_VERIFIED; 1152 parent values, 3691 compact values, maximum absolute difference 0. Full original JSON not independently compared, artifact ZIP not independently extracted.
