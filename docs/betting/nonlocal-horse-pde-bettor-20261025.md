# Nonlocal crowding connects horse ABM, finite-horse PDE and bettor ABM

**2026-10-25. Draft-only mechanistic sensitivity; NO empirically fitted JRA horse position dynamics, ballot flows, predictive edge, or profitable wagering.** Parent: [PR #16](https://github.com/zuizui0223/keiba/pull/16). Horse form from original JRA older results was reconstructed after the target race for the five Oct 12 races, so these are NOT authentic forward independent horse signals. It remains invalid to transplant the unrelated Racing Queensland early-GPS behavioral repeatability cohort onto these JRA horse IDs.

## Scientific question: a horse-level mechanism, not an independent model juxtaposition

> If individual horse interactions affect top-three outcomes, **through which information-dependent voting rules** can the effect propagate into observed market prices? Is the corresponding horse-group PDE closure close to the actual finite-agent process in a *specified toy law*, or does the factorization approximation visibly fail?

Both horse motion and population density now use a common *ahead-only* kernel, rather than combining a separately coded finite-rank interference term with an unrelated Gaussian drift PDE.

For n horses and forward distance d=X_j-X_i, define the speed-penalty kernel (units 1/metre)

\[
K(d)=\ell^{-1} e^{-d/\ell}{\bf1}(0<d\le R),\quad
\ell=3\text{ m},\ R=8\text{ m}.
\]

Each individual runs the **hypothetical** SDE (c units m²/s, D units m²/s):

\[
dX_i(t)=\left[16.8+
0.10(\log p_i+G_i)-
\frac{c}{n-1}\sum_{j\ne i}K(X_j-X_i)\right]dt
+\sqrt{2D}\,dW_i.
\]

The Gumbel \(G_i\) and Wiener perturbations are *synthetic* and common to the paired \(c=0\) and \(c=2\) horse scenarios. An agent that has already finished is removed from other horses' front-density interactions; interpolation gives its first finish-crossing time. Without empirical horse trajectory and rider data, \(0.10\), \(c=2\), \(D=0.25\), kernel range, start SD=2 m, etc. are not calibrated physiological parameters.

In a **moving reference frame**, subtracting the common baseline 16.8 m/s from the position and holding *individual deterministic* offsets \(\delta_i=0.10[\log p_i-\mathrm{mean}_j\log p_j]\) fixed, the **factorized marginal PDE** is

\[
\partial_t\rho_i=-\partial_x[(\delta_i-c B_i(x,t))\rho_i]
+D\partial_{xx}\rho_i,
\quad
B_i=\frac{1}{n-1}\sum_{j\ne i}\int_0^R K(z)\rho_j(x+z,t)\,dz.
\]

Each \(\int\rho_i(x,t)dx=1\), not 1/n. We explicitly subtract the focal horse's own density and divide by **n−1**, just as in the particle dynamics. This approximates multi-agent correlations by a product of one-horse marginals; it is **not an exact nonlinear finite-N PDE**, nor the full ranking probability. A separate no-Gumbel, fixed-drift particle ensemble obeys exactly the SDE corresponding to this marginal PDE, so that the particle/PDE terminal density error tests the **numerical discretization plus the closure approximation**, rather than two completely different dynamics.

The upwind conservative advection/centered diffusion finite-volume solver validates nonnegative density, per-horse mass 1, an explicit CFL bound and terminal maximum CDF discrepancy against the corresponding interacting particle ensemble. Zero-flux boundaries and ample residual domain avoid synthetic edge leakage at short times. The PDE is tested on a **12-second residual-position window**, not claimed to yield a full 3000m race's finish order or true competitive drafting.

## This physical effect reaches the betting market

For the same early saved WIN quote vector \(q_0\), each physical horse prior \(p_i\) is one of:

- The early quoted WIN proxy **q0** (not a true winning probability).
- The strictly earlier historical-run-derived **h**, source-locked but not independently archived before the original 2026 targets.

The horse SDE produces two full **ordered finish** Monte Carlo ensembles (no crowd/crowd), transformed into mass-preserving WIN and Top3 distributions with fixed two-pseudo-count smoothing **from the horse input prior p itself**, not market q0.

For each condition the old PR #14 **bettor ABM receives the actual q0 as initial market state** and the simulated horse winner distribution as a signal. Exactly the same voter uniforms are used under crowd/no crowd. The old five market rules are applied: **independent, herding, informed, mixed, threshold-mixed**. The cumulative relative vote counts become a synthetic quote index \(q(t)\). Its WIN and Top3 probabilities and the cross-pool ticket events derive from the existing coherent ordered-three Plackett-Luce rank distribution, not separately fitted pair scores.

**Negative controls:** Under no-information "independent" and "herding" voting rules, changing the horse crowding does not change the generated market at all, since those agents are permitted to see only q0; the code refuses a nonzero effect. Under informed/mixed rules, the changed physical winner signal can propagate into q(t). This is the integration's falsifiable causal wiring test **within the constructed model**, not identification of real human herd behavior.

All six race-day JRA podiums enter **after all** crowd/vote/physical and market-index predictions exist. Market-index TV distances and winner Log loss/Top3 Brier both remain visible, because a model can fit podiums retrospectively yet fit future quote dynamics poorly. No model choice or coefficient gets selected based on these six scoring outcomes.

## Model provenance and limits

The source-locked cohort comprises five different Kyoto races on **2026-10-12** and one Shuka Sho on **2026-10-18**. They comprise only **2 meeting dates**, 6 real events and 84 horse-race entries. Same-date runners, dependent WIN/WIDE pairs and many simulated paths are **not independent new races**. Kyoto two-quote windows ~51–69 minutes differ from the overnight Shuka Sho mixed-source ~21.7h. There is no independently authenticated original before-first-quote horse-history reception on these six historical races.

Synthetic shared physical coefficients and the factorized PDE do **not** estimate the actual form of real horse-to-horse social/drafting effects, first sectional velocity, jockey strategy, partial GPS sample selection or horse-speed reaction norms. A detected change in hypothetical simulation probabilities should not be promoted into a gambling edge, biological interaction, or observed market regime threshold.

## Run from checked-out PR branch

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests -p 'test_keiba_nonlocal_horse_pde_bettor_bridge.py' -v
    python scripts/keiba_nonlocal_horse_pde_bettor_bridge.py \
        --draws 350 --pde-particles 1500 \
        --output tmp/nonlocal-horse-pde-coupled.json

Outputs aggregate only, reporting probability scores, PDE closure mass/CDF accuracy, mean paired differences between crowd/no crowd and matching-market price-index errors. No raw horse IDs, full protected quote table, source telemetric datasets, or calibrated gambling claims are published.

**Next real experiment:** Obtain independently before-race timestamped true horse-ID GPS/lap movement, confirmed starters including missing GPS, and prestart market snapshots on *the same racing population*. Fit only earlier dates, then test a future-date holdout separately for physical motion and market-price innovations. Test class/going/jockey effects only with adequate repeated within-horse support. Extend PDE to a justified nonlocal joint-density/closure with overtaking and lane choice only after the measured positions support it.


## Reproducible source-locked numerical result (fixed c=2, seed=20261025)

[Source-locked dedicated numerical CI #40165928292](https://github.com/zuizui0223/keiba/actions/runs/40165928292) ran on 2026-10-25. These are **counterfactual synthetic interaction** results evaluated against six historical JRA race labels; never a calibrated horse–market causal effect.

### Matched horse-particle vs nonlocal marginal PDE

| Original physical input | Mean paired race simulations where hypothetical WINNER changes when crowding is switched on | Mean crowd-induced WIN-probability distribution TV | Largest per-horse terminal CDF difference, particle vs factorized PDE (over six races) |
|---|---:|---:|---:|
| Earliest quoted market q0 | 9.90% | 2.841 percentage points | 0.05196 |
| Past-only horse-form h (reconstructed postrace) | 11.33% | 3.977 percentage points | 0.05099 |

Each horse marginal PDE retained mass = 1 to numerical precision. The PDE/particle maximum CDF difference has **multiple sources**: finite particle Monte Carlo, grid/time discretization, and the factorization's neglect of finite-horse correlations. The test is on a **12-second non-finishing, no-Gumbel** conditional slice. No real horse positions were supplied to the PDE.

### Precisely how physical crowding passes to the synthetic voter market

Average across SIX *real race labels* (the numerator/denominator of all pp values is an invented physical world and simulated bettor pool, not independent real ballot observations):

| Voter mechanism | Market-index TV between the paired crowd vs no-crowd scenarios, from q0 prior | Same TV from historical-form prior |
|---|---:|---:|
| Independent, no information about horse motion | **0.000 pp** | **0.000 pp** |
| Herding-only, no information about horse motion | **0.000 pp** | **0.000 pp** |
| Information-following bettor | 0.850 pp | 1.025 pp |
| Information + herding mix | 0.588 pp | 1.046 pp |
| Invented speed-threshold herding rule + information | 0.496 pp | 1.217 pp |

This is the key **mechanism identifiability check within the synthetic model**: changing a horse's physical crowding can change market price only along rules receiving the generated horse signal. It is not evidence that real investors changed their wagers because horses crowded one another.

The synthetic **threshold gate step count** changed by 0 (market initial prior) or −1 (history prior) out of six race trajectories with four hypothetical voter updates each. The original hypothesized discontinuous market transition is **not discovered**: any threshold switch was built into the voting rule beforehand.

### Same official six podiums, paired historical scoring (winner log loss ↓)

| Model arm | Crowding off | Nonlocal crowding on | Change |
| --- | ---: | ---: | ---: |
| q0-driven horse -> information-following bettors | 1.71326 | 1.72066 | +0.00740 (worse) |
| q0-driven horse -> threshold-mixed bettors | 1.64720 | 1.65614 | +0.00894 (worse) |
| historical h-driven horse -> information-following bettors | 1.81022 | 1.80785 | −0.00237 (better) |
| historical h-driven horse -> threshold-mixed bettors | 1.68186 | 1.67407 | −0.00780 (better) |

Observed later-market-only PL M0 winner log loss is **1.696959**. A favorable *retrospective* score direction in one synthetic rule is not proof of real predictive gain, since these coefficients, horse priors, source clocks and the six outcomes do not constitute a fitted, externally sealed, future cohort. The q0 case and the past-form case even show opposing tendencies; selecting the better after seeing six races would create post-hoc bias.

Comparisons of actual later relative WIN quote shape to these simulated market endpoints are separately recorded in the CI (often favoring different policies from the retrospective podium score). The actual amount and timing of bets are absent.

**Decision:** The physical/social coupling can now be *numerically exercised from one shared interaction law*; biological crowd causality, nonlinear PDE calibration, threshold discovery and positive wagering ROI all remain HOLD.
