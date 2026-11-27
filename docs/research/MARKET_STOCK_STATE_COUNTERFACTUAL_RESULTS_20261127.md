# Stock–state factorial: early-information advantage is not only accumulated stock

27 November 2026 JST. [Protocol](MARKET_STOCK_STATE_COUNTERFACTUAL_PROTOCOL_20261127.md) · [committed compact results](../evidence/market-stock-state-counterfactual-summary-20261127.json) · [Actions run](https://github.com/zuizui0223/keiba/actions/runs/45971343651).

96 result rows (48 base conditions × differential and symmetric news), 128 history replications each. Preserve PR123 untreated dynamics and both mirrored worlds; use pre-news snapshots at batch 10 (E, stock 200) and batch 40 (L, stock 560). Cross composition E/L and stock S/L with exactly normalized fractional historical count weights. New arrivals 120 in ten batches, common fresh independent pseudo-random stream. Each treated arm compared to its own untreated arm. All 240 PR123 no-news terminal means reproduced. All exact finite-step identities and first-arrival invariance at fixed shares across stocks passed.

## Main factorial result

Selected continuity with PR123: alpha=1.5, tau=0, d=4. Effect on initially disfavored A's signed relative support balance, treated minus untreated. Total = ES−LL, state half[(ES−LS)+(EL−LL)], stock half[(ES−EL)+(LS−LL)]. These are symmetric arithmetic contributions of two model interventions, not observed causal effects.

| Field | ES | EL | LS | LL | Total | Stock | State |
|---|---:|---:|---:|---:|---:|---:|---:|
| Equal | .083030 | .035330 | .048941 | .021655 | .061374 | .037493 | .023882 |
| Pair advantaged | .080193 | .037120 | .025564 | .011763 | .068430 | .028437 | .039993 |
| Pair disadvantaged | .021361 | .011657 | .014200 | .006398 | .014963 | .008753 | .006210 |
| Heterogeneous | .027130 | .013184 | .010965 | .005375 | .021755 | .009768 | .011987 |

| Field | Stock component conditional MC95 | State component conditional MC95 | Interaction conditional MC95 |
|---|---|---|---|
| Equal | [.032170,.042815] | [.017758,.030006] | [.013271,.027555] |
| Pair advantaged | [.023324,.033550] | [.033668,.046319] | [.022967,.035579] |
| Pair disadvantaged | [.005257,.012249] | [.002100,.010320] | [-.003955,.007759] |
| Heterogeneous | [.007184,.012351] | [.008228,.015746] | [.002692,.014020] |

Both state and stock contribute positively in these four scenarios; in heterogeneous field state is 55.1% of the point contrast (not a universal fraction or inferential partition). Conditional MC95 counts across all 48 base cells for differential signal and signed relative support balance: total positive 43, negative 0, unresolved 5; stock 39/0/9; state 27/1/20; interaction 19/0/29. State effects at same small stock 26/1/21, same large stock 27/1/20. Do not suppress negative or unresolved cases. For new-arrival signed full-cohort A-minus-B response, state 27 positive, 6 negative, 15 unresolved; stock 24 positive, 6 negative, 18 unresolved. Thus state and stock contributions differ by metric; first batch exact invariance at fixed normalized state does not imply subsequent flow invariance. Symmetric attention intervention total early-small vs late-large D effect positive in 34/48, negative 0, unresolved 14; stock component 31/0/17, state 22/1/25.

The model is Markov in support counts plus current exogenous inputs; absolute clock has no separate effect by construction. State includes pair total attention, internal bias, and six other alternatives; stock effect includes the changing marginal weight of new arrivals and subsequent feedback, not mere algebraic dilution. Fractional rescaling is a model intervention. Fresh post shocks change estimand relative to original PR123 calendar-continuation simulation; do not equate point magnitudes. No empirical inference, causal real-market interpretation, actual odds, wagering, or changes to frozen ledgers. Next isolate state into pair mass, internal imbalance, and outside composition on a common stock; then consider data feasibility for actual synchronized observed market trajectories.

Replay status: COMPACT_REPLAY_VERIFIED. CI verified 6934 compact numerical values, maximum absolute discrepancy 0. Full aggregate generated as Actions artifact, not full original JSON comparison; ZIP bytes not independently verified. No main merge.
