# 単勝率・複勝率：Plackett–Luce → ABM → PDE 検証

**Status: synthetic sensitivity only; not calibrated win/place forecasts, ecological H1/H2 evidence, or profitable-wager claims.** Updated 2026-10-23.

## Source boundary

Input: [archived Yahoo!中間オッズ](../../data/2026-10-18/ticket-odds-snapshot.json), received on 2026-10-18 around 12:31 JST: Kyoto 7/8/10/11/12, Tokyo 11/12 and Niigata 10/11, **nine races, 117 horse entries**. Odds are not certified final JRA quotes and the underlying per-market update times are unverified.

Horse numbers, names, displayed win/place quote ranges and some wide quotes are available. **Not available** in this data: stable longitudinal horse ID, verified historical sectionals, actual in-race positions, running style, fatigue, lane, GPS trajectories, past race records with a pre-race cutoff, verified actual riders/finishers. No historical horse-by-race physical parameter is fitted in this simulation.

## Market baseline: exact ranking probabilities

For horse i, set weight $w_i=1/o_i$, where $o_i$ is saved decimal win odds. The Plackett–Luce (PL) model gives $P(i\text{ wins})=w_i/\sum_j w_j$. Top-two and top-three probabilities are calculated by exact ordered, distinct-horse enumeration; **Monte Carlo is unnecessary for this PL baseline**. The total masses are 1, 2, 3, respectively.

Kyoto 11R: market-reference No. 8 win **56.159%**, Top-3 **93.196%**, from the 17-horse archived snapshot. The inverse-odds sum is **1.2719** (the overround): reciprocal odds by themselves are *not* a probability distribution. The separate displayed place-odds range is not a calibrated place likelihood; no positive expected return is inferred.

## Synthetic ABM with first-passage finish lines

[scripts/betting_abm_pde_sensitivity.py](../../scripts/betting_abm_pde_sensitivity.py) draws each fictional agent's log(inverse-odds) + independent Gumbel utility and an independent cosine-shaped pace term. Its hypothetical instantaneous speed in m/s is

$$
v_{it}=16.8 + 0.10 U_i + A_i\cos(2\pi t/T)
-c\,e^{-g_{it}/6}\mathbf1(0<g_{it}<6).
$$

Here, $g_{it}$ is the nearest **still-running** agent's gap in metres ahead on a **one-dimensional** track. Invented crowding penalties $c=0,\;0.08,\;0.20$ m/s are sensitivity scenarios, not estimated effects. The model linearly interpolates actual first crossing times at the finish, rather than ranking progress at a fixed time (a weakness in the original scratch demo).

Three crowding scenarios reuse the **same Gumbel and pace draws for each synthetic race**. Every horse gets win/top-two/top-three simulated probability and paired strong-minus-zero crowding deltas with Monte Carlo confidence intervals. These intervals describe sampling noise from these artificial replicates only. There is no uncertainty propagation for true horse ability, source version, assumptions, fitted physical parameters, weather or race selection.

### Example: 10,000 synthetic Kyoto 11R repetitions

| Conditional model | No. 8 win | No. 8 Top 3 |
| --- | ---: | ---: |
| Exact saved-market PL benchmark | 56.159% | 93.196% |
| First-passage ABM, no crowding | 55.55% | 93.30% |
| ABM, weak crowding | 55.31% | 93.13% |
| ABM, strong crowding | 54.02% | 92.31% |

Strong-minus-none win delta **−1.53 percentage points** (paired Monte Carlo-noise 95% interval **−2.13 to −0.93 pp**). This demonstrates only that an invented interaction can change the numerical outcome distribution. It is **not evidence** that the crowding effect exists at this strength in real races.

At a 50% probability, the usual single-probability Monte Carlo 95% half-width is approximately **0.98 pp with 10,000 repetitions**, or **0.31 pp with 100,000**. Paired contrasts must use the actual within-run paired differences instead. When exact PL probabilities are used, no such Monte Carlo error exists.

## PDE: mathematical smoke test, not a probability shortcut

The same file independently solves a conservative finite-volume one-dimensional Fokker–Planck / advection–diffusion equation:

