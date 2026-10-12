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
