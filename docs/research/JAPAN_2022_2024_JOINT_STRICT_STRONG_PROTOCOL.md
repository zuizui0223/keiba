# Joint 2022–24 strict-ranked races × strong old-source prehistory (post-hoc)

**New design logged 2026-11-16, *after* observing both previous separate favorable sensitivities.** This joint evaluation is **exploratory**; it must not be promoted to a preregistered, fresh holdout.

## One fixed question

On only those 2022–2024 races whose final ranks and declared field sizes agree across the **same independent-source Race.horses and Horse.races tables**, does the original sire/dam-sharing other-horse history continue to reduce normalized-rank RMSE when pretarget own-horse age, last-known sex, days since previous pre-2022 start, 10-start mean and former JRA share are included?

## Three mandatory reproductions before scoring

1. **Source A and B SHA256** must equal their original fixed hashes. At least two corroborated race outcomes on distinct **pre-2022** dates link old and new source IDs. No later result enters model identity or training.
2. Full 2022–24 cohort exactly **255,484** rows / **12,919** horses. Refit original frozen model and confirm no-parent RMSE **0.31277751588017505** and real-parent RMSE **0.3124550620307501** to 1e−8.
3. Refit post-hoc expanded models on the same source-A pre-2022 calendar-year training and verify **all-row expanded no-parent 0.31169267268761647 and expanded +parent 0.31143282328331967** to 1e−8.
4. Independent-source race field/rank audit must select exactly **244,147** rows / **12,887** previously checked strict-complete participants. On those rows the **original** model must reproduce RMSE **0.31354335632983643** (no parent) and **0.3132186661774923** (+parent) to 1e−8. Do not cherry-pick a different complete-race subset.
5. **Only then**, with the same fixed enlarged coefficients and no resampling/tuning, score the expanded no-parent and expanded +parent models on the strict rows. Report pooled, 2022, 2023, 2024, fixed midpoint reference, and separate 399-draw horse/day one-way bootstrap intervals. Preserve a null/negative result.

False family shuffles (19) and initial 2022–24 outcomes were inspected already and do **not** become new independent evidence by combining filters. Source B is a second source release, not an officially certified race result or studbook. The strict ranked subset excludes nonfinishers and ties, and includes only 2021-preexisting horses matched by historical events: limitations on selection and generalization remain.

## Implementation

scripts/ecology_japan_2022_joint_strict_strong.py combines existing published and unit-tested components; new evidence is aggregate-only. No third-party raw rows, horse IDs, names, actual later-source crosswalk or individual predictions are distributed. Upstream racing-record rights are not independently cleared. Only family-history **prediction association** can be discussed: additive genetic variance/heritability, true genome G, multi-generation pedigree A, causal father/mother effect, odds or betting-profit improvement remain HOLD.
