# H2 method note: individual pace phenotype × competitive environment

Status: **exploratory software pilot with fabricated records only** (2026-10-12).
The research objective is ecological, but the present coefficients are not
scientific findings about real horses.

## Ecological question and estimand

**Question:** Does the *same* horse's relative race performance covary with
differences in the pre-race running-style composition of its opponents,
after accounting for its own previous relative performance and the known
strength of the rival field?

- Focal pre-race style, `S_ir`: mean **previous-race** first-call
  normalized position, computed from strictly earlier calendar days. Larger
  values mean a greater tendency to be near the front early.
- Rival context, `F_ir`: leave-one-out fraction of the **other entrants**
  whose own historical style exceeds the pre-specified threshold 0.7.
  Never use the target race's realized running positions to construct this
  exposure.
- Prior ability `A_ir`: focal horse's mean previous within-field finish
  percentile over at most five earlier starts.
- Rival ability `O_ir`: mean historical finish percentile of other entrants
  with observed histories. Exclude the race if insufficient historical coverage.
- Outcome `y_ir`: race-centred individual speed, standardized by
  same-race spread; available after the race only. This is **relative
  competitive performance**, not fitness, survival, heritability or winning
  probability.

The baseline pilot uses:

```
M0: y ~ A + O + S + F + (1 | horse_id)

M1: y ~ A + O + S + F + S:F + (1 | horse_id)
```

`S`, `F`, `A` and `O` are centred on *training-date means only*.
The focal question is the interaction `S:F`, **not** the existence of a
simple positive/negative association between final placing and the size
of the field. M1–M0 is also evaluated on later race dates by paired,
race-block bootstrapped relative-speed RMSE differences.

This is a **statistical interaction**, not directly observed competitive
interference. Relative speed can shift because of skill selection, jockey
strategy, running tactics, gate draw, class, track, weather, etc.

## Existing scientific literature and novelty

Spence, Thurman, Maher & Wilson (2012), *Biology Letters*, DOI:
https://doi.org/10.1098/rsbl.2011.1120 analyzed the pacing and position
of 44,803 tracked horses in 3,357 races and demonstrated aerodynamic drafting
and pacing associations. They explicitly discuss front-runner/chaser roles.
Therefore competitor effects, pace, drafting and individual pacing roles
are **existing knowledge**.

Oda & Onogi (2024), *Journal of Animal Breeding and Genetics*, DOI:
https://doi.org/10.1111/jbg.12822 modeled individual Japanese Thoroughbred
performance including race, age, jockey and course/distance dimensions.
Therefore a mixed model of horse ability is **not by itself new**.

Potential novelty, requiring direct verification against additional literature,
is the *longitudinal within-horse opponent-phenotype-composition interaction*
computed without hindsight, and its persistence after adjusting for plausible
entry-selection and racing-condition confounding.

## Identification checks

1. Historical identity continuity: same stable horse ID linked over years.
2. Within-horse context contrasts: horses observed >=4 times with a valid
   pre-race competitive-profile history and >=2 distinct values of `F_ir`.
   This is a *necessary engineering gate*, not power or identification.
3. A fully observed rival roster for each race, including non-finishers
   represented with missing outcomes rather than zero time. The current
   H2 smoke model excludes races without complete finishing times and
   historical coverage, potentially biasing the cohort.
4. Temporal split by date. No random split of rows from the same horse's
   historical series; all learned centres and horse random effects come
   from earlier training dates.
5. No extrapolation beyond observed surfaces/class/venue/going combinations
   without showing comparable support.
6. Report ground/surface, distance, field size, weather, jockey,
   age/fitness and relative opponent strength. The pilot currently lacks
   confirmatory joint adjustment for all of these.

## Confounding, mathematical coupling and sensitivity analyses

**Important mathematical coupling:** with a leave-one-out rival share, a
horse's `F_ir` partly depends on whether the focal horse is classified as
a front-runner and how many front-runners are in that same field. An apparent
`S:F` interaction can arise from this construction without behavioral
interference. A future confirmatory test must additionally compare field-level
front-runner composition, centered focal style, a horse-level
fixed-effect or appropriately crossed random-effects specification, and
sensitivity to field size/threshold choice.

