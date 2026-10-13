# Ecological research plan: racehorse individual × environment × competition

Status: **research proposal, not empirical support** (2026-10-12).
This is a biological research track independent of betting-market optimisation. No causal claims, validated fitted model, or ecological finding is made here.

## Central question

競走馬の競走パフォーマンスは、一貫した個体差だけで説明できるのか。それとも、同じ個体の環境応答（reaction norms）と競争相手の構成によって系統的に変化するのか。

### Ecological interpretation and limitations

- **Individual ecology / phenotypic plasticity**: quantify among-horse heterogeneity in environment–performance slopes rather than only average ability. An individual regression slope in observational competition data is *context-dependent performance*, not automatically physiological plasticity or adaptation.
- **Biotic interactions / competitive context**: test whether a horse's pre-race running-style history interacts with pre-race competitor composition. Direct dominance/interference cannot be inferred from order of finish alone.
- **Performance niches** (exploratory): compare conditional performance breadth with peak performance in observed race conditions. Entry/placement is selective, so this is not a realized ecological niche in the wild.
- Races are highly managed and nonrandomly assigned. Racing results do not identify natural selection, evolutionary adaptation, or horse personality without additional evidence.

## Confirmatory hypotheses (freeze before viewing new outcomes)

**H1: heterogeneous environmental reaction norms.**
Within horse and conditional on surface, distance, class, venue, year/season and jockey, response to ground condition differs among horses (variance of horse-specific ground-effect slopes > 0).

- Null: all horse-specific slopes are exchangeable with zero among-horse slope variance after adjustment.
- Competing explanation: apparent interactions arise from differential race entry, class changes, fitness/layoffs, jockey assignment or different conditions being experienced at different ages.
- Identification check: horses must be repeatedly observed under distinguishable ground conditions with overlap in distances/classes; quantify within-horse support before fitting. Results for unsupported extrapolations are HOLD.
- Success requires an interpretable slope-variance estimate with uncertainty **and** pre-registered time-forward improvement over the no-slope model. Statistical evidence alone is not sufficient to call a new ecological mechanism.

**H2: competitive-context dependence.**
Pre-race running-style profile of a horse interacts with the proportion of other entrants previously observed as early leaders. Test, for example, whether historical front-runners fare relatively worse when several other front-runners are entered, after accounting for opponents' pre-race strength and race conditions.

- Null: no horse-style × competitors'-style interaction.
- Alternative explanations: stronger fields, jockey strategy, post-entry horse selection, course geometry and ground condition.
- Define running style exclusively using *prior* races; do not use pace, positions, or sectionals from the target race as predictors. If only actual race pace is available, analyze it descriptively, not as a leakage-free pre-race predictor.
- Include a negative-control interaction or a permutation within plausible pre-race strata, and do not equate a correlational interaction with a behavioral mechanism.

**H3: specialization vs generalism (exploratory).**
After entry selection and unequal sample size are addressed, horses with more peaked conditional performance curves may have stronger performance in preferred conditions but lower consistency across environments. Do not label this an adaptive trade-off based on a negative correlation alone.

## Data requirements

**Grain: one row per horse–race start**, indexed by stable horse_id and race_id, with source URLs, source license, collection timestamp and availability cutoff.

| Layer | Minimum fields | Status in existing repository |
| --- | --- | --- |
| Individual | horse_id, age, sex, pre-race starts, previous outcomes | partial: horse names and selected course aggregates; no complete repeated-start panel |
| Environment | race date, track, turf/dirt, distance, ground condition, weather, course geometry | partial: track, surface, distance, date for one Kyoto card; weather and ground labels not consistently present |
| Competitive context | entrants, field size, gate, carried weight, jockey, pre-race style, opponent pre-race performance | partial: field size, horse number, some historical jockey data; style/ability series absent |
| Response | official placing, individual finishing time, race-time comparison, withdrawals/nonfinishers | partial: selected retrospective narrative, not a consistent historical outcome table |
| Provenance | public data source, observed_at, feature_available_at, source terms | partial: existing timestamp/source conventions provide a useful template |

