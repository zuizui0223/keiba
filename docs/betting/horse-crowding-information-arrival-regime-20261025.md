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


## A real *clock-declaration* can be mapped to these rounds (no alleged time proof)

The new [horse-signal clock gate](../../scripts/keiba_coupled_signal_clock_gate.py) connects local publisher/receipt timestamps to the **same** signal_start_step parameter used by the integrated bettor ABM. It does not hardcode the number of hours to information reception or reuse a later quote as a horse signal.

The source declaration (KEIBA_CAUSAL_HORSE_SIGNAL_AND_MARKET_RECEIPTS_V1) must include eight timezone-aware clocks: first WIN quote publisher/update and receipt; later WIN publisher/update and receipt; local model creation; scheduled post; horse-signal publisher/update and receipt. Hard chronological constraints:
- first published <= first received < later published <= later received <= model creation <= post minus ten minutes;
- horse-signal publication <= horse-signal receipt <= model creation.
- A horse signal already received when the first market q0 is locally available can enter round 1. If it arrives between voting-round start times it enters the **next** round. At the exact start of round 3 it is usable in round 3. Once all four round-start times have passed, return round 5 (not available in this quote interval).

For four equal hypothetical rounds within the first-to-later quote **receipt** interval, the integer mapping is:
\[
r =
\begin{cases}
1,& t_{\mathrm{horse\ received}}\le t_{\mathrm{first\ quote\ received}},\\
1+\lceil4(t_{\mathrm{horse}}-t_{\mathrm{first}})/(t_{\mathrm{later}}-t_{\mathrm{first}})\rceil,
& t_{\mathrm{first}}<t_{\mathrm{horse}}<t_{\mathrm{later}},\\
5,&t_{\mathrm{horse}}\ge t_{\mathrm{later}}.
\end{cases}
\]

The market simulation still uses q0 as observed initial support; the horse signal is unavailable before its assigned round. If \`externally_authenticated_by_third_party=true\` is merely self-declared in JSON, the gate rejects the input outright. A source SHA and internally consistent local clock cannot prove that the source actually existed or was public before the simulated market. The output is ALWAYS LOCAL_EVENT_ORDER_AND_ROUND_ASSIGNMENT_NOT_EXTERNALLY_ATTESTED; it cannot be inserted into v3.1 or any formal prospective ledger.

**Distinction from the stricter earlier preflight:** the full-window [independent-horse source gate](../../scripts/keiba_independent_horse_asof_preflight.py) correctly refused sources received after q0 when modeling the *entire* interval as if already informed. With the new explicit information arrival, later but before-forecast sources may be used **only from their actual declared reception round onward**. Neither route imputes an earlier receipt or simulates knowledge of a result that had not arrived.


## Source-locked results of the 2026-10-25 coupled regime scan

Reproduced by the [full 350-draw source-locked numerical workflow](https://github.com/zuizui0223/keiba/actions/runs/40167058492), followed by [five synthetic seed-only repeats](https://github.com/zuizui0223/keiba/actions/runs/40167234795). The six original race labels are reused and do NOT become 350×6 independent racing outcomes. Fixed grid and thresholds were chosen as illustrative model assumptions, not fitted to real labels.

### First-stage physical response, same Gumbel/Brownian draws for each c

| c (m²/s) | q0 physical prior: paired hypothetical winners changed | history physical prior: paired hypothetical winners changed |
| ---: | ---: | ---: |
| 0 | 0% | 0% |
| 0.5 | 2.57% | 3.00% |
| 1 | 5.43% | 5.52% |
| 2 | **9.90%** | **11.33%** |
| 4 | 18.57% | 19.95% |
| 8 | 31.38% | 34.81% |

These are changes to the **same virtual race outcome under two counterfactual c choices**, NOT actual race result errors. In the finite grid the response grows over c; no physical discontinuity or biological critical point has been identified.

### Second-stage information arrival modifies synthetic price response

Market-index TV(pp) caused by switching physical c from 0 to 2, while preserving the same underlying q0 and random voter choices:

| Horse prior | Horse information from round 1 | First received at round 3 | Never received in four rounds |
| --- | ---: | ---: | ---: |
| First saved quote q0 | **0.850** | **0.438** | **0.000** |
| Historical form h | **1.025** | **0.625** | **0.000** |

The independent and no-information herding-only voter models have **zero effect in every tested c, release time and physical prior**. This is a structural causal-wiring constraint from the simulated information pathways, not proof that real bettors react to horse crowding. Market output may depend on information content and arrival even when its fixed voter threshold never changes. Threshold step counts reflect the deliberately coded 0.10/hour gate, not a learned market boundary.

### Five seeds stress the finite-draw sensitivity

A second audit **reused the same six historic races** for 5 different synthetic seeds, 150 virtual horse races per source race and seed. For c=2 the equal-real-race market-index TV responses were:

| Horse prior | Signal early: mean [seed min, seed max] | Signal late: mean [min, max] | Never |
| --- | ---: | ---: | ---: |
| q0 | 1.331 [1.200, 1.504] | 0.734 [0.700, 0.775] | 0 |
| h | 1.420 [1.292, 1.521] | 0.784 [0.729, 0.921] | 0 |

The early response exceeded delayed in **5/5 artificial seed replications** in both source-prior scenarios. These are **simulation-noise ranges on the same input race labels**, not population confidence intervals, independent experiments, calibrated market effects, or new data supporting a phase transition. Because this audit uses 150 rather than 350 virtual draws, its seed-mean response need not numerically equal the main 350-draw run.

### PDE closure diagnostic: numerical error is not the whole particle/PDE difference

One representative historical 11-horse roster under each prior, 12-second fixed ability/no-Gumbel short-time residual process, and 1500 independent particle replicas:

| Physical prior | c=0 PDE vs analytic Gaussian max CDF deviation | c=0 particle-vs-PDE max CDF difference | c=8 particle-vs-PDE max CDF difference | c=0 → c=8 mean absolute off-diagonal synthetic horse-position correlation |
| --- | ---: | ---: | ---: | ---: |
| q0 | **0.00761** | 0.02938 | 0.06288 | 0.02065 → 0.05264 |
| h | **0.00178** | 0.03243 | 0.05525 | 0.02065 → 0.05289 |

All one-horse PDE densities retained total mass 1 to floating point precision. The c=0 Gaussian comparison supplies a **discretization-only** reference; the interacting particle-vs-factorized-PDE discrepancy still mixes sampling, numerical method differences and ignored joint spatial correlations. The correlation statistic is itself a finite synthetic-sample statistic, not a real GPS observation. These data cannot allocate an exact percentage of discrepancy to the mean-field closure.

### Negative and conflicting scores must remain visible

The source-locked retrospective **official outcome** score for the q0-prior, c=2 information-only vote scenario was WIN Log loss **1.72066** if the signal was released in round 1, **1.71583** if received in round 3, and **1.70740** if never received. Better fit to hypothetical physical crowding **did not** mean better historical winner scoring. No rule can be selected as a future betting advantage from these six known labels or from matching later quoted market indices.

**Conclusion:** One linked physical/social mathematical model now connects interaction intensity, PDE closure diagnostics, as-of-limited source-clock arrival, voter information response, price indices and ordered finish probabilities. **Real-world crowding coefficient, critical threshold, real bettor imitation, true winning probability calibration, expected wagering return and cross-date generalization: HOLD.**