**Nonrandom entry:** race entrants are selected by trainers/owners. Horses
may avoid hostile tracks or classes, and certain styles may preferentially
enter races with weak/strong opponents. Adjust for past class, surface,
distance, venue, rest and previous performance; assess overlap and
entry-selection sensitivity. Do not describe observational associations as
causal competition.

**Negative-control plan:** use simulations in which the planted
style×rival interaction is exactly zero and compare false-flag frequencies;
add a pre-specified, restricted opponent-context label permutation
within feasible race strata. Neither is currently a demonstrated
real-data inference procedure.

**Independence plan:** account for two-way horse and race dependence,
and possible repeated jockey/team allocation. A horse-random-intercept
model with race-centred outcome is only exploratory; it does not provide
valid horse+race crossed-cluster uncertainty for `S:F`.

**Multiple testing:** assess the pre-specified interaction separately
from exploratory nonlinear, distance-conditional, and ground-conditioned
terms. New interactions introduced after seeing the data must be reported
as exploratory.

## What is implemented

- `scripts/ecology_demo_competitors.py`: fictional longitudinal
  panel with a controlled interaction parameter (default -0.9).
  100 fabricated race days × 12 entrants per race from a pool of 48
  fictional horses is the standalone default. Some horses see changing
  rival compositions across races. This dataset is *not* a realistic
  model of injury, entry, trainer selection or ecological selection.
- `scripts/ecology_panel.py`: validator, temporal provenance,
  own/rival profile construction, context-overlap audit.
- `scripts/ecology_h2_pilot.py`: M0/M1 exploratory fit, future-date
  scoring, synthetic versus real rights gates, explicit noncausal output.
- `tests/test_ecology_h2_pilot.py`: verifies same-horse composition
  variation, incomplete-roster rejection, training-only centring,
  synthetic-only safeguards, and a constructed-effect fit.
- CI: `.github/workflows/ecology-tests.yml`.

## Decision hierarchy

- **Software check passing:** the synthetic pipeline can reproduce a planted
  association without using target-date results as predictors. This says
  nothing about ecology.
- **Data-ready, not science-ready:** licensed multi-year racing histories
  have variable rivals, complete pre-race predictors and outcome records.
- **Exploratory real-data signal:** interaction appears in an adjusted model
  and later-date prediction improves. This is *not* proof of a causal
  interaction.
- **Credible ecological claim:** results survive pre-registered prior
  literature review, within-horse design and overlap, competing mechanism
  checks, stringent entry/jockey/class sensitivity and correct multiway
  uncertainty estimation. The project has **not** reached this stage.

**Current archive:** the separate Kyoto 2026-10-12 historical card
contains seven races on one date. It is not capable of establishing
within-individual shifts in rival composition. See
[Kyoto archive gap audit](ecology-archive-gap-audit.md).


## Stronger longitudinal within/between pilot (October 12, 2026)

`scripts/ecology_h2_within_between.py` adds a **horse fixed-intercept**
sensitivity beyond the previous mixed-model pilot:

```text
y_ir = α_i + βA A_ir + βO O_ir + βS S_ir
       + βW (F_ir - mean_train(F_i))
       + γ (mean_train(S_i) - mean_train(S))
           × (F_ir - mean_train(F_i))
       + βG Going_ir + βSG (mean_train(S_i)-mean_train(S)) × Going_ir
       + error_ir
```

- `α_i` removes stable horse-level performance differences in the **training**
  panel. Individual historical style traits and competitor composition
  baselines are fitted exclusively from earlier training dates and frozen
  during future-date evaluation. This is **not an instrument or causal
  identification** for the remaining time-varying selection.
- `F_ir` is compared both as the *other entrants only* fraction and the
  *full field* fraction. Their potentially different coefficients explicitly
  probe the compositional coupling between a focal horse's own label and its
  leave-one-out rival share.
- `Going_ir` and its interaction with focal style test a competing
  **horse-style×track-condition** explanation. More complete adjustment
  for class, course, jockey, weather, fitness and entry remains necessary.
