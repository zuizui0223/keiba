# Frozen post-hoc comparator: horse history versus other horses' earlier source profiles

**Design locked 2026-10-14 BEFORE inspecting this new comparator's
original RQ outcomes.** Prior favorable within-horse ICC,
cross-jockey repeatability, and past-horse-versus-zero forward
results were known. This is therefore post-hoc, exploratory,
not a preregistered independent replicate, true rider effect,
or an out-of-source pre-race forecast.

## Scientific alternative explanations to challenge

The original fixed 12 Cannon Park (2026) source-date cohort gave
a roughly 0.042-second equal-horse-weighted RMSE reduction
from *strictly earlier horse-specific* first-GPS race-relative
times versus a fixed zero-mean population reference among
source records with an original Jockey/@Id not documented
previously for the same horse at the matched marker/distance.

A source-linked stable horse profile may nevertheless be a
proxy for the **historical event context**, **trainer**,
or **rider**. This audit tests a more relevant benchmark,
using a strictly earlier mean of **OTHER original HORSES IDs**
whose race distance and first GPS marker agree with the focal
future source record, and secondary benchmarks based on
previous other horses with the same documented trainer/rider.

## Population and strict time ordering

- Reuse the already original-source-locked Cannon Park
  12 dates, official races 1–8, stable numeric source HORSES
  IDs matched uniquely to positive first GPS race sectionals.
  Peers with missing role metadata remain in each race's GPS
  focal outcome. Do not add dates or select rows based on
  whether the comparator succeeds.
- Focal future outcomes are exactly the earlier scored
  **new documented jockey** category from
  ecology_rq_rider_forward_check.py:
  at least one prior dated horse measurement with a numeric
  Jockey/@Id in the same original official race distance and
  exact first-GPS marker context; future registered source
  Jockey/@Id is numeric and absent among that focal horse's
  previously documented licences within the matched context.
  This does NOT guarantee a genuinely new final race rider.
- All predictions for a source date are constructed from
  **strictly prior source dates**. Never update a history
  using another race on the focal date. Race-relative targets
  are measured after the actual race and observed GPS field.
  This is NOT a pre-race prediction or wagering model.
- Primary context is identical official race distance and
  first GPS distance marker; the secondary stricter analysis
  adds identical official Class.

## Fixed models and matched scoring cohorts

The original historical horse predictor uses the EXACT
preexisting fixed shrinkage n/(n+2) on the mean of all its
prior same-context race-relative first-GPS times.
A **new context-peer predictor** uses the mean of all earlier
matched-context race-relative observations among **other**
numeric HORSES IDs, explicitly excluding ALL observations
of the focal HORSES ID (even if recorded with the same trainer).
The same deterministic n/(n+2) shrinkage toward zero is
applied. The existing zero benchmark is also scored
on the **identical future rows**.

Evaluate the primary paired comparison only among eligible
future focal rows with >=1 earlier different-HORSES-ID
matched-context GPS-positive record. Scoring uses **equal
horse weight**: mean future-record MSE within each horse,
then mean across original HORSES IDs and square root.
Also report equal-horse MAE and event-weighted RMSE.

For **secondary** role-proxy controls, separately restrict
to focal rows with:
(a) a numeric current Trainer/@Id and at least one earlier
OTHER HORSES ID with the identical original trainer
licence plus identical context, or (b) a numeric current
Jockey/@Id and an earlier OTHER HORSES ID with that same
documented jockey plus identical context. Exclude focal
horse's own earlier rows from the role benchmark. Profile
means use exactly the same fixed shrinkage. Compare
the historical horse predictor, same-role-other-horses
predictor, and zero on the IDENTICAL scored rows.
Do not use another source date or change original
primary acceptance criteria because a role sample is sparse.
Never interpret subgroup differences as jockey/trainer
causal contributions.

Original sample and gate frozen BEFORE numerical outcomes:
each primary and secondary paired comparison requires
at least **20 distinct focal HORSES IDs**, at least
**20 matched future source observations**, at least
**6 distinct later source meeting dates**, and at least
**20 horse-by-context strata**. If any threshold fails,
emit HOLD with source support counts, not a forced point
estimate or numeric zero. These are support heuristics,
not a power calculation, valid p-value, or 95% CI.

A favorable horse-versus-context baseline result
would make *purely generic prior context* an insufficient
explanation for this selected source sample. It still
would not distinguish inherited temperament from horse
age, training, stable source sensing, nonrandom horse
and rider assignment, or fitness. A negative result
would reduce confidence that horse-specific past
performance is needed beyond basic source context.
Either outcome is useful; the benchmark must not be
retuned after viewing it.

## Source version and publication discipline

All 12 original dates must have successful verified
Racing Queensland SOAP HORSES and positive GPS joins
before any empirical summary is adopted; otherwise
return source availability HOLD. Retain per-date
original meeting/race/GPS and aggregated HORSES roster
response SHA256s, acknowledging historical 548 vs
543 candidate source snapshot difference.

Output only anonymous matched numbers, summaries,
HOLD codes, source-provenance hashes and static code.
NEVER export source horse name, numeric HORSES/jockey/
trainer ID, individual GPS split, individual predicted
time, or wagers/odds.

This is not H1 horse×ground response variance,
H2 competitor/social effect, selection/adaptation,
heritability, a biological population CI, or evidence
of an actual confirmed jockey change.