$$
\partial_t\rho=-v\partial_x\rho+D\partial_{xx}\rho.
$$

A Gaussian initial position density (mean 0 m, SD 10 m), with constant drift 0.5 m/s and diffusion 3 m²/s over 40 s, has an analytical terminal Normal(mean 20 m, variance 340 m²) solution. The numerical solver is checked for total mass near 1, nonnegative density and closeness to this analytical reference. This is **not yet coupled to the ABM** and does not provide joint order-of-finish or win/top-three probabilities. Such a macro-to-micro closure would need separate empirical justification.

## Reproduce and check

From the repo root, with Python 3.12 and numpy 1.26 or later, run:

    python -m unittest discover -s tests -p 'test_betting_abm_pde_sensitivity.py' -v
    python scripts/betting_abm_pde_sensitivity.py --venue 京都 --race 11 --runs 10000 --seed 20261023 --output tmp/shuka-abm
    python scripts/betting_abm_pde_sensitivity.py --all-races --runs 1000 --output tmp/nine-race-abm

Outputs: summary.json (source/time caveats and the PDE diagnostic) plus horses.csv (all horses and synthetic scenario uncertainty). The nine races are processed from the saved source; this workflow changes no betting decisions, odds, mainline freeze manifests or v3.1 holdout ledgers.

## The empirical next step, not yet satisfied

Before interpreting ABM parameters as biology or improving prediction: obtain a legally usable longitudinal horse-ID × race-ID panel with pre-race sectional/pace history, course, going, class, actual rider, verified starters and finish/withdrawal status. Estimate style and crowding on *past* races only, and compare on chronologically later races against (a) a frozen market-only baseline and (b) a horse-history-only baseline using win/Top3 Brier scores, log loss and calibration. The current frozen v3.1 holdout is a separate candidate-generation study; **this exploratory synthetic analysis must not enter its formal 20-race ledger**.


## Additional 2026-10-23 result — official postrace evaluation, nine archived races

**Observed outcomes, not synthetic:** The first three finishers for the nine pre-existing saved-odds races were manually verified against individual JRA official result pages, and minimal per-race top-three numbers and source URLs are pinned in [postrace source ledger](../evidence/betting-20261018-official-top3-postrace.json). **This is deliberately a different input than pre-race betting snapshots; the outcome file must only be used after generating the probability predictions.** This work is retrospective and is not appended to the v3.1 holdout.

| Race | JRA actual Top3 horse numbers, in order | Top-three win-odds favorites appearing in actual Top3 |
| --- | --- | ---: |
| 京都7R | 7,8,3 | 2/3 |
| 京都8R | 5,2,3 | 3/3 |
| 京都10R | 8,2,4 | 1/3 |
| 京都11R 秋華賞 | 8,1,13 | 2/3 |
| 京都12R | 3,8,10 | 1/3 |
| 東京11R | 9,11,6 | 3/3 |
| 東京12R | 14,15,13 | 2/3 |
| 新潟10R | 16,15,9 | 1/3 |
| 新潟11R | 3,1,5 | 2/3 |

Total: 9 races, 117 archived runners, top-three market-ranking inclusion **17 / 27 = 62.96%**. Winner ranked joint top in archived win quotes **4/9** (Tokyo11R has a tied top quote); *this is not the accuracy of a new calibrated win model*.

New executable [postrace scoring audit](../../scripts/betting_abm_pde_postrace_audit.py) evaluates independently saved odds versus JRA podiums, using:

- Categorical winner log loss: \(-\log p_{\mathrm{winner}}\), mean of 9 races.
- Top-three per-horse binary Brier score, averaging within each race then averaging 9 races. Top-three inclusion events are dependent; **117 horse entries are not 117 independent races**.
- Binary Top3 log loss as a secondary descriptive metric.
- Identical score definitions for: uniform \(1/n\) win and \(3/n\) Top3, exact market-only PL and each synthetic ABM scenario. No scenario may use actual winners as features.

| Locked market-only descriptive score | Uniform entry baseline | Pre-race archived win odds → PL |
| --- | ---: | ---: |
| Mean winner log loss (lower better) | 2.5370 | **1.9119** |
| Mean Top3 binary Brier (lower better) | 0.1813 | **0.1364** |
| Mean Top3 binary log loss (lower better) | 0.5469 | **0.4204** |

