# Real Thoroughbred repeatability of early race-relative timing (exploratory)

**Independent real-data replication:** 2026-10-13,
[GitHub Actions run #38348581714](https://github.com/zuizui0223/keiba/actions/runs/38348581714).

**Evidence class:** authentic source-linked individual HORSES-ID
observational association with temporal and within-race-label
permutation checks. **NOT** a ground-reaction H1 test, **NOT** social
interaction H2, **NOT** a standard ICC, and **NOT** a causal or
preregistered experiment.

This is a **new, narrower and biologically interpretable question**:
can a horse's *relative early sectional timing* be reproduced in
subsequent races? The research question and permutation analysis were
added **after inspecting the original H1 data overlap**. The
finding is exploratory, not a blinded independent hypothesis test.

## Sources and analysis population

Official original source:
[Racing Queensland Thoroughbred Sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
and [Open Data Web Services](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf).
All individual identities are original source numeric \`HORSES\` IDs,
joined in memory to the public dated GPS row by unique same-race
normalized name. No individual IDs, names, or horse-specific rows are
published in the repository or aggregated CI artifact. Publisher:
Racing Queensland; review its [open-data conditions](https://www.racingqueensland.com.au/about/reports-and-data/open-data).

The 12 fixed meeting dates, selected previously for ecological
source-coverage assessment, are documented in the
[2026 cohort calendar](ecology-rq-2026-calendar-cohort-lock.md).
The project had observed only 0 strict Good/wet individual
reaction-norm units in the
[2026 multigoing audit](ecology-rq-real-h1-multigoing-expanded-audit.md).
This new question is **individual persistence independent of
varying ground**, not a rebranding of H1.

| Source filter | Actual count |
| --- | ---: |
| All original official-ID × positive first GPS interval candidates | 548 |
| Distinct recorded source races among positive candidates | 84 |
| Races with >=4 positive timed GPS observations | 74 |
| Horse × race positive GPS observations retained | 523 |
| Independent source meeting dates | 12 |
| Race conditions | Good, Soft, Heavy; includes a meeting whose races differ from the meeting-level ground description |

No race result or finishing place was used for the outcome, only the
published **initial GPS sectional time** in seconds. All records
with GPS all-zero/unknown/invalid segment values, ambiguous
same-day horse IDs/names or a race with <4 positive GPS
horses were excluded. **This filters GPS availability**, not the
biological population of all declared or actual starters, and
may be selectively missing.

## Estimand and calculation

For horse \`i\` in race \`r\`, the descriptive relative
initial sectional time is:

\`\`\`text
d_ir = observed_initial_segment_sec(i,r)
       - mean(observed_initial_segment_sec(j,r), j≠i)
\`\`\`

The *other timed GPS horses* define a contemporaneous peer
reference: negative \`d_ir\` = faster first segment compared with
the observed GPS subset, positive = slower. This is **not an
absolute focal speed** and changes mechanically when rivals
change their own sectional times. No H2 social effect is inferred
from it.

A horse-by-source-stratum is identified by the same original
HORSES ID, the same official race distance, the same exact first
measurement marker and optionally the same broad official
race Class. There must be >=2 distinct meeting dates. For
each eligible stratum \`g\`, average every distinct-date
product \`d_{g,r}d_{g,s}\`. Then average those stratum
products, giving each eligible horse-by-stratum **equal
weight**. Units are **seconds squared**. A positive
average can reflect stable individual early relative
timing, not directly an ICC (which requires variance
partitioning) or genetic/physiological stability.

The computational null shuffles \`d_ir\` values across horse IDs
**within each original race**, preserving each race's observed
distribution, field size and each horse's recorded meeting/class
assignment. Run **299** seeded shuffles. This is only a
software/descriptive randomization reference; actual race
entry is not random and the question was not preregistered.
The fraction of permutation reference values >= the observed
statistic is **not a defensible causal p-value**. Multiple
comparisons are exploratory.

## Results on actual Thoroughbreds

| Condition | Original horse IDs | Horse-by-strata | Paired observations | Observed equal-stratum mean pair product | Mean shuffled reference |
| --- | ---: | ---: | ---: | ---: | ---: |
| Same official race distance + first sectional marker | **99** | 105 | 209 | **+0.051925 s²** | +0.001735 s² |
| Plus matching original race class label | **50** | 53 | 81 | **+0.035633 s²** | +0.001136 s² |

The descriptive within-race ID-label shuffle reference gave:
- Distance + first-section marker: 5th/50th/95th
  quantiles **−0.015247 / +0.001821 / +0.017276 s²**,
  with fraction >= observed **1/300** (=0.00333).
- Plus class: 5th/50th/95th quantiles
  **−0.019987 / +0.001368 / +0.021503 s²**,
  with fraction >= observed **2/300** (=0.00667).

These tiny reference fractions are **algorithmic diagnostics,
NOT prespecified family-wise corrected inferential p-values**,
and cannot be interpreted as proof of physiology, evolved
animal personality or a social causal effect.

### Time-ordered retrospective sensitivity

Earlier source dates through **2026-08-22** supply past
horse profiles. Records from **2026-08-28 onwards** are
held out chronologically, without random horse-run row splits.

A simple horse-specific historical mean \`d_ir\`
uses *training-date profiles only*, with **fixed shrinkage
n/(n+2)**. Compare the later error to a baseline of
zero relative first-sectional time:

| Pairing gate | Later horse×race observations | Different source IDs | Zero-profile RMSE | Prior-horse-profile RMSE | Improvement |
| --- | ---: | ---: | ---: | ---: | ---: |
| Distance + first marker | 54 | 53 | 0.333181 s | 0.287796 s | **+0.045385 s** |
| Plus original class | 20 | 20 | 0.282634 s | 0.256963 s | **+0.025671 s** |

The **target** uses contemporaneous rivals' observed times
and is constructed *after* each race; only explanatory
horse profiles are strictly historical. This is a
retrospective persistence check, **not a real-time
betting model, not a blinded external cohort**, and the
fixed shrinkage rule has not been independently calibrated.
Uncertainty for the RMSE gain is not estimated here.

## Post-hoc field-coverage robustness (at least SIX positive GPS horses)

A **second, more restrictive selection after seeing the original
result** repeated the exact same original 12 dates but excluded
race groups with fewer than six positive first-section GPS times.
This is an **exploratory post-hoc sensitivity**, not an
independent hypothesis test or a replication with new horses.

Independently executed with the 12-source-date workflow:
[GitHub Actions #38349061899](https://github.com/zuizui0223/keiba/actions/runs/38349061899).

| Data/signal comparison | Main threshold >=4 GPS horses | Sensitivity >=6 GPS horses |
| --- | ---: | ---: |
| Retained original races | 74 | **55** |
| Horse×race positive GPS observations | 523 | **436** |
| Repeated official IDs in distance+first-marker strata | 99 | **75** |
| Equal-stratum pair cross-product (distance/marker) | +0.051925 s² | **+0.057802 s²** |
| Shuffled within-race ID reference mean | +0.001735 s² | **+0.000054 s²** |
| Repeated official IDs ALSO matched on race class | 50 | **37** |
| Equal-stratum pair cross-product (plus class) | +0.035633 s² | **+0.040590 s²** |
| Shuffled class-matched reference mean | +0.001136 s² | **−0.000083 s²** |

The descriptive positive concordance **did not disappear**
when excluding smaller observed GPS fields; however, this
subset was chosen after first observing a positive pattern,
so it cannot be called confirmatory replication.

### Temporal check after stricter field coverage

Using the same date split (train through 2026-08-22,
later dates from 2026-08-28):

| Condition and later held-out source rows | Null zero-relative-timing RMSE | Past-ID-profile RMSE | Reduction |
| --- | ---: | ---: | ---: |
| Distance + marker, 49 later rows | 0.338765 s | 0.286904 s | **0.051861 s** |
| Plus broad class, 18 later rows | 0.295268 s | 0.259955 s | **0.035313 s** |

This is a **retrospective timing-persistence outcome**:
even the target is relative to the *postrace observed*
GPS subset, so these numbers cannot be interpreted as
pre-race bets, causal social responses or absolute pace
predictions. Selection and measurement coverage differ
between the >=4 and >=6 filters. Multiple comparisons
and the time-split choice remain exploratory.

## Interpretation

**Supported as a limited descriptive data claim:** original
numeric HORSES IDs have more consistent relative first-sectional
times than expected under within-race reassignment of
identity labels for these observed source records; same-distance/
marker and class-matched subsets retain a positive signal.
Prior horse-level relative early timing also reduced
out-of-date retrospective prediction error in the same
fixed official source cohort.

**Still untested:** whether the persistence survives
*age, jockey/trainer, layoff, rail positions, finer race-class
restriction, recent condition, selection into races,
completion/measurement dropout or complete official starters*
in a fitted multilevel model. A race-level peer average
can change because of competition context even when the
focal horse's absolute speed is constant, so this result is
about **relative early performance consistency**, not
behavioral/social plasticity.

**No ground reaction-norm conclusion:** the strict
Good/non-Good matched Class/distance/marker replication
gate remains **0** in this original 12-date sample.
The new result does not overturn that absence of H1
identifiability or establish H2.

**No evolutionary or genetic claim:** managed racehorses
have nonrandom entry, training, jockey and breeding. This
does not estimate heritability, selection, innate animal
personality, or a wild ecological fitness trait.

A standard individual repeatability analysis should
eventually estimate the among-horse component in a
mixed-effects variance partition with adequate
race/horse clustered uncertainty and validated source
identity/censoring, consistent with Nakagawa & Schielzeth
(2010), [DOI 10.1111/j.1469-185X.2010.00141.x](https://doi.org/10.1111/j.1469-185X.2010.00141.x).

## Reproduction

[Source-linked calendar/H1 audit script](../scripts/ecology_rq_2026_calendar_overlap.py)
reuses its **in-memory** official HORSES-ID and GPS
first-section rows for
[\`ecology_rq_early_pace_repeatability.py\`](../scripts/ecology_rq_early_pace_repeatability.py):

\`\`\`bash
python scripts/ecology_rq_2026_calendar_overlap.py \\
  --output tmp/cannon-park-2026-12-dates.json

python -m unittest discover -s tests -p 'test_ecology_rq_early_pace_repeatability.py' -v
\`\`\`

CI [38348581714](https://github.com/zuizui0223/keiba/actions/runs/38348581714)
archived the summary as an **aggregate JSON artifact**.
All source-data rights and results limitations in the
[calendar protocol](ecology-rq-2026-calendar-cohort-lock.md)
still apply.

**Decision:** Report the positive real-data *early relative
pacing persistence* signal **only as exploratory and
context-dependent**; do not describe H1/H2 as supported.
