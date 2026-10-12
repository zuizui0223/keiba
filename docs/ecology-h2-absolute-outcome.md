# H2 response-variable audit: relative scores versus focal absolute speed

Status: **RESEARCH METHOD CHECK, SYNTHETIC ONLY**. Added on 2026-10-12;
no empirical horse-racing social-effect result is asserted.

## A mathematically generated false signal to avoid

A standardized within-race performance outcome was previously used:
`z_ir = (v_ir - mean_r(v)) / sd_r(v)`.

Holding the focal horse's own speed `v_ir` fixed while changing an
*opponent's finishing speed* necessarily changes both the race mean and
standard deviation, and therefore changes `z_ir`. Thus `z_ir` may
respond to an opponent's strength **without the focal horse changing its
behavior or absolute velocity at all**.

A unit test,
`tests/test_ecology_h2_absolute_speed.py::test_rival_outcome_can_change_focal_z_but_not_focal_raw_speed`,
demonstrates this arithmetic artifact on wholly fictional races.

A nonzero competitor-context association on race-relative z-speed,
place or rank alone is **not evidence of a causal social response**.

## Improved primary exploratory outcome

Use individual `v_ir = race_distance_m / individual_finish_time_s`
(metres per second), with *crossed horse and race fixed intercepts*:

```text
v_ir = horse_i + race_r
     + beta_ability × own_prior_ability_ir
     + beta_style × own_prior_style_ir
     + beta_going_style × frozen_horse_style_i × poor_going_r
     + gamma × frozen_horse_style_i
         × (opponent_front_share_ir - horse_i_training_mean_share)
     + error_ir
```

- Horse effects remove each animal's time-invariant baseline.
- Race effects absorb common date, track, class, going and overall rival
  environment shifts shared by all starters in that race.
- Horse-style×going remains separately fitted because a style-dependent
  reaction to environmental conditions could otherwise mimic H2.
- The main effect of overall rival composition is not separately
  identifiable after including race FE for full-field composition.
  Similarly, mean rival *ability* is algebraically decomposable into
  race mean ability and focal own ability in complete fixed-size fields.
  The code therefore drops those exactly redundant main effects.
- `gamma` is a **within-horse association conditioned on observed fields**.
  It still cannot by itself distinguish direct social responses from
  selective entry, jockey strategy, mechanical draft/traffic interactions,
  age changes, or other unmeasured time-varying factors.
- Before each heldout race, future race fixed intercepts are unknown.
  Evaluation consequently compares *within-race centred RAW SPEEDS*
  (m/s) without calculating the z-score denominator `sd_r(v)`.
  This is a different, more restricted metric than predicting absolute
  elapsed time in isolation.

The implemented experimental model is
`scripts/ecology_h2_absolute_speed.py`; test coverage is
`tests/test_ecology_h2_absolute_speed.py`, and a companion
`scripts/ecology_h2_absolute_stress.py` runs null, planted and
assortative-entry/ground-confounded fictional cohorts. Explicit guardrails
reject fabricated data unless demo mode is chosen. Approximate two-way
horse/race cluster intervals are for descriptive sensitivity only.

## Ecological interpretation and previous literature

The **biological question** is whether a horse's *focal performance*
changes conditionally on the phenotypes of its rivals, not whether it
ranks differently against a stronger opponent field.

- van de Pol & Wright (2009), within- vs between-individual
  centering: https://doi.org/10.1016/j.anbehav.2008.11.006
- Martin & Jaeggi (2022), social plasticity and assortment:
  https://doi.org/10.1111/jeb.13900
- Spence et al. (2012), pacing and drafting in horse racing:
  https://doi.org/10.1098/rsbl.2011.1120

These are conceptual/methodological benchmarks; a full social animal
model (measurement error, partners' latent phenotypes, genomic relatedness,
indirect genetic effects, causal selection) is **not** fitted here.

## Evidence threshold

Even if the new `gamma` is nominally nonzero in a factual
longitudinal dataset, this is **only a conditional association** until
it survives prespecified trainer/jockey/class selection controls,
history-aware rival composition, changing-field overlap, alternative
style thresholds and definitions, multiway dependence, and a genuinely
independent temporal cohort. The current Kyoto 2026-10-12 dataset has
no suitable complete repeated-start panel.

Data rights must be independently checked:
[ecological data-source feasibility](ecology-data-source-feasibility.md).


## DNF / incomplete speed amendment (2026-10-12)

The `ecology_h2_absolute_speed.py` model **no longer requires every
confirmed starter to have an observed finishing time**.
A complete starter roster with sufficient historical pre-race features
is retained; nonfinishers remain in every competitor exposure, while
the speed response is defined only among actual timed finishers.
This reduces whole-race complete-case deletion but still leaves
speed-outcome selection and pre-race history coverage biases.

The model records an `outcome_selection_audit` and scientific
`HOLD_POTENTIALLY_INFORMATIVE_SPEED_MISSINGNESS` when eligible
speed outcomes are missing. Do not interpret the regression as
an all-starter performance effect without a documented selection
model and sensitivity analysis. See
[H2 missing-outcome and informative selection](ecology-h2-outcome-selection.md).