These nine races show the market-only reference beat a naïve equal-probability baseline on that day's observed outcomes. This is **not an estimate of future generalization or a statistical superiority finding**. More importantly, no genuine *empirically fitted* physical/social parameters exist yet to show that ABM beats the market. Any apparent difference among the synthetic crowding scenarios is model-specification sensitivity and cannot justify betting.

Reproduce the fixed source audit independently of ABM Monte Carlo:

    python scripts/betting_abm_pde_postrace_audit.py --market-only --output tmp/abm-postrace-market.json

Run the exact same outcome metrics on the predeclared synthetic mechanisms, without refitting them:

    python scripts/betting_abm_pde_postrace_audit.py --runs 10000 --seed 20261023 --output tmp/abm-postrace-allmodels.json

### Actual toy ABM ↔ PDE connection — not the crowded horse ABM

A [new particle-to-density bridge](../../scripts/betting_abm_pde_particle_bridge.py) compares \(N=20{,}000\) independent stochastic agents \(dX=v\,dt+\sqrt{2D}\,dW\) with a **finite-volume PDE using the exact same drift and diffusivity**:

\[
\partial_t\rho=-v\partial_x\rho+D\partial_{xx}\rho.
\]

It checks terminal means, empirical-versus-numerical cumulative densities (KS), total mass, variance and agreement with the analytical Gaussian solution. This is a genuine **toy stochastic-particle/Fokker–Planck numerical correspondence**, not a claim that the full horse-level, crowded, finite-agent race is solved by that PDE. A separate **nonlocal nonlinear mean-field closure** would be needed to model density-dependent overtaking/crowding. At \(17\) horses, ABM is still the primary individual-ranking model; PDE can only serve as a theoretically justified auxiliary model if validated.

    python scripts/betting_abm_pde_particle_bridge.py --particles 20000 --seed 20261023

**Audit gate:** All new scripts and their individual tests live on Draft PR #9, without changing the mainline frozen v3.1 source, thresholds or the formal evaluation ledger.


### Completed 10,000-draw × nine-race same-outcome score (2026-10-23 CI)

Reproducible run: [GitHub Actions #39863368081](https://github.com/zuizui0223/keiba/actions/runs/39863368081). Each of the three ABM conditions was run **10,000 times per race** with shared random inputs, then judged on the identical **official JRA** outcomes. No actual outcome entered the generator. The real outcomes are not 10,000 repetitions: they are **nine actual races**.

| Frozen condition | Winner log loss (lower better) | Top3 binary Brier (lower better) |
| --- | ---: | ---: |
| Uniform probability | 2.5370 | 0.181255 |
| Market-only exact PL | 1.9119 | 0.136433 |
| Fictional ABM: no crowding | 1.8976 | 0.136320 |
| Fictional ABM: weak crowding | 1.9001 | 0.136238 |
| Fictional ABM: strong crowding | 1.9113 | 0.136601 |

The *no crowding* model's winner-log-loss difference from PL is only **−0.0143**, the *weak crowding* Top3-Brier difference is only **−0.000195**, and the strong-crowding Top3 Brier **worsens** by **+0.000167**. These small retrospective numerical differences do **not** identify actual crowding or forecast skill. ABM is not independently parameter-fitted or prospectively tested; changes are due to hypothetical pace/crowding and finite-simulation noise. Selecting the apparent best row based on this table and then declaring a betting model would be outcome-guided tuning.

The corresponding toy Brownian ABM–PDE check from the same CI used **20,000 particles × 400 steps** and obtained PDE mass = 1.0, ABM mean = 6.42745 m, PDE mean = 6.40000 m, and maximum CDF discrepancy = 0.006988. This establishes numerical agreement for an uncoupled stochastic process, **not** a nonlinear finite-horse competition PDE.

**Decision: keep ABM/PDE as synthetic exploratory models; retain market PL as the unmodified empirical benchmark.** Next is prospective, race-date-blocked calibration on licensed real pre-race horse/race/sectional features and complete official outcomes.