Do **not** derive individual time-series observations by expanding a horse's aggregate Kyoto record [win, second, third, other]. Those summaries contain no race-specific exposures, times, or contemporaneous competitors. Archived 2026-10-12 odds snapshots are market metadata, **not** an ecological performance panel.

Suggested source assessment: JRA official race results (historical lookup); JRA-VAN Data Lab historical structured feeds where permitted. Inspect access terms, attribution and redistribution limits before collecting or committing any licensed data. Avoid committing restricted raw records.

## Analyses

1. **Cohort definition**: specify date range, eligible flat races, surfaces, distance classes, standard exclusions (nonfinishers/invalid time handled transparently). Record sample counts, repeated-start counts, exposure overlap, missingness and loss to follow-up. Use several years and multiple racecourses; do not rely on a single race-day card.
2. **Response**: primary observed speed (distance / individual finishing time), with flexible distance, surface/track, class and calendar adjustments; race-level random effects for common shocks. Secondary normalized relative rank or time-behind-winner for within-race comparisons. Neither is fitness in the evolutionary sense.
3. **M0 (individual heterogeneity)**: horse random intercept + race random intercept + jockey effect (where estimable), adjusted for age, class, distance, surface, venue and season.
4. **M1 (reaction norms)**: add a horse random slope for ground condition (possibly separate for turf/dirt), and horse intercept–slope covariance; use partial pooling. Examine within-horse variation; environmental main effects and race fixed intercepts cannot be simultaneously identified when the environment is shared within each race.
5. **M2 (competitive composition)**: on a race-relative performance outcome, add pre-race horse-style × pre-race front-runner share among *other* entrants; adjust for pre-race opponent strength and field size, using only past data.
6. **Variance decomposition**: quantify horse intercept, individual environment slope, jockey, race and residual uncertainty, acknowledging dependence on chosen scale. Do not call the components genetic heritability or adaptive fitness.
7. **Temporal evaluation**: rolling forward held-out race dates, with training features recomputed strictly as of each start date. Report log score/MAE as appropriate, uncertainty calibration and effect stability; include cold-start horses separately. Never randomly split horse-race rows when future records leak into past feature history.
8. **Robustness**: separate turf and dirt, stratify by distance/class and venue; rerun with age and rest intervals, historical opponent strength and entry propensity adjustment where possible; report multiplicity/exploratory status.

### Decision rules

- H1 supported **only if** the repeat-exposure diagnostic passes, slope heterogeneity is distinguishable from the preregistered null with uncertainty, time-forward prediction improves under the chosen score, and sensitivity checks do not overturn interpretation.
- H2 supported **only if** the preregistered interaction is stable in unseen race dates and survives opponent-strength and cohort-selection sensitivity. Otherwise report inconclusive or unsupported, not “ecological competition proved.”
- No inference until panel data, feature cutoffs, official outcomes and a reproducible pipeline exist.

## Deliverables and boundaries

Research-focused outputs: response curves with horse-level partial pooling intervals; individual intercept–slope covariance; variation partitioning with uncertainty; competition-context interaction; tests against ecological null hypotheses; readable limitations.

Betting/odds optimization from analysis/kyoto-20261012 and PR #1 remains a separate application. Do not use odds improvements, wager ROI or one-day hit rates as evidence that H1/H2 hold.

## Prior literature (not a novelty claim)

- Dingemanse et al. (2010), *Behavioural reaction norms: animal personality meets individual plasticity*. Trends in Ecology & Evolution. DOI: 10.1016/j.tree.2009.07.013.
- van de Pol (2012), *Quantifying individual variation in reaction norms: how study design affects the accuracy, precision and power of random regression models*. Methods in Ecology and Evolution. DOI: 10.1111/j.2041-210X.2011.00160.x.
- Maeda et al. (2012), *Influence of Track Surface Condition on Racing Times of Thoroughbred Racehorses in Flat Races*. Journal of Equine Veterinary Science. DOI: 10.1016/j.jevs.2012.02.012.
- Oda et al. (2024), *Assessing the predictability of racing performance of Thoroughbreds using mixed-effects model*. Journal of Animal Breeding and Genetics. DOI: 10.1111/jbg.12822. Individual ability and venue/distance models are not by themselves a new contribution; genuine novelty of H1/H2 needs a formal literature review.

