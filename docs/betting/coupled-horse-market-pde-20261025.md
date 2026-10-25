# Horse × bettor × odds threshold × PDE: one coupled mechanism

**2026-10-25 / Draft research only.** Dependent on [PR #13](https://github.com/zuizui0223/keiba/pull/13). The original [PR #9](https://github.com/zuizui0223/keiba/pull/9) files are copied **byte-for-byte** as an integration dependency; PR #9 itself is unchanged. PR #10's official Kikuka precommit SHA (9ef880b4decf3b38c4ea01ece9570bd4c6c61d636db26f05af8181fe41fe857), PR #12, main, frozen v3.1 and 20-race ledger are **not edited**.

## Directed, time-ordered model

At the time of the **earliest archived intermediate quote** (not certified opening odds), we form q0 from the normalized reciprocal of the complete WIN quote vector. q0 is a **market index**, neither a true winner probability nor the number of tickets.

1. **Horse agents:** The *unchanged* PR #9 1D first-finish horse ABM initializes synthetic latent abilities as log(q0) + IID Gumbel and synthetic pace; evaluates zero/weak/strong crowding. A *new* Brownian first-passage horse ensemble shares the latent premise, but lets positions follow dX_i = [16.8 + 0.10 a_i + period pace_i − crowd_i]dt + sqrt(2D)dW_i. Paired crowd/no-crowd simulations share initial/pace/Brownian draws. Neither estimates genuine horse ability, pace, jockey strategy or lane choices. No race result or later market quote is fed to either physical ensemble.
2. **Bettor agents:** A fixed 50:50 *hypothetical* average of the PR #9 weak-crowd WIN distribution and the new Brownian no-crowd WIN distribution becomes the agent's common information signal. It is **not new empirical evidence**: both source the same early market index. To avoid undefined log loss from finite simulated zero wins, each Monte Carlo WIN and Top3 vector is smoothed with a **fixed two-draw-equivalent prestart PL prior** derived exclusively from q0 (not from actual results). At 4 prestart rounds, independently voting categorical agents are simulated by inverse-CDF draws from common uniform random numbers across the five market rules. Their resulting count vectors have the multinomial law, while paired draws reduce confounding by different Monte Carlo seeds. The vote pool is explicitly synthetic: initial pseudo-stakes 3000, 250 votes per round. The market update is cumulative, q(t+1) = (N_t q_t + b_t) / (N_t+250), preserving mass. Candidate mechanisms:
    - independent: no social feedback, new votes distributed by q0;
    - herding: propensity proportional to q(t)^1.25;
    - information: propensity proportional to the common horse-ensemble signal;
    - mixed: propensity proportional to q(t)^0.75 × signal^0.75;
    - threshold_mixed: the mixed rule, but switching the **hypothetical** herding exponent to 1.50 when the maximum observed absolute log-support change per elapsed hour reaches 0.10.
3. **Market and ranking bridge:** Each simulated cumulative market trajectory is converted to reversible **synthetic** decimal price proxies, 1/q. PR #13's M0/M1/M2/M3 machinery then produces coherent PL WIN and Top3 probabilities (then the same ordered-top-three law determines cross-pool WIDE/quinella/trio/trifecta event probabilities). For the *same* simulated market, the **coupled forecast is its M0**, since the horse-ensemble signal already entered the voters; multiplying that signal into the forecast a second time would double-count it. Simulated M1-M3 remain labeled sensitivity diagnostics. The separately saved **actual** early/later quotes yield their existing observed M0-M3 baselines; no new model is retrospectively chosen based on results.
4. **Shared ticket universe (PR #10/#12 interface):** The connected market q(t) is supplied to the *existing* coherent ordered-Top3 enumeration, with horse/pair residual coefficients exactly zero for this audit (no invented independent pair information). Every WIN, Top2, Top3, WIDE pair, exacta, unordered trio and ordered trifecta comes from the **same 3-place joint law**. In particular WIDE pair probabilities sum to 3 because three pairs win per completed top-three outcome; unordered trio and ordered exacta/trifecta probabilities each sum to 1. The real six-race scores of WIDE pair inclusion and unordered trio are computed **after** official top-three outcomes are loaded. **These scores compare predicted event probabilities, not final quoted ticket returns**, and WIDE pairs within one race are not independent observations. Raw synchronous market quotes from PR #12 are *not* injected as if they were calibrated horse interaction parameters.
5. **PDE closure:** The Brownian horse model uses initial independent position SD=2 m and D=0.25 m²/s. Conditional on no crowding, after removing the deterministic skill + pace trajectory, the remaining process is R_i(t) = R_i(0) + sqrt(2D)W_i(t). The unchanged PR #9 numerical particle/PDE bridge receives **the same** initial SD and D to check the Fokker–Planck equation ∂_t rho = D∂_xx rho on this residual submodel. It is a **shared stochastic law**, not a claim that the PDE solves finite-horse drafting, jockey interference, nonlinear crowding or race finishing order. A crowd-dependent nonlocal nonlinear closure remains a research task.
6. **Outcome firewall:** ALL six archived predictions are calculated first. Only after that are JRA official finishing top-3 labels loaded for six-race historical descriptive scoring. Only race-level scores are averaged; 84 horse entries and dependent pairs are not 84 independent outcomes.

The graph is **horse scenario -> information -> bettor votes -> market q(t) -> coherent finish-ranking forecast -> later evaluation**. There is no arrow from **future** realized horse finishes to prestart voters, nor any assumed physical arrow from displayed odds to actual horse motion. A reverse arrow would require a separately specified, observed behavioural mechanism (e.g. an independently measured jockey response), not a default assumption.

## What the initial coupled experiment can and cannot identify

The comparison suite contains **five counterfactual voting rules**, the *original market-only* M0-M3, the *PR #9* synthetic horse output, and the *Brownian SDE* horse output. It can test reproducibility, first-passage rank mass, voter-pool conservation, smooth/threshold price response, as-of isolation, and shared-noise SDE/PDE numerical correspondence. The archived historical six-race comparison can evaluate conditional scores, but it **cannot** estimate real herding, true horse crowding, market-to-horse causality, a real critical threshold, calibrated new independent information, or betting ROI.

Especially important: a superior SDE/PR #9 forecast from q0 would not yet be independent horse evidence. Both use market-derived ability priors. The next empirical bridge requires independent past horse ID, fractional/GPS speeds, going, distance, draw, rider and finish histories with **pre-event** source clocks, trained on earlier dates only. Genuine bettor micro-level timestamps/pool totals are needed to distinguish voting reinforcement from mechanical persistence. Quote proxies cannot identify individual ballots. Cross-pool WIDE/quinella/trio indices can be added only at verified matching as-of clocks, retaining a coherent ordered finish distribution.

For stronger physical coupling, the horse SDE should be fitted to actual position distributions and compared with its density PDE on **real GPS slices**, and a separately derived nonlocal crowd-density closure should be evaluated rather than assuming the uncrowded Gaussian process is enough.

## Run (private/output contains no quote table)

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests -p 'test_keiba_coupled_horse_market_pde.py' -v
    python scripts/keiba_coupled_horse_market_pde.py --prestart-only --draws 250 --output tmp/coupled-prestart.json
    python scripts/keiba_coupled_horse_market_pde.py --draws 250 --output tmp/coupled-retrospective.json
    python scripts/keiba_coupled_seed_sensitivity.py --seeds 7 --draws 120 --output tmp/coupled-seed-sensitivity.json

Neither command writes to v3.1's ledger or official Kikka prediction freeze. Only aggregate counters and scoring are exported, not per-horse proprietary quote trajectories. The speed/latent/crowding coefficients, PDE D, voter counts and exponents are **synthetic fixed assumptions**, not fitted parameters. Multiple random seeds characterize **Monte Carlo variability on the same six actual outcomes**, not additional independent races or a confidence interval for future performance. Future externally timestamped holdouts must compare:
- actual latest-market M0;
- latest market plus *independent, historically trained* horse features;
- market-only time path M1/M2/M3;
- combined animal and voting model, **without double counting**, against the same real outcomes;
- a physically justified stochastic-ABM/PDE discrepancy, with crowding separately tested.

**Scientific state: HOLD until independent horse observations, vote-flow data, several meeting dates and prospective market snapshots are available.**
