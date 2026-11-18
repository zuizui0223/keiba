# Japanese race history 2022–2024: real-parent vs matched false-parent outcomes

**Status (2026-11-16): 19-shuffle post-hoc falsification completed on a locked second-source cohort.** Positive family-ID association; **no claim of genetic causation, heritability or national all-horse pedigree**.

## Real observations and benchmark

A pre-2022-only name-plus-two-event crosswalk identified 20,400 candidate horses between the original 2010–2021 race-history archive and a separate 1990–2025/03 historical SQLite database. On the eligible **2022–2024** out-of-period cohort, **12,919 horses, 255,484 start records**, the frozen 2018–2021-trained ridge models give:

| Prediction | Normalized-rank RMSE (equal horse weights) |
|---|---:|
| No parent-family history (baseline) | 0.312777516 |
| Actual same-sire and same-dam other-horse prior histories | **0.312455062** |
| **No-parent minus actual-parent gain** | **+0.000322454** |

The primary gain is only **0.103%** of the no-parent baseline RMSE. It is not a probability calibration or betting return. The earlier per-year gain attenuates from **+0.000472 in 2022** to **+0.000212 in 2023** to **+0.000069 in 2024**; in 2024 both learned models lose to the fixed midpoint. Partial 2025 reverses the gain (−0.000360), and is excluded from this primary analysis.

## New actual-source matched negative controls

[Successful empirical GitHub Actions run #43889528129](https://github.com/zuizui0223/keiba/actions/runs/43889528129), 2026-11-16 14:52 UTC. Its head SHA was **37fe04c6fc3a7401b0abda40c015550c666122b2**, job **133376636858**. GitHub artifact **14234479873**, name **japan-2022-2024-parent-placebo-aggregate-only**, ZIP SHA256 **5234f7517cad47b4e676635205910e76ac75d815cd1397bb50243ad5e1c9023e**.

All pre-existing source SHA, 255,484-row cohort, 12,919-horse cohort, and exact original no-parent/true-parent RMSE values passed parity checks before evaluating the shams. The workflow also passed seven synthetic focal-exclusion, missing-parent, parent-pair-count and identity-map tests. The false parent pair was swapped only within an old-source five-year birth cohort, first JRA/NAR circuit and known/missing sire/dam groups; the **two parent IDs were permuted as a pair**, not independently.

| Metric | Parent-ID history RMSE gain |
|---|---:|
| **Original observed kin mapping** | **+0.000322454** |
| **Mean of 19 false-family mappings** | −0.000040235 |
| Best false-family mapping | −0.000006040 |
| Worst false-family mapping | −0.000104792 |
| 95% empirical sham percentile range (not a CI for the real effect) | −0.000093407 to −0.000006419 |
| Shams beating or tying real gain | 0 / 19 |
| Plus-one Monte Carlo upper-tail rank | **p = 0.05** |

This Monte Carlo rank p is exactly **the smallest possible with only 19 permutations**, selected in the protocol before executing the placebo test but **after observing the original positive effect**. Do not report p<0.05 or reinterpret these as a fully confirmatory randomization test. All 19 shuffled parent models were slightly worse than the no-kin baseline; the real mapping was modestly better.

The logged per-seed gain for all 19 simulations, the source SHAs and the artifact digest are retained permanently in [aggregate evidence JSON](../evidence/japan-2022-2024-parent-placebo-19-20261116.json). The source artifact is time-limited; the JSON is a traceable reconstruction of logged **aggregate** statistics, not a claim to reproduce or redistribute copyrighted horse-level records.

## Mechanistic interpretation

**Supported:** conditional on exact source releases, the historical identity of recorded same-sire or same-dam relatives provides more information about heldout normalized finish order than a set of matched fake parent assignments. This argues against the entire real-parent improvement being produced only by parent-label frequency or simple birth-cohort/JRA-NAR/missingness marginals.

**Not supported:** a horse's additive genetic breeding value, a quantitative genetic heritability estimate, stable inherited racing ability, MSTN genotype effects, population-wide full pedigree A, animal social behavior, or the existence of a profitable odds threshold. Family IDs also encode stable stud-farm, owner/selection, training and management conditions. The matched permutation does not hold those environmental pathways constant. Original 2010–21 and later 2022–24 sources may share upstream race websites. The prior historical-event crosswalk is not official registry verification.

**Important unresolved outcome issue:** the original races normalized rank by consecutive *classified finishers*, while the independent source divides by its *declared field size*. This is not an identical response variable across datasets. A true outcome-denominator audit, stronger portable baseline and official identity join have priority over scaling this small statistical gain into a claim about genetic mechanism.

## Decision / next test

Keep this as a **positive but small, conditional family-history prediction result** and leave the PR **draft**. Before interpreting genetics, first verify a more comparable classified-finisher denominator on the actual 2022–24 race source, and evaluate a strong no-family model with pre-race age, sex and historical race-class/track context where reliably comparable. Next, independent future validation and licensed official pedigree IDs would be needed to connect this to the 5,878-horse partial Wikipedia A or the unrelated 370-horse anonymous genomic G. Never join on surname, racing name prefix (including Meisho) or an unverified ID.

The implementation, 19 seeds, limitations and null construction are frozen in [the separate protocol](JAPAN_2022_2024_PARENT_PLACEBO_PROTOCOL.md), which is expressly **post-hoc** relative to the previously observed improvement.
