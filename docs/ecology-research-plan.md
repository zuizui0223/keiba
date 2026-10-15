# Ecological research plan: racehorse individual × environment × competition

Status: **H1 environment-reaction and H2 social-interaction hypotheses remain untested/unsupported in real horses** (2026-10-13). This is a biological research track independent of betting-market optimisation. A separate secondary **exploratory source-backed repeatability signal in relative early-section timing** is now documented, not a causal effect or a preregistered adjusted ICC.

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


## 2026-10-13: a separate, source-backed secondary ecological finding

After finding that the strict Good/wet H1 matched-class
replication threshold remained zero even with 12
official meetings, we tested a *different, explicitly
exploratory question*: is an individual horse's
early performance **relative to its contemporaneous
timed-GPS competitors** consistent across independent
racing dates?

For this, original Racing Queensland `HORSES`
identifiers, original first GPS section duration,
distance, section marker, race class and the
12-source-date calendar were reused. Excluded
incomplete first-section measurements, ambiguous
same-day identities, and race groups with fewer
than 4 valid timed-GPS horses. Result: 523
horse×race observations over 74 races.

- Repeated individual ID/first-marker/race-distance:
  99 IDs, 209 different-date pairs, equal-stratum
  mean within-ID cross-product **+0.051925 s²**.
  Within-race ID-label permutations (299) averaged
  **+0.001735 s²**.
- Also matching original race class:
  50 IDs, 81 different-date pairs, observed mean
  cross-product **+0.035633 s²**, shuffled mean
  **+0.001136 s²**.
- Later-date retrospective persistence:
  first-matched 54 observations RMSE 0.333181
  → 0.287796 s; with class matching 20
  observations RMSE 0.282634 → 0.256963 s,
  based on earlier horse-profile shrinkage fixed
  before the future outcomes.

