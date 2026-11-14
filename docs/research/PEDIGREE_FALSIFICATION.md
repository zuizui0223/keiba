# Pedigree-vs-management falsification and real-data source gate (2026-11-14)

**Evidence level: SIMULATION ONLY. No empirical horse kin predictive effect has been estimated.**

## Implemented and checked

- scripts/ecology_pedigree_forward.py: frozen outer chronological split, earlier inner lambda tuning, true first-observed cold starts versus already-seen horses lacking same-context histories, sire/dam numerator A, kin prediction vs own historical profile.
- scripts/ecology_pedigree_ablation.py: frozen all-kin lambda applied *without additional tuning* to **full siblings, paternal half-siblings, maternal half-siblings, other related horses, kin observed under different trainer IDs and different breeder IDs**. The manager contrast is made on **training rows from different assigned IDs** only. Maternal/paternal half sibs require both nonshared parents to be known; unknown parentage is not promoted to a half-sib class. All ablations report their own exposed horse and row denominator.
- scripts/ecology_pedigree_stress.py: completely artificial scenarios, three fixed seeds, with the same test schedule and 8 sire families of 8 offspring; never exposed to real horse identities or outcomes.
- No original runner or family identifiers printed or saved. Genetic causality, heritability, H1/H2 and bettor return remain **HOLD**.

## Falsification test results — entirely fabricated data

GitHub Actions run: https://github.com/zuizui0223/keiba/actions/runs/43578464728

| Artificial generator | Mean cold-start kin ΔRMSE in seconds (M0 − M1) | Seeds with Δ > 0 / 3 | Mean test horses with cross-trainer related histories |
| --- | ---: | ---: | ---: |
| Sire-family latent timing shift + independent weak trainer variation | **+0.235763** | 3/3 | 64 |
| NO genetic timing signal; sire groups placed in perfectly matching trainer groups | **+0.238727** | 3/3 | **0** |
| NO genetic timing signal; trainer groups cross sire families | **0.000000** (λ selected 0) | 0/3 | 64 |

This is a *constructive counterexample*: predictive improvement **cannot identify genetic causation** when bloodline and trainer are perfectly collinear. The 0 cross-trainer-exposed group in the confounded synthetic population is **absence of overlap**, not evidence that genetic transmission is absent. The all-kin model uses the identical 0/0.25/0.5/1 lambda grid and 20-day fabricated calendar in every scenario. Absolute simulated effect sizes are arbitrary and have no interpretation as real racehorse seconds, power, or true family-variance magnitudes.

The cross-trainer ablation can reduce *one* shared management explanation but cannot exclude shared owners, breeder selection, maternal environment, training routines before the observed race, or assortative race entry. In real cohorts, partial/blank IDs are **HOLD** rather than a negative relationship. Even a positive cross-trainer result is still observational.

## Real dataset metadata audit

Dryad source DOI: https://doi.org/10.5061/dryad.qbzkh18m0 (Wilson 2022; companion study Sharman, Young and Wilson 2022, https://doi.org/10.1098/rsos.220691).

GitHub Actions source probe: https://github.com/zuizui0223/keiba/actions/runs/43578098393

- Official Dryad API returned dataset ID **91509**, versionNumber **4**, publication date **2022-10-24**, licence declaration **CC0-1.0**.
- Ephemeral download attempts for original README and archive returned **401** on the version-agnostic file API routes and **403** on the official file-stream URLs.
- Therefore **no raw dataset bytes were obtained**, not even a verified column schema; the unrelated paper's published counts must **never** be reported as rows processed here.
- The publication reports **906,027 racing performances, 101,257 horses, 41,107 dams, 2,887 sires** on British turf flat races (1996–2019). These are published study numbers, not measurements in this repository.
- The paper's identity variance decomposition (offspring **18.9%**, dam **2.7%**, sire **4.3%**) explicitly does **not** cleanly separate genetic and environmental effects. Reference: https://pmc.ncbi.nlm.nih.gov/articles/PMC9532991/.
- This Dryad release is potentially relevant to full-race speed, **not** the current RQ first-GPS target. Never combine those outcomes as identical without measurement mapping.

## Next empirical gates

1. Obtain source-allowed horse-ID × sire/dam registry linkage and verify exact identities *without guessed name matches*. If a Dryad public file becomes accessible through an approved route, verify its true column schema and exact time order; do not guess race dates or first-section values.
2. Separately source and authenticate trainer IDs, breeder IDs, sex, age and full actual-starter/finisher denominators. A source-assigned trainer ID is not a validated treatment history.
3. Freeze the same context and time split; compare M0 vs all-kin vs full/paternal/maternal/other vs cross-trainer **on identical held-out eligible cases**, with exposure denominators and uncertainty clustered by sire family, horse and race; do not compare disjoint channels without matching case sets.
4. Inspect support for different breeder × sire assignments, one-parent unknownness, pedigree truncation, inbreeding F and batch-dependent parentage provenance. Do not present F computed from a shallow pedigree as genomic F.
5. Only after support, fit a mixed animal model with additive genetic A/G, permanent individual effects, maternal/management effects, race and measurement terms, and compare **out-of-time predictive log score/RMSE** as well as uncertainty, before any heritability claims.

## Connection with the existing horse ABM–PDE–market architecture

**Design-only interface; NOT an implemented connection.** In a later authorised private run, the earlier-validated kin forecast K_i(t) can be frozen as a pre-race component of horse i's latent pacing/ability distribution. Horse ABM then simulates competition, PDE aggregates outcome distributions, and market/voter ABM sees only information actually available by the pre-race price snapshot, never results from the race being scored. Keep the original no-pedigree M0 and the odds-only baselines unchanged; evaluate the incremental predictive loss/RMSE of one frozen kin channel against identical future races. Existing unmerged betting PRs do not justify declaring this integrated or statistically validated.

**Scientific conclusion now:** bloodline-linked prediction and genetically inherited pacing are **different estimands**. We have an explicit simulation showing how conflating them leads to false biological interpretations, and a reproducible method/hold gate for the eventual real-data test.
