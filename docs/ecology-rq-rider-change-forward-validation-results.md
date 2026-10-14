# Forward-only early race-relative timing under a newly documented original jockey

**2026-10-14; genuine original Racing Queensland horses; exploratory/post-hoc.**
Evidence: [successful original official 12-date source execution
#38501390778](https://github.com/zuizui0223/keiba/actions/runs/38501390778)
and its anonymous aggregated JSON artifact.
[Source-selection and decision gates](ecology-rq-rider-change-forward-validation-lock.md)
were committed before evaluating this new forward-only score,
**but earlier positive horse-ID repeatability / rider-switch
results were already known**. This is not an independent preregistered
biological test.

## What this adds to the prior observational findings

The prior source-linked Census of Cannon Park had a positive
race-adjusted horse-associated ICC and a positive pair product
between separate races even with different source-declared jockeys.
Both are in-sample association diagnostics. The new question is
different: **does a strictly earlier history of a horse's early
race-relative timing reduce error for that horse on a later date,
when the later source records a Jockey/@Id not previously documented
for that horse under the same original measurement context?**

Only the *horse's earlier* dated records in the identical original
race distance + first GPS marker contribute to the horse-specific
profile. On each date, predictions are evaluated before observations
from the current day enter history. The historical mean is shrunk
with fixed n/(n+2) toward 0, reusing the previously fixed shrinkage
from the historical time-ordered persistence checks; no weight is
trained on this evaluation target. The comparator always predicts
zero race-relative initial timing (no individual horse profile).

The observed target is focal first-GPS split duration MINUS
the other GPS-positive runners' same-race average duration.
The **actual target cannot be observed until the race/sectional
data exist**, so the result is a retrospective *out-of-time
ecological persistence check*, not an external validation,
real-time pre-race forecast, betting model, or true individual
full-course finish time.

Source: [Racing Queensland Sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
and the original GetMeetingsForDate -> GetRacesForMeeting ->
GetHorsesForRace numeric internal HORSES ID; exact normalized
same-race-name linkage to original first GPS-positive split.
Source entry records and Jockey/@Id values may be nominations;
the actual starter/finisher and final jockey are not independently
verified. Original HORSES/horse names/rider/trainer IDs and
individual outcome/prediction rows remain in memory.

## Real 12-date Cannon Park output

All **12/12** previously locked 2026 original Cannon Park
meeting dates were successfully retrieved. The current
original-source snapshot contained **543** positive GPS
candidate rows; **519** rows across 74 races survived
the >=4 GPS-positive peers threshold. Exactly **378/519**
timed rows had a valid numeric source Jockey/@Id.

The *primary* future observations require at least one
earlier matched-context observation with a valid documented
jockey and a current numeric Jockey/@Id that does not occur
among any **previously documented** jockeys in that context.
This does **not** prove an actual newly changed rider if
other historical source jockey fields were absent; one of
the 46 primary future records had a prior unknown jockey.

| Past-only evaluation (equal weight per original HORSES ID) | 0-personalization benchmark RMSE | Shrunk historical individual profile RMSE | Reduction |
| --- | ---: | ---: | ---: |
| Same official distance + first GPS marker; previously undocumented source jockey: **36 IDs, 46 scored rows, 11 future source dates, 38 matching contexts** | **0.297676 s** | **0.255809 s** | **+0.041867 s**, approximately **14.1%** |
| Same requirements plus identical original race Class: **20 IDs, 22 rows, 9 future source dates, 20 contexts** | 0.369825 s | 0.320113 s | +0.049712 s |
| Main context, also same documented original trainer somewhere in prior matched context: **29 IDs, 39 rows, 11 source dates, 31 contexts** | 0.306119 s | 0.262200 s | +0.043919 s |
| Main context, source Jockey/@Id *previously observed* for the horse: **44 IDs, 51 rows, 11 source dates, 46 contexts** | 0.395747 s | 0.345896 s | +0.049852 s |

The secondary subsets include different horses/date/race histories;
the differences among rows of this table are **not causal
effects of changing jockey or changing trainer**.
The stricter same-Class result sits exactly on the minimum
20-ID/20-context support boundary and is particularly fragile.
The even stricter same-Class plus same-trainer group has
only 16 IDs and is **HOLD, not zero improvement**.
The same-Class previously-seen-jockey group has 19 IDs,
also **HOLD**.

For the main 36-ID future subset, secondary precision summaries:

- Equal-HORSES-ID MAE: **0.243281 -> 0.200538 seconds**.
- Row-weighted RMSE: **0.320277 -> 0.266649 seconds**.
- RMSE reduction is a point result for the selected observational
  source cohort, NOT a valid confidence interval, permutation p value,
  population-wide forecast improvement, or guarantee on unobserved
  later meetings.

### Reproducibility and source-snapshot uncertainty

The fresh all-12-date read again yielded **543** linked positive
first-GPS candidate rows, the same as the recent rider-switch
analyses and **five fewer than the previous 548** official matches
in the older original Cannon Park audit. The prior historical
GetHorsesForRace response SHA256 fingerprints were not archived,
so the reason for five fewer linked candidates is unresolved.
The current manifest saves meeting/race/GPS and aggregate
per-date original HORSES roster response SHA256s, but it cannot
reconstruct unrecorded historical source editions.

Past-only synthetic falsification passed **all 11 new tests**,
including no future/same-date leakage, source Jockey missingness,
input row order invariance, fixed shrinkage, explicit support
HOLDs, and no individual-level data publication. The full
[research QA #38501390724](https://github.com/zuizui0223/keiba/actions/runs/38501390724)
passed **192 tests**. Source-level analysis run #38501390778
completed successfully.

Program:
- scripts/ecology_rq_rider_forward_check.py
- scripts/ecology_rq_rider_switch_consistency.py (in-memory integration)
- tests/test_ecology_rq_rider_forward_check.py

The artifact contains only anonymous source/sample counts,
conditional aggregate RMSE/MAE results, source date hashes,
and scientific HOLD codes. No actual HORSES names, IDs,
jockey/trainer licence IDs, original GPS row timings,
or per-horse prediction history are exported.

## Scientific interpretation

**Supported only as post-hoc observational/measurement-conditional
evidence:** earlier race-relative first-section timing for
a horse contains predictive information for later source-timed
first-section timing, even among records in which a new
source-nominated jockey licence is documented for that
matched race-distance + first-marker context. That is
additional evidence of temporal horse-ID-associated consistency
within this selected one-course data source.

**Not supported:** the same animal's result under actual verified
rider changes, intrinsic neural/physiological personality,
causal jockey/trainer/horse contributions, unmeasured fitness
or training effects, independent source/vendor replication,
heritability, adaptation, H1 ground-dependent reaction norm
or H2 effects of opponent social interactions. Races and horses
were not randomly sampled or assigned; age, selection,
sensor missingness and actual start/finish state remain unresolved.

**Main next scientific priority:** independently verified actual
starter/jockey/result rosters and source rights for a
prospectively fixed validation cohort that allows rider/trainer
disentanglement and representative measurement coverage.
Do not increase inclusion by selecting later meetings based on
this favorable score, and do not describe the above as
a wagering model.