## Near-term milestones

- M1: freeze ecological questions, data dictionary, prior literature and exclusion rules.
- M2: establish source/license, assemble historical *longitudinal* horse–race panel, audit coverage.
- M3: fit M0/M1 and perform time-forward checks; report supported, inconclusive or rejected hypotheses.
- M4: assess H2 with pre-race running-style indicators and repeated changing opponent composition. A synthetic exploratory interaction pipeline is implemented; **empirical validation remains HOLD pending longitudinal licensed data**.


## Implemented computational progression (2026-10-12)

The code on this research branch now provides:

1. `scripts/ecology_panel.py`: rights/provenance/clock validation, full-roster
   audits and strict prior-calendar-date construction of own running-style
   history and leave-one-out competitor composition. Produces a machine-readable
   `HOLD_*` gate when repeated observations or data rights are lacking.
2. `scripts/ecology_h1_pilot.py`: **exploratory, not confirmatory** race-relative
   standardized speed, mixed-model M0 random horse intercept vs M1 random
   horse intercept + within-horse ground-response slope, separated from
   between-horse exposure frequency. Horse exposure means are derived from
   training dates only, followed by forward-date evaluation and paired race
   bootstrap of prediction-error differences. No valid random-slope
   confidence interval or race- and horse-clustered inferential p-value
   is claimed.
3. `scripts/ecology_demo_data.py`: deliberately fabricated longitudinal
   records for testing implementation. Synthetic data cannot support H1/H2.
4. `tests/test_ecology_*.py` + GitHub Actions: guardrails for future leakage,
   duplicates, roster completeness, time split and a strictly labelled
   synthetic model smoke run.

**Methodological boundary:** standard random regression on race-centred
performance is susceptible to within-race dependence, nonrandom entry,
class/age/fitness variation, and jockey interactions. It is an operational
preliminary check and does not satisfy the prespecified H1 inference
criteria above. The next confirmatory version should use a crossed
horse/race/jockey hierarchical structure (or an appropriately adjusted
race-relative model), assess horse-by-going overlap conditional on class
and venue, and estimate uncertainty for heterogeneous within-horse
responses through simulation or a suitable bootstrap/Bayesian model.
The pilot contains no H2 fitted inference yet.

**Source terms, verified on 2026-10-12:** JRA-VAN Article 7:
https://jra-van.jp/info/rule.html ; JRA-VAN developer statement on
data redistribution, 2026-07-06:
https://developer.jra-van.jp/t/topic/899.
Use any restricted real records only under appropriate permission;
never commit those source files by default.


## H2 novelty and existing biological literature

**Established before this repository**: Spence, Thurman, Maher & Wilson
(2012), *Speed, pacing strategy and aerodynamic drafting in Thoroughbred
horse racing*, *Biology Letters* 8:678–681, DOI:
https://doi.org/10.1098/rsbl.2011.1120, analyzed 44,803 tracked runners in
3,357 races. The authors explicitly discuss front-running/chasing roles,
pacing and aerodynamic drafting. It is **not novel** to say competitors
influence racing tactics or that individual pace phenotypes vary.

The proposed narrower H2 test concerns **within-individual
between-race changes in competitor-style composition**, calculated strictly
from pre-race historical profiles and evaluated after controlling for
prior ability and opponent quality, with date-heldout replication. A distinct
H2 effect is still **only a hypothesis**; data availability and selection
bias may ultimately prevent its identification.

New exploratory code:
- `scripts/ecology_demo_competitors.py`: fabricated horses rotating through
  fictional race fields, with an inserted interaction parameter.
- `scripts/ecology_h2_pilot.py`: baseline vs own-style × rivals'-historical-
  front-running interaction, horse random intercept, frozen predictor means,
  and later-date error evaluation.
- `tests/test_ecology_h2_pilot.py`: turnover, incomplete rosters, predictor
  scaling, mixed source rejection and correct sign in a specifically
  fabricated effect scenario.