- Approximate descriptive uncertainty is clustered on horse **and race**.
  Nominal 95% intervals and race-block held-out RMSE changes must **not**
  be mistaken for credible intervals for causal social plasticity.
- Between-individual assortment is reported as a **descriptive association**
  between training-period mean focal style and mean encountered competitor
  style. A horse fixed intercept absorbs time-constant exposure means; the
  model does not estimate causal assortative assignment or fitness.
- This pilot uses relative race-centred z-speed, not winning probability.
  It excludes races with incomplete official finishing-time rosters,
  introducing a potential selection filter.

## Falsification design and negative-control generators

`scripts/ecology_h2_falsification.py` executes three deterministic
**wholly fabricated** mechanisms, via `ecology_demo_competitors.py`:

| Scenario | Rival-effect planted | Other mechanism |
| --- | --- | --- |
| null_random_entry | 0 | randomized horse participation |
| planted_opponent_interaction | −0.9 generator speed-scale parameter | same randomized participation |
| confounded_null | 0 | assortative (nonrandom) field entry + style-dependent ground performance |

These parameters define a *fabricated data-generating process* and are
**not numerically comparable** to the fitted interaction coefficient on
the race-relative z-speed scale. Single synthetic null draws may show a
nonzero fitted coefficient. A nominal interval excluding zero in a
confounded null indicates vulnerability to model/design artifacts, **not
evidence of a competitive mechanism**. The default two seeds and three
scenarios give just six software design probes, not stable estimates of
power, false-positive rates or calibrated uncertainty.

The pipeline deliberately records missing within-horse overlap as `HOLD`
instead of calling the hypothesis rejected. All simulated labels have
`source_license=synthetic`. Actual published racing history is still absent.

## Ecological-theory anchor: social plasticity vs assortment

- **van de Pol & Wright (2009)**, *A simple method for distinguishing within-
  versus between-subject effects using mixed models*, *Animal Behaviour*
  77:753–758, DOI https://doi.org/10.1016/j.anbehav.2008.11.006.
- **Martin & Jaeggi (2022)**, *Social animal models for quantifying plasticity,
  assortment, and selection on interacting phenotypes*, *Journal of
  Evolutionary Biology* 35:520–538, DOI https://doi.org/10.1111/jeb.13900.

The 2022 paper estimates **social reaction norms** and explicitly separates
within-individual responsiveness from nonrandom assortment. Its full
measurement-error and social-genetic approach is **NOT implemented** in
this repository. Genetic relatedness, heritability, selection and
fitness are not available here. Consequently we call the outputs
*exploratory individual-context associations*, rather than social
animal model estimates or selection coefficients.

### Next genuine empirical milestones

1. Legally authorized repeated horse×race records across multiple seasons,
   many courses and varied rival lineups, including ground and first-call
   tracking, with verified release terms.
2. Explicit overlap tables by course/distance/class/going/jockey, race
   entry propensity, and environment-dependent selective withdrawal.
3. Model direct competing explanations, including field-strength selection,
   field-size, within-horse front-position changes, race-level shocks,
   interactions with going, and changing training/jockey decisions.
4. In advance, freeze exposure threshold (currently 0.7), outcome definition,
   training/validation splits, uncertainty and multiplicity rules.
5. A holdout independent of the case used to settle model design, then
   a biological claim only if defensible sensitivity and uncertainty remain.


## Outcome alert: standardized speed is not a focal social response

For H2, `z_ir = (v_ir - mean_r(v))/sd_r(v)` can vary when another
horse's speed changes even if `v_ir` is held fixed. Therefore a
nonzero rival-context association on `z_ir` may be **mathematical
relative-performance coupling**, not a behavioral social reaction.

The experimental H2 primary alternative is
`scripts/ecology_h2_absolute_speed.py`, modeling focal **raw m/s**
conditional on crossed horse and race fixed effects, with two-way
descriptive uncertainty and time-forward contrasts. The zero-effect
null and deliberately confounded null are reported in
[the versioned absolute-speed audit](ecology-h2-absolute-stress-audit.md).

This correction reduces a specific inference risk; it does not
demonstrate causation, ecological selection or a valid social animal
model. Full details: [absolute-speed method](ecology-h2-absolute-outcome.md).
