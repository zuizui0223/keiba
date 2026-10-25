# Independent horse form as a market-innovation hypothesis, not simply a finish predictor

**2026-10-25 | Draft exploratory reconstruction after real races.**
This depends on [PR #15](https://github.com/zuizui0223/keiba/pull/15), which depends on [PR #14](https://github.com/zuizui0223/keiba/pull/14). The external 2026 菊花賞 M0/M1/M2 sealed prediction SHA, official v3.1 holdout and main are not modified.

## Why another integration diagnostic is essential

A horse-history-informed model may (a) describe observed later finishing outcomes, yet (b) fail to explain the *realized odds trajectory*. Prior experiments found these could disagree. Neither provides a causal interpretation of bettor imitation. The new bridge asks a sharply defined observational question:

> Given the earliest SAVED full-field WIN odds q0 for a race, does the independently sourced **past-only** horse-form vector h point toward the subsequently SAVED market price index q1? Does it do so better than assigning the identical histories to the wrong horses?

The key is to keep the **same** horse-history prior as the upstream physical horse ABM and its bettor information channel in PR #15, rather than inventing an unconnected second model. The future market is a *validation target*, never a horse-skill feature.

## A real implementation error corrected

The PR #15 external history-only horse input was partially contaminated by q0 through the fixed 2-draw equivalent Monte Carlo smoothing. The numerical safeguard itself is valid, but in a history-only horse arm its baseline must be the *horse's own input prior*, not the market prior. This branch makes the smoothing conditional on the actual physical input prior:
- market-proxy horse arm -> smoothing with q0, backward-compatible with PR #14;
- history-only and shuffled-history arms -> smoothing with their corresponding history priors;
- mixed early-market/history arm -> smoothing with its actual mixed prior.

A regression test holds the history prior and all physical randomness fixed while **changing early market odds**. All three horse-only distributions (legacy, SDE/no crowd, SDE/weak) and the downstream voter information signal must stay identical; only the voter pool q0 and its later simulated price are allowed to change. This guards against hidden double counting at the model boundary.

## Fixed market-innovation experiment

Let \(q_{0,i}\) be inverse-first-quote relative support, \(q_{1,i}\) inverse-later-quote relative support, and \(h_i\) the source-locked past-only horse form. All three are positive vectors summing to one.

Define a **non-fitted** source-bridged quote-index prediction:

\[
\widehat q^{\,H}_{1,i}
  = \frac{q_{0,i}^{0.8}h_i^{0.2}}
         {\sum_j q_{0,j}^{0.8}h_j^{0.2}}.
\]

Its negative-control comparator uses the identical \(h\), shifted by one horse ID *within each race*:

\[
\widehat q^{\,S}_{1,i} \propto
     q_{0,i}^{0.8}h_{\text{cyclic-shift}(i)}^{0.2}.
\]

The reference is simply \(\widehat q_{1}=q_0\) — no new information beyond initial price. The 20% form weight was chosen as a fixed *illustrative* coefficient; it is not fitted or claimed optimal. No threshold is selected from the six scored results.

Only after the three candidate vectors have been created do we compare them against the actual later q1 using:
- **TV distance** in percentage points between normalized quote indices;
- **KL divergence** \(D_{\rm KL}(q_1\|\widehat q_1)\) in nats, an index-shape discrepancy;
- the weighted dot product of the observed log market change and premarket history-vs-market residual (a descriptive alignment only).

A quote-index value is **NOT** a vote share, nor the empirical win probability. Therefore these metrics are **not** event log-loss, genuine bet-flow inference, or evidence that traders learned the historic horse result.

## Timeline and source limitations

The complete early/later WIN panel comprises 2026-10-12 Kyoto R8–R12 (5 races, 51–69 minute quote windows) and 2026-10-18 秋華賞 (1 race, ~21.67 hours, mixed source/update-clock semantics): 6 independent race outcomes on **only 2 dates**, 84 horse–race entries. The earliest saved quote is NOT the opening market. A price update stamp is not the same as actual bet transaction time.

- The October 12 horse-history file was retrieved and normalized **after** the target race even though it contains only older starts.
- The October 18 pre-draw history lacks independent evidence of public reception before the model decision time, and its horse numbers require the separately fixed JRA name/draw crosswalk.
- This source cannot be promoted to authenticated as-of performance. Both the history and price comparison are **exploratory postrace reconstructions**, even if the implementation enforces that no event outcome is a feature.
- Winner or WIDE-event scores from PR #15 must NOT be mixed with next market-index distances and optimized using the same tiny six-race cohort. Matched live receipts, independent official outcomes, and new race days are required.
- More sophisticated market microsimulation would need synchronized ticket volume or pool data to distinguish informed buyers from mechanical price inertia. This study only has displayed, updated quote indices.

## Replay and CI

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests -p 'test_keiba_history_market_innovation_audit.py' -v
    python -m unittest discover -s tests -p 'test_keiba_coupled_history_falsification.py' -v
    python scripts/keiba_history_market_innovation_audit.py --output tmp/history-market-innovation.json

The output contains only race-level diagnostics and aggregate mean scores, not the full raw individual horse-history rows. Each contribution is preserved by race and meeting date, and future quote access occurs **only** after model vectors are constructed.

## Scientific decision

The independently sourced past form is now a clean **physical horse input** to the coupled ABM and a clearly separated *candidate* market innovation feature. A positive market-alignment score, if observed, would support further prospective testing of information assimilation. It would not identify actual imitation, a transition threshold, or a guaranteed wagering advantage. The **future** target is multi-date, externally timestamped horse histories, market snapshots and authentic race results; until then **HOLD**.


## 2026-10-25 source-locked six-race result

[Dedicated CI](https://github.com/zuizui0223/keiba/actions/runs/40164391767) passed the new two-stage no-future-quote tests and the source-locked JRA archive check.

| Candidate next WIN quote-price INDEX | Mean 6-race TV distance (pp) ↓ | Mean KL(q1 || candidate), nats ↓ |
| --- | ---: | ---: |
| Earliest saved quoted q0 unchanged | **3.43655** | **0.004713** |
| Same q0 + 20% correct horse history h | 6.53113 | 0.012543 |
| Same q0 + same historical scores shifted to the wrong horse | 7.40114 | 0.016072 |

Adding h improves next-quote TV in just **1/6 races** versus q0 alone; the correct history beats the shifted identity in **4/6 races**. When stratifying by date, the correct history minus q0 distance is +3.81616 pp (worse) for five 2026-10-12 races, but −0.51332 pp (better) for the sole 2026-10-18 race. Comparing these price indices does **not** estimate actual betting stakes, new information arrival times, bettor imitation or future finishing performance.

**Correction to previous physical simulation:** after changing the finite-MC prior to use the actual physical input prior (no cross-contamination from q0), the information-voter WIN Log loss on the SAME six already observed podiums is:

| Input to both horse ABMs | Information-voter WIN LL ↓ | Threshold-mixed WIN LL ↓ |
| --- | ---: | ---: |
| Earliest saved market q0 | **1.703731** | **1.652295** |
| Correct horse historical form | 1.810225 | 1.691430 |
| Same history shifted to a different horse | 1.853751 | 1.709529 |
| 80% earliest q0 + 20% historical form | 1.715829 | 1.655729 |

These replace the prior PR #15 *uncorrected history-only* scores; the market-only reference stays exactly unchanged. The negative-control direction persists but there is still no incremental benefit over the q0-informed integrated model under these fixed assumptions. This is NOT future holdout performance; it is a source-limited retrospective sensitivity on two dates, and the history file's reception before the target race is unverified.
