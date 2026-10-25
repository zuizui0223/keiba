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
