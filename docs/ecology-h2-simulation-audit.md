# H2 simulation / negative-control audit (fabricated data only)

Status: **SYNTHETIC_DESIGN_STRESS_ONLY**. This is NOT a finding from
real horses, not a statistical-power analysis, and not a causal estimate.

Reproduced by GitHub Actions
[run #38223619834](https://github.com/zuizui0223/keiba/actions/runs/38223619834)
at code commit [c4a901a](https://github.com/zuizui0223/keiba/commit/c4a901a93baa9c9c1330365b205d4cd3d4da8547),
using `python scripts/ecology_h2_falsification.py --output tmp/h2-null-stress.json --seeds 512 911 --days 65 --horses 36 --runners 12`.

Exactly **6** artificial panels: 3 generator mechanisms × 2 RNG seeds,
65 fictitious race dates, 36 fictitious horses, 12 entrants/race, with
pre-race history construction. The `status` of these panels is
`synthetic`; all models fitted using the exact same software.

## Reported software outputs

| Fabricated mechanism | Successful fits | Leave-one-out nominal interval excludes 0 | Full-field nominal interval excludes 0 | Mean future-RMSE gain, LOO | Mean future-RMSE gain, full |
| --- | ---: | ---: | ---: | ---: | ---: |
| Zero opponent effect, random entry | 2/2 | 0/2 | 0/2 | −0.000063 | −0.000082 |
| Planted opponent effect (raw speed-scale coefficient = −0.9) | 2/2 | 2/2 | 2/2 | +0.016411 | +0.015843 |
| Zero opponent effect, assortative entry plus style×going effect | 2/2 | **1/2** | 0/2 | −0.001791 | −0.002386 |

**Gain** = RMSE of baseline model minus RMSE of interaction model, on
**standardized within-race speed**; positive means the interaction
model improved chronological predictions. These are *simulation-only*.
Planted DGP parameter `−0.9` is on raw speed scale and **cannot be
numerically compared** with the fitted regression coefficient on
race-relative standardized speed.

These observations demonstrate a *methodological failure mode*:
one of two deliberately confounded zero-competition simulations produced
a **nominal** LOO interaction interval excluding zero, while the model
did **not** improve out-of-time predictive error. A nominal confidence
interval is not a causal effect, and both definitions of social exposure
must be scrutinized.

Two seeds per scenario are far too few to estimate error rates or
statistical power. In particular `1/2` is not a population false
discovery rate or a valid hypothesis test; simulation outcomes depend on
generator parameters and field construction.

## Falsification decision

- **Technical result supported:** code handles null, planted, and
  deliberately confounded artificial panels, with strictly prior-day
  features, horse fixed intercepts, two-way horse/race nominal covariance,
  frozen training means, and later-date prediction comparisons.
- **Technical vulnerability observed:** under a planted
  assortative-entry/track-going confounder, a nominal within-horse
  interaction can appear under a zero true competitor effect.
- **Biological inference HOLD:** no multi-year horse×race panel from
  an authorized source has been used; therefore **there is no evidence
  yet for H2 among real horses**.
- **Model upgrade required before empirical H2 claims:** genuine
  within-horse opponent variation conditional on track/distance/class,
  covariate-adjusted entry/withdrawal, jockey interactions, race
  heterogeneity, simultaneous companions' behavior and quality, threshold
  sensitivity, and realistic measurement-error treatment.

Related methodological literature:
- van de Pol & Wright (2009), DOI 10.1016/j.anbehav.2008.11.006.
- Martin & Jaeggi (2022), DOI 10.1111/jeb.13900.

This record is frozen to the above versioned software run. Newer runs
must not silently replace its values without recording the new run,
hash, generator settings, and validation scope.
