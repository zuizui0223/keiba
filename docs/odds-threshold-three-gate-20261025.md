# オッズの3階層閾値：初期人気・変化速度・予測情報

**2026-10-25 / Source-locked historical analysis, not a prospective discovery.** This is a new, optional exploratory branch based on Draft PR #10. The precommitted 2026 Kikuka Sho M0/M1/M2 (`9ef880b4…fe857`, GitHub server receipt 2026-10-24 17:07 JST), the v3.1 20-race ledger, Draft PR #9 horse ABM/PDE, and Draft PR #12 cross-pool shape analysis are **not modified**. New M3 has **no status as a sealed Kikuka forecast**. No post-start or final market quote is used as a forecast feature.

## Why one 10x cutoff is not enough

Three distinct hypotheses need three different measurements:

1. **Popularity gate** `tau_o`: an *earliest saved intermediate* win quote (not a certified opening quote) is at least 10.0x; this is the original M2 feature rule. Also report 5, 20, 50x purely as outcome-free sensitivity counts.
2. **Market-rate gate** `tau_v`: the absolute *normalized inverse-quote support* log change per elapsed clock hour is at least 0.10 log units/hour. This is **an average over the two saved snapshots**, not a local instantaneous rate, changepoint, or true flow of bets. Also count 0.05 and 0.20 as prespecified diagnostic cutoffs.
3. **Information/predictability gate** `tau_I`: a **pre-outcome** KL separation of at least 0.005 nats between M0 and the alternative, measured race-wise. This is only a stratum for prospective scoring. A high KL itself does not establish new information, a probability improvement, or a market phase transition; **improvement must subsequently be established with strictly future proper scores**.

Let `q0_i`, `qT_i` be each saved full-field win-odds vector's normalized reciprocal, `d_i=log(qT_i/q0_i)`, and `v_i=abs(d_i)/elapsed_hours`. The candidate ranking weight is

```
M0: w_i = qT_i
M1: w_i = qT_i * exp(0.25*d_i)
M2: w_i = qT_i * exp(0.25*d_i*I(initial_odds_i >= 10))
M3: w_i = qT_i * exp(0.25*d_i*I(initial_odds_i >= 10)*I(v_i >= 0.10))
```

Normalize `w` and enumerate Plackett–Luce ordered triples exactly; win probabilities sum to 1, per-horse Top3 probabilities sum to 3. The 0.25, 10.0, 0.10, and 0.005 values are **fixed exploratory assumptions**, not data-estimated optima. In particular, two observations cannot tell whether a true within-path jump occurred. **Do not reinterpret M3 as an improved M2, a fitted physical ABM, or a Kikuka precommitment.**

## Independent actual source check (historical, October 12 and 18)

All numbers below were recomputed with the source-locked original odds and independent JRA postrace top-three labels. Predictions were calculated before opening outcomes; both source-file SHA and race-start clock are guarded. The six races contain 84 horse–race rows but **only six racing outcomes and two dates**. Five same-day comparisons span 51–69 minutes, while the Shuka Sho comparison spans ~21.67 hours and changes source/time meaning: pooling these as if they were uniform observations is invalid.

| Policy | Historical mean winner log loss (six races) | Mean per-horse Top3 Brier | Races beating M0 on winner score |
|---|---:|---:|---:|
| M0 latest quote only | 1.696959 | 0.121811 | — |
| M1 smooth all horses | 1.696682 | 0.121502 | 3/6 |
| M2 old 10x gate | 1.698632 | 0.122020 | 3/6 |
| **M3 new rate + 10x gate** | **1.697686** | **0.121960** | **1/6** |

M3–M0 winner-log-loss difference = **+0.000727** (worse) with six races equally weighted; the **two meeting dates equally weighted** difference = **+0.000436** (worse). This does **not** prove that the effect is zero, either: with only two days, no independent prospective calibration/selection or meaningful confidence interval is available.

