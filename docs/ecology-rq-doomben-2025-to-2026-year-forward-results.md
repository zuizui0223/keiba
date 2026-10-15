# Doomben original HORSES IDs: 2025 history does NOT improve 2026 early relative timing

**Frozen original-source retrospective evaluation, 2026-10-15.**
Independent read-only original-source [GitHub Actions run
#38677957462](https://github.com/zuizui0223/keiba/actions/runs/38677957462).
**This is a negative exploratory result; do not turn it into a biological
year effect, absence of personality or an absence of horse-specific
variation.**

Pre-scoring methodological protocol:
[2025→2026 own-versus-other history source lock](ecology-rq-doomben-cross-year-own-vs-other-history-lock.md).

Source: [Racing Queensland Thoroughbred Sectionals and Position
Maps](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
and original HORSES-ID records from
[Queensland Open Data Web Services](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf).

## Why this test was needed

The same Doomben first **150m** positive-GPS sources gave a race fixed
Gaussian conditional horse-ID ICC **0.653589** on selected 2025 dates,
but **0.180116** after combining those 2025 observations with the
previously date-locked 2026 cohort. Those two estimates describe
*different source populations and time mixtures*. They are not proof
that an individual racehorse's behavior changed.

We asked a more directly interpretable source-conditional question:
**Does the very same original internal HORSES ID's 2025 initial pacing
history predict its 2026 relative initial pacing better than the
2025 histories of different horses under the same source conditions?**

This is deliberately a *year-forward holdout*. This research question
was proposed after observing the pooled ICC contrast and after the
source identity-availability study. It is **not a prospective,
preregistered, independent biological confirmation**, and no
additional dates/horses were chosen based on the 2026 score.

## Fixed source sample and data preparation

- Exactly 23 prelocked 2025 Doomben dates and the same unchanged
  19 previously locked 2026 Doomben dates, race numbers 1–6.
- **38 of 42 source dates** fetched and linked successfully in the
  independent real-data CI. Four remain upstream/source **HOLD**:
  2025-01-22, 2025-05-28, 2025-08-27 and 2026-08-26.
  No missing date has been interpreted as zero horses, a nonfinish
  or a zero early-section time.
- Source race-relative target among **observed positive-GPS horses
  only**: the individual's first sectional duration in seconds minus
  the mean first sectional duration of the **other timed-GPS horses
  in the same race**. Require ≥4 valid timed GPS horses in each
  original race.
- Original numeric HORSES ID is validated by same-race exact name,
  repeated name consistency and same-day identity checks.
- **Training ONLY in 2025**, never using 2026 outcomes to update
  the historical mean even for a horse with multiple 2026 starts.
- Outcome-only scoring on 2026 source records from the *same HORSES
  ID, same initial 150m/200m GPS marker and identical original
  official race distance* as 2025. A stricter exact **Race Class**
  check is reported separately.
- Compare a zero race-relative baseline, a historical **OTHER
  HORSES** same-marker/distance mean *excluding focal animal
  entirely*, and the focal HORSES ID's 2025 mean; apply identical
  fixed history shrinkage \`n/(n+2)\`. At least 3 distinct other
  HORSES IDs are necessary for the alternative.
- Report **RMSE with equal weight per focal HORSES ID** across
  exactly the same held-out 2026 observations for every comparator.
  No individual horse results or predictions are published.

All numeric comparisons required **at least 20 original HORSES IDs
crossing source years in matched contexts, 20 2026 scored records
and at least 3 original dates per year**. This engineering gate was
frozen in the research protocol *before examining these 2026 scores*.
It is a support threshold, not a statistical power calculation.

## Actual official-source score results

| Original GPS first marker and source context | 150m, matching original race distance |
| --- | ---: |
| 2025 source dates contributing observed 150m timing | 18 |
| 2026 source dates contributing observed 150m timing | 14 |
| Distinct original HORSES IDs with matched 2025/26 history | **26** |
| Future 2026 observed GPS rows scored on those horses | **27** |
| Source matches excluded for lack of ≥3 OTHER HORSES historical IDs | **0** |
| Equal-HORSES-ID-weighted RMSE, no focal history | **0.368844 seconds** |
| RMSE, historical OTHER HORSES same marker/distance | **0.368906 seconds** |
| RMSE, focal horse's own 2025 history | **0.386131 seconds** |
| Gain (OTHER RMSE − OWN RMSE), positive would mean own better | **−0.017225 seconds** |
| Gain (zero RMSE − OWN RMSE) | **−0.017287 seconds** |

**The originally proposed positive cross-year generalization did
NOT occur in this selected observational sample.** The focal
horse's own 2025 mean was **less useful** for 2026 race-relative first
sectional timing than either the unpersonalized zero baseline or
other original horses' 2025 source-context mean, under the fixed
prediction rule. This negative outcome is preserved unmodified.
Do not tune shrinkage, loosen thresholds or switch to a different
marker/class definition just to obtain a positive result.

This is **not** a confidence interval, causal test, or population
proof of no stable individual variation. The historical source
sampling and the 2026 outcome groups were selected by race
participation, positive sensor availability and original ID
availability, with no independently verified starters/finishers.

## Other source conditions: explicitly HOLD, not zero improvement

| Matched condition | Original HORSES IDs | 2026 records | Scientific scoring status |
| --- | ---: | ---: | --- |
| 150m + same original race distance + Class | 6 | 6 | **HOLD**, fewer than 20 IDs |
| 200m + same original race distance | 13 | 14 | **HOLD**, fewer than 20 IDs |
| 200m + same original race distance + Class | 3 | 3 | **HOLD**, fewer than 20 IDs |

These are slightly fewer than earlier source **availability**
counts (6/4 Class-matched at marker) because the present
evaluation additionally requires a race with ≥4 positive
GPS-timed animals and an actual 2025 historical timing record.

No RMSE or positive/negative effect was computed or reported as
a scientific result for the three HOLD contexts.

## Interpretation for animal ecology

**Previous intra-2026 evidence:** at Cannon Park, a horse-specific
history of earlier relative first-section times was associated
with later relative first-section time under the same source
distance/marker, and was more useful than alternate histories
from OTHER horses. Its positive source-ID variance and forward
checks were not separated from training/rider selection.

**New interannual Doomben result:** the same direct old-horse
history criterion, applied *strictly from 2025 to 2026*
at a different original venue, was not predictive in
26 eligible source IDs. It therefore challenges a
**stronger, universal claim that individual early relative pacing
always persists across calendar years and racing contexts**.

But this contrast does **NOT** isolate an individual's aging or
behavioral change: it simultaneously changes source venue,
source year, observed animal population, race Class, rider/trainer
arrangements, contemporaneous peers and potentially GPS hardware,
and only 6 animals satisfy even the broad original Class match.

**Most defensible biological framing**:
repeated horse-ID-associated pacing within one selected study
context need not generalize to other years and source cohorts.
Whether the reason is real context-dependent behavior,
selective race entry, training/development, race class or
measurement quality remains **unidentified**.

This result must not be rebranded as H1 individual
Good/Soft/Heavy random slopes (not fitted), H2
competition/social plasticity (not estimated),
heritability, personality, natural selection,
adaptation, welfare, wagering advice or expected profit.

## Reproduction and QA

Source protocol: [locked 2025/2026 dates + cross-year
comparator](ecology-rq-doomben-cross-year-own-vs-other-history-lock.md).

Code: [\`scripts/ecology_rq_doomben_cross_year_forward.py\`](../scripts/ecology_rq_doomben_cross_year_forward.py).

Fake-data falsification:
[\`tests/test_ecology_rq_doomben_cross_year_forward.py\`](../tests/test_ecology_rq_doomben_cross_year_forward.py).
The generated tests include stable and **flipped**
individual histories: the algorithm must correctly return
a negative benefit when fake individual tendencies reverse.
They also enforce the ≥20-HORSES-ID HOLD, strict source
Class matching, exclusively earlier 2025 training,
and conservative original ID matching.

CI:
[Doomben 2025→2026 real original-source run
38677957462](https://github.com/zuizui0223/keiba/actions/runs/38677957462),
[GitHub main research suite 245 checks
38677957345](https://github.com/zuizui0223/keiba/actions/runs/38677957345).

~~~bash
python -m unittest discover -s tests \
  -p 'test_ecology_rq_doomben_cross_year_forward.py' -v

python scripts/ecology_rq_doomben_cross_year_forward.py \
  --output tmp/doomben-2025-to-2026-horse-history-aggregate.json
~~~

The CI artifact contains dated source-status and SHA-256 fingerprint
provenance plus **anonymous aggregate score/HOLD output only**.
No horse ID, name, rider/trainer licence, raw GPS time,
individual prediction or betting record is published by the pipeline.

### Next data need

At least 20 actual, officially confirmed starters with
**2+ first-section GPS observations in EACH year** at the
same marker, distance and controlled source Class, along
with age, final jockey/trainer/weight and a more representative
source-date sample. Prefer an independent future year
fixed before any new outcomes and validated
complete/failed sensor coverage. The currently observed
zero repeated-ID support at the 2+ each-year gate is
a design limit, not an effect of zero individuality.
