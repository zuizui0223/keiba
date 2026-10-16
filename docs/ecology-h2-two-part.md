# H2 two-part outcome: race completion versus finishing speed

**Research-method and synthetic-software note.** Updated 2026-10-13.
No actual horse×race dataset or empirical ecological association has been fitted.

## Biological reason for two outcomes

An animal that does not complete the event has **no observed full-distance
finish time**. Assigning zero speed to such a horse changes the biological
quantity being studied. Dropping every nonfinisher also selects observed
performance. Analyze two distinct responses:

1. **Completion among confirmed starters:** binary finished versus
   did_not_finish. This may reflect injury, incidents, tactical stops or
   administrative conditions, not necessarily competitor interference,
   survival, evolutionary fitness or adaptation.
2. **Focal speed among timed finishers:** distance_m / finish_time_s
   only when positive individual time was observed. A finish without
   a time has completion=1 but timing-observed=0, a separate
   instrumentation/source missingness problem.

This is **two independently fitted exploratory models**, not a
jointly estimated hurdle likelihood, a causal social animal model,
or a welfare prediction.

## Models

Let S represent the focal horse's historical early-run position and
F the pre-race front-running fraction of OTHER starters, both
computed only from dates earlier than the target start.

Stage A: completion among all actual race starters

~~~text
M0: logit(P(finished)) = intercept + past focal ability + past rival ability
                         + past focal style + rival style share
                         + ground indicator + focal style × ground
M1: M0 + past focal style × rival style share
~~~

The code uses a small **ridge regularization** for the binary model,
centers/scales only on training dates, and compares out-of-time
**log loss** and **Brier score**. It makes no statistical significance
or causal claim. A small number of DNF events triggers HOLD:
fewer than 12 in training or 3 in future test.
These are software design gates, not a sample-size power calculation.

Stage B: speed among observed timed finishers

~~~text
raw_speed_mps ~ horse fixed effect + race fixed effect
              + past focal strength + past focal style
              + focal style × ground
              + focal historical style × within-horse rival context
~~~

All confirmed starters, including eventual DNFs, remain in the
*opponent exposure* denominator. No unobserved velocity is set to 0.
The Stage B fit conditions on timed finishers and remains subject to
possible outcome-selection bias.

## Reproduce on deliberately fictional animals

~~~bash
python scripts/ecology_demo_completion.py --output tmp/artificial-DNF.csv --days 100 --horses 48 --runners 12 --seed 512 --loss random
python scripts/ecology_h2_two_part.py --input tmp/artificial-DNF.csv --output tmp/h2-two-part-fake.json --surface turf --permit-synthetic-demo
~~~

All rows are labelled synthetic; the expected result is
SYNTHETIC_TWO_PART_H2_DEMO_ONLY. See
tests/test_ecology_h2_two_part.py and the GitHub Actions workflow.

## Empirical prerequisites

- Independently verify actual start-versus-withdrawal and
  DNF-versus-missing-time coding for the source.
- Verify longitudinal horse IDs, source rights and **true chronological
  ordering**; a candidate Hong Kong dataset uses obscured dates.
- Record age, class, venue, surface, ground, trainer, jockey, fitness,
  earlier performance, and starter-selection effects where available.
- Document enough DNFs and missing-time events for independent analyses,
  not just a large number of horse starts.
- Obtain appropriately clustered/uncertainty-calibrated estimates for
  completion, robust age/class/jockey and racing-day controls for speed,
  and independent forward validation.
- Apply a pre-registered multiple-testing/sensitivity plan. Ridge
  coefficients alone are not an ecological discovery.

**Biological claims remain HOLD.** Dumelle et al. (2025),
Ecological Monographs, https://doi.org/10.1002/ecm.70037
discusses why accounting for missingness mechanisms matters.
A DNF is a distinct outcome, not a zero or a normal missing
continuous measurement.