[Complete data/methods/source audit](ecology-rq-real-early-pacing-repeatability.md)
and [successful original-source independent CI
run](https://github.com/zuizui0223/keiba/actions/runs/38348581714)
freeze the computation and its limitations.

The measurement is **focal first-section seconds
minus the other timed horses' mean seconds in
the SAME race**, not absolute velocity; it can
change with opponent ability or incomplete GPS
coverage even without a focal biological
change. There are no certified true-starter/
finisher statuses, and jockey, weight, age,
trainer and selective field composition have
not been fully adjusted. The pseudo-permutation
null is exploratory and *not* a valid biological
randomization experiment or confirmatory
p-value. This project has NOT fitted adjusted
ICC, reaction-norm variance or H2 causal
competitor-effects to the real data.

Conceptual reference: Nakagawa & Schielzeth
(2010), https://doi.org/10.1111/j.1469-185X.2010.00141.x,
recommends hierarchical variance partition
and valid uncertainty methods for biological
individual repeatability. This project should
treat the present repeatable relative pacing
signal as a **candidate ecological observation
for a follow-up confirmatory study**, not as
proof of heritable strategy or adaptation.

Next use a verified official all-starter and
individual result/age/rider/weight panel,
add a joint crossed horse×race adjusted
repeatability analysis, predefine new
evaluation dates and appropriate negative
controls, and only then consider a
scientifically supported population-level
individual-behavior claim. H1/H2 remain
separate, unanswered hypotheses.


## Adjusted within-horse repeatability of ABSOLUTE first GPS interval (2026-10-13)

A Gaussian `first GPS section seconds ~ fixed race + random HORSES ID`
model was implemented by eliminating all source-race intercepts with
Helmert contrasts and profiling the Gaussian REML variance
components. This is **not** an H1 environment random-slope
or H2 opponent interaction model. Its conditional ICC is
`variance(horse)/(variance(horse)+residual variance)`.

Source-based original data:
- 523 positive first GPS records, 74 race fields with
  >=4 timed horses, and 269 numeric source HORSES IDs
  (139 observed more than once).
- Horse random-intercept variance 0.0403995 sec²;
  residual variance 0.0531745 sec²; conditional
  **ICC = 0.431738**.
- Same model at >=6 valid GPS horses/race:
  **ICC = 0.419445** (436 rows in 55 fields).
- Delete one entire source date at a time:
  **ICC 0.390814–0.499262**, a source stability
  range and **NOT** a model-based or clustered
  95% confidence interval.
- Within-race shuffled original HORSES labels,
  99 repeats: mean reference **ICC = 0.016736**.
  This is **not** a causal treatment randomization
  or a confirmatory test, but a useful negative control.
- 150m original section marker alone:
  **ICC 0.547296** on 209 rows/29 races;
  250m marker: **ICC 0.418787** on
  226 rows/33 races. Original 100m/200m
  marker cohorts **HOLD** for too few repeat
  IDs/dates. The marker difference may reflect
  different racing populations/sensors/variance,
  not a biological marker-length effect.

This is the first in-repo genuinely source-backed
conditional mixed-model variance decomposition.
It tests a narrower exploratory *individual
consistency in early section timing* question,
not adaptation, genetic heritability or
a horse-by-ground reaction norm. Model residual
homoscedasticity, date dependence, actual-starter
status, and horse-specific jockey/weight/age
covariates are not established. No valid
effect-size uncertainty or independent prospective
holdout cohort has yet been calibrated.

[Verified real-data numerical audit,
identifiability math and interpretation limits](ecology-rq-real-horse-race-adjusted-icc.md).
Method context: Nakagawa & Schielzeth 2010,
https://doi.org/10.1111/j.1469-185X.2010.00141.x.
**Keep H1 and H2 on HOLD** until genuinely
matched environmental repeated exposures
and historical full opponent rosters with
verified result measurements exist.


## 2026-10-13: documented Weight, Jockey and Trainer adjustment

The official RQ `GetHorsesForRace` source
returns a registered numerical riding weight,
original `Jockey/@Id` and `Trainer/@Id`
license IDs. A new source-verified parser and
race-orthonormal REML nuisance projection
[`ecology_rq_covariate_icc.py`](../scripts/ecology_rq_covariate_icc.py)
now compares **exactly the same 279 positive
first-GPS HORSES-ID records** on race-fixed
random horse intercept models with nested
source covariates:

| Fixed nuisances beyond original race FE | Conditional ICC (same 279 source rows) |
| --- | ---: |
| None | 0.503005 |
| Riding weight | 0.509202 |
| Weight + jockey licence ID | 0.513500 |
| Weight + jockey + trainer licence IDs | **0.487447** |

The 279-record complete-source stratum is
much more selected than the original 523-record
race-FE sample and 548 original positive-GPS
source rows: valid registered Weight/Jockey/
Trainer fields existed together in only 337
original rows, and >=4 fully documented GPS
rows/race gave 279. **Good kept 47.8%, Soft
56.9%, Heavy 45.9%** of initial source
GPS records, and 2026-04-04 had 21 original
positive records but zero retained after
complete-field race filtering.

The source documents **45 observed horses
with multiple jockey licence IDs but only
1 with multiple trainer licences**, so
stable horse/trainer combinations make
their separate attribution confounded.
The source API does not provide reliable
horse age, independently certified actual
riders/finishers, official horse-specific
finish times, or true source GPS selection
mechanisms.

See [original source/completeness/model
audit](ecology-rq-real-horse-weight-jockey-trainer-adjusted-icc.md).
Results are a **model-dependence sensitivity**,
not a new independent confirmation of
innate animal personality, H1, H2, natural
selection, adapted behavior or horse genotype.


## New real-data falsification of strong source-adjusted ICC claims (2026-10-13)

The 2026 12-date original HORSES-ID/GPS sample
provides useful but restricted **source-
conditional individual consistency**.
Two new tests were performed to avoid
overinterpreting a point estimate from
the role/weight-complete 279-row cohort.

1. **Source-field documentation
   completeness vs already observed GPS
   timing, within the *same race*.**
   Sixty-eight original fields included
   both source complete and incomplete
   jockey/trainer/weight rows (491 positive
   GPS horse records). The equal-race
   mean complete−incomplete first interval
   was **−0.02355 seconds**, compared with
   499 within-original-race shuffled
   completeness-label values (two-sided
   descriptive fraction **0.416**). The
   result does NOT identify the
   missingness mechanism among horses
   without GPS or real finish times,
   nor certify MCAR/MAR for any sample.
   See [source selection audit](ecology-rq-source-role-missingness-vs-early-gps.md).

2. **One meeting-day deletion in the 279-row
   complete-source adjustment cohort.**
   All 11 leave-one-date-out fitted cohorts
   were numerically identifiable. Original
   race-FE only ICC ranged **0.429–0.551**,
   full Weight/Jockey/Trainer fixed-effect
   adjusted ICC **0.385–0.577**; the full
   minus baseline change ranged
   **−0.079 to +0.034**, negative on
   8 of 11 source-date deletions and
   positive on 3. Thus adjusting for
   the three original source variables
   is **NOT a stable, isolated causal
   explanation** for the horse variance.
   The effective source universe
   only contains 11 original meeting
   date clusters (one entire date
   lost all original adjusted records),
   and source availability is
   associated with race and going
   conditions. These ranges are
   **NOT** uncertainty intervals.

[Original source-adjusted ICC/identification
limitations](ecology-rq-real-horse-weight-jockey-trainer-adjusted-icc.md).
This work does not establish an H1
environment random slope, H2 social effect,
horse genetic personality, adaptation,
or true population-wide repeatability.
The needed next data are confirmed starters,
actual jockey assignments, horse age,
fully observed results, stronger trainer
crossovers and an independent date/track cohort.


## 2026-10-13: first different-racecourse source-ID ICC and failure of same-segment replication

A new source cohort of 12 Eagle Farm 2026 meetings was
[committed before inspecting its horse-ID or early-GPS
outcomes](ecology-rq-eagle-farm-2026-independent-track-lock.md)
and analyzed from original Racing Queensland SOAP+GPS,
using the same race-FE Gaussian HORSES random-intercept
variance decomposition previously run at Cannon Park.

Original source IDs/first positive GPS: 391 candidate records,
339 IDs, 48 IDs recurring over dates. The race >=4-timed cohort
has **382 observations, 51 races and 45 repeated HORSES IDs**;
Eagle Farm conditional ICC point **0.452894**. A
>=6-timed source sensitivity returned **0.441609**.
The same operator's Cannon Park 12-date original cohort
had conditional ICC **0.431738**. Eagle Farm leave-one-date
range was **0.331549–0.563767** (not a confidence interval).

**However, direct cross-venue repeatability on the SAME first-GPS
distance marker remains HOLD**. Original Cannon Park numeric
150m and 250m models cannot be evaluated at Eagle Farm because
that cohort has zero such rows. Eagle Farm's 200m segment has
a numeric ICC (~0.5283), while Cannon Park 200m did not have
adequate repeated-source support. Therefore the two pooled ICC
point values are DIFFERENT measurement mixtures and cannot
be compared as effect sizes of a universal racehorse trait.

The source-recorded registered Weight/Jockey/Trainer analysis
is even more restricted at Eagle Farm: 179/391 original
source rows have every field; only 108 survive within-race
complete peer coverage (21 races, 10 dates), with
**only THREE repeated numeric HORSES IDs**. We discovered
that a high point estimate could be produced after projecting
many nuisance licences despite near-absent repeated
individual source information. The algorithm has been corrected:
if its same-cohort race-FE baseline cannot identify a
HORSES random variance or <20 original IDs recur,
all nuisance-adjusted ICC point estimates are **HOLD**
rather than published, even if a numerical
optimizer converges.

This is a **methodological falsification of an overstrong
generalization**, not evidence against biological
individuality. See the [original Eagle Farm venue audit](ecology-rq-eagle-farm-real-icc-cross-site-audit.md),
[software tests and source limitations](../scripts/ecology_rq_eagle_farm_external_icc.py),
and [official CI](https://github.com/zuizui0223/keiba/actions/runs/38412116293).
Original race starters, age, definitive riders, outcomes,
and H1/H2 remain HOLD. A next truly comparable test must
use the same first-sectional measurement distance in
both venues, with adequate repeated official HORSES IDs.


## 2026-10-14 third venue: a genuine marker-matched source design cannot yet identify horse ICC

The external Eagle Farm site yielded pooled original
race-adjusted ICC 0.452894, but no exact first GPS
measurement marker had numerical ICC support in
**both** Cannon Park and Eagle Farm. Further,
the original cross-venue identity check found
two shared HORSES IDs, zero with a matched
first interval marker+official race distance.

A separately locked **19-date Doomben source**
was then audited with original official RQ
HORSES IDs, six original race numbers per
date and positive first GPS interval records,
explicitly to test whether one racecourse
could bridge **150m Cannon and 200m Eagle**
measurement cohorts.

[Original source and support audit](ecology-rq-doomben-third-venue-original-marker-audit.md)
and [original GitHub source execution](https://github.com/zuizui0223/keiba/actions/runs/38499396097)
give **18 completed dates / 19 planned**,
**617** source records, 541 original numeric
animal IDs and 65 with repetition across
dates irrespective of initial segment distance.

Within exact 150m first markers, there were
**177** records but only **9** original IDs
with observations on 2+ dates. Within 200m
first markers, there were **205** original
observations, again only **9** repeated IDs.
Both fail the prior >=20 source-repeat gate
for Gaussian race-fixed horse ICC. The
cross-venue same-marker ICC test remains
**HOLD, not a numerical zero**.

One source date, 2026-08-26, had its
official meeting and GPS CSV present,
but the first-party \`GetRacesForMeeting\`
API returned a backend string-truncation
error instead of race IDs. We recorded
this as missing source metadata and
did not reconstruct arbitrary IDs.

**Biological conclusion:** the
existing pooled source-level
individual ICC signals are
compatible with sustained original
horse-ID associations but do **not**
establish a replicated identical
first-section biological trait
or genetic individuality.
This is a real model-identifiability
and data-provenance gate, not
negative evidence about H1/H2.


## 2026-10-14: model-conditional Gaussian ICC variability and source comparability

The real-source, Gaussian race-FE / random HORSES-ID ICC had been
reported on the Cannon Park and Eagle Farm original 12-date
cohorts, but **not accompanied by a validated population-level
uncertainty estimate**. A conditional parametric simulation
was subsequently designed **after the positive ICCs were known**.
It retains each venue's source ID × race incidence, source
positive first GPS coverage, observed original
race-fixed-effect projection and fitted Gaussian variance
components, then generates and refits 299 parametric
Gaussian responses from the model. An additional 199
responses impose a zero horse intercept component as
a narrow model-based negative control.

[Original-source executable and quantitative
results](ecology-rq-real-icc-source-conditional-sampling.md) /
[post-hoc model conditions](ecology-rq-icc-conditional-simulation-protocol.md) /
[reproduced paired site jobs
#38501941730](https://github.com/zuizui0223/keiba/actions/runs/38501941730).

Original-source refit, 12/12 meeting dates on each venue:

- **Cannon**: ICC point **0.430147**,
  fitted-Gaussian ICC estimator 2.5th–97.5th
  quantiles **0.313683–0.528432**.
- **Eagle**: ICC point **0.453332**,
  same conditional quantiles **0.166828–0.708244**.
- Marker-specific sensitivity:
  Cannon 150m ICC 0.539528 (conditional
  0.321931–0.684309), Cannon 250m
  0.418787 (0.248634–0.600394),
  Eagle 200m 0.527731
  (0.200194–0.786889).
- **No identical first GPS distance marker
  supplies independently identifiable
  source horse ICC across both venues**.
  Doomben 150m and 200m source marker
  cohorts also fail strict recurring-ID support.
- Source historical roster/GPS data are
  mutable: previous points 0.431738 and
  0.452894 differ slightly from fresh
  re-reads. Source hashes are necessary
  for scientific reproducibility.

The model-conditional simulated quantiles
are **not a validated 95% confidence interval**:
the true data-generating process, source
missingness/nomination selection,
trainer/rider assignments, different early
GPS section markers, and correlated date-level
shifts have not been calibrated. Under a
narrow Gaussian zero-horse-effect simulation,
reestimated ICCs were generally near zero,
but this does not produce a causal or
source-population p-value for real
racehorses.

### Decision

Evidence remains **consistent with an
exploratory, model-dependent HORSES-ID
association in early first GPS segment
duration**, but precision and measurement
identity differ across venues. It is
scientifically incorrect to call similar
pooled Cannon/Eagle ICCs a
replicated **same-trait** biological
individual repeatability result,
or to call a parametric sampling
quantile a robust confidence interval.

H1 ground-response random-slope variance,
H2 causal rivalry context,
phenotypic plasticity, personality,
genetic heritability, adaptation and
betting profit continue to be **HOLD**.
For a genuine reproducible biological
effect, prioritize real official result/
actual-starter source joins, complete
first-marker-compatible repeated IDs,
independent source operator/sensor
calibration and source-date/
horse-cluster uncertainty.


## Genuine first-section marker feasibility at a third venue (2026-10-15)

The previously locked 2026 Doomben 19-date source audit
could **not** estimate ICC at exactly the original 150m
or 200m first GPS section marker: only **9** recurring
numeric HORSES IDs at either marker.

A separate [23-date 2025 Doomben calendar lock](ecology-rq-doomben-2025-marker-calendar-lock.md)
was committed before collecting the newly included 2025
horse IDs/first-interval times. It selects original public
2025 turf sectionals: first and last published source CSV
per month (one in March), 1–6 official race numbers.
This is **post-hoc design expansion** following positive
Cannon/Eagle ICCs, NOT an independent biological
hypothesis preregistration.

Independent first-party original-source data reads
[38674631028](https://github.com/zuizui0223/keiba/actions/runs/38674631028)
and [38674654236](https://github.com/zuizui0223/keiba/actions/runs/38674654236)
showed 38 of 42 total 2025–2026 source dates
successfully audited, original ID/first-GPS
candidates **660** in 2025 and **1277** in the
pooled 2025/2026 source. At exact 150m,
repeated IDs **25 (2025)** and **60 (pooled)**,
with Gaussian race-FE ICC **0.654** and **0.180**,
respectively. At 200m, **19** repeated IDs and
numeric HOLD in 2025 alone, versus **42** and
ICC **0.412** after pooling across source years.

**The strong 150m discrepancy makes a universal
individual early-pace trait parameter especially
uncertain**. It may reflect different entrants,
training, timing technology, source dropout,
jockeys and changing original race cohorts,
not any year-induced change in horse biology.
Even common first GPS markers across venue
source cohorts do NOT imply cross-vendor
calibration, exact common animals, genetically
based personality, causal track geometry or
adaptation.

[Original 2025/2026 Doomben source and exact
marker results](ecology-rq-doomben-2025-2026-exact-marker-source-results.md).
The follow-up code is also prepared to audit
**same numeric original horse identities across
years at matching marker/distance/Class**, not
just pooled between-horse variance. H1 and
H2 remain HOLD.


## Exact source-HORSES ID cross-year context, not just a pooled ICC (2026-10-15)

The [independent date-locked original-source rerun
#38675223586](https://github.com/zuizui0223/keiba/actions/runs/38675223586)
followed up the mixed Doomben 150m/200m ICC
sensitivity with actual original numeric source
HORSES ID continuity from 2025 to 2026.

**101 IDs** were observed in both original source
years; **27** of them had positive 150m first
GPS records in both years and **17** had positive
200m first GPS records in both years.
Adding exactly matched scheduled race distance
gave 27 and 16, respectively; original Class
agreement reduced them to **6 and 4** source IDs.
**Zero at either marker** had two independent
source meeting dates *in each source year*.

The 2025-only Doomben 150m ICC (0.654)
versus combined 2025/2026 ICC (0.180)
thus cannot be attributed to an individual
horse's response to year/aging/training:
the selected original animal population
and event/measurement contexts differ, and
no strong within-individual cross-year
repeat replication was established.

The source identity-matching gate, hashes,
two-year mixed source/partial API failures
and biological/H1/H2 HOLDs are documented
in [the Doomben 2025/2026 original-data
audit](ecology-rq-doomben-2025-2026-exact-marker-source-results.md).
