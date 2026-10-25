# Kyoto 8R: a real three-time market path, conditional vote-noise envelope, and one connected horse × WIDE × bettor mechanism

**2026-10-25 | Nested Draft study above [PR #20](https://github.com/zuizui0223/keiba/pull/20), not an externally precommitted forward prediction.** The object is the **NEXT displayed market quote**, not the race winner or betting ROI. The only real race is 2026-10-12 京都8R (11 horse numbers). Market prices are **normalized reciprocals of displayed payout odds**, neither genuine tote stake shares nor calibrated horse win probabilities.

## Why this is the next test

The earlier source-locked 6-race/two-date audit showed that the significance of a nominal log-price "threshold" changed dramatically across assumed new-pool fractions, effective vote counts, and overdispersion. In particular, information-free synthetic bettors often cross the preset 0.10/hour rate. The next useful measurement is a **genuine earlier/middle/later full-field quote sequence** at one fixed provider, so future-price fit can be scored separately from the famous official podium.

Kyoto R8 supplies:
- 12:21 source-updated WIN full-field, **observed later** at approximately 12:35:59;
- 13:26 source-updated full-field WIN, observed 13:27:02, plus the complete 55 WIDE pairs from another same-provider page with **the same displayed update minute** (NOT a proven atomic transaction);
- 13:44 source-updated WIN complete full-field in **another hash-locked archive**. Its original source-receipt stamp is verified to be after the 13:26 data were received and before scheduled post.

The three observations have verified matching race/horse numbers and provider. A displayed update minute is **not** a timestamped sequence of individual bettors or total sales. This is still **one real race**, not independent 55-WIDE or 11-horse samples.

The 18-minute evaluation horizon is **fixed by this retrospective design after knowing the archival panel existed**, not externally precommitted before October 12. Do not call it a prospective holdout.

## True information firewall inside this software replay

\`build_pre_1344_forecasts()\` opens only the SHA-locked early WIN, middle WIN and WIDE, race-card/source clocks, and the separately stored historical past-start records. It **does not read** the 13:44 target file or an official race result. It creates 21 fixed candidate next-price distributions from the same middle q:

**Three market-only controls:** persistence of q(13:26); linear-in-log support momentum extrapolation over the previous 65 minutes into 18 more minutes; the same momentum plus the **complete-graph WIDE residual horse-node effect** with illustrative beta 0.25. These are predeclared computational contrasts, not coefficients calibrated on the market target.

**The same physical→social model, not standalone horse fit:**
- PR #17's ahead-of-horse nonlocal first-passage SDE at hypothetical \(c=2\) m²/s gives a physically coupled top-one distribution \(s^\mathrm{horse}_i\).
- The horse physical initial information is either the observed **13:26 q** (the voter market is also initialized with 13:26 q), or a **separate** past-only JRA form \(h\). The h data were collected/normalized after the October 12 target: this second arm is explicitly a *postrace source reconstruction*, not an authentic then-known horse signal.
- The PR #19 **continuous no-sharp-threshold** voting law uses four synthetic rounds, cumulative pseudo-stakes 3000, and four batches of 250 imaginary votes; the horse signal is available from round **1, 3, or never (5)**. Identical physical/voter seeds are used across contrasts.
- NEW: Instead of simply comparing WIDE nodes to horse ABM independently, add the 13:26 WIDE residual ONCE **to the physical horse signal before voters see it**:
  \[
  s_i^{\mathrm{horse+WIDE}}
  =\frac{s_i^\mathrm{horse}e^{0.25\,r_i^\mathrm{WIDE}}}
         {\sum_js_j^\mathrm{horse}e^{0.25\,r_j^\mathrm{WIDE}}}.
  \]
  Then feed this modified signal into **the same PR #19 smooth bettor model** starting from the same observed q(13:26). No second multiplication by the WIDE node is applied at final ranking. Keep an exactly paired source-aligned \`WIDE_residual\` branch and a **fixed one-horse cyclic node-shift placebo** that retains node values but breaks their assigned horse identities.
- Negative controls demand that the unmodified physical signal reproduces PR #19's original physical→voter output (identical seeds), and that **neither real WIDE nodes nor rotated placebo affect the price at all if their information is never released**.

All 21 prior-to-target probability vectors are built and frozen in memory **before** \`validate_later_quote()\` opens the separate SHA-locked 13:44 prices. No podium, payouts, finish order or outcome labels are accessed anywhere in this new audit. Score them only against the next **price-index shape** via TV and KL; not race winner Log loss.

## Observed same-provider quote movement, one race only

| Interval by source update minutes | Observed relative WIN-price-index TV movement | Movement / elapsed hour |
|---|---:|---:|
| 12:21 → 13:26 (65 minutes) | **5.36864 pp** | 4.95567 pp/hour |
| 13:26 → 13:44 (18 minutes) | **9.65636 pp** | 32.18788 pp/hour |

This is a sharp descriptive *change in two interval-average rates*. It **does not establish** a market critical point, a new information event or a causal bettor imitation effect: the post-13:26 volume/volatility process and true stake denominator are unknown. Under an illustrative ±0.05 decimal display half-bin (NOT the authenticated JRA rounding rule), even the **conservative marginal TV lower bound** for 13:26→13:44 remains **8.34316 pp**.

## Genuine later-price target vs pre-target model candidates

These numbers are fixed-seed source-locked TV distances to the one real 13:44 full-field WIN quote; smaller is better. They are **not** relative profitability or horse finish accuracy.

| 13:26 information admitted to candidate forecast | Next-market TV (pp) ↓ |
|---|---:|
| Latest 13:26 WIN index held unchanged | 9.65636 |
| WIN market momentum alone | 8.18097 |
| WIN momentum + mid-source WIDE node, fixed beta 0.25 | **7.10411** |
| PR17 horse(qmid) → PR19 smooth informed voter, round 1 | 11.26506 |
| Same with WIDE node added to horse information before voting | 10.79006 |
| Same physical signal plus **horse-ID-shifted placebo** WIDE node | 11.36506 |
| PR17 horse(retrospective h) → informed voter, round 1 | 10.60256 |
| Same retrospective h + correctly aligned WIDE node → voter | 10.20256 |
| Same retrospective h + horse-ID-shifted WIDE node → voter | 10.55256 |

The WIDE-residual vector has meaningful horse-label alignment **inside this exact illustrative score**, but the fully coupled horse→WIDE→voter version still fails to beat the market-only momentum+WIDE baseline. This is a **negative** comparison to retain, not a reason to optimize beta/c after seeing one q2. Same-minute WIN and WIDE pages need not reflect the same atomic underlying money pools, so the apparent signal may be compositional/timing noise.

## Conditional votes: does the observed 18-minute move require new information?

Keep PR #20's **twelve predeclared** sensitivity configurations:
- hypothetical new-to-final pool fraction λ=0.20 or 0.80;
- effective newly sampled vote count N=100/1000/10000;
- stationary independent pseudo-voters qmid, versus an **unobserved heterogeneous** Dirichlet(80×qmid) probability draw followed by multinomial votes.

For each simulated set, compare the observed future q with the **full-field** TV statistic and the **maximum across all 11 horses** of absolute relative log-support change. A tail fraction conditional on a fictional volume/noise model is NOT a real p-value and does NOT identify any real people, their ballots or social behavior. The target q2 is never used to generate the nulls.

For a hypothetical **exact** cumulative-pool-share identity, the later q2 would require a minimum new-to-final fraction

\[
\lambda_{\min}=\max_i(1-q_{\mathrm{13:44},i}/q_{\mathrm{13:26},i})
=\mathbf{0.29262}.
\]

Thus **all six λ=0.20 cells are infeasible under that strong, unverified exact-share interpretation**. Under λ=0.80, all six scenarios are algebraically feasible but the observed q movement is in the upper 5% conditional TV tail in only **2/6**: the **independent** N=1000 and N=10000 assumptions. The independent N=100 case, and all three **overdispersed** cases, do NOT regard the observed movement as extreme. The output appropriately labels this one next market interval **ASSUMPTION_DEPENDENT**. That label does not establish that the exact-share assumption is true.

The no-information null is therefore **not rejected robustly across plausible simulated nuisance configurations**, and even rejection of every listed stationary null would not prove informational herding: other unmodeled drift, stake selection and systematic price-provider behavior could explain the movement.

## Finite synthetic-seed robustness (not additional races)

[The seed-only audit](../../scripts/keiba_r8_threepoint_seed_noise.py) runs five different PR17 horse Gumbel/Brownian and PR19 bettor-uniform seeds (120 virtual horse draws per seed) **against the SAME one real 13:44 market target**. Deterministic persistence/momentum/WIDE prices remain exactly unchanged by horse/voter random seed.

| Candidate (all round-1 horse information) | Mean next-market TV across 5 seeds | Min–max across synthetic seeds |
|---|---:|---:|
| qmid-based horse→voter, no WIDE | 10.438 | 8.432–11.265 |
| qmid-based horse→WIDE node→voter | 10.118 | 8.157–10.990 |
| qmid-based horse→rotated WIDE placebo→voter | 10.412 | 8.682–11.365 |
| retrospective h-based horse→voter, no WIDE | 9.758 | 8.507–11.328 |
| retrospective h-based horse→WIDE node→voter | 9.457 | 8.169–11.178 |
| retrospective h-based horse→rotated WIDE placebo→voter | 9.683 | 8.707–10.903 |
| deterministic WIN momentum+WIDE-node direct forecast | **7.104** | **7.104–7.104** |

Averages reflect simulation noise, not error bars over additional dates or horse populations. In this one observed market interval the illustrative WIDE signal added to horse information lowers the **five-seed mean** error but remains weaker than the direct market baseline. No claim of significance, future predictive value or superiority over a trained model is justified.

## Reproduce, preserving source-clock and no-result firewall

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests -p 'test_keiba_r8_threepoint_conditional_shadow.py' -v
    python scripts/keiba_r8_threepoint_conditional_shadow.py \
      --null-draws 2000 --horse-draws 120 \
      --output tmp/kyoto8-threepoint-shadow.json
    python scripts/keiba_r8_threepoint_seed_noise.py \
      --seeds 5 --horse-draws 120 \
      --output tmp/kyoto8-seed-only.json

Review [GitHub Actions reproducibility](https://github.com/zuizui0223/keiba/actions/runs/40186889486) and the nested PR; source and model data are SHA-locked. The target is always opened **after all forecasts and nulls exist**. This is a retrospective, one-race same-provider shadow, not certified as-of possession of each original horse record. Neither full proprietary quote tables nor underlying past-horse histories nor recommended wagers are published in the new aggregate output.

**Next empirical step:** lock **multiple independently collected upcoming races** with at least three complete WIN timepoints, paired same-time WIDE price panels, actual market total/turnover if licensed, original source reception clock receipts and true horse past movement/going histories. Fit coefficients and nuisance volatility strictly on earlier dates and score full next-market price vectors on new dates; only then ask whether WIDE residual information and physical horse interactions add calibrated, generalizable evidence beyond an autoregressive price-only benchmark.

**Decision now:** movement/market signal **ASSUMPTION_DEPENDENT**; positive physical/behavioral/market criticality, calibrated win probabilities, profit, independent real market next-event replication all **HOLD**. PR #9–#20, main, 2026 Kikuka preseal and formal v3.1 holdout ledger remain unchanged.