The preregistered gate's 10x *initial* price cut includes **55/84 horse entries** without the speed constraint, but only **5/84** pass **both** the 10x and 0.10/h filters in these six races (two Kyoto 8R, two Kyoto 9R, one Kyoto 10R; none Kyoto 11/12R or Shuka Sho). Among all 84 entries regardless of odds threshold, **11/84** have speed >= 0.10/h. None of the six real races has **M1 vs M0 win KL >= 0.005 nats**. These are overlapping horse rows, not independent threshold trial replicates.

The early 10x gate and the market-velocity gate depend on different information; a high early price is not evidence of a speed regime, and a large rate is not evidence of more information about the winner. **Current result: HOLD for all three empirical threshold hypotheses.**

## Why Kyoto 8R is a useful, but not sufficient, dynamic contrast

The saved 11-horse win path has *three* full prestart publisher timestamps: 12:21, 13:26, 13:44 on October 12. Its mean absolute log-relative-support change rate across horses was **0.0959/h** in the first 65-minute interval, versus **0.6328/h** in the last 18-minute interval. The count above 0.10/h rose from **5/11** to **11/11**. After observing the JRA outcome, the winner's baseline PL log loss at the three times was 1.7780 → 1.8199 → 1.9921 (**worse**, not better). Distinct quote intervals and 1 race cannot identify a changepoint or an endogenous informational cascade.

## ABM, PDE, and other PR boundaries

- **Market-voter ABM (PR #10)**: can simulate herding/new-information arrivals generating threshold-shaped *quote dynamics*. The current parameters have **not** been measured from actual bettor flow. An early-vs-latest correlation can arise mechanically from cumulative tote accounting even under no herding.
- **Market M0–M3**: produce distributions over winning horse and top-three sets, using market price proxies alone. Their proper future labels are actual JRA results; market-quote fit, price movement, price correlation, or WIDE TV are **not substitutes** for those outcome scores.
- **Horse-movement ABM (PR #9)**: first-passage individual agents can accept M3's ranking weights as an *explicitly hypothetical prior* if separated from horse-ability calibration. Actual crowding, pace, jockey and lane coefficients remain unidentified. Do not call a sensitivity run a validated horse-performance forecast.
- **Density PDE (PR #9)**: currently a linear independent Brownian particle ↔ Fokker–Planck numerical agreement, **not** an empirically fitted nonlinear interacting horse-traffic PDE. Valid PDE density mass does not validate M3 or a race-winning probability.
- **Cross-pool prices (PR #12)**: a pair-index discrepancy can motivate another covariate but pools can have nonsynchronous timestamps, so it does not identify `tau_I` without future JRA proper scoring.

## Strict next empirical test

Use the existing `odds_local_timeseries_preflight.py` source-clock/rights gate and `odds_prequential_cohort.py` external server SHA proof. For each future eligible race, acquire **three or more full-field publisher-timestamped win quote snapshots** with at least one forecast cutoff >=10 minutes before post. Treat missing or mismatched clocks as HOLD; keep quoted update time distinct from web retrieval time. Register M0/M1/M2/M3 coefficients and candidate popularity/rate thresholds **before** target starts, then score on separate future racing dates. Compare future winner log loss, Top3 Brier, market quote-shuffle controls and M0↔M3 KL strata; group uncertainty by meeting date, not by the number of overlapping horse/pair entries. The 60-race/8-date software gate is a **minimum feasibility rule only**, not a statistical-power guarantee.

Keep **the existing presealed Kikuka M0 vs M1 outcome contrast untouched**, score it independently once officially available, and never add M3 to that precommitted comparison. Never interpret a strategy chosen after inspecting these six historic outcomes as prospective or as a positive expected-return bet.

### Reproduce (Draft PR based on #10; stdlib)

```
python -m unittest discover -s tests -p 'test_odds_threshold_regime_bridge.py' -v
python scripts/odds_threshold_regime_bridge.py --prestart-only --output tmp/odds-threshold-prestart.json
python scripts/odds_threshold_regime_bridge.py --output tmp/odds-threshold-historical.json
```

Outputs contain only aggregate odds-gate counts, market separation and historical score metrics, never full price panels, betting stakes, per-horse model probabilities or payoffs.
