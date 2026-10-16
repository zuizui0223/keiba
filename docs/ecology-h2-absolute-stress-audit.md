# Absolute-speed H2 model: synthetic stress test audit

**Status: SIMULATION ONLY — not a biological finding** (2026-10-12).

Verified GitHub Actions run:
[38224958124](https://github.com/zuizui0223/keiba/actions/runs/38224958124)
at commit [b769ce1](https://github.com/zuizui0223/keiba/commit/b769ce1f801fe2600563d037668621370e905b22).

Commands:

```bash
python scripts/ecology_demo_competitors.py --output tmp/fake-competitors.csv --days 65 --horses 36 --runners 12 --seed 512
python scripts/ecology_h2_absolute_speed.py --input tmp/fake-competitors.csv --output tmp/h2-raw-speed.json --permit-synthetic-demo
python scripts/ecology_h2_absolute_stress.py --output tmp/h2-raw-speed-stress.json --seeds 512 911
```

GitHub Actions reported **35 successful automated tests**, and both
synthetic pipelines completed. No actual JRA, HKJC, real horse identity,
official result or licensed source data is used.

## What changed and why it matters

The previous H2 pipeline fitted within-race z-scored speed:

`(focal_speed - race_mean_speed) / race_sd_speed`.

That result changes when an opponent's speed changes **even if the focal
horse does not change its own speed**. The dedicated test
`test_rival_outcome_can_change_focal_z_but_not_focal_raw_speed`
demonstrates this arithmetic trap using fabricated data.

The additional `ecology_h2_absolute_speed.py` instead models focal
absolute m/s, with individual horse and race fixed intercepts.
The race effect absorbs common conditions; the horse effect absorbs
a stable individual baseline. The interaction of a frozen focal style
trait with within-horse changes in opponent composition is assessed
both using leave-one-out and all-entrant field shares. Raw speed is
the *fitted outcome*, whereas future-race prediction error is on
heldout within-race raw speed differences (m/s), avoiding the
contemporaneous z-score denominator.

The model still does NOT resolve nonrandom entry, jockey decisions,
horse fatigue, complete measurement error, ecological fitness, indirect
genetic effects or causality.

## Paired simulation result (TWO SEEDS per artificial mechanism)

The same three synthetic mechanisms were run on both versions.
The table counts cases where a nominal two-way clustered 95% interval
for the H2 interaction excludes zero. **This is not a type-I error rate,
statistical power or causal p-value.**

| Synthetic mechanism | Previous z-speed FE: leave-one-out / full-field | New raw-speed horse+race FE: leave-one-out / full-field |
| --- | ---: | ---: |
| Random entry, zero true competitor effect | 0/2 · 0/2 | 0/2 · 0/2 |
| Planted true competitor effect | 2/2 · 2/2 | 2/2 · 2/2 |
| Zero true competitor effect, nonrandom entry plus horse-style×going effect | **1/2 · 0/2** | **0/2 · 0/2** |

For the raw-speed crossed-FE pilot, mean future within-race prediction
RMSE *gain* (baseline minus H2 interaction) was:

| Mechanism | Leave-one-out | Full-field |
| --- | ---: | ---: |
| Random entry, null | +0.00000693 m/s | +0.00000398 m/s |
| Planted interaction | +0.002591 m/s | +0.002517 m/s |
| Confounded null | +0.000155 m/s | +0.000156 m/s |

The tiny positive gains in null cases are **not proof of a real effect**;
they are consequences of noise, model fitting and a minuscule simulation
sample. We have not preregistered a clinically/biologically meaningful
speed improvement threshold.

For the seed-512 planted simulation, nominal focal-style×rival-context
coefficient estimates were **−0.680 m/s** (leave-one-out) and
**−0.741 m/s** (full-field), compared with the *generator*
parameter **−0.9**. Even with synthetic known effects, measurement
error, coarse historical position profiles, outcome scaling and
selection mean fitted coefficients need not equal generating parameters.

## Conclusion

**Supported technical improvement:** modeling raw individual speed with
crossed horse/race intercepts avoids an especially important mechanical
dependency of within-race standardized speed and passed the tested null
and planted-effect *fictional* cases.

**Not supported:** "competition causes real horses to slow down" or
"individual social plasticity has been demonstrated." Both require
licensed long-term race-level histories, robust contemporaneous
opponent-style measurement, full confounder sensitivity, substantive
validation and appropriately identified partner effects.

Important limitations of this simulation:

- 2 seeds per DGP are **far** too few to estimate operating
  characteristics; do not extrapolate 0/2 to a general low false-positive
  rate.
- The generator has an overly simple competition structure and no realistic
  training, injury, weather uncertainty, career censoring or jockey changes.
- With race FE, race-constant going and field-wide mean contextual terms
  are not identifiable separately from those intercepts; the focal
  style×context interaction remains the central test.
- The outcome is still observational; fit conditional on finishing races
  can introduce selection bias.
- The summary is frozen to a specific CI run; updated code/seeds require
  an independently versioned new audit.

Read [absolute-speed method](ecology-h2-absolute-outcome.md) and
[data rights audit](ecology-data-source-feasibility.md) before treating
the code as an empirical ecological study.
