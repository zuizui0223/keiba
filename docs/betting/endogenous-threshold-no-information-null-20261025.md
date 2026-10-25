# No-information threshold falsification inside the coupled horse–bettor–market model

**2026-10-25 | Draft PR #19 (nested on #18).** Source-locked six-race historical sensitivity, **not** a new JRA prospective cohort, true betting flow, real horse movement parameter estimate, phase transition, positive expectation, or a new validated betting recommendation.

## Research question

The original M2/M3-style hypothesis suggested that odds dynamics or their information content can change after crossing a popularity/relative-price-change threshold. The PR #18 voting layer ALSO contains a *preinstalled* switch at **max absolute normalized log-support movement per hour >= 0.10**. Seeing this switch in a simulation cannot discover the threshold scientifically; it has to happen because the software explicitly forces it.

This PR separates **three** different propositions:

1. The imposed hard rule is a discontinuous choice of feedback coefficient (true by definition, not discovery).
2. A smooth, switch-free social feedback rule might describe the same retrospective price paths or JRA finishing outcomes just as well.
3. Without any new horse signal, independently randomized synthetic bets might nevertheless cross the same "critical" price-rate threshold. In that case, a crossing is **not a diagnostic of information arrival, market consensus or criticality**.

## One connected model (not independent standalone calculations)

PR #17's physically interacting first-passage horse ABM uses the same synthetic nonlocal forward kernel and Brownian diffusion as the factorized horse-density PDE. The physical horse prior comes from (a) the earliest saved q0 single-WIN quote index or (b) past-JRA-race-derived form h (not independently source-time attested on this already-completed cohort). For the **same** paired horse-no-crowd/c=2 race simulation we pass each WIN distribution to the existing PR #18 information-arrival voter step (round 1/3/5). The synthetic market begins from **real early saved q0** in both physical-prior arms.

There are four market vote rounds, each with 250 categorical choices, plus an initial hypothetical pseudo-pool of 3,000 shares. The **same uniform random numbers** are used to compare all three social response laws below. State \(q_t\) is a *normalized synthetic voting index*; it is not a JRA pool size, measured tickets, or empirically calibrated winner probability.

Let

\[
r_t =
\max_i\left|\log\left(q_{t,i}/q_{0,i}\right)\right|/(t-t_0)
\quad\text{(hours}^{-1}\text{)}.
\]

When an interval begins at \(t=t_0\), define \(r_0=0\). The same information signal \(s\) may enter only when its stipulated receipt round arrives. All three voter rules take propensity proportional to \(q_{t,i}^{\gamma(r_t)}s_{i,t}^{0.75}\).

| Social rule | Social feedback exponent \(\gamma\) | What it tests |
|---|---|---|
| Fixed (existing "mixed") | 0.75 | No dynamic gate |
| Hard (existing "threshold_mixed") | 0.75 for r below 0.10, else 1.50 | An **assumed** sharp change |
| Smooth, **new** | \(0.75+0.75\,r/(r+0.10)\) | A continuous alternative with the same lower/upper asymptotes |