The `H2` software demo has **no causal standard errors or inference**.
A preregistered ecological claim requires an independent real cohort,
rival-composition variation per individual, class/venue/jockey/going
checks, opponent selection sensitivity, a suitable multiway
uncertainty method and substantive effect plausibility.


## Additional within-individual competition test and null contrasts

H2 has now been split into (a) **within-horse contextual response**
and (b) **between-horse nonrandom participation (assortment)**.
The methodological references are van de Pol & Wright (2009),
https://doi.org/10.1016/j.anbehav.2008.11.006, and
Martin & Jaeggi (2022), https://doi.org/10.1111/jeb.13900.

`scripts/ecology_h2_within_between.py` is an exploratory horse fixed-
intercept model using strictly historical style profiles, past opponent
ability, context deviations relative to horse-specific training means,
binary going and trait×going adjustment. It reports horse×race two-way
clustered **nominal** uncertainty and compares leave-one-out versus
full-field front-running composition. It cannot resolve time-varying
trainer, jockey, class and nonrandom entry biases.

`scripts/ecology_h2_falsification.py` supplies synthetic null, planted-effect
and *confounded null* with assortative entry and individual going response.
Observed failure on a null case must be interpreted as **a warning**;
a pass on a planted effect is not biological evidence. Implementation
checks can operate with wholly synthetic datasets, whereas the actual
Kyoto one-day historical card remains **HOLD for H1 and H2**.


## Outcome-dependence correction for H2 (2026-10-12)

An important failure mode was identified: race-relative z-speed changes
mechanically when opponents' finish times change, even if the focal horse
is unchanged. Therefore, **H2 biological interpretations must not be
based solely on within-race z-scored speed or rank**.

`scripts/ecology_h2_absolute_speed.py` fits focal **raw individual
speed (m/s)** with crossed horse and race fixed intercepts and
style×going controls, restricting the competitor-context question to
an identifiable focal style×within-horse contextual interaction.
A held-out race has an unknown race intercept; prediction is evaluated
on *within-race raw speed contrasts* rather than the misleading
race-relative z denominator. Both leave-one-out and whole-field
context definitions are retained.

A versioned fictional null/planted/confounded stress check is recorded
in [the absolute-speed synthetic audit](ecology-h2-absolute-stress-audit.md).
The new method is **exploratory only**, not a causal solution to
nonrandom entry, race performance censoring, or changing jockey/fitness.
Read [outcome methods](ecology-h2-absolute-outcome.md).


## Selection, missing speed and real-data onboarding (2026-10-12)

The H2 raw-speed model now retains all confirmed starters as rivals even
when some horses do not finish; it records an explicit postrace speed
selection diagnostic. Former complete-**outcome**-roster exclusion
was an unnecessary, potentially biased selection. A complete
**pre-race starter roster** and sufficient historical pre-race
features remain necessary for identification.

- Regression response is defined only for horses with observed
  positive finish times; missing speed is **not** zero and
  unrecorded finishing times are not automatically imputed.
- A speed-selection report stratifies retention by going, focal
  style and competitor composition. Any missing eligible speed
  triggers a scientific **HOLD** on interpreting the coefficient as
  an all-starter effect.
- A synthetic stress uses both outcome-independent and
  **deliberately outcome/ground-dependent** noncompletion to
  inspect sensitivity; this does not identify real missingness.
- Missingness discussion: Dumelle et al. 2025, *Ecological Monographs*,
  https://doi.org/10.1002/ecm.70037.
- Data-source screening: published Kaggle Hong Kong horse×race
  data are promising for H1/H2 by column names, but have **obscured
  dates** and a source-redistribution rights gap. A new offline,
  aggregate-only schema/overlap auditor is in
  `scripts/ecology_hk_preflight.py`; no actual records have
  been acquired or fitted.

See [full H2 missing-outcome note](ecology-h2-outcome-selection.md)
and [data-source feasibility](ecology-data-source-feasibility.md).


## H2 extension: explicit completion and conditional performance (2026-10-13)

