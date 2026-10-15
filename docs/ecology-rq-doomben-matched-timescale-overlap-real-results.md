# Same original horses are absent from BOTH time-horizon scoring populations

**Real original RQ Doomben source result, 2026-10-15.**
**Scientific finding: complete lack of within-animal two-horizon
overlap at the identical first-GPS marker and official race distance.**
This is a genuine *source design/identifiability* result, NOT evidence
for or against biological aging, behavioral personality, temporal
decay, selection, heritability or an H1/H2 mechanism.

The [post-hoc methodological lock](ecology-rq-doomben-matched-individual-timescale-overlap-lock.md)
was committed **before the first numeric source-ID overlap was
inspected for this precise question**. The positive 2025
within-year and negative 2025→2026 history scores were already
known, however. This is NOT an independently prospective
preregistration.

## Why the new test was necessary

Previously the same operator's Doomben 2025 positive-GPS source
yielded a source-conditional **within-2025** historical own-horse
RMSE 0.211065 s versus historical OTHER-horse RMSE 0.240692 s
in 23 HORSES IDs and 24 later GPS records. This was numerically
reproduced in two byte-identical anonymous 38/42-date reruns
but was sensitive to HTTP source availability in earlier reruns.

The **2025→2026** historical horse-history source evaluation was
unfavorable: among 26 source numeric HORSES IDs and 27
held-out 2026 records, own-horse RMSE 0.386131 s exceeded
OTHER-horse 2025 source-context RMSE 0.368906 s.

**The paired-timescale biological question is NOT whether
23 and 26 are different sample sizes. It is whether the
same horse IDs and same measurement contexts occur in
BOTH populations.** A positive 2025 and unfavorable
2026 statistic from nonoverlapping animals is NOT a
within-animal comparison of behavioral persistence.

## Exact source population and two independent audits

Source: [Racing Queensland original Thoroughbred Sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
and source Open Data Web Services numeric HORSES ID,
uniquely matched by race/date/horse-name consistency,
first positive GPS duration and >=4 positive-GPS
timed horses per original race.

Exactly the previously locked **23 Doomben 2025 dates and
19 Doomben 2026 dates**, race numbers 1–6 as available.
Original official source replay succeeded for **38/42**;
four unavailable source dates remained scientific/source
HOLD: 2025-01-22, 2025-05-28, 2025-08-27 and 2026-08-26.
No dates, horses, results or marker values were
added or replaced after observing the result.

- [First original source score-population run #38702929634](https://github.com/zuizui0223/keiba/actions/runs/38702929634),
  which passed nine synthetic falsification tests and
  fetched 38 source dates.
- [Source-only date-incidence independent cross-check
  #38703717378](https://github.com/zuizui0223/keiba/actions/runs/38703717378),
  which recomputed overlap using only original source
  numeric IDs, dates, marker, distance and optional
  Class, **without any predicted or measured GPS durations
  in the incidence counts**.
- [Source-lock and scientific decision rules](ecology-rq-doomben-matched-individual-timescale-overlap-lock.md).
- Code:
  [ecology_rq_doomben_matched_timescale_overlap.py](../scripts/ecology_rq_doomben_matched_timescale_overlap.py).
  All original animal data remain in memory;
  output stores only anonymous aggregate counts
  and date-level source SHA256 fingerprints.

The full source pass linked **1,277 positive first-GPS candidate
records, 977 distinct official numeric HORSES IDs**, of which
**228 IDs** appeared on two or more source dates when **all first
GPS markers and official race contexts are pooled**. Zero
HORSES IDs were rejected for inconsistently changed names
across the original dates. There were **1,227 records
in original races with >=4 positive GPS horses**.
Therefore the zero two-horizon overlap cannot be attributed
to a blanket absence of stable source ID matching;
the exact marker/distance/year repetition design is critical.

## Actual source incidence and outcome-scorer agreement

| Original HORSES-ID source criterion | 150m + identical official distance | Also require identical original Class |
| --- | ---: | ---: |
| Individuals with **2+ distinct 2025 source days** | **23** | **17** |
| Individuals with **>=1 source day in EACH of 2025 and 2026** | **26** | **6** |
| Individuals with **>=2 source days in 2025 AND >=1 source day in 2026** | **0** | **0** |
| Individuals with **>=2 distinct source days in EACH year** | **0** | **0** |
| Original distinct source horse ID × matching marker/distance(/Class) contexts satisfying the >=2, >=1 gate | **0** | **0** |

The **source date/identity-only counts (which did not inspect
GPS time outcomes) independently agree** with the two pre-existing
strict historical forecast scorer groups:

| Existing source-conditional scoring population | Original HORSES IDs |
| --- | ---: |
| Later 2025 same-horse **within-year** history scores | **23** |
| Held-out 2026 same-horse history scores using 2025 only | **26** |
| Original HORSES IDs appearing in BOTH evaluated prediction groups, **even ignoring exact context** | **0** |
| Shared numeric HORSES IDs at the exact 150m marker + race distance | **0** |

Under the pre-fixed minimum 20 identical horse IDs and 20
future observations per horizon, this result returns:

**HOLD_INSUFFICIENT_SAME_HORSE_TWO_TIMESCALE_CONTEXT_SUPPORT**

No matched-horse RMSE, RMSE change from 2025 to 2026,
p-value or 95% confidence interval was fitted.
An unsupported comparison is NOT an estimated zero.

### Ecological inference

This is a **common-support / positivity failure** for any
stronger claim of a temporally changing within-animal
behavioral trait under the required measurement context.

The separately observed source-conditional positive
within-2025 and nonpositive 2025→2026 scores
remain genuine descriptive outputs **for their own,
different source-exposure populations**.
The *difference of those scores does not estimate
a source year, individual age or temporal memory-decay effect.*
Even their first-interval marker/distance measurements
do not make the animals exchangeable, because Class,
source-peers, training, stage of career, source
availability and entry into races are uncontrolled.

Identifying a population-relevant ecological timescale
would require observing the **same official horse ID
at least twice in the earlier year under an identical
GPS marker, race distance and preferably Class,
and repeatedly in the next year under the same
conditions**. One observation next year would permit
the most basic paired predictive transfer, and
two or more in EACH year would be substantially
more defensible for a repeated-measures model.
The current locked source has **zero** even under
the weaker 2+ earlier plus 1+ later gate.

The missing actual starter list, final assigned rider,
horse age/training, official finish time and GPS
coverage denominator remain material confounders.
The original RQ SOAP specification shows that
GetHorsesForRace/GetHorseDetailsInRace supply
assigned jockey/trainer fields but do not by
themselves verify final actual postrace outcomes:
[official source scope audit](ecology-rq-official-soap-vs-final-starters-jockey-data-scope.md).

### Publication decision

Retain the 2025 in-sample source history gain and
2025→2026 same-ID history non-transfer as **two
separately conditional observations**.
Explicitly annotate Figure 1 and its caption with
the lack of matched same-animal time-horizon
overlap when discussing apparent temporal generalization.
**Do not describe their contrast as an estimate
of a within-animal or age-related decline.**

This is evidence about **identifiability**, not
a result that repeatability actually disappears.
Original H1 individual responses to ground,
H2 causal opponents and evolutionary
heritability/adaptation remain HOLD.

No original horse identities, names,
licensed jockey/trainer identifiers,
individual source split times, or
horse-specific predicted outcomes were
published in the associated aggregate-only
workflows and artifacts.
