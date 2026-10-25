# Horse crowding × information-arrival regimes in one coupled ABM/PDE/bettor process

**2026-10-25. Draft PR dependency of [PR #17](https://github.com/zuizui0223/keiba/pull/17). Scientific status: SYNTHETIC mechanism and source-locked retrospective sensitivity only. NOT JRA race forecast calibration, social imitation identification, market critical-point discovery, genuine horse ecology causality or positive return.** Neither main nor v3.1's 20-race ledger nor the externally precommitted 2026 菊花賞 M0/M1/M2 SHA is changed.

## The new falsifiable question

PR #17 connected a forward-neighbour kernel in the horse SDE with the product-marginal nonlocal PDE and a voter ABM. However, the previous bettor law supplied the hypothetical full horse outcome signal to **all informed voters at the first of four simulated rounds**. An empirical hypothesis about hierarchical information timing or price threshold cannot be examined with only this instantaneous-release assumption.

This branch runs **one coupled model**, not four independent analyses:

1. **Past horse state / first saved market**: early JRA WIN index q0 as observed market initialization, and either q0 or separately sourced past-form h for the hypothetical horse agents; h is never treated as contemporaneously authenticated for the historical cohort.
2. **Horse social movement**: simulate the exactly same PR #17 nonlocal *ahead-only* first-passage law with paired Gumbel/Brownian randomness, but vary c over **0, 0.5, 1, 2, 4, 8 m²/s**. Kernel scale 3 m, range 8 m, D = 0.25 m²/s are fixed invented assumptions, not fitted parameters. For every c, the no-crowd baseline is bit-for-bit the same Monte Carlo outcome.
3. **Information time / bettor ABM**: the exact previously coded, cumulative-pool voting model gets its horse-signal information at round **1 (initial), 3 (delayed), or 5 (never; there are only 4 voting rounds)**, with the same random uniforms across c and arrival choices. Before horse information is released, those bettors may use q0 but NOT the future horse signal. The signal-free independent and herding-only voters never react to changing horse crowding. The original first-round argument is the backwards-compatible default and does not alter older sealed runs.
4. **Market and event distribution**: those votes update the synthetic relative index q(t). A single ordered Plackett–Luce ranking gives coherent WIN/Top3 probabilities (and, by the existing PR #10 ordered-triple interface, WIDE, quinella/exacta and trio/trifecta). Do not mix original WIN/WIDE quote timestamps from different publisher pools.
5. **Two distinct independent outcome targets**: only **after all** 6 archived source-locked race/horse scenario forecasts are computed do we (A) compare synthetic price-index q(t) to the later SAVED relative WIN-index q1 and (B) score the official JRA winner/Top3 against the joint ranking law. Price-index TV is not winner Log loss or observed votes.

## Mathematical noncriticality controls

The proposed critical behavior must not be *found* merely because the model contains a hardcoded threshold:

- **Physical intensity c=0**: all crowds have the exact no-crowd paired distribution.
- **No horse-information release until a nonexistent fifth round**: physical c can change first-passage rank probabilities but **must not change ANY of the five voter-model market trajectories** (including the threshold-mixed rule), checked bit-for-bit.
- **No-information voter rules, any arrival**: independent and herding-only paths must stay identical across physical c. Any deviation is a wiring leak, not an empirical mechanism.
- **Predeclared c and release grids**: no parameter selection on the official six results, no last-price optimization, and no claim that maximum adjacent finite-grid slope is a genuine discontinuous transition. Finite Monte Carlo draws, race-specific finishes and the imposed voting \`0.10/hour\` switch can create staircase effects even with smooth stochastic physics.
- **Two independent real meeting dates**: 2026-10-12 Kyoto 8–12R (five races) and 2026-10-18 Shuka (one race), 84 horse entries but only six real podiums and two dates. Do not bootstrap horses, simulated paths, or overlapping WIDE pairs as independent race replications. Price update intervals differ strongly across the two dates.
- **Early saved quotes are not true opening odds**; historical inputs from Oct 12 were downloaded/normalized after target races, making these **retrospective reconstructions** even though the source past races precede target date.

### Separate PDE discretization error from the missing finite-horse joint distribution

The underlying PR #17 PDE is a mass-conserving product-marginal closure. Individual horse velocities use the same kernel as the SDE; however the joint spatial correlations are discarded. The existing PDE-vs-particle Kolmogorov (max CDF) diagnostic therefore contains **three terms**, not one known “model error”: finite particle Monte Carlo, PDE numerical discretization, and mean-field factorization.

We add two independent diagnostics to the existing PDE numerical routine:

- at **c=0**, a known Gaussian solution with mean v_i t and variance start_SD² + 2Dt exists, so direct PDE-vs-analytic CDF deviation estimates a numerical floor *without particle sampling or interaction closure*;
- at **c=0,2,8**, report absolute off-diagonal terminal horse-position correlations across Monte Carlo replicas (empirical synthetic property that the product-marginal PDE discards) alongside the particle-vs-PDE terminal CDF error. Correlation does not alone quantify marginal closure bias or identify any real horse-grou​p causal effect.

PDE parameter sweep is **one representative archived 11-horse race** under q0 and h priors, not a new physical dataset. Every marginal retains probability mass 1. The full race ranks from the Gumbel/crowded SDE remain separate from this 12-second fixed-ability, no-Gumbel PDE diagnostic.

## Fixed-vote comparison without artificial count inflation

Four rounds of 250 fictional voter choices each plus an initial pseudo-pool 3000 are unchanged from PR #14. The 0.10/hour threshold is *assumed*, not fitted. Reporting the threshold-gate round count only describes this fabricated rule; it cannot show that any JRA bettors transitioned. Signal-timing rounds represent **within-quote interval ordering**, not measured underlying stake timestamps; day-long Shuka quote updates do not justify equal clock intervals.

For every (source prior, c, arrival, vote mode) report:
- horse winner/Top3 marginal probability displacement vs c=0;
- synthetic bettor price-index TV displacement vs c=0;
- number of switched fixed voting-threshold rounds;
- synthetic index TV distance from the next recorded market quote;
- postrace official winner Log loss and Top3 Brier, not combined into one cherry-picked number;
- separate summaries for the two meeting dates.

The primary science result is the **causal wiring and structural falsification within the numerical model**: whether delayed information suppresses the transmission from horse movement to simulated bettors, and whether PDE closure mismatch changes at higher c. This is not a test that the actual horse positions or real bettors obey these equations.

## Reproduce

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests -p 'test_keiba_coupled_info_delay_regime_surface.py' -v
    python scripts/keiba_coupled_info_delay_regime_surface.py \
      --draws 120 --pde-particles 800 \
      --output tmp/coupled-regime-surface.json

For strict outcome-firewall verification:

    python scripts/keiba_coupled_info_delay_regime_surface.py \
      --preoutcome-only --draws 60 --pde-particles 400 \
      --output tmp/coupled-regime-preoutcome.json

Neither mode downloads protected sources, submits bets, rewrites any frozen forecast, or appends to v3.1's official results ledger.

**Actual empirical next step:** use lawful, independently server-timestamped past-ID/GPS/lap movement for the SAME upcoming racing horses as the WIN quote panels, measure when a given information item reaches the public market, model actual as-of quote reception rather than invented equal voting rounds, and then score a genuinely separate future date cohort. Until then all biological/social criticality claims remain HOLD.