The two-part exploratory design is in
[scripts/ecology_h2_two_part.py](../scripts/ecology_h2_two_part.py),
with detailed [methods](ecology-h2-two-part.md):

- **Part A:** race completion among all starters
  (finished versus did_not_finish), modeled with ridge-regularized
  binomial GLM using only pre-race histories; baseline versus
  previous focal style × previous rival style composition, evaluated
  by chronological log loss and Brier score. Does not estimate the
  cause of DNF. Sparse DNF events trigger an explicit HOLD.
- **Part B:** raw individual speed only for timed finishers,
  with horse and race fixed effects, loss-to-observation reporting,
  and no fictitious numeric speeds for nonfinishers.

These stages have **different estimands** and are not jointly
estimated; stage A is not a correction automatically debiasing stage B.
Any causal claim needs independent validation, comprehensive
competition/ground/class/jockey confounder coverage and biological
interpretation of noncompletion categories.

Data onboarding now requires *within comparable environment-stratum*
overlap: 2+ starts in at least two going labels for the same horse,
venue, surface, distance, class, plus changing rival sets. An
unstratified count of repeated starts may conceal complete
environment/class confounding.


## First reproducible real racing-animal data test (2026-10-13)

To prevent indefinite reliance on invented effects, the project
performed a **real-data technical/descriptive test in Queensland
GREYHOUNDS, not Thoroughbred horses**. This analogue was chosen
because the public dataset's ODC-BY attribution and Racing
Queensland open-data origin could be documented and a fixed Git
blob independently verified.

- 25,679 real dog–run GPS records, 6,021 date × venue × race keys,
  3,603 dog **names**.
- 2,302 dog-name × venue strata with >=2 observations in both inner
  versus outer starting box groups.
- Exploratory outer-minus-inner first-50m split contrast: +0.01097 s,
  descriptive name-cluster 95% resampling interval
  [+0.00823, +0.01340] s. **Not a causal CI or preregistered test**.
- Similar direction in early versus late descriptive time subsets,
  but no external prediction test; the straight-course positive
  contrast and assignment confounding undermine a simple
  turn-geometry explanation.
- No complete official opponent-roster guarantee, dog names not
  proven stable IDs, track/class and start design not fully adjusted.
  This analysis **does not** estimate H1 individual slope variance,
  H2 causal interactions, evolutionary fitness or any horse effect.

Reproduction and full limitations:
[real greyhound benchmark](ecology-real-greyhound-method-benchmark.md).
The target remains actual horse data from an authorized source with
stable horse ID, real chronological start dates, all competitors and
environment-specific repeated outcomes. The official Racing Queensland
thoroughbred open-data catalogue is the next field-level source to
verify. Horse H1/H2 remain **HOLD**.


## 2026-10-13: first independently reproduced original Thoroughbred telemetry audit

**New factual input:** Racing Queensland official downloadable
Thoroughbred sectional CSVs for 2026-10-10 Eagle Farm and 2026-10-11
Cannon Park were retrieved by a bounded, versioned workflow and
recalculated independently. Across **18 source race headers and 197
horse-labelled section strings, 162** had positive timing telemetry
and **35** contained only zeros. Five repeated horse names on the
same meeting date appeared in separate race headers with mixed zero
and positive measurements; no stable individual or DNF interpretation
has been inferred from those rows.

[Official-source audit and hashes](ecology-rq-thoroughbred-source-audit.md)
documents the semicolon-packed per-section distance/signal/time schema,
the race-level header timestamp, and the independent GitHub Actions
execution. The source is **really Thoroughbred** (unlike the earlier
greyhound analogue), but lacks a verified link between sectional names
and official `HORSES` horse IDs, certified individual finish times,
and complete starter/competitor histories.

**Inference gate still not passed:** H1 heterogeneous environmental
reaction norms and H2 social competition context remain scientifically
unidentified. Next perform **one official race** linked source-ID
validation: `GetRacesForMeeting` → `GetHorsesForRace` → matching
sectional row / official result, with explicit ambiguity and zero-data
rejections. Only after proving a stable repeated horse ID and
history-complete starters may real horse models be considered.


