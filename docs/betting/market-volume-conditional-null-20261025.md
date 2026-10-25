# Price-index changes beyond count noise: conditional volume/overdispersion audit

**2026-10-25 — nested Draft on [PR #19](https://github.com/zuizui0223/keiba/pull/19).** This is a source-locked descriptive sensitivity using six archived JRA race/quote panels from two dates. It is not a live prediction, real bettor-volume measurement, identified social imitation, discovered market critical point, or an evaluated wagering edge. Previous presealed Kikuka M0/M1/M2 SHA, v3.1 formal ledger and parent PRs remain immutable.

## Motivation and link to the unified mechanism

PR #17 supplies a forward-neighbour nonlocal physical law used in both interacting horse agents and a **factorized** horse-position PDE. PR #18 delays the availability of the hypothetical horse signal until the correct voting round; PR #19 compares a fixed, hard-jump and smooth social feedback rule in the **same** bettor market. These connections already exist.

PR #19's crucial negative control showed that the fixed 0.10/hour odds threshold can be crossed by independent pseudo-votes without new horse information. The question now is **how large a subsequent quote-index movement would be unusual relative to a stipulated no-new-information voting mechanism?** A raw clock rate cannot answer this by itself.

This branch does **not** turn pseudo-stakes into observed stakes. It constructs explicit ranges conditional on what fraction of the cumulative pool is new, how many effective independent votes are counted, and whether those votes are overdispersed. It simultaneously evaluates PR #19's **same already-implemented physically coupled horse→smooth bettor ABM** against each saved subsequent quote. The horse ABM signal enters once as voter information, not as an extra multiplier at final ranking.

## Defined null experiment (including count/volume assumptions)

Given a full-field earliest-saved quoted WIN vector \(\mathbf q_0\), define \(\mathbf q_0\) as normalized reciprocals of the *displayed payout odds*. For a specified hypothesized fraction \(\lambda\) of the final pool received after the first quote and an effective count \(N\) of new bets, simulate

\[
\widehat{\mathbf q}_1=(1-\lambda)\mathbf q_0+
\lambda \frac{\mathbf n}{N}, \quad
\mathbf n\sim\operatorname{Multinomial}(N,\mathbf p).
\]

Under **stationary independent** no-horse-information votes, \(\mathbf p=\mathbf q_0\). An explicitly overdispersed **no-horse-signal competitor** draws a latent vote-propensity vector \(\mathbf p\sim\mathrm{Dirichlet}(80\mathbf q_0)\) before drawing multinomial counts. This latter null is not necessarily iid unconditionally, but still has no arrival of new horse information. It can represent synthetic correlated/heterogeneous pseudo-vote conditions, not demonstrate real herding.

The source-independent, fixed sensitivity grid is:
- \(\lambda=0.20,0.80\) (new-to-final hypothetical fractions);
- \(N=100,1000,10000\) *effective* new votes;
- independent versus \(\kappa=80\) Dirichlet-overdispersed conditional model.

**No real pool sizes, stake counts or effective transaction units were observed**, so no single cell is privileged. Each of the 12 settings generates an independent synthetic null distribution with fixed seed. The actual later \(\mathbf q_1\) is read solely for **descriptive evaluation after the simulation and the PR #19 horse/voter trajectories have already been created for all races**.

Three noise-conditioned measurements are retained:

1. **Quote-index TV**: \(50\sum_i|\widehat q_{1,i}-q_{0,i}|\), in percentage points, compared with \(50\sum_i|q_{1,i}-q_{0,i}|\). This is a market-index **shape**, not a proper horse-race outcome score.
2. **Simultaneous maximal log-price shift**: \(\max_i|\log(\widehat q_{1,i}/q_{0,i})|\). Compare the observed corresponding value with the null distribution of the **maximum over all horses**, not a selected horse's uncorrected statistic. Dividing BOTH null and observed values by the same elapsed hours leaves the calibrated tail area unchanged; the preinstalled 0.10/hour cutoff does not have this invariance.
3. **Conditional Monte Carlo tail area**: \((1+\#\{\mathrm{simulated\ null\ statistic}\ge\mathrm{observed\ statistic}\})/(B+1)\), without calling it a real-world p-value. The score depends on \(\lambda,N,\kappa\), quote-proxy transformation, rounding and source timestamps, none of which is independently identified.

A **disjoint synthetic null-vs-null split** checks whether an internally computed 95% threshold triggers about 5% of heldout generated null paths; it evaluates software self-calibration only, not real market false-positive rate.

## Pool-flow identifiability and decimal quotation limitations

Under a mathematically exact cumulative-pool model \(\mathbf q_1=(1-\lambda)\mathbf q_0+\lambda\mathbf b\), where \(\mathbf b\) has nonnegative entries summing to 1, any feasible \(\lambda\) satisfies

\[
\lambda\ge\lambda_{\min}
=\max\{0,\,\max_i(1-q_{1,i}/q_{0,i})\}.
\]

For any \(\lambda\) above that bound, the exact flow witness
\(\mathbf b=(\mathbf q_1-(1-\lambda)\mathbf q_0)/\lambda\)
is a valid probability vector. Infinitely many choices of \(\lambda,\mathbf b\) fit the *same pair* of q-vectors. The quote pair therefore does not identify whether bettors copied others, reacted to news or arrived randomly.

**Most importantly**, normalized inverse displayed JRA WIN payout odds are **not established as exact actual pool shares**; the relation is thus algebra applied to a price-derived **proxy**, *not an observed turnover constraint*. We preserve whether each nominal grid cell would be feasible under the false simplifying assumption of exact shares; an infeasible cell is not a detected real-market mechanism.

To audit display precision, we also compute conservative marginal intervals if every printed decimal odds were within **±0.05** of an unrounded value. This is a hypothetical symmetric-bin diagnostic, **not** an assertion of actual JRA display rounding/truncation rules. The lower bound of TV under those intervals is reported alongside the central reciprocal-quote TV. It cannot remove unknown takeout, pool rules, betting stakes or provider clock differences.

## Same physical→social ABM remains in the calculation

For each locked historical race and prior type (earliest displayed q0 versus source-locked *older* JRA horse history h), call the pre-existing PR #19 **nonlocal crowd \(c=2\)** horse SDE→social bettor model. Its **smooth continuous** social response, with fixed arriving-at-round 1, 3 or never (5), supplies an independent candidate terminal market index. Those candidate indices are constructed before the real next q1 is read. For each, the observed price-index TV mismatch is reported, *without fitting weight parameters or using the result to choose a winner*.

Thus the **same race IDs, q0, physical prior, physical interaction, buyer-information timing and q1** are shared by both the newly calibrated null sensitivities and the original coupled social model. The null calibration does not retroactively alter the horse/voter paths.

No horse's actual finishing result, payout or race outcome is read anywhere in this PR's experiment. These prices are already historic and do not constitute prospective market forecasts.

## What this source can support

There are only **six** original real races / **two** meeting dates / 84 horse-race entries. October 12's five earlier/later quotes are Yahoo/SportsNavi source-locked, while the overnight Shuka Sho includes different publisher/update-clock semantics. Shuka cannot silently be pooled as one equivalent 22-hour same-provider vote process. The target-relative past-horse profile for the October 12 cohort was retrieved/normalized **after the target races**; historical past-start dates do not prove model input was available at the earlier market timestamp.

The null test's actual scientific outcome can only be: **under precisely specified assumed effective pool size, new-stake fraction and pseudo-vote dispersion, the real quoted proxy movement is atypical or not atypical**. That cannot be promoted into detected new information, identified herding, a sharp continuous/discontinuous critical threshold, true win-probability calibration or profitable stakes.

## Reproduction

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests -p 'test_keiba_conditional_volume_null_bridge.py' -v
    python scripts/keiba_conditional_volume_null_bridge.py \
      --null-draws 2000 --horse-draws 80 \
      --output tmp/conditional-volume-market-null.json

Only race-level and aggregate SOURCE-CONDITIONAL metrics are emitted. No full original individual quote/protected horse-history tables are published; no official race outcome is accessed. This is a **Draft investigation / full HOLD**, not a tool for recommended bets.

**Future identification gate**: obtain source-authorized aggregate per-pool stake *amounts*, synchronized quote/sale timestamps and independent third-party receipts, fit the null count/overdispersion process on earlier meeting dates, then freeze it before truly future races. If those volumes remain unavailable, the correct claim is partial identification and volume-sensitivity, not true significance.


## Source-locked 2026-10-25 result: the conclusion depends on the unknown vote units

[Dedicated 2,000-draw CI](https://github.com/zuizui0223/keiba/actions/runs/40181450712) generated the new source-condition sensitivity and reused the exact same nonlocal-horse/crowded physical prior → delayed smooth social-voter simulator. The source cohort is still five Kyoto R8–12 races (October 12) and one Shuka race (October 18).

**Observed price-derived index movement:**

| Archived source window | n real races | Mean central TV between q0 and q1 (pp) | Mean minimum TV under *hypothetical* ±0.05 decimal odds bins (pp) | Mean lower bound λ_min if price indices were exact pool shares |
| --- | ---: | ---: | ---: | ---: |
| Kyoto Oct 12, ~0.85–1.15h, same provider | 5 | **2.59158** | 1.69820 | 0.11906 |
| Shuka Oct 18, ~21.67h, mixed provider/update semantics | 1 | **7.66140** | 5.64403 | 0.22874 |

The rounding lower bound is conditional on an invented symmetric interval around the display, not an authenticated JRA net payout/rounding function. The λ lower bound is a theorem about *exact* cumulative pool shares and cannot be treated as actual JRA new turnover when derived from quoted payout reciprocals.

**Sensitivity to conditional Monte Carlo vote assumptions:**

Number of the FIVE Kyoto race quote-index movements with conditional TV tail area below 0.05 (not actual population tests), holding the *hypothetical* new fraction at λ=0.2:

| Assumed effective N of new pseudo-votes | iid q0-vote null | Overdispersed Dirichlet(80 q0) null |
| ---: | ---: | ---: |
| 100 | 1/5 | 1/5 |
| 1,000 | 4/5 | 1/5 |
| 10,000 | **5/5** | **1/5** |

At assumed λ=0.8, 100 pseudo-votes, NEITHER model puts any of the five Kyoto observations in the extreme upper 5% tail; the assumed noise process is too broad to regard that particular observed price-index movement as unusual. At λ=0.2,N=10,000, the stationary iid null is very narrow, but correlated pseudo-voters have much broader results. **Thus without real effective stake volume or vote dispersion, simply calling these movements unusual cannot identify informed voting or criticality.**

For the mixed-source **Shuka** quote pair, the proxy simplex bound is **λ_min=0.22874**. Therefore the λ=0.20 sensitivity is **mathematically infeasible if the quoted reciprocal indices were exact cumulative pool shares**. Its very small simulated TV tail areas must not be counted as meaningful evidence for this conditional cumulative-pool representation. The λ=0.80 scenario is feasible under that proxy assumption but gives conflicting results: with N=1,000 the iid tail is at the simulation floor, whereas the overdispersed model's tail is about **0.761**; with N=10,000, the latter is about **0.729**. This is also provider-clock confounded, not an independently authenticated 22-hour stake history. The executable aggregate audit separately flags feasible cells before interpreting tail counts.

**Noise calibration sanity check.** In an independent synthetic null split (not real source data), the nominal 5% threshold rejected **4.95%** of generated held-out TV paths and **5.25%** of maximal log-change paths. Crucially, the maximal-statistic tail area calibrates the *largest move among every horse in a single race*, and is mathematically unchanged by dividing both the observed and reference change by the same 1-hour or 22-hour interval. This removes the trivial time-denominator dependence of PR #19's fixed 0.10/hour gate *inside the stated null model*; it does not authenticate a real null process.

**Horse↔voter integration did not disappear.** The PR #19 physical SDE with forward nonlocal crowd c=2, first-round/third-round/never information arrival and smooth-social voting remains in the same executed study. For the five same-provider Kyoto races, the **first-round** smooth bettor market candidates based on q0 physical priors were on average about 6.004pp from the *later displayed quote proxy*, compared with roughly 4.562pp for the retrospectively reconstructed historical form physical prior; both are worse than simply retaining the first observed q0 quote proxy (2.592pp). For mixed-provider Shuka, historical-form first-round model TV was about 5.302pp versus simply retaining original q0 at 7.661pp, but this single race with source mismatch and unproven original history reception cannot establish extra independent predictive information. The other information arrival times are preserved in the source-scoped aggregate results, not selected by hindsight.

**Interpretation:** This is partial identification with explicit measurement/proxy and effective-count caveats. It is **not** a real p-value, volume estimate, biological behavioral effect, superior next-market model, or a licensed betting rule. Evidence for a real odds critical threshold, new information arrival, winning probability calibration, positive expected return and future-date transferability remains **HOLD**.