The \`0.10\` in the **smooth denominator is a prespecified scale**, not a discontinuity or empirical critical threshold. The \`0.10\` in the hard gate is explicitly a software-imposed jump. Fixed/hard versions are tested **bit-for-bit identical** to the existing PR #18 implementation at all three information release schedules. We neither optimize the scale nor choose a law by inspecting these six known historical outcomes.

Cumulative simulated market prices are mapped through the **same single ordered Plackett–Luce ranking distribution** to WIN and Top3. The earlier PR #17 coherent ticket-event bridge is unchanged and can derive pair/trio events from this law; this experiment scores only WIN and Top3 plus price-index shape.

## Crucial negative control: what if no horse signal arrives?

Run TWO artificial betting populations on the exact same archived first-q0 race-index vectors, but with no incoming horse signal:

- **Independent null:** 250 draws per round i.i.d. from q0; no information, no herding. Calculate how often the resulting price path *would cross* the preset 0.10/hour diagnostic even though no social gate is implemented.
- **Endogenous hard-feedback null:** synthetic bettors have the preset threshold rule but their horse-information signal is absent until round 5 (after all four rounds). They can still feed back onto their own noisy q(t), potentially switching without any external information.

Each source race's 30 synthetic seeds is replayed at **three duration denominators with identical source q0 and random sequences**: its saved early-to-late quote interval, exactly 1 hour, exactly 22 hours. Only the denominator changes; this is **not real JRA price evolution under different elapsed times**.

### Source-locked negative-control result

[Dedicated GitHub Actions run](https://github.com/zuizui0223/keiba/actions/runs/40179368299), 2026-10-25:

| No-horse-information scenario | Independent null: paths with >=1 apparent rate-crossing | Hard-feedback null: paths with >=1 switch |
|---|---:|---:|
| Kyoto Oct 12 five saved early/later quote windows (51–69 min) | **97.3%** | **100%** |
| Shuka Sho Oct 18 saved quotes (~21.67 hours) | **0%** | **0%** |
| Force each initial q0 through 1-hour synthetic interval | **98–100%** | **100%** |
| Force each initial q0 through 22-hour synthetic interval | **0%** | **0%** |

**Interpretation:** The diagnostic's crossing is neither a sufficient condition for a new information shock nor evidence of a voter feedback phase change: it occurs under entirely independent random votes. In this synthetic design, simply changing the artificial observation horizon converts an almost-certain "threshold event" to zero. The publication/reception clocks and history provenance of the six archived races differ; the result suggests replacing the simplistic rate gate with an exposure/noise-standardized model **before** claiming information-phase inference.

Do not report these percentages as actual JRA voter behavior or as the Type I error of a trained real-world detector. There are just six different race q0 vectors, two dates, and synthetic pseudo-stakes/vote allocations; the 30 seeds reuse the same source races.

## Hard vs smooth on the same historical outcome/published price labels

The returned six-race equal-race aggregate includes *every* law, source prior, c=0/2, and release round 1/3/5. It separately reports:

- Winner Log loss and horse-wise Top3 Brier against official podium **only after all forecasts and nulls have been computed**;
- Total Variation distance from the *later saved normalized reciprocal-WIN-price index q1*, which is a quote shape, not a coherent observed vote share nor a true winner probability;
- how many of the **hard** simulated rule's rounds meet its preset trigger;
- crowd-on vs crowd-off shift in each simulated final voter q(t).

With physical prior q0, c=2 and horse-signal from the first round:

| Fixed coefficient | WIN Log loss (smaller better) | Top3 Brier | TV vs real next saved WIN index (pp, smaller better) |
|---|---:|---:|---:|
| Fixed | 1.65808 | 0.12146 | **6.360** |
| Hard preinstalled threshold | 1.65488 | 0.12096 | 8.248 |
| Smooth switch-free | **1.65230** | **0.12107** | 7.881 |

The three outcome differences are tiny on six known labels and the observed next-price shape instead favors the fixed no-switch law. The hard rule isn't uniquely favored across these two different explanatory targets. The source h prior, release lag and date-stratified comparisons have further conflicting signs; these are recorded rather than selecting the winning variant.

The **hard rule's mean 2.5 threshold-active rounds per race** across these saved sources (out of four), even when horse signal is *never released*, highlights why counting imposed switches is not evidence of information assimilation. The smooth rule yields no discrete "threshold rounds" by definition.

## Limits and future falsification of genuinely emerging regimes

- The historical race count is **6**, across only **2 dates**; 84 horse-race entries and 30 synthetic seeds are not 84+30 independent outcomes. The Kyoto price windows are ~0.85–1.15h while the Shuka source windows are ~21.67h with mixed provider clocks.
- Original detailed Oct12 JRA historic past-form was normalized **after** the targets. Past run dates precede the targets, but original horse-source reception is not independently attested. No JRA horse GPS, actual stake feed or bettor ID/ticket histories enter the simulation.
- The physically interacting horse SDE and factorized PDE remain hypothetical; no real horse crowding or overtaking effect is identified.
- Repeated random ballots produce stepwise q(t), even when the underlying voter propensities are smooth. A few apparent abrupt movements in the sampled price index do **not** identify a thermodynamic or economic phase transition.
- The smooth response was deliberately prespecified as an alternative; one cannot claim it is the fitted best social model from these six outcomes either.
- A future independent-data study must define \`q(t)\` at coherent source/reception clock times, obtain information-release and real aggregated flow timestamps, fit smooth time-varying volatility and social response on **earlier** independent dates, fix detection/selection rules BEFORE future race outcomes, and test change-point models against continuous alternatives with date-clustered uncertainty.
- The external 2026 菊花賞 M0/M1/M2 preseal SHA, formal v3.1 20-race ledger, main and all parent PRs are unchanged.

## Reproduce

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests -p 'test_keiba_endogenous_threshold_null_bridge.py' -v
    python scripts/keiba_endogenous_threshold_null_bridge.py \
      --preoutcome-only --draws 100 --null-seeds 30 \
      --output tmp/endogenous-null-preoutcome.json
    python scripts/keiba_endogenous_threshold_null_bridge.py \
      --draws 150 --null-seeds 30 \
      --output tmp/endogenous-null-retrospective.json

The outputs provide source-date-level aggregate null activation fractions and six-race equal-race/date-equal scenario scores. They do **not** redistribute original per-horse odds/history, issue recommended bets, or promote a retrospective threshold.

**Scientific decision: no criticality or independent betting edge has been established. The null produces many false "threshold" events by construction and clock normalization. HOLD until real time-stamped flow and independent forward cohorts exist.**
