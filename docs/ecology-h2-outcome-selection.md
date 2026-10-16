# Observed race starts versus available finishing times (H2)

Status: **method and software validation, not an empirical effect**.
October 12, 2026. This note documents the missing-outcome safeguard in
`scripts/ecology_h2_absolute_speed.py`.

## Why missingness matters biologically

A horse can start a race but not finish or can finish without a verified
individual time. Excluding an entire field whenever one horse lacks a
finish time conditions analysis on every member's race outcome. If
noncompletion is related to ground, running style, competition intensity,
injury, tactical behavior or unobserved fatigue, this can preferentially
remove environmentally challenging encounters.

Dumelle et al. (2025), *Missing data in ecology: Syntheses, clarifications,
and considerations*, Ecological Monographs, DOI
https://doi.org/10.1002/ecm.70037, reviews complete-case analysis, MAR,
MNAR, multiple imputation, inverse-probability weighting and other
ecological missingness methods. Not all missingness is equivalent or
necessarily correctable from the recorded variables.

## Population, selection stages and estimation target

- **Starting population:** horses that truly started and are therefore
  competitors in the observed race. Pre-start withdrawals must NOT
  be confused with `did_not_finish` and must be omitted from the
  confirmed starter denominator.
- **Pre-race exposure:** all confirmed starting horses, including eventual
  nonfinishers, count in the number/composition of rivals. Historical
  style and ability are computed exclusively from races prior to the
  target date.
- **Outcome:** raw focal speed is `course_distance_m/finish_time_s`
  only where a positive verified individual time is observed. Missing
  time has no defined speed and must NEVER be set to zero, a penalty
  speed, or the winner's speed.
- **Strict pre-race history gate:** the current model still excludes a
  race if any starter lacks required historical style/ability data.
  This is a **separate pre-exposure cohort-selection bias** and must be
  reported, not confused with missing finishing times.
- **Post-race speed gate:** a field with a complete starter roster and
  sufficient historical coverage can now enter the regression even if
  one or more horses lack a finishing time, provided >=4 timed
  finishers remain. The missing-outcome horses remain in the exposure
  denominator but contribute no speed outcome.
- **Inference target is now explicitly conditional on timed finishers,**
  not automatically representative of every entrant.

## Data-quality reporting implemented

`frame_with_individual_speed` returns a dataframe with an
`outcome_selection_audit`, included in final JSON output by
`run`:

- Candidate race and starter counts, full-roster eligibility and
  race exclusions by reason.
- Eligible starters versus observed individual times.
- Number of actual nonfinishers versus finishers whose time is
  unavailable (different reasons).
- Fraction with usable speed by observed ground condition,
  pre-race individual style, and pre-race opponent front-runner context.
- The explicit `HOLD_POTENTIALLY_INFORMATIVE_SPEED_MISSINGNESS`
  status whenever a usable cohort contains missing speeds.
- Explicit inability to diagnose or resolve MNAR solely from
  speed-observed cases.

The H1 pilot and older race-z-score H2 approaches are not
automatically converted into this safer sample design; their separate
historical limitations remain documented.

## Deliberate negative-control stress

Run locally on wholly fictional records:

```bash
python scripts/ecology_h2_outcome_loss_stress.py --output tmp/h2-outcome-loss-stress.json --seed 512
```

Three design scenarios:

1. `none`: all simulated times observed.
2. `random`: a small fraction of late-event records are
   artificially designated as nonfinishers independently of speed.
3. `speed_dependent`: in poor going, one earlier-positioned
   horse with the worse *latent generated speed* is selectively
   censored in chosen late races. The simulator is allowed to
   know this hidden counterfactual; **this information is never
   an observable real-world predictor**.

A shift in the fitted interaction between these artificial panels
demonstrates potential sensitivity, not population bias size.
`HOLD` is recorded even if the coefficient happens to barely move:
the diagnostic flags uncertainty in the missingness mechanism,
not a threshold for statistical significance.

## Required next empirical controls

- Capture **all confirmed starters** and postrace completion status;
  document horse/venue/class/distance/time distribution of attrition.
- Distinguish racehorse welfare and injury-related noncompletion,
  tactical DNF, missing timing instrumentation and administrative
  non-results where the provider supports it.
- Pre-register whether the scientific estimand concerns
  *finishing performers* or *all starters*.
- Analyze the binary outcome `timed finish observed` as its own
  descriptive quality/selection process using pre-race predictors.
- Where missing-at-random assumptions are defensible, consider
  inverse-probability adjustment or joint response/selection models
  with appropriately clustered uncertainty. Avoid presenting either
  as a mechanical causal correction.
- For missing-not-at-random alternatives, use scenario-based
  sensitivity analysis; do not impute unobserved race speeds without
  substantively supported assumptions.
- Account for horse, race and jockey dependence and selective entry
  **before** stating any social plasticity conclusion.

**Crucially:** neither this code nor the associated simulated outcomes
has yet measured a real racehorse ecological effect.