## Official horse-ID crosswalk: code ready, actual join still HOLD

The project now includes an offline,
[fail-closed official Racing Queensland HORSES-ID crosswalk](ecology-rq-official-id-crosswalk.md)
which compares a private verified race-result/starter snapshot with
the already audited sectional CSV. One-to-one race name and date
matching is necessary but not evidence of stable biological identity.
Contradictory or nonunique official IDs, same-day repeated horse
names, and data-zero rows are explicitly held, never guessed.
Synthetic tests run in CI. **No actual historical HORSES-ID crosswalk
has been verified and no real equine H1/H2 has been fitted.**


## Result of the actual original-source ID verification (2026-10-13)

The earlier ID-crosswalk proposal has now been tested against the
genuine Racing Queensland SOAP API and original GPS files, first for
one race and then for a deliberately small two-date subset at the
same venue. The former produced **11/11 exact official-ID/name/GPS
matches** at 2026-10-11 Cannon Park Race 1. The latter found **two
source-level numeric HORSES ID recurrences across 2026-08-29 and
2026-10-11**, both with positive GPS telemetry on both dates.
Reproduction: [two-date verified audit](ecology-rq-two-date-official-id-recurrence.md).

This supplies actual equine IDs over more than one date, but **not**
a complete longitudinal dataset for H1/H2:
- Both dates' selected races were `Good`, providing **no within-horse
  contrasting ground exposures**.
- October's sampled races even contained one ID in two same-day
  official race lists, showing the API list cannot be assumed to
  represent one confirmed starter per race.
- The SOAP detail methods do not provide individual certified finishing
  times/placings, and the GPS CSV zeros are not DNFs.
- The omitted August race number 5 was not guessed or imputed.

The next *biological* milestone is to find sufficient verified
same-ID repeat starts under unlike ground conditions and varying
opponent lineups, conditional on course/distance/class and confirmed
results. A source-level cross-date ID match is not an evolved
environmental preference or social response.


## First REAL cross-going equine overlap and falsification of overconfident inference (2026-10-13)

Original source: Racing Queensland SOAP numeric HORSES IDs
and dated first-section GPS records for the same
Cannon Park venue. The five selected dates comprise:
2026-05-15 Heavy; 2026-05-29 Soft; 2026-08-22 Soft;
2026-08-29 Good; 2026-10-11 Good. Ground is
categorical, not an equally spaced ordinal score.

Source-hash-verified [focused cohort](ecology-rq-real-h1-multigoing-feasibility.md):
20 race numbers, 143 official-ID-positive-GPS rows,
20 repeated horse IDs crossing Good and wet, 10 at
a matching race distance+first-section marker,
1 also matching original race class, **0** with
2+ independent first-section measurements in both
environment groups under the same class/distance/marker.

[Explicitly exploratory full-race coverage follow-up](ecology-rq-real-h1-multigoing-expanded-audit.md):
38 official race IDs (two original SOAP race numbers
not returned), 280 linked positive-GPS observations,
65 recurring IDs across dates, 37 with both Good
and non-Good records, 17 matching distance+marker,
2 matching original class as well, and still **0**
meeting the original 2+ each-ground strict
replication gate.

This is a **valid research-design finding** that class,
distance and entrant selection severely limit H1
identifiability even in genuine longitudinal horse
records. It is NOT a negative biological test of
whether individual animals vary in track response.
`Class` can be broad, so age/weight/rail/jockey
conditions can further reduce comparability.

Do not publish a claim that wet tracks make the
animals faster/slower using the exploratory
17-ID difference: the naive non-Good minus Good
first-section mean was negative, but this is
observational class/entry confounding, not evidence
of environment-dependent adaptive performance.
The project deliberately fitted **neither** H1
random-slope variance **nor** H2 rival interaction
to these actual horse records.

Evidence required next: a preselected larger
cohort with verified all-starter/finish outcomes,
stable IDs across repeated seasons, within-horse
ground and opponent-context overlap under
credible controls for class/distance/age/weight,
race/jockey selection, correctly time-lagged
features and independent temporal validation.
