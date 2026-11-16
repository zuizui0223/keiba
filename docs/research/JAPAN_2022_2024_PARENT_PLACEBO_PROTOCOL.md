# Post-hoc parent-ID permutation falsification: Japan 2022–2024

**Protocol added 2026-11-16 after the +0.000322454 RMSE improvement was already inspected.** This is a **post-hoc negative-control experiment**, not preregistered independent confirmation, a claim of inheritance, or a new heldout set. The original scores and data versions are locked.

## Question and null

The already recorded positive difference between (1) a model using only the focal horse's prior performances and racing contexts and (2) the same model plus historical performances of **other horses sharing a recorded sire or dam** can arise from real family clustering, source artifacts, cohort selection or breeding environments. It need not arise from causal genetic inheritance.

**Negative control:** Break which focal horses are assigned which recorded sire/dam **pairs**, holding their pre-2022 source distributions stable. If performance is better for the real mapping than for similarly structured fake family mappings, that supports *identity-specific shared-parent history as additional prediction information*. It still does **not** distinguish genes from stud farm, age, training, commercial selection or historical source structure.

## Immutable empirical target

- Source A archive (2010–2021): SHA256 c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f
- Source B independent SQLite (2022–24 scoring only): SHA256 7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9
- Match: exact normalized name + two matching distinct **pre-2022** racing days, ranks and distances; no future result used for identity.
- Historical training years: 2018–2021, each with only previous-year records. Frozen ridge alpha=100, no heldout labels in model fitting.
- Test cohort: **255,484** eligible race-horse rows, **12,919** distinct previously active horses, 2022–2024 only.
- Frozen primary results: no-kin RMSE **0.31277751588017505**; real direct-parent history RMSE **0.3124550620307501**. Absolute gain **+0.0003224538494249751**. Any mismatch >1e−8 in this exact result is a **hard HOLD**, not a new number.

## Placebo intervention

For each original horse, infer a 5-year birth cohort from its **pre-2022 first-source racing year minus age**; put invalid ages in a separate unknown cohort. Determine circuit from first valid old-source appearance (JRA/NAR); distinguish missing/known sire and dam.

Within each *(birth bin × first circuit × sire-known × dam-known)* stratum, shuffle **entire (sire ID, dam ID) pairs** across horses, including blank fields. **Do not** independently shuffle sire and dam, which would generate artificial combinations and change family structure. This preserves the aggregate parent-pair multiset, each horse's known/missing parent pattern, and stratified training sample. It intentionally changes which individual belongs to which family.

For each seed, apply the **same historical-only permutation map** to all training years and the heldout target horses. Aggregate each focal horse's prior racing history to one mean per *(horse × track-type × distance bin)* as in the original peer-history feature; reconstruct only the four sire/dam-history features. Exclude the focal horse from relative histories. **Refit** the same ridge model on the frozen original training-year labels; never refit the no-kin baseline. The heldout labels are used solely once per pseudo-model for RMSE scoring. Synthetic unit tests enforce exact identity-map feature parity, unknown-parent safety, parent-pair multiset invariance and no self-peer.

Use seeds **2026111600–2026111618** (**19** permutations) as the first feasibility/negative-control run. For actual parent-history gain Δobs and sham gains Δb define the Monte Carlo upper-tail rank p=(1+#{Δb ≥ Δobs})/(B+1). With B=19, **the minimum possible p is 0.05**; therefore it is a limited-resolution *post-hoc falsification screen*. It must not be called a definitive confirmatory p-value. More permutations or an external cohort would be needed for a stronger conclusion, with no seed or stratification tuning after seeing outcomes.

## Interpretation

| Finding | Permitted conclusion | What it does not show |
|---|---|---|
| Real gain exceeds most shuffled parent pair gains | The particular source-recorded family mapping adds information compared with matched random mappings | Genetic heritability, biological mechanism or external population effect |
| Real gain resembles/shrinks below shuffled gains | Incremental familial predictive signal is not robust to this placebo | Biological relatedness is absent |
| 2024 models both lose to fixed midpoint, and 2025 partial reverses | Time transfer is limited; even a positive pooled gain may be operationally weak | A reliable wager, an odds-market edge |

**Deliberate remaining HOLD:** the source-A relative rank denominator is complete classified finishers, while source B uses declared field size. Do not pretend they are exactly commensurate. An outcome harmonization audit, horse-by-race official identity verification, richer no-kin features and a true independent future cohort remain separate work. Real multi-generation pedigree A (Wikipedia selective sample), anonymous genomic G (370 horses) and family-race-history labels cannot be joined without audited identifiers.

## Implementation and provenance

- Script: [ecology_japan_2022_parent_placebo.py](../../scripts/ecology_japan_2022_parent_placebo.py)
- Synthetic unit tests: [test_ecology_japan_2022_parent_placebo.py](../../tests/test_ecology_japan_2022_parent_placebo.py)
- Dedicated workflow: [ecology-japan-2022-parent-placebo.yml](../../.github/workflows/ecology-japan-2022-parent-placebo.yml)

The source rows are downloaded only transiently on the runner and deleted before uploading aggregate-only diagnostics. Source-A license is unknown; source-B upstream race rights have not been independently verified. Raw third-party records, horse names, IDs, pseudo-pedigree assignments and individual predictions are not redistributed.
