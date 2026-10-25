# Independent past-race horse form → physical ABM → bettor ABM → market, with horse-identity placebo

**2026-10-25 | Nested Draft, retrospective-source reconstruction only.**
Parent: [PR #14](https://github.com/zuizui0223/keiba/pull/14). It does not edit PR #10's externally presealed Kikka forecast SHA, PR #9's horse model files, PR #12 or frozen v3.1 / 20-race ledger.

## Why this changes the integrated graph

PR #14 seeded *both* its physical horse ABMs and its initial voter market from the same earliest intermediate WIN quotes, so the horse ensemble could not supply a genuinely separately sourced view of horses. We now permit an **external horse prior** to enter both horse motion models, while the bettor market's initial q0 remains the **actual earlier archived WIN quote**. Both derived agents therefore react to a common history-informed horse scenario that is not simply a re-labeled latest odds quote.

Three kinds of information are kept distinct:

1. **Horse history input** — purely dated past JRA race results: previous finish rank, date, race distance and turf/dirt/obstacle. Current market odds, prior market popularity, present official podium and current payout are excluded from horse-form features by an explicit whitelist.
2. **Physical horse model** — frozen PR #9 1D first passage ABM + the stochastic Brownian-crowding variant. Both use history-derived *hypothetical latent ranking priors* if supplied. Their running speed and crowding parameters still come from invented scenarios; past ranking is **not observed velocity, GPS or a calibrated biological ability**.
3. **Social market model** — begins from the preserved earliest **real quoted-market index q0**, receives physical ensemble output as a voter information signal, applies five originally fixed vote rules, updates hypothetical cumulative voting counts and produces coherent WIN, Top3, WIDE, exacta, trio and trifecta event probabilities from an ordered finish law. Market odds do not physically push horses unless evidence for such a pathway is supplied.

The coupled equation used is therefore:

\[
H_i(t<t_0)\;\to\; A_i^{\mathrm{hypothetical}}\;\to\; P_{\mathrm{horse}}\;\to\;
S_{\mathrm{voters}};\qquad(q_0,S_{\mathrm{voters}})\to q_t\to P_{\mathrm{finish}}.
\]

The same initial market q0 is not multiplied in again as separate “horse evidence” after it has already entered the voter state.

## Source audit and temporal limitations

- **2026-10-12 Kyoto 8–12R:** 67 horse–race rows, 66 have at least one historical prior start; one horse has none and gets the neutral shrinkage prior. These structured detailed JRA career histories were **retrieved/normalized after October 12**, as the archive itself explicitly records. All source rows have dates strictly prior to the target, but that cannot verify that this detailed reconstruction was actually available at the prediction timestamp.
- **2026-10-18 秋華賞:** all 17 history rows linked by a unique, *official-draw* name-to-horse-number crosswalk. Pre-draw archive includes an explicit warning not to confuse entry order with official start number. No independently authenticated historical-profile receipt is supplied for the as-of scoring point.
- **84 horse entries ≠ 84 independent outcomes.** Six real races on only two dates are all that are scored. All five Kyoto histories' field sizes are present, but the Shuka Sho history lacks those fields. We refuse to silently make up field sizes or claim an identical past finish percentile; the common fixed diagnostic transforms historical finish rank using \(\exp[-(\text{finish}-1)/3]\).
- SHA-locked source bytes are required and record dates on/after each target are hard-rejected. Horse names and numbers must match across historical rosters and sealed pre-race cards. No contemporary target outcome is loaded before all model forecasts and identity-placebo forecasts have been constructed.
- Source authorizations, independent pre-race availability, bettor ballots and actual horse GPS are **HOLD**. The script **refuses** a \`--prestart-only\` option or an \`historical_source_asof_certified=True\` override for these archives. A reconstruction is never a genuinely sealed future forecast.

## Source feature and negative control, fixed without target labels

Historical (unfitted) horse-form scores for past starts \(j\) of horse \(i\):

\[
w_{ij} = \exp(-\mathrm{age}_{ij}/200)\,
         \exp(-|d_{ij}-d_0|/700)\,
         \begin{cases}1,&\text{same surface}\\0.30,&\text{other surface}\end{cases}
\]

\[
h_i = \frac{\sum_j w_{ij}\,\exp[-(\mathrm{finish}_{ij}-1)/3]}
           {2+\sum_j w_{ij}},
\qquad
p_i^\mathrm{history} = \mathrm{softmax}(2h_i).
\]

These arbitrary, disclosed numbers define a **diagnostic sensitivity model**, not a fitted winning probability. Past performance rankings can be heavily affected by field strength/class; no causal performance claims are attached.

All six real races are run under four predeclared upstream physical-prior arms with matched horse and voter random seeds:

| Arm | Horse-model initial distribution | Research function |
| --- | --- | --- |
| Existing market proxy | original early WIN-based q0 | PR #14 reference, exactly compatible |
| History only | past-only \(p^\mathrm{history}\) | independent *source* of form information, but not statistically independent of market opinion |
| Cyclically shifted history | deterministic one-horse number shift within the same race | negative control destroying history-to-entrant identity while preserving all history scores |
| 80% early market / 20% history | normalized \(q_0^{0.8}(p^\mathrm{history})^{0.2}\) | fixed model mixing; **not** a learned optimal coefficient |

The target score is not used to select the winning arm. **Even if the history arm exceeds the identity-shuffled placebo on the same six races, that is not proof of forward generalization**, because the source retrieval is postrace and model assumptions have not been trained/held out on new race dates.

## Reproduce

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests -p 'test_keiba_coupled_history_falsification.py' -v
    python scripts/keiba_coupled_history_falsification.py --draws 120 --output tmp/coupled-history-identity-falsification.json

The output is an aggregate audit. It reports the six-race equal-weight WIN Log loss, Top3 Brier and market-index distance for each prior arm, along with the identity-placebo difference and historical source HOLDs. Original restricted odds rows, original detailed per-horse histories and individual betting simulations are not redistributed in new outputs.

**Next empirical requirement:** obtain independently timestamped, source-permitted full past-horse histories (preferably past GPS sectionals and documented rider/going context) **before the real target prediction cutoff**, freeze the physically and socially coupled model without seeing the outcome, and score across genuinely distinct subsequent race dates. The Racing Queensland first-GPS early-section results from the ecology track cannot simply be transplanted into JRA winners; their response is a different physical interval with different horses and observation selection.


## Real archived historical reconstruction: fixed-seed preliminary results

[GitHub Actions reproducible run #40163483271](https://github.com/zuizui0223/keiba/actions/runs/40163483271) completed the numerical and source-locked checks on six archived races / two distinct race dates / 84 horse-race entries. The source reconstruction and all seven assumptions above remain **strictly retrospective**, not independently as-of verified. Each horse model used 120 Monte Carlo draws and fixed seed 20261025 (the same count across arms).

| Physical horse-model upstream prior | Information-voter path: winner LL ↓ | Mixed-voter path: winner LL ↓ | Threshold-mixed path: winner LL ↓ | Information-voter Top3 Brier ↓ |
|---|---:|---:|---:|---:|
| Saved early WIN quote | 1.703731 | 1.670977 | **1.652295** | 0.122181 |
| Past-race form only | 1.807772 | 1.702158 | 1.691369 | 0.128548 |
| Fixed rotated horse identity (placebo) | 1.852078 | 1.740307 | 1.705576 | 0.131588 |
| 80% early WIN + 20% past form | 1.715458 | 1.675384 | 1.654930 | 0.123259 |
| Actual later WIN quote M0 (single benchmark) | 1.696959 | 1.696959 | 1.696959 | 0.121811 |

The historical identity-shuffle contrast in the *information-voter* path is **−0.044307 winner log-loss** (history correctly mapped minus one deterministic cyclic permutation), and the analogous Top3 Brier for correctly mapped history is 0.128548 vs 0.131588. This is a useful **software/identity negative-control response**, not a statistical significance test or evidence that past form adds information beyond the real contemporary market.

More revealing: adding historical features at fixed 20% to market-informed horse agents did **not** improve the frozen market-proxy version of the same integrated voting rule. The threshold-mixed winner log loss moved from 1.652295 to 1.654930; information-voter 1.703731 to 1.715458. True incremental forecasting value conditional on the observed market is thus **not established**. The market-based model may already encode much of the historical race performance, and the form transform is uncalibrated.

For the INFORMATION-only voter mechanism, the actual later-quote TV distance was **4.072 pp** from the original market horse prior, **8.117 pp** from the form-only horse prior, and **9.441 pp** after identity shuffling. For the threshold-mixed voter mechanism, TV distance was **8.111 pp** from the original market prior versus **4.482 pp** from form only. Thus *predicting eventual podiums* and *reproducing market price changes* can select different mechanisms—this contradiction remains, not to be hidden by post-hoc selection.

The elapsed time differs strongly across cohorts (Kyoto 8–12R ~51–69 minutes, 秋華賞 ~21.7 hours with heterogeneous sources). A **date-equal** decomposition is added to the executable audit, rather than assuming 5+1 independent and exchangeable forecasts. With only two meeting dates, its sign is descriptive and no bootstrap confidence interval is promoted.

No target outcome labels are consumed by either the horse-history transform or the coupled ABMs; JRA results are opened only for later retrospective evaluation. All previous externally presealed models and formal v3.1 ledger remain unchanged.
