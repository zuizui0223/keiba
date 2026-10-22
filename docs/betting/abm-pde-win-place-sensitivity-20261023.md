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
